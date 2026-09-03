import csv
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from dashboard.permissions import get_profile, panel_required
from .forms import AmbarKayitForm, DevirBasvuruForm
from .models import AbonelikKaydi, DevirBasvurusu, DevirHareketi
from abonelik.models import Ambar, AmbarHareketi, AmbarYetkisi, SayacEnvanteri


def _hareket(basvuru, user, islem, aciklama="", onceki="", yeni=""):
    return DevirHareketi.objects.create(
        basvuru=basvuru,
        kullanici=user if getattr(user, "is_authenticated", False) else None,
        islem=islem,
        aciklama=aciklama,
        onceki_durum=onceki,
        yeni_durum=yeni,
    )


def _operasyon_profili(request, tip):
    if request.user.is_superuser:
        raise PermissionDenied("Sistem yöneticisi bu operasyonu yapamaz; yalnızca izleme yetkisine sahiptir.")
    p = get_profile(request.user)
    if not p or not p.aktif or p.rol.panel_tipi != tip:
        raise PermissionDenied("Bu işlem için uygun rolünüz bulunmuyor.")
    return p


def _ambar_operasyon_profili(request):
    """V54: Yerel ambar işlemini eski ambar hesabı veya ilçenin ambar yetkili şefi yapabilir."""
    if request.user.is_superuser:
        raise PermissionDenied("Sistem yöneticisi ambar operasyonu yapamaz; izleme yetkisine sahiptir.")
    p = get_profile(request.user)
    if not p or not p.aktif:
        raise PermissionDenied("Aktif personel profili bulunamadı.")
    if p.rol.panel_tipi == "ambar":
        return p, None
    if p.rol.panel_tipi == "sef":
        yetki = AmbarYetkisi.objects.select_related("ilce", "ambar").filter(personel=p, aktif=True).first()
        if yetki:
            return p, yetki
    raise PermissionDenied("Bu kullanıcı yerel ambar işlemlerine yetkili değil.")


def _devir_sayacini_ambarda_esitle(basvuru, hedef_ambar, durum, kullanici, aciklama):
    if not basvuru.sayac_seri_no or not hedef_ambar:
        return None
    # Sayaç numarası ve üretici seri numarası ayrı alanlardır. Devirden ilk kez
    # envantere giren sayaç için iç sistem sayaç numarası ayrıca üretilir.
    sayac_no = f"DV-SYC-{basvuru.pk:06d}"
    sayac, _ = SayacEnvanteri.objects.get_or_create(
        seri_no=basvuru.sayac_seri_no,
        defaults={
            "sayac_no": sayac_no,
            "marka_model": basvuru.sayac_marka_model or "",
            "son_endeks": basvuru.sayac_endeks,
            "durum": durum,
            "ambar": hedef_ambar,
            "aktif": durum not in ("kullanim_disi", "hurda"),
        },
    )
    kaynak = sayac.ambar
    sayac.ambar = hedef_ambar
    sayac.durum = durum
    if basvuru.sayac_marka_model and not sayac.marka_model:
        sayac.marka_model = basvuru.sayac_marka_model
    if basvuru.sayac_endeks is not None:
        sayac.son_endeks = basvuru.sayac_endeks
    sayac.save()
    AmbarHareketi.objects.create(
        sayac=sayac, kaynak_ambar=kaynak, hedef_ambar=hedef_ambar,
        islem="teslim" if durum == "kontrol_bekliyor" else "sevk",
        kullanici=kullanici, aciklama=aciklama,
    )
    return sayac



@login_required
def panel_yonlendir(request):
    if request.user.is_superuser:
        return redirect("devirambar:sistem")
    p = get_profile(request.user)
    if not p:
        raise PermissionDenied("Personel profili bulunamadı.")
    if p.rol.panel_tipi == "devir":
        return redirect("devirambar:devir_paneli")
    if p.rol.panel_tipi == "ambar":
        return redirect("devirambar:ambar_paneli")
    if p.rol.panel_tipi == "merkez_ambar":
        return redirect("devirambar:merkez_ambar_paneli")
    if p.rol.panel_tipi == "sef" and AmbarYetkisi.objects.filter(personel=p, aktif=True).exists():
        return redirect("devirambar:ambar_paneli")
    raise PermissionDenied("Bu modül için yetkiniz bulunmuyor.")


