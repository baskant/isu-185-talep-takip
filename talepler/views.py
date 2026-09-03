from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from .models import IsAltTuru, Talep
from .services import kullanici_talepleri, talep_erisim_var_mi


@login_required
def alt_turler(request):
    qs=IsAltTuru.objects.filter(
        is_turu_id=request.GET.get("is_turu"),
        aktif=True
    ).order_by("ad")
    return JsonResponse([{"id":x.id,"ad":x.ad} for x in qs],safe=False)


@login_required
def timeline(request,pk):
    talep=get_object_or_404(Talep,pk=pk)
    if not talep_erisim_var_mi(request.user,talep):
        return JsonResponse({"detail":"Yetkisiz."},status=403)

    return JsonResponse({"items":[{
        "tarih":g.tarih.strftime("%d.%m.%Y %H:%M"),
        "kullanici":(
            g.kullanici.get_full_name() or g.kullanici.username
        ) if g.kullanici else "Sistem",
        "mesaj":g.mesaj,
        "durum":g.durum,
        "sistem":g.sistem_mesaji
    } for g in talep.geri_bildirimler.all()[:50]]})


@login_required
def operasyon_ozet(request):
    """
    Kullanıcının yetkili olduğu taleplerin canlı durum özeti.
    Koordinatör, 185 ve sistem ekranlarında aynı merkezi durum bilgisi kullanılır.
    """
    qs = kullanici_talepleri(request.user).select_related(
        "ilce","mahalle","is_turu","is_alt_turu",
        "sorumlu_saha__kullanici","sorumlu_saha__rol"
    )

    field_states = [
        "sahaya_atandi","kabul_edildi","yolda","yerinde","islemde"
    ]
    active_states = field_states + ["onay_bekliyor"]

    items = []
    for t in qs.filter(durum__in=active_states).order_by("-guncellenme_tarihi")[:100]:
        last = t.geri_bildirimler.first()
        items.append({
            "id": t.id,
            "no": t.talep_no,
            "durum": t.durum,
            "durum_label": t.get_durum_display(),
            "oncelik": t.oncelik,
            "oncelik_label": t.get_oncelik_display(),
            "ilce": t.ilce.ad,
            "mahalle": t.mahalle.ad,
            "tur": t.is_turu.ad,
            "alt_tur": t.is_alt_turu.ad,
            "saha": (
                t.sorumlu_saha.kullanici.get_full_name()
                or t.sorumlu_saha.kullanici.username
            ) if t.sorumlu_saha else "-",
            "saha_rol": t.sorumlu_saha.rol.ad if t.sorumlu_saha else "-",
            "son_hareket": last.mesaj if last else "",
            "son_hareket_tarih": last.tarih.strftime("%H:%M") if last else "",
        })

    return JsonResponse({
        "counts": {
            "bekleyen": qs.filter(
                durum__in=["yeni","sefe_gonderildi"]
            ).count(),
            "sahada": qs.filter(durum__in=field_states).count(),
            "onay_bekleyen": qs.filter(durum="onay_bekliyor").count(),
            "tamam": qs.filter(durum="tamamlandi").count(),
            "geri_bildirim_bekleyen": qs.filter(
                durum="tamamlandi",
                vatandas_bildirim_durumu__in=["bekliyor","tekrar_aranacak"],
            ).count(),
            "acil": qs.filter(oncelik="acil").exclude(
                durum__in=["tamamlandi","iptal"]
            ).count(),
        },
        "items": items,
    })
