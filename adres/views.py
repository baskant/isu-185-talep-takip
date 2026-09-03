import json
import urllib.parse
import urllib.request

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse

from .models import Ilce, Mahalle, Yol
from .realdata import sync_ilce_mahalleleri

NOMINATIM = "https://nominatim.openstreetmap.org/search"
OVERPASS = "https://overpass-api.de/api/interpreter"
USER_AGENT = "ISU185-Staj-Projesi/3.0"

def _http_json(url, *, data=None, timeout=18):
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    body = None
    if data is not None:
        body = urllib.parse.urlencode(data).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

def _find_osm_area(query):
    url = NOMINATIM + "?" + urllib.parse.urlencode({
        "q": query,
        "format": "jsonv2",
        "limit": 3,
        "countrycodes": "tr",
        "addressdetails": 1,
    })
    data = _http_json(url, timeout=10)
    if not data:
        return None
    item = next(
        (x for x in data if "kocaeli" in (x.get("display_name") or "").lower()),
        data[0]
    )
    osm_type = item.get("osm_type")
    osm_id = int(item.get("osm_id"))
    area_id = None
    if osm_type == "relation":
        area_id = 3600000000 + osm_id
    elif osm_type == "way":
        area_id = 2400000000 + osm_id
    bbox = item.get("boundingbox") or []
    if len(bbox) == 4:
        south, north, west, east = map(float, bbox)
        bbox = (south, west, north, east)
    else:
        bbox = None
    return {
        "area_id": area_id,
        "bbox": bbox,
        "lat": float(item["lat"]),
        "lng": float(item["lon"]),
    }

def _overpass_elements(query):
    return _http_json(OVERPASS, data={"data": query}, timeout=25).get("elements", [])

def _center(element):
    if "lat" in element and "lon" in element:
        return element["lat"], element["lon"]
    c = element.get("center") or {}
    return c.get("lat"), c.get("lon")

def _sync_yollar(mahalle):
    cache_key = f"isu185:osm:yol:{mahalle.pk}"
    if cache.get(cache_key):
        return

    loc = _find_osm_area(
        f"{mahalle.ad}, {mahalle.ilce.ad}, Kocaeli, Türkiye"
    )
    if not loc:
        cache.set(cache_key, True, 900)
        return

    if loc["area_id"]:
        scope = f"(area:{loc['area_id']})"
    elif loc["bbox"]:
        s, w, n, e = loc["bbox"]
        scope = f"({s},{w},{n},{e})"
    else:
        return

    query = f"""
    [out:json][timeout:22];
    way["highway"]["name"]{scope};
    out center tags;
    """
    try:
        elements = _overpass_elements(query)
    except Exception:
        cache.set(cache_key, True, 300)
        return

    tur_map = {
        "street": "sokak",
        "residential": "sokak",
        "living_street": "sokak",
        "service": "sokak",
        "primary": "cadde",
        "secondary": "cadde",
        "tertiary": "cadde",
        "trunk": "bulvar",
    }

    seen = set()
    for el in elements:
        tags = el.get("tags") or {}
        name = (tags.get("name") or "").strip()
        if not name or name.casefold() in seen:
            continue
        seen.add(name.casefold())

        highway = tags.get("highway") or ""
        tur = tur_map.get(highway, "diger")
        lower = name.casefold()
        if "bulvar" in lower:
            tur = "bulvar"
        elif "cadde" in lower or "caddesi" in lower:
            tur = "cadde"
        elif "sokak" in lower or "sokağı" in lower or "sokagi" in lower:
            tur = "sokak"

        lat, lng = _center(el)
        defaults = {"aktif": True, "tur": tur}
        if lat is not None:
            defaults["merkez_lat"] = lat
        if lng is not None:
            defaults["merkez_lng"] = lng
        Yol.objects.get_or_create(
            mahalle=mahalle,
            ad=name,
            defaults=defaults,
        )

    cache.set(cache_key, True, 24 * 60 * 60)