@panel_required("devir")
def devir_paneli(request):
    _operasyon_profili(request, "devir")
    secili_abonelik = None
    abonelik_sorgu = (request.GET.get("abonelik_sorgu") or "").strip()

    if request.method == "POST":
        form = DevirBasvuruForm(request.POST)
        abonelik_id = (request.POST.get("eski_abonelik_id") or "").strip()
        if abonelik_id:
            secili_abonelik = AbonelikKaydi.objects.filter(pk=abonelik_id, aktif=True).first()

        if not secili_abonelik:
            messages.error(request, "Önce aktif bir mevcut aboneliği sorgulayıp seçmelisiniz.")
        elif form.is_valid():
            with transaction.atomic():
                eski = get_object_or_404(
                    AbonelikKaydi.objects.select_for_update(),
                    pk=secili_abonelik.pk,
                    aktif=True,
                )
                yeni_no = AbonelikKaydi.yeni_abone_no_uret()

                # Yeni abone numarası sistem tarafından oluşturulur. Eski sayaç ise
                # devir/ambar akışına çıktığı için yeni aktif aboneliğe otomatik bağlanmaz.
                yeni_abonelik = AbonelikKaydi.objects.create(
                    abone_no=yeni_no,
                    abone_ad_soyad=form.cleaned_data["vatandas_ad_soyad"],
                    telefon=form.cleaned_data["telefon"],
                    tc_kimlik_no=form.cleaned_data.get("tc_kimlik_no", ""),
                    ilce=eski.ilce,
                    adres=eski.adres,
                    sayac_seri_no="",
                    sayac_marka_model="",
                    sayac_endeks=None,
                    aktif=True,
                    onceki_abonelik=eski,
                )

                basvuru = form.save(commit=False)
                basvuru.olusturan = request.user
                basvuru.eski_abonelik = eski
                basvuru.yeni_abonelik = yeni_abonelik
                basvuru.eski_abone_no = eski.abone_no
                basvuru.eski_abone_ad_soyad = eski.abone_ad_soyad
                basvuru.yeni_abone_no = yeni_no
                basvuru.ilce = eski.ilce
                basvuru.adres = eski.adres
                basvuru.sayac_seri_no = eski.sayac_seri_no
                basvuru.sayac_marka_model = eski.sayac_marka_model
                basvuru.sayac_endeks = eski.sayac_endeks
                basvuru.save()

                eski.aktif = False
                eski.kapanis_tarihi = timezone.now()
                eski.save(update_fields=["aktif", "kapanis_tarihi"])

                _hareket(
                    basvuru,
                    request.user,
                    "Abonelik devri oluşturuldu",
                    f"Eski abonelik {eski.abone_no} kapatıldı; yeni abonelik {yeni_no} sistem tarafından oluşturuldu.",
                    "",
                    basvuru.durum,
                )
            messages.success(
                request,
                f"{basvuru.basvuru_no} oluşturuldu. Yeni Abone No: {basvuru.yeni_abone_no}",
            )
            return redirect("devirambar:devir_paneli")
    else:
        form = DevirBasvuruForm()
        if abonelik_sorgu:
            secili_abonelik = (
                AbonelikKaydi.objects.filter(aktif=True)
                .filter(Q(abone_no__iexact=abonelik_sorgu) | Q(sayac_seri_no__iexact=abonelik_sorgu))
                .first()
            )
            if not secili_abonelik:
                messages.warning(request, "Aktif abonelik bulunamadı. Abone No veya Sayaç Seri No bilgisini kontrol edin.")

    kayitlar = DevirBasvurusu.objects.select_related(
        "olusturan", "ambara_gonderen", "eski_abonelik", "yeni_abonelik"
    ).all()[:80]
    ozet = {
        "hazirlaniyor": DevirBasvurusu.objects.filter(durum="hazirlaniyor").count(),
        "ambara_gonderildi": DevirBasvurusu.objects.filter(durum="ambara_gonderildi").count(),
        "ambarda": DevirBasvurusu.objects.filter(durum__in=["teslim_alindi", "kontrol_edildi", "merkez_ambara_gonderildi", "merkez_teslim_alindi", "merkez_kontrol_edildi"]).count(),
        "tamam": DevirBasvurusu.objects.filter(durum__in=["ambara_kaydedildi", "merkez_ambara_kaydedildi"]).count(),
    }
    return render(request, "devirambar/devir_paneli.html", {
        "form": form,
        "kayitlar": kayitlar,
        "ozet": ozet,
        "secili_abonelik": secili_abonelik,
        "abonelik_sorgu": abonelik_sorgu,
    })


