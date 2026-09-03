import json
import unicodedata
import urllib.parse
import urllib.request

from django.core.cache import cache
from django.db import transaction

from .models import Ilce, Mahalle

API_BASE = "https://api.turkiyeapi.dev/v2"
KOCAELI_PROVINCE_ID = 41
USER_AGENT = "ISU185-Staj-Projesi/3.0"

def _norm(value):
    value = (value or "").strip().casefold()
    value = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in value if not unicodedata.combining(ch))

def _get_json(url, timeout=15):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

def _district_id(ilce_adi):
    cache_key = f"isu185:turkiyeapi:district:{_norm(ilce_adi)}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    params = urllib.parse.urlencode({
        "provinceId": KOCAELI_PROVINCE_ID,
        "search": ilce_adi,
        "fields": "id,name",
        "sort": "name",
        "limit": 100,
    })
    payload = _get_json(f"{API_BASE}/districts?{params}")
    data = payload.get("data") or []

    wanted = _norm(ilce_adi)
    exact = next((x for x in data if _norm(x.get("name")) == wanted), None)
    if not exact:
        raise ValueError(f"Türkiye adres verisinde {ilce_adi} ilçesi bulunamadı.")

    district_id = int(exact["id"])
    cache.set(cache_key, district_id, 7 * 24 * 60 * 60)
    return district_id

def _display_name(raw):
    name = (raw or "").strip()
    if not name:
        return ""
    n = _norm(name)
    # Kaynak çoğunlukla yalnız mahalle adını verir. Kullanıcı ekranında açık olsun.
    if "mahalle" not in n:
        return f"{name} Mahallesi"
    return name

def sync_ilce_mahalleleri(ilce):
    """
    Seçilen Kocaeli ilçesinin gerçek mahalle listesini TurkiyeAPI'nin
    sürümlü idari veri setinden alır ve yerel DB'ye senkronlar.

    Başarılı senkron sonrası o ilçe için yalnız kaynakta bulunan mahalleler
    aktif kalır. Eski/demo/yanlış kayıtlar silinmez; geçmiş talepler bozulmasın
    diye yalnızca pasife alınır.
    """
    district_id = _district_id(ilce.ad)
    params = urllib.parse.urlencode({
        "fields": "id,name,postalCode,postalCodeStatus",
        "limit": 1000,
    })
    payload = _get_json(
        f"{API_BASE}/districts/{district_id}/neighborhoods?{params}",
        timeout=20,
    )
    remote = payload.get("data") or []
    if not remote:
        raise ValueError(f"{ilce.ad} için mahalle verisi boş döndü.")

    names = []
    seen = set()
    for item in remote:
        name = _display_name(item.get("name"))
        key = _norm(name)
        if not name or key in seen:
            continue
        seen.add(key)
        names.append(name)

    if not names:
        raise ValueError(f"{ilce.ad} için kullanılabilir mahalle bulunamadı.")

    with transaction.atomic():
        # Eski/demo kayıtları silmek yerine pasif bırak: mevcut talepler korunur.
        Mahalle.objects.filter(ilce=ilce).update(aktif=False)

        for name in names:
            # Daha önce farklı büyük/küçük harfle eklenmiş eşleşmeyi de yakala.
            existing = None
            for m in Mahalle.objects.filter(ilce=ilce):
                if _norm(m.ad) == _norm(name):
                    existing = m
                    break

            if existing:
                if existing.ad != name or not existing.aktif:
                    existing.ad = name
                    existing.aktif = True
                    existing.save(update_fields=["ad", "aktif"])
            else:
                Mahalle.objects.create(ilce=ilce, ad=name, aktif=True)

    meta = payload.get("meta") or {}
    return {
        "count": len(names),
        "datasetVersion": meta.get("datasetVersion"),
        "lastUpdated": meta.get("lastUpdated"),
    }

def sync_kocaeli_mahalleleri():
    results = []
    for ilce in Ilce.objects.filter(aktif=True).order_by("ad"):
        result = sync_ilce_mahalleleri(ilce)
        results.append((ilce.ad, result))
    return results
