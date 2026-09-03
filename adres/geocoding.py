import json
import urllib.parse
import urllib.request

from django.core.cache import cache

NOMINATIM = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "ISU185-Staj-Projesi/6.0"

def _request_point(query, timeout=6):
    query = (query or "").strip()
    if not query:
        return None

    key = "isu185:geocode:" + query.casefold()
    cached = cache.get(key)
    if cached is not None:
        return cached or None

    url = NOMINATIM + "?" + urllib.parse.urlencode({
        "q": query,
        "format": "jsonv2",
        "limit": 1,
        "countrycodes": "tr",
    })
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception:
        data = []

    if data:
        result = {
            "lat": float(data[0]["lat"]),
            "lng": float(data[0]["lon"]),
            "display_name": data[0].get("display_name", query),
        }
        cache.set(key, result, 30 * 24 * 60 * 60)
        return result

    cache.set(key, {}, 6 * 60 * 60)
    return None

def _object_center(obj):
    if obj is None:
        return None
    lat = getattr(obj, "merkez_lat", None)
    lng = getattr(obj, "merkez_lng", None)
    if lat is None or lng is None:
        return None
    return float(lat), float(lng)

def talep_konumla(talep, *, force=False, save=True):
    """
    Talebin harita konumunu mümkün olduğunca gerçek adresten bulur.

    Öncelik:
      1. Zaten kullanıcı tarafından belirlenmiş koordinat (force=False)
      2. Tam yol/mahalle/ilçe adresi
      3. Mahalle merkezi için geocode
      4. Yol / mahalle / ilçe tablosundaki kayıtlı merkez
      5. Kocaeli merkezi

    Böylece hiçbir talep sistem haritasından kaybolmaz.
    """
    if not force and talep.lat is not None and talep.lng is not None:
        return {
            "lat": float(talep.lat),
            "lng": float(talep.lng),
            "source": "mevcut",
        }

    road = getattr(talep, "yol", None)
    neighborhood = getattr(talep, "mahalle", None)
    district = getattr(talep, "ilce", None)

    road_name = getattr(road, "ad", "") or ""
    neighborhood_name = getattr(neighborhood, "ad", "") or ""
    district_name = getattr(district, "ad", "") or ""

    exact_query = ", ".join(
        x for x in [
            talep.kapi_no,
            road_name,
            neighborhood_name,
            district_name,
            "Kocaeli",
            "Türkiye",
        ] if x
    )
    point = _request_point(exact_query)
    source = "adres"

    if not point and neighborhood_name:
        neighborhood_query = ", ".join(
            x for x in [neighborhood_name, district_name, "Kocaeli", "Türkiye"] if x
        )
        point = _request_point(neighborhood_query)
        source = "mahalle"

    if point:
        lat, lng = point["lat"], point["lng"]
    else:
        center = (
            _object_center(road)
            or _object_center(neighborhood)
            or _object_center(district)
            or (40.7656, 29.9408)
        )
        lat, lng = center
        source = "yerel_merkez"

    talep.lat = lat
    talep.lng = lng

    if save and talep.pk:
        talep.save(update_fields=["lat", "lng", "guncellenme_tarihi"])

    return {"lat": lat, "lng": lng, "source": source}