@panel_required("devir")
@require_POST
def ambara_gonder(request, pk):
    _operasyon_profili(request, "devir")
    with transaction.atomic():
        basvuru = get_object_or_404(DevirBasvurusu.objects.select_for_update(), pk=pk)
        if basvuru.durum != "hazirlaniyor":
            messages.warning(request, "Bu sayaç daha önce ambar sürecine gönderilmiş.")
            return redirect("devirambar:devir_paneli")

        eksikler = basvuru.eksik_zorunlu_alanlar()
        if eksikler:
            messages.error(
                request,
                "Başvuru ambar kuyruğuna gönderilemez. Eksik zorunlu alanlar: " + ", ".join(eksikler) + ".",
            )
            return redirect("devirambar:devir_paneli")

        onceki = basvuru.durum
        basvuru.durum = "ambara_gonderildi"
        basvuru.ambara_gonderen = request.user
        basvuru.ambara_gonderim_tarihi = timezone.now()
        basvuru.save(update_fields=["durum", "ambara_gonderen", "ambara_gonderim_tarihi", "guncellenme_tarihi"])
        _hareket(
            basvuru, request.user, "Sayaç ambara gönderildi",
            f"{basvuru.sayac_seri_no} seri numaralı sayaç ambar teslim kuyruğuna aktarıldı.",
            onceki, basvuru.durum,
        )
    messages.success(request, f"{basvuru.basvuru_no}: sayaç ambar kuyruğuna gönderildi.")
    return redirect("devirambar:devir_paneli")


@login_required
def ambar_paneli(request):
    profil, ambar_yetkisi = _ambar_operasyon_profili(request)
    bekleyen = DevirBasvurusu.objects.filter(
        durum__in=["ambara_gonderildi", "teslim_alindi", "kontrol_edildi"]
    ).select_related("olusturan", "ambara_gonderen", "teslim_alan", "kontrol_eden").order_by("ambara_gonderim_tarihi")
    sevk_edilen = DevirBasvurusu.objects.filter(
        durum__in=["merkez_ambara_gonderildi", "merkez_teslim_alindi", "merkez_kontrol_edildi", "merkez_ambara_kaydedildi"]
    ).select_related("merkeze_gonderen")
    if ambar_yetkisi:
        bekleyen = bekleyen.filter(ilce=ambar_yetkisi.ilce.ad)
        sevk_edilen = sevk_edilen.filter(ilce=ambar_yetkisi.ilce.ad)
    ozet = {
        "teslim_bekleyen": bekleyen.filter(durum="ambara_gonderildi").count(),
        "kontrol_bekleyen": bekleyen.filter(durum="teslim_alindi").count(),
        "merkez_sevk_bekleyen": bekleyen.filter(durum="kontrol_edildi").count(),
        "merkeze_gonderilen": sevk_edilen.count() if hasattr(sevk_edilen, "count") else len(sevk_edilen),
    }
    sevk_edilen = sevk_edilen[:40]
    return render(request, "devirambar/ambar_paneli.html", {
        "bekleyen": bekleyen, "sevk_edilen": sevk_edilen, "ozet": ozet,
        "profil": profil, "ambar_yetkisi": ambar_yetkisi,
    })