@login_required
def mahalleler(request):
    ilce = Ilce.objects.filter(
        pk=request.GET.get("ilce"),
        aktif=True
    ).first()
    if not ilce:
        return JsonResponse([], safe=False)

    # Her ilçe seçildiğinde güncel kaynak senkronu en fazla 24 saatte bir yapılır.
    sync_key = f"isu185:trusted:mahalle:{ilce.pk}"
    source_info = None
    if not cache.get(sync_key):
        try:
            source_info = sync_ilce_mahalleleri(ilce)
            cache.set(sync_key, source_info, 24 * 60 * 60)
        except Exception as exc:
            # İnternet/API geçici olarak yoksa daha önce senkronlanmış yerel veriyle devam et.
            if not Mahalle.objects.filter(ilce=ilce, aktif=True).exists():
                return JsonResponse({
                    "items": [],
                    "source": "unavailable",
                    "message": "Güncel mahalle veri servisine şu anda ulaşılamadı. Tekrar deneyin."
                }, status=503)

    qs = Mahalle.objects.filter(ilce=ilce, aktif=True).order_by("ad")
    info = source_info or cache.get(sync_key) or {}
    return JsonResponse({
        "items": [
            {
                "id": x.id,
                "ad": x.ad,
                "lat": x.merkez_lat,
                "lng": x.merkez_lng,
            }
            for x in qs
        ],
        "source": "TurkiyeAPI 2025",
        "datasetVersion": info.get("datasetVersion"),
        "lastUpdated": info.get("lastUpdated"),
    })

@login_required
def yollar(request):
    mahalle = Mahalle.objects.select_related("ilce").filter(
        pk=request.GET.get("mahalle"),
        aktif=True
    ).first()
    if not mahalle:
        return JsonResponse([], safe=False)

    if Yol.objects.filter(mahalle=mahalle, aktif=True).count() < 3:
        try:
            _sync_yollar(mahalle)
        except Exception:
            pass

    qs = Yol.objects.filter(mahalle=mahalle, aktif=True).order_by("ad")
    return JsonResponse([
        {
            "id": x.id,
            "ad": x.ad,
            "tur": x.tur,
            "lat": x.merkez_lat,
            "lng": x.merkez_lng,
        }
        for x in qs
    ], safe=False)

@login_required
def ilce_detay(request):
    x = Ilce.objects.filter(pk=request.GET.get("ilce"), aktif=True).first()
    if not x:
        return JsonResponse({}, status=404)
    return JsonResponse({
        "id": x.id,
        "ad": x.ad,
        "lat": x.merkez_lat,
        "lng": x.merkez_lng,
    })

@login_required
def geocode(request):
    ilce = (request.GET.get("ilce") or "").strip()
    mahalle = (request.GET.get("mahalle") or "").strip()
    yol = (request.GET.get("yol") or "").strip()
    kapi = (request.GET.get("kapi") or "").strip()

    if not ilce:
        return JsonResponse(
            {"ok": False, "message": "İlçe seçilmedi."},
            status=400
        )

    q = ", ".join([
        x for x in [kapi, yol, mahalle, ilce, "Kocaeli", "Türkiye"] if x
    ])
    cache_key = "geo:" + q.lower()
    cached = cache.get(cache_key)
    if cached:
        return JsonResponse(cached)

    url = NOMINATIM + "?" + urllib.parse.urlencode({
        "q": q,
        "format": "jsonv2",
        "limit": 1,
        "countrycodes": "tr",
    })
    try:
        data = _http_json(url, timeout=10)
        if not data:
            result = {"ok": False, "message": "Adres haritada bulunamadı."}
        else:
            result = {
                "ok": True,
                "lat": float(data[0]["lat"]),
                "lng": float(data[0]["lon"]),
                "display_name": data[0].get("display_name", q),
            }
        cache.set(cache_key, result, 60 * 60)
        return JsonResponse(result)
    except Exception:
        return JsonResponse({
            "ok": False,
            "message": "Harita adres servisine ulaşılamadı. Konumu haritadan seçebilirsiniz.",
        }, status=503)