@login_required
@require_POST
def ambar_durum(request, pk, aksiyon):
    profil, ambar_yetkisi = _ambar_operasyon_profili(request)
    with transaction.atomic():
        basvuru = get_object_or_404(DevirBasvurusu.objects.select_for_update(), pk=pk)
        if ambar_yetkisi and basvuru.ilce != ambar_yetkisi.ilce.ad:
            raise PermissionDenied("Bu sayaç başka ilçenin ambar sürecine aittir.")
        now = timezone.now()
        onceki = basvuru.durum

        if aksiyon == "teslim-al":
            if basvuru.durum != "ambara_gonderildi":
                messages.warning(request, "Bu sayaç teslim alma aşamasında değil.")
                return redirect("devirambar:ambar_paneli")
            basvuru.durum = "teslim_alindi"
            basvuru.teslim_alan = request.user
            basvuru.teslim_tarihi = now
            alanlar = ["durum", "teslim_alan", "teslim_tarihi", "guncellenme_tarihi"]
            islem = "Sayaç yerel ambarda teslim alındı"
            aciklama = "Sayaç fiziksel olarak yerel ambar/depo personeli tarafından teslim alındı."

        elif aksiyon == "kontrol-et":
            if basvuru.durum != "teslim_alindi":
                messages.warning(request, "Önce sayacı teslim almalısınız.")
                return redirect("devirambar:ambar_paneli")
            basvuru.durum = "kontrol_edildi"
            basvuru.kontrol_eden = request.user
            basvuru.kontrol_tarihi = now
            alanlar = ["durum", "kontrol_eden", "kontrol_tarihi", "guncellenme_tarihi"]
            islem = "Sayaç yerel ambarda kontrol edildi"
            aciklama = "Sayaç seri numarası ve fiziksel durumu merkez ambar sevki öncesinde kontrol edildi."

        elif aksiyon == "merkeze-gonder":
            if basvuru.durum != "kontrol_edildi":
                messages.warning(request, "Merkez ambara göndermeden önce sayaç kontrolünü tamamlamalısınız.")
                return redirect("devirambar:ambar_paneli")
            basvuru.durum = "merkez_ambara_gonderildi"
            basvuru.merkeze_gonderen = request.user
            basvuru.merkeze_gonderim_tarihi = now
            alanlar = ["durum", "merkeze_gonderen", "merkeze_gonderim_tarihi", "guncellenme_tarihi"]
            islem = "Sayaç merkez ambara gönderildi"
            aciklama = "Yerel ambar kontrolü tamamlanan sayaç Merkez Ambar teslim kuyruğuna sevk edildi."
        else:
            raise PermissionDenied("Geçersiz ambar işlemi.")

        basvuru.save(update_fields=alanlar)
        _hareket(basvuru, request.user, islem, aciklama, onceki, basvuru.durum)
        if aksiyon == "teslim-al":
            yerel = ambar_yetkisi.ambar if ambar_yetkisi else Ambar.objects.filter(tur="ilce", ilce__ad=basvuru.ilce, aktif=True).first()
            _devir_sayacini_ambarda_esitle(
                basvuru, yerel, "kontrol_bekliyor", request.user,
                f"{basvuru.basvuru_no} devir kaydından yerel ambara teslim alındı."
            )
        elif aksiyon == "merkeze-gonder":
            merkez = Ambar.objects.filter(tur="merkez", aktif=True).first()
            _devir_sayacini_ambarda_esitle(
                basvuru, merkez, "kontrol_bekliyor", request.user,
                f"{basvuru.basvuru_no} yerel ambardan Merkez Ambara sevk edildi."
            )

    messages.success(request, f"{basvuru.basvuru_no}: {islem}.")
    return redirect("devirambar:ambar_paneli")


@panel_required("merkez_ambar")
def merkez_ambar_paneli(request):
    _operasyon_profili(request, "merkez_ambar")
    bekleyen = DevirBasvurusu.objects.filter(
        durum__in=["merkez_ambara_gonderildi", "merkez_teslim_alindi", "merkez_kontrol_edildi"]
    ).select_related("merkeze_gonderen", "merkez_teslim_alan", "merkez_kontrol_eden").order_by("merkeze_gonderim_tarihi")
    kapanan = DevirBasvurusu.objects.filter(durum="merkez_ambara_kaydedildi").select_related("merkez_ambara_kaydeden")[:50]
    ozet = {
        "teslim_bekleyen": bekleyen.filter(durum="merkez_ambara_gonderildi").count(),
        "kontrol_bekleyen": bekleyen.filter(durum="merkez_teslim_alindi").count(),
        "kayit_bekleyen": bekleyen.filter(durum="merkez_kontrol_edildi").count(),
        "bugun": DevirBasvurusu.objects.filter(durum="merkez_ambara_kaydedildi", merkez_ambar_kayit_tarihi__date=timezone.localdate()).count(),
    }
    return render(request, "devirambar/merkez_ambar_paneli.html", {
        "bekleyen": bekleyen, "kapanan": kapanan, "ozet": ozet, "ambar_form": AmbarKayitForm(),
    })


@panel_required("merkez_ambar")
@require_POST
def merkez_ambar_durum(request, pk, aksiyon):
    _operasyon_profili(request, "merkez_ambar")
    with transaction.atomic():
        basvuru = get_object_or_404(DevirBasvurusu.objects.select_for_update(), pk=pk)
        now = timezone.now()
        onceki = basvuru.durum

        if aksiyon == "teslim-al":
            if basvuru.durum != "merkez_ambara_gonderildi":
                messages.warning(request, "Bu sayaç merkez ambar teslim aşamasında değil.")
                return redirect("devirambar:merkez_ambar_paneli")
            basvuru.durum = "merkez_teslim_alindi"
            basvuru.merkez_teslim_alan = request.user
            basvuru.merkez_teslim_tarihi = now
            alanlar = ["durum", "merkez_teslim_alan", "merkez_teslim_tarihi", "guncellenme_tarihi"]
            islem = "Merkez ambar sayacı teslim aldı"
            aciklama = "Sayaç Merkez Ambar personeli tarafından fiziksel olarak teslim alındı."

        elif aksiyon == "kontrol-et":
            if basvuru.durum != "merkez_teslim_alindi":
                messages.warning(request, "Önce merkez ambar teslim işlemini yapmalısınız.")
                return redirect("devirambar:merkez_ambar_paneli")
            basvuru.durum = "merkez_kontrol_edildi"
            basvuru.merkez_kontrol_eden = request.user
            basvuru.merkez_kontrol_tarihi = now
            alanlar = ["durum", "merkez_kontrol_eden", "merkez_kontrol_tarihi", "guncellenme_tarihi"]
            islem = "Merkez ambar sayacı kontrol etti"
            aciklama = "Sayaç seri numarası ve fiziksel durumu merkez depoya kayıt öncesinde kontrol edildi."

        elif aksiyon == "ambara-kaydet":
            if basvuru.durum != "merkez_kontrol_edildi":
                messages.warning(request, "Önce merkez ambar kontrolünü tamamlamalısınız.")
                return redirect("devirambar:merkez_ambar_paneli")
            form = AmbarKayitForm(request.POST)
            if not form.is_valid():
                messages.error(request, "Merkez depo / raf konumu zorunludur.")
                return redirect("devirambar:merkez_ambar_paneli")
            basvuru.durum = "merkez_ambara_kaydedildi"
            basvuru.merkez_ambara_kaydeden = request.user
            basvuru.merkez_ambar_kayit_tarihi = now
            basvuru.merkez_depo_konumu = form.cleaned_data["depo_konumu"]
            basvuru.merkez_ambar_notu = form.cleaned_data.get("ambar_notu", "")
            alanlar = ["durum", "merkez_ambara_kaydeden", "merkez_ambar_kayit_tarihi", "merkez_depo_konumu", "merkez_ambar_notu", "guncellenme_tarihi"]
            islem = "Sayaç merkez ambara kaydedildi"
            aciklama = f"Merkez depo konumu: {basvuru.merkez_depo_konumu}." + (f" Not: {basvuru.merkez_ambar_notu}" if basvuru.merkez_ambar_notu else "")
        else:
            raise PermissionDenied("Geçersiz merkez ambar işlemi.")

        basvuru.save(update_fields=alanlar)
        _hareket(basvuru, request.user, islem, aciklama, onceki, basvuru.durum)
        if aksiyon == "ambara-kaydet":
            merkez = Ambar.objects.filter(tur="merkez", aktif=True).first()
            _devir_sayacini_ambarda_esitle(
                basvuru, merkez, "stokta", request.user,
                f"{basvuru.basvuru_no} Merkez Ambar kayıt işlemi tamamlandı. Konum: {basvuru.merkez_depo_konumu}"
            )

    messages.success(request, f"{basvuru.basvuru_no}: {islem}.")
    return redirect("devirambar:merkez_ambar_paneli")


@panel_required("admin")
def sistem_devir_ambar(request):
    qs = DevirBasvurusu.objects.select_related(
        "olusturan", "ambara_gonderen", "teslim_alan", "kontrol_eden", "ambara_kaydeden",
        "merkeze_gonderen", "merkez_teslim_alan", "merkez_kontrol_eden", "merkez_ambara_kaydeden",
        "eski_abonelik", "yeni_abonelik"
    )
    durum = (request.GET.get("durum") or "").strip()
    ilce = (request.GET.get("ilce") or "").strip()
    q = (request.GET.get("q") or "").strip()
    if durum:
        qs = qs.filter(durum=durum)
    if ilce:
        qs = qs.filter(ilce=ilce)
    if q:
        qs = qs.filter(
            Q(basvuru_no__icontains=q) | Q(vatandas_ad_soyad__icontains=q) |
            Q(sayac_seri_no__icontains=q) | Q(eski_abone_no__icontains=q) | Q(yeni_abone_no__icontains=q)
        )
    durum_sayilari = {x["durum"]: x["adet"] for x in DevirBasvurusu.objects.values("durum").annotate(adet=Count("id"))}
    hareketler = DevirHareketi.objects.select_related("basvuru", "kullanici")[:30]
    return render(request, "devirambar/sistem_devir_ambar.html", {
        "kayitlar": qs[:300], "hareketler": hareketler, "durum_sayilari": durum_sayilari,
        "durumlar": DevirBasvurusu.DURUMLAR, "ilceler": sorted(set(DevirBasvurusu.objects.values_list("ilce", flat=True))),
        "secili_durum": durum, "secili_ilce": ilce, "q": q,
        "toplam_kayit": DevirBasvurusu.objects.count(),
        "aktif_abonelik": AbonelikKaydi.objects.filter(aktif=True).count(),
        "aktif_baslangic": durum_sayilari.get("hazirlaniyor", 0) + durum_sayilari.get("ambara_gonderildi", 0),
        "ambar_islemde": durum_sayilari.get("teslim_alindi", 0) + durum_sayilari.get("kontrol_edildi", 0),
        "merkez_islemde": durum_sayilari.get("merkez_ambara_gonderildi", 0) + durum_sayilari.get("merkez_teslim_alindi", 0) + durum_sayilari.get("merkez_kontrol_edildi", 0),
    })


@panel_required("admin")
def sistem_csv(request):
    qs = DevirBasvurusu.objects.select_related("olusturan", "ambara_gonderen", "teslim_alan", "ambara_kaydeden").all()
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="isu_devir_ambar_raporu.csv"'
    response.write("\ufeff")
    w = csv.writer(response, delimiter=";")
    w.writerow(["Başvuru No", "Tarih", "Vatandaş", "Telefon", "İlçe", "Sayaç Seri No", "Eski Abone", "Yeni Abone", "Durum", "Yerel Gönderim", "Yerel Teslim", "Merkez Gönderim", "Merkez Teslim", "Merkez Depo Konumu"])
    for x in qs:
        w.writerow([
            x.basvuru_no, timezone.localtime(x.olusturulma_tarihi).strftime("%d.%m.%Y %H:%M"),
            x.vatandas_ad_soyad, x.telefon, x.ilce, x.sayac_seri_no, x.eski_abone_no, x.yeni_abone_no,
            x.get_durum_display(),
            timezone.localtime(x.ambara_gonderim_tarihi).strftime("%d.%m.%Y %H:%M") if x.ambara_gonderim_tarihi else "",
            timezone.localtime(x.teslim_tarihi).strftime("%d.%m.%Y %H:%M") if x.teslim_tarihi else "",
            timezone.localtime(x.merkeze_gonderim_tarihi).strftime("%d.%m.%Y %H:%M") if x.merkeze_gonderim_tarihi else "",
            timezone.localtime(x.merkez_teslim_tarihi).strftime("%d.%m.%Y %H:%M") if x.merkez_teslim_tarihi else "",
            x.merkez_depo_konumu or x.depo_konumu,
        ])
    return response
