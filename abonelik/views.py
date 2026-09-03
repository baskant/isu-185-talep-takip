from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from dashboard.permissions import get_profile
from .forms import (
    AmbarSayacTalepForm,
    IletisimForm,
    MerkezStokGirisForm,
    SayacAtamaForm,
    SozlesmeForm,
    VatandasSicilForm,
)
from .models import (
    AboneSayac,
    Ambar,
    AmbarHareketi,
    AmbarSayacTalebi,
    AmbarYetkisi,
    HizmetAdresi,
    SayacEnvanteri,
    Sozlesme,
    VatandasIletisim,
    VatandasSicili,
)


def _form_error_ozeti(form):
    """Kullanıcıya teknik olmayan, kısa ama alan bazlı doğrulama özeti üretir."""
    hatalar = []
    for alan, alan_hatalari in form.errors.items():
        if alan == "__all__":
            etiket = "Form"
        else:
            etiket = form.fields.get(alan).label if alan in form.fields else alan
        for hata in alan_hatalari:
            hatalar.append(f"{etiket}: {hata}")
    return " | ".join(hatalar[:4])


def _abone_web_role(rol):
    if not rol:
        return False
    kod = (rol.kod or "").casefold().replace("_", "-")
    ad = (rol.ad or "").casefold()
    return kod in {"abone-sayac-saha", "sayac-abone-saha"} or (("sayaç" in ad or "sayac" in ad) and "abone" in ad)


def _abone_erisim(request):
    if request.user.is_superuser:
        return None
    p = get_profile(request.user)
    if not p or not p.aktif or p.rol.panel_tipi != "abone" or not _abone_web_role(p.rol):
        raise PermissionDenied("Bu ekran yalnız Abone Personeline aittir.")
    return p


def _yetkili_ilce_ids(profil):
    if profil is None:
        return None
    return list(profil.yetkili_ilceler.values_list("id", flat=True))


def _sicil_qs_for_profile(profil):
    """Abone personeli yalnız yetkili ilçesindeki veya kendisinin yeni oluşturduğu sicili görür."""
    qs = VatandasSicili.objects.all()
    ilce_ids = _yetkili_ilce_ids(profil)
    if ilce_ids is None:
        return qs
    return qs.filter(
        Q(sozlesmeler__adres__ilce_id__in=ilce_ids)
        | Q(sozlesmeler__isnull=True, olusturan=profil.kullanici)
    ).distinct()


def _ambar_erisim(request):
    """V56: Yerel ambarı yalnız ambar yetkili şef, merkez ambarı merkez personeli yönetir."""
    if request.user.is_superuser:
        return None, "merkez"
    p = get_profile(request.user)
    if not p or not p.aktif:
        raise PermissionDenied("Aktif personel profili bulunamadı.")
    if p.rol.panel_tipi == "merkez_ambar":
        return None, "merkez"
    if p.rol.panel_tipi == "sef":
        yetki = AmbarYetkisi.objects.select_related("ilce", "ambar", "personel__kullanici").filter(personel=p, aktif=True).first()
        if not yetki:
            raise PermissionDenied("Bu şef/koordinatöre ambar sorumluluğu tanımlanmamış.")
        return yetki, "ilce"
    raise PermissionDenied("Ambar yönetimi yalnız ambar yetkili şef/koordinatör veya Merkez Ambar personeline aittir.")




def _stok_sayaclari_for_sozlesme(sozlesme):
    """Sözleşmenin ilçesindeki yerel ambarda takılmaya hazır sayaçlar."""
    return SayacEnvanteri.objects.select_related("ambar").filter(
        ambar__tur="ilce",
        ambar__ilce=sozlesme.adres.ilce,
        ambar__aktif=True,
        durum="stokta",
        aktif=True,
    ).order_by("sayac_tipi", "cap_mm", "sayac_no")

def _sozlesme_qs_for_profile(profil):
    qs = Sozlesme.objects.select_related("sicil", "adres", "adres__ilce").prefetch_related(
        "sayac_baglantilari__sayac", "sicil__iletisim_kayitlari"
    )
    ilce_ids = _yetkili_ilce_ids(profil)
    if ilce_ids is not None:
        qs = qs.filter(adres__ilce_id__in=ilce_ids)
    return qs


@login_required
def izleme(request):
    profil = _abone_erisim(request)
    q = (request.GET.get("q") or "").strip()
    durum = (request.GET.get("durum") or "tumu").strip()
    abonelik_turu = (request.GET.get("tur") or "").strip()
    sozlesme_id = request.GET.get("sozlesme")
    qs = _sozlesme_qs_for_profile(profil)

    if durum == "aktif":
        qs = qs.filter(aktif=True)
    elif durum == "pasif":
        qs = qs.filter(aktif=False)

    if abonelik_turu:
        qs = qs.filter(abonelik_turu=abonelik_turu)

    if q:
        qs = qs.filter(
            Q(abone_no__icontains=q)
            | Q(sozlesme_no__icontains=q)
            | Q(sicil__sicil_no__icontains=q)
            | Q(sicil__tc_kimlik_no__icontains=q)
            | Q(sicil__ad__icontains=q)
            | Q(sicil__soyad__icontains=q)
            | Q(adres__adres_kodu__icontains=q)
            | Q(adres__mahalle__icontains=q)
            | Q(adres__cadde_sokak__icontains=q)
            | Q(sayac_baglantilari__sayac__sayac_no__icontains=q)
            | Q(sayac_baglantilari__sayac__seri_no__icontains=q)
        ).distinct()

    secili = None
    if sozlesme_id:
        secili = _sozlesme_qs_for_profile(profil).filter(pk=sozlesme_id).first()
    if not secili:
        secili = qs.order_by("-aktif", "-guncellenme_tarihi").first()

    base_qs = _sozlesme_qs_for_profile(profil)
    iletisim_form = IletisimForm()
    stok_qs = _stok_sayaclari_for_sozlesme(secili) if secili and secili.aktif else SayacEnvanteri.objects.none()
    sayac_atama_form = SayacAtamaForm(
        sayac_queryset=stok_qs,
        initial={"takilma_tarihi": timezone.localdate()},
    )
    return render(request, "abonelik/izleme.html", {
        "profil": profil,
        "q": q,
        "durum": durum,
        "abonelik_turu": abonelik_turu,
        "abonelik_turleri": Sozlesme.ABONELIK_TURLERI,
        "sonuclar": qs[:100],
        "secili": secili,
        "iletisim_form": iletisim_form,
        "sayac_atama_form": sayac_atama_form,
        "stok_sayac_sayisi": stok_qs.count(),
        "aktif_sozlesme": base_qs.filter(aktif=True).count(),
        "pasif_sozlesme": base_qs.filter(aktif=False).count(),
        "sayac_sayisi": AboneSayac.objects.filter(sozlesme__in=base_qs, aktif=True).count(),
    })



@login_required
@require_POST
def izleme_iletisim_ekle(request, pk):
    profil = _abone_erisim(request)
    soz = get_object_or_404(_sozlesme_qs_for_profile(profil), pk=pk)
    form = IletisimForm(request.POST)
    if not form.is_valid():
        messages.error(request, "İletişim bilgisi kaydedilemedi. " + _form_error_ozeti(form))
        return redirect(f"/abonelik/?sozlesme={soz.pk}")
    yeni = form.save(commit=False)
    yeni.sicil = soz.sicil
    yeni.kaydeden = request.user
    ayni_aktif = VatandasIletisim.objects.filter(
        sicil=soz.sicil, tur=yeni.tur, aktif=True, deger__iexact=yeni.deger
    ).first()
    if ayni_aktif:
        messages.info(request, f"{ayni_aktif.get_tur_display()} için aynı değer zaten aktif. Yeni kayıt oluşturulmadı.")
        return redirect(f"/abonelik/?sozlesme={soz.pk}")
    with transaction.atomic():
        # Aynı türdeki mevcut aktif bilgi tarihçeye alınır; hiçbir kayıt silinmez.
        VatandasIletisim.objects.filter(sicil=soz.sicil, tur=yeni.tur, aktif=True).update(
            aktif=False, bitis_tarihi=timezone.now()
        )
        yeni.aktif = True
        yeni.baslangic_tarihi = timezone.now()
        yeni.save()
    messages.success(request, f"{yeni.get_tur_display()} güncellendi. Önceki değer geçmiş kaydı olarak korundu.")
    return redirect(f"/abonelik/?sozlesme={soz.pk}")


@login_required
@require_POST
def sayac_ata(request, pk):
    profil = _abone_erisim(request)
    soz = get_object_or_404(_sozlesme_qs_for_profile(profil), pk=pk)
    if not soz.aktif:
        messages.error(request, "Pasif sözleşmeye sayaç atanamaz.")
        return redirect(f"/abonelik/?sozlesme={soz.pk}")
    stok_qs = _stok_sayaclari_for_sozlesme(soz)
    form = SayacAtamaForm(request.POST, sayac_queryset=stok_qs)
    if not form.is_valid():
        messages.error(request, "Sayaç ataması yapılamadı. " + _form_error_ozeti(form))
        return redirect(f"/abonelik/?sozlesme={soz.pk}")

    secilen_sayac = form.cleaned_data["sayac"]
    takilma_tarihi = form.cleaned_data["takilma_tarihi"]
    ilk_endeks = form.cleaned_data.get("ilk_endeks")
    aciklama = (form.cleaned_data.get("aciklama") or "").strip()
    with transaction.atomic():
        # Form açıldıktan sonra başka kullanıcı stok sayacını kullanmış olabilir; işlem anında tekrar kilitle/doğrula.
        yeni_sayac = SayacEnvanteri.objects.select_for_update().filter(
            pk=secilen_sayac.pk,
            ambar__tur="ilce",
            ambar__ilce=soz.adres.ilce,
            ambar__aktif=True,
            durum="stokta",
            aktif=True,
        ).first()
        if not yeni_sayac:
            messages.error(request, "Seçilen sayaç artık uygun ilçe stoğunda değil. Listeyi yenileyip başka sayaç seçin.")
            return redirect(f"/abonelik/?sozlesme={soz.pk}")
        # Mevcut aktif sayaç varsa bağlantısı kapatılır; sayaç kullanım dışı/hurda değerlendirmesine gider.
        mevcut_baglar = list(AboneSayac.objects.select_for_update().select_related("sayac").filter(sozlesme=soz, aktif=True))
        for bag in mevcut_baglar:
            bag.aktif = False
            bag.sokulme_tarihi = takilma_tarihi
            bag.save(update_fields=["aktif", "sokulme_tarihi"])
            eski = bag.sayac
            eski.durum = "kullanim_disi"
            eski.aktif = False
            eski.save(update_fields=["durum", "aktif", "guncellenme_tarihi"])
            AmbarHareketi.objects.create(
                sayac=eski, kaynak_ambar=eski.ambar, hedef_ambar=None,
                islem="aboneden_sokme", kullanici=request.user,
                aciklama=f"{soz.abone_no} aboneliğinden sayaç değişimi nedeniyle söküldü; Hurda Ambar değerlendirmesi bekliyor.",
            )

        kaynak_ambar = yeni_sayac.ambar
        yeni_sayac.ambar = None
        yeni_sayac.durum = "aboneye_takili"
        yeni_sayac.aktif = True
        if ilk_endeks is not None:
            yeni_sayac.son_endeks = ilk_endeks
        yeni_sayac.save(update_fields=["ambar", "durum", "aktif", "son_endeks", "guncellenme_tarihi"])
        bag = AboneSayac.objects.create(
            sozlesme=soz, sayac=yeni_sayac, aktif=True, takilma_tarihi=takilma_tarihi,
            ilk_endeks=ilk_endeks, son_endeks=ilk_endeks, aciklama=aciklama,
        )
        AmbarHareketi.objects.create(
            sayac=yeni_sayac, kaynak_ambar=kaynak_ambar, hedef_ambar=None,
            islem="aboneye_takma", kullanici=request.user,
            aciklama=f"{soz.abone_no} aboneliğine takıldı. {aciklama}".strip(),
        )
    messages.success(request, f"{bag.sayac.sayac_no} sayacı aboneliğe bağlandı. Önceki sayaç geçmişi korundu.")
    return redirect(f"/abonelik/?sozlesme={soz.pk}")

@login_required
def sicil(request):
    profil = _abone_erisim(request)
    q = (request.GET.get("q") or "").strip()
    durum = (request.GET.get("durum") or "tumu").strip()
    secili_id = request.GET.get("sicil")
    siciller = _sicil_qs_for_profile(profil).prefetch_related("iletisim_kayitlari", "sozlesmeler__adres__ilce")
    if durum == "aktif":
        siciller = siciller.filter(aktif=True)
    elif durum == "pasif":
        siciller = siciller.filter(aktif=False)
    if q:
        siciller = siciller.filter(
            Q(sicil_no__icontains=q) | Q(tc_kimlik_no__icontains=q) |
            Q(ad__icontains=q) | Q(soyad__icontains=q) |
            Q(iletisim_kayitlari__deger__icontains=q)
        ).distinct()
    secili = siciller.filter(pk=secili_id).first() if secili_id else siciller.order_by("-guncellenme_tarihi").first()

    sicil_form = VatandasSicilForm()
    iletisim_form = IletisimForm()
    if request.method == "POST":
        islem = request.POST.get("islem")
        if islem == "sicil_ekle":
            sicil_form = VatandasSicilForm(request.POST)
            if sicil_form.is_valid():
                yeni = sicil_form.save(commit=False)
                yeni.olusturan = request.user
                yeni.save()
                cep = (sicil_form.cleaned_data.get("cep_telefonu") or "").strip()
                eposta = (sicil_form.cleaned_data.get("eposta") or "").strip()
                if cep:
                    VatandasIletisim.objects.create(
                        sicil=yeni, tur=VatandasIletisim.IletisimTuru.CEP_TELEFONU, deger=cep,
                        aktif=True, kaydeden=request.user, aciklama="İlk sicil kaydında girilen cep telefonu",
                    )
                if eposta:
                    VatandasIletisim.objects.create(
                        sicil=yeni, tur=VatandasIletisim.IletisimTuru.EPOSTA, deger=eposta,
                        aktif=True, kaydeden=request.user, aciklama="İlk sicil kaydında girilen e-posta",
                    )
                messages.success(request, f"{yeni.sicil_no} vatandaş sicili oluşturuldu.")
                return redirect(f"/abonelik/sicil/?sicil={yeni.pk}")
            messages.error(request, "Vatandaş sicili oluşturulamadı. " + _form_error_ozeti(sicil_form))
        elif islem == "iletisim_ekle":
            secili = get_object_or_404(_sicil_qs_for_profile(profil), pk=request.POST.get("sicil_id"))
            iletisim_form = IletisimForm(request.POST)
            if iletisim_form.is_valid():
                yeni = iletisim_form.save(commit=False)
                yeni.sicil = secili
                yeni.kaydeden = request.user
                ayni_aktif = VatandasIletisim.objects.filter(
                    sicil=secili, tur=yeni.tur, aktif=True, deger__iexact=yeni.deger
                ).first()
                if ayni_aktif:
                    messages.info(request, "Aynı iletişim bilgisi zaten aktif. Yeni kayıt oluşturulmadı.")
                    return redirect(f"/abonelik/sicil/?sicil={secili.pk}")
                with transaction.atomic():
                    VatandasIletisim.objects.filter(sicil=secili, tur=yeni.tur, aktif=True).update(
                        aktif=False, bitis_tarihi=timezone.now()
                    )
                    yeni.aktif = True
                    yeni.baslangic_tarihi = timezone.now()
                    yeni.save()
                messages.success(request, "Yeni iletişim bilgisi aktif edildi; eski kayıt silinmeden pasife alındı.")
                return redirect(f"/abonelik/sicil/?sicil={secili.pk}")
            messages.error(request, "İletişim bilgisi eklenemedi. " + _form_error_ozeti(iletisim_form))

    return render(request, "abonelik/sicil.html", {
        "profil": profil, "q": q, "durum": durum, "siciller": siciller[:150], "secili": secili,
        "sicil_form": sicil_form, "iletisim_form": iletisim_form,
    })


@login_required
@require_POST
def sicil_toggle(request, pk):
    profil = _abone_erisim(request)
    sicil = get_object_or_404(_sicil_qs_for_profile(profil), pk=pk)
    if sicil.aktif and sicil.sozlesmeler.filter(aktif=True).exists():
        messages.warning(request, "Aktif sözleşmesi bulunan vatandaş sicili pasife alınamaz. Önce aktif sözleşmeyi kapatın.")
        return redirect(f"/abonelik/sicil/?sicil={sicil.pk}")
    sicil.aktif = not sicil.aktif
    sicil.save(update_fields=["aktif", "guncellenme_tarihi"])
    messages.success(request, f"{sicil.sicil_no} {'aktif' if sicil.aktif else 'pasif'} duruma alındı. Sicil geçmişi silinmedi.")
    return redirect(f"/abonelik/sicil/?sicil={sicil.pk}")


@login_required
@require_POST
def iletisim_toggle(request, pk):
    profil = _abone_erisim(request)
    kayit = get_object_or_404(
        VatandasIletisim.objects.select_related("sicil").filter(sicil__in=_sicil_qs_for_profile(profil)),
        pk=pk,
    )
    if not kayit.aktif:
        messages.info(request, "Geçmiş iletişim kaydı yeniden yazılmaz. Aynı bilgi tekrar kullanılacaksa yeni iletişim kaydı ekleyin.")
        return redirect(f"/abonelik/sicil/?sicil={kayit.sicil_id}")
    kayit.aktif = False
    kayit.bitis_tarihi = timezone.now()
    kayit.save(update_fields=["aktif", "bitis_tarihi"])
    messages.success(request, "İletişim bilgisi pasife alındı; eski değer tarihçede kalmaya devam ediyor.")
    return redirect(f"/abonelik/sicil/?sicil={kayit.sicil_id}")


@login_required
def sozlesmeler(request):
    profil = _abone_erisim(request)
    q = (request.GET.get("q") or "").strip()
    durum = (request.GET.get("durum") or "tumu").strip()
    abonelik_turu = (request.GET.get("tur") or "").strip()
    kaynak = (request.GET.get("kaynak") or "").strip()
    sicil_id = request.GET.get("sicil") or request.POST.get("sicil_id")
    siciller = _sicil_qs_for_profile(profil).filter(aktif=True)
    ilce_ids = _yetkili_ilce_ids(profil)
    adresler = HizmetAdresi.objects.filter(aktif=True).select_related("ilce")
    if ilce_ids is not None:
        adresler = adresler.filter(ilce_id__in=ilce_ids)

    secili_sicil = siciller.filter(pk=sicil_id).first() if sicil_id else None
    form = SozlesmeForm()
    form.fields["adres"].queryset = adresler

    if request.method == "POST" and request.POST.get("islem") == "sozlesme_ekle":
        if not secili_sicil:
            messages.error(request, "Önce vatandaş sicili seçilmelidir.")
        else:
            form = SozlesmeForm(request.POST)
            form.fields["adres"].queryset = adresler
            if form.is_valid():
                with transaction.atomic():
                    yeni = form.save(commit=False)
                    yeni.sicil = secili_sicil
                    yeni.olusturan = request.user
                    Sozlesme.objects.filter(adres=yeni.adres, aktif=True).update(aktif=False, bitis_tarihi=timezone.localdate())
                    yeni.aktif = True
                    yeni.save()
                messages.success(request, f"{yeni.sozlesme_no} sözleşmesi aktif olarak oluşturuldu.")
                return redirect(f"/abonelik/sozlesmeler/?sicil={secili_sicil.pk}")
            messages.error(request, "Sözleşme oluşturulamadı. " + _form_error_ozeti(form))

    soz_qs = _sozlesme_qs_for_profile(profil)
    if durum == "aktif":
        soz_qs = soz_qs.filter(aktif=True)
    elif durum == "pasif":
        soz_qs = soz_qs.filter(aktif=False)
    if abonelik_turu:
        soz_qs = soz_qs.filter(abonelik_turu=abonelik_turu)
    if kaynak:
        soz_qs = soz_qs.filter(kaynak=kaynak)
    if q:
        soz_qs = soz_qs.filter(
            Q(abone_no__icontains=q) | Q(sozlesme_no__icontains=q) |
            Q(sicil__tc_kimlik_no__icontains=q) | Q(sicil__sicil_no__icontains=q) |
            Q(sicil__ad__icontains=q) | Q(sicil__soyad__icontains=q) |
            Q(adres__adres_kodu__icontains=q)
        )
    return render(request, "abonelik/sozlesmeler.html", {
        "profil": profil, "q": q, "durum": durum, "abonelik_turu": abonelik_turu, "kaynak": kaynak,
        "abonelik_turleri": Sozlesme.ABONELIK_TURLERI, "kaynaklar": [x for x in Sozlesme.KAYNAKLAR if x[0] != "devir"],
        "sozlesmeler": soz_qs[:200], "siciller": siciller[:150],
        "secili_sicil": secili_sicil, "form": form, "adresler": adresler,
    })


@login_required
@require_POST
def sozlesme_toggle(request, pk):
    profil = _abone_erisim(request)
    soz = get_object_or_404(_sozlesme_qs_for_profile(profil), pk=pk)
    with transaction.atomic():
        if soz.aktif:
            soz.aktif = False
            soz.bitis_tarihi = timezone.localdate()
        else:
            Sozlesme.objects.filter(adres=soz.adres, aktif=True).exclude(pk=soz.pk).update(
                aktif=False, bitis_tarihi=timezone.localdate()
            )
            soz.aktif = True
            soz.bitis_tarihi = None
        soz.save(update_fields=["aktif", "bitis_tarihi", "guncellenme_tarihi"])
    messages.success(request, f"{soz.sozlesme_no} {'aktif' if soz.aktif else 'pasif'} duruma alındı. Geçmiş kayıt korunuyor.")
    return redirect("abonelik:sozlesmeler")


@login_required
@require_POST
def sayac_kullanim_disi(request, pk):
    profil = _abone_erisim(request)
    bag = get_object_or_404(
        AboneSayac.objects.select_related("sozlesme__adres__ilce", "sayac").filter(sozlesme__in=_sozlesme_qs_for_profile(profil)), pk=pk
    )
    if not bag.aktif:
        messages.warning(request, "Bu sayaç bağlantısı zaten pasif.")
        return redirect(f"/abonelik/?sozlesme={bag.sozlesme_id}")
    with transaction.atomic():
        bag.aktif = False
        bag.sokulme_tarihi = timezone.localdate()
        bag.save(update_fields=["aktif", "sokulme_tarihi"])
        sayac = bag.sayac
        sayac.durum = "kullanim_disi"
        sayac.aktif = False
        sayac.save(update_fields=["durum", "aktif", "guncellenme_tarihi"])
        AmbarHareketi.objects.create(
            sayac=sayac, kaynak_ambar=sayac.ambar, hedef_ambar=None,
            islem="aboneden_sokme", kullanici=request.user,
            aciklama=f"{bag.sozlesme.abone_no} aboneliğinden söküldü; Hurda Ambar değerlendirmesi bekliyor."
        )
    messages.success(request, "Sayaç kullanım dışı kaydedildi. Ambar yetkilisinin Hurda Ambar değerlendirme kuyruğuna alındı.")
    return redirect(f"/abonelik/?sozlesme={bag.sozlesme_id}")


@login_required
def ambar_yonetimi(request):
    yetki, mod = _ambar_erisim(request)
    merkez = Ambar.objects.filter(tur="merkez", aktif=True).first()
    hurda = Ambar.objects.filter(tur="hurda", aktif=True).first()
    talep_form = AmbarSayacTalepForm()
    stok_giris_form = MerkezStokGirisForm()

    if request.method == "POST" and request.POST.get("islem") == "stok_giris":
        if mod != "merkez":
            raise PermissionDenied("Merkez stok girişi yalnız Merkez Ambar tarafından yapılabilir.")
        if not merkez:
            messages.error(request, "Aktif Merkez Ambar tanımı bulunamadı.")
            return redirect("abonelik:ambar_yonetimi")
        stok_giris_form = MerkezStokGirisForm(request.POST)
        if stok_giris_form.is_valid():
            with transaction.atomic():
                sayac = stok_giris_form.save(commit=False)
                sayac.ambar = merkez
                sayac.durum = "stokta"
                sayac.aktif = True
                sayac.save()
                AmbarHareketi.objects.create(
                    sayac=sayac, hedef_ambar=merkez, islem="stok_giris", kullanici=request.user,
                    aciklama="Merkez Ambar tarafından yeni sayaç stok girişi yapıldı.",
                )
            messages.success(request, f"{sayac.sayac_no} Merkez Ambar stoğuna kaydedildi.")
            return redirect("abonelik:ambar_yonetimi")
        messages.error(request, "Stok girişi kaydedilemedi. " + _form_error_ozeti(stok_giris_form))

    if request.method == "POST" and request.POST.get("islem") == "sayac_talebi":
        if mod != "ilce" or not yetki:
            raise PermissionDenied("Sayaç talebini yalnız ilçe ambar sorumlusu oluşturabilir.")
        talep_form = AmbarSayacTalepForm(request.POST)
        if talep_form.is_valid():
            if not merkez:
                messages.error(request, "Aktif Merkez Ambar tanımı bulunamadı.")
                return redirect("abonelik:ambar_yonetimi")
            temiz = talep_form.cleaned_data
            ayni_acik = AmbarSayacTalebi.objects.filter(
                yetki=yetki,
                sayac_tipi=temiz["sayac_tipi"],
                cap_mm=temiz["cap_mm"],
                adet=temiz["adet"],
                gerekce__iexact=temiz["gerekce"],
                durum__in=["talep_edildi", "hazirlaniyor", "sevk_edildi"],
            ).first()
            if ayni_acik:
                messages.warning(request, f"Aynı içerikte açık talep zaten var: {ayni_acik.talep_no}. Mükerrer kayıt oluşturulmadı.")
                return redirect("abonelik:ambar_yonetimi")
            talep = talep_form.save(commit=False)
            talep.yetki = yetki
            talep.kaynak_ambar = merkez
            talep.hedef_ambar = yetki.ambar
            talep.olusturan = request.user
            talep.save()
            AmbarHareketi.objects.create(
                talep=talep, kaynak_ambar=merkez, hedef_ambar=yetki.ambar,
                islem="sayac_talebi", kullanici=request.user,
                aciklama=f"{talep.adet} adet {talep.get_sayac_tipi_display()} {talep.cap_mm} mm sayaç talep edildi."
            )
            messages.success(request, f"{talep.talep_no} Merkez Ambara iletildi.")
            return redirect("abonelik:ambar_yonetimi")
        messages.error(request, "Sayaç talebi oluşturulamadı. " + _form_error_ozeti(talep_form))

    talepler = AmbarSayacTalebi.objects.select_related(
        "yetki__ilce", "yetki__personel__kullanici", "kaynak_ambar", "hedef_ambar"
    )
    tum_sayaclar = SayacEnvanteri.objects.select_related("ambar")
    kullanim_disi = tum_sayaclar.none()

    if mod == "ilce" and yetki:
        talepler = talepler.filter(yetki=yetki)
        sayaclar = tum_sayaclar.filter(ambar=yetki.ambar).distinct()
        kullanim_disi = tum_sayaclar.filter(
            durum="kullanim_disi",
            abone_baglantilari__sozlesme__adres__ilce=yetki.ilce,
        ).distinct()
    else:
        # Merkez personeli yalnız Merkez Ambar stoğunu ve yoldaki merkez çıkışlarını görür.
        sayaclar = tum_sayaclar.filter(ambar=merkez) if merkez else tum_sayaclar.none()

    hareketler = AmbarHareketi.objects.select_related(
        "sayac", "kaynak_ambar", "hedef_ambar", "kullanici", "talep"
    )
    if mod == "ilce" and yetki:
        hareketler = hareketler.filter(Q(kaynak_ambar=yetki.ambar) | Q(hedef_ambar=yetki.ambar))
    elif mod == "merkez" and merkez:
        hareketler = hareketler.filter(Q(kaynak_ambar=merkez) | Q(hedef_ambar=merkez))

    ilce_stok = sayaclar.filter(durum="stokta").count() if mod == "ilce" else 0
    acik_talep_sayisi = talepler.exclude(durum__in=["teslim_alindi", "reddedildi"]).count() if mod == "ilce" else 0
    hurda_bekleyen_sayisi = kullanim_disi.count() if mod == "ilce" else 0
    merkez_stok = SayacEnvanteri.objects.filter(ambar=merkez, durum="stokta").count() if merkez else 0
    merkez_bekleyen_sayisi = talepler.filter(durum__in=["talep_edildi", "hazirlaniyor"]).count() if mod == "merkez" else 0
    sevkte_sayisi = talepler.filter(durum="sevk_edildi").count() if mod == "merkez" else 0

    # V60: Merkez Ambar personeli, kendisine ulaşan devir sayaçlarının vatandaş ve
    # işlem ayrıntılarını tıklanabilir bilgi ikonundan aynı ekranda görebilir.
    merkez_devir_kayitlari = []
    if mod == "merkez":
        from devirambar.models import DevirBasvurusu
        merkez_devir_kayitlari = DevirBasvurusu.objects.filter(
            durum__in=[
                "merkez_ambara_gonderildi", "merkez_teslim_alindi",
                "merkez_kontrol_edildi", "merkez_ambara_kaydedildi",
            ]
        ).select_related(
            "merkeze_gonderen", "merkez_teslim_alan", "merkez_kontrol_eden",
            "merkez_ambara_kaydeden",
        ).order_by("-guncellenme_tarihi")[:60]

    return render(request, "abonelik/ambar_yonetimi.html", {
        "yetki": yetki, "mod": mod, "merkez": merkez, "hurda": hurda,
        "talep_form": talep_form, "stok_giris_form": stok_giris_form,
        "talepler": talepler[:120], "sayaclar": sayaclar[:200],
        "kullanim_disi": kullanim_disi[:80], "hareketler": hareketler[:100],
        "ilce_stok": ilce_stok, "acik_talep_sayisi": acik_talep_sayisi,
        "hurda_bekleyen_sayisi": hurda_bekleyen_sayisi,
        "merkez_stok": merkez_stok, "merkez_bekleyen_sayisi": merkez_bekleyen_sayisi,
        "sevkte_sayisi": sevkte_sayisi,
        "merkez_devir_kayitlari": merkez_devir_kayitlari,
    })


@login_required
@require_POST
def ambar_talep_durum(request, pk, aksiyon):
    yetki, mod = _ambar_erisim(request)
    talep = get_object_or_404(AmbarSayacTalebi.objects.select_related("yetki__ilce", "hedef_ambar", "kaynak_ambar"), pk=pk)
    if mod == "ilce" and (not yetki or talep.yetki_id != yetki.id):
        raise PermissionDenied("Bu sayaç talebi başka ilçe ambarına aittir.")
    with transaction.atomic():
        if aksiyon == "hazirla":
            if mod != "merkez" or talep.durum != "talep_edildi":
                raise PermissionDenied("Bu işlem Merkez Ambar hazırlık aşamasına ait.")
            uygun_stok = SayacEnvanteri.objects.filter(
                ambar=talep.kaynak_ambar, durum="stokta", sayac_tipi=talep.sayac_tipi, cap_mm=talep.cap_mm
            ).count()
            if uygun_stok < talep.adet:
                messages.error(request, f"Talep hazırlanamadı: istenen {talep.adet}, uygun merkez stoğu {uygun_stok}.")
                return redirect("abonelik:ambar_yonetimi")
            talep.durum = "hazirlaniyor"
            talep.merkez_islem_yapan = request.user
            talep.save(update_fields=["durum", "merkez_islem_yapan"])

        elif aksiyon == "reddet":
            if mod != "merkez" or talep.durum not in ("talep_edildi", "hazirlaniyor"):
                raise PermissionDenied("Yalnız açık Merkez Ambar talepleri reddedilebilir.")
            talep.durum = "reddedildi"
            talep.not_alani = (request.POST.get("not") or "Merkez Ambar tarafından reddedildi.").strip()[:300]
            talep.merkez_islem_yapan = request.user
            talep.save(update_fields=["durum", "not_alani", "merkez_islem_yapan"])

        elif aksiyon == "sevk-et":
            if mod != "merkez" or talep.durum not in ("talep_edildi", "hazirlaniyor"):
                raise PermissionDenied("Bu talep sevk aşamasında değil.")
            uygun = list(SayacEnvanteri.objects.select_for_update().filter(
                ambar=talep.kaynak_ambar, durum="stokta", sayac_tipi=talep.sayac_tipi, cap_mm=talep.cap_mm
            ).order_by("id")[:talep.adet])
            if len(uygun) < talep.adet:
                messages.error(request, f"Merkez stok yetersiz. İstenen {talep.adet}, uygun stok {len(uygun)}.")
                return redirect("abonelik:ambar_yonetimi")
            for sayac in uygun:
                kaynak = sayac.ambar
                # Fiziksel teslim gerçekleşene kadar sayaç Merkez Ambar stok konumundan çıkmış, yolda görünür.
                sayac.durum = "sevk_ediliyor"
                sayac.save(update_fields=["durum", "guncellenme_tarihi"])
                AmbarHareketi.objects.create(
                    sayac=sayac, talep=talep, kaynak_ambar=kaynak, hedef_ambar=talep.hedef_ambar,
                    islem="sevk", kullanici=request.user, aciklama=f"{talep.talep_no} kapsamında ilçe ambarına sevk edildi; teslim bekleniyor."
                )
            talep.durum = "sevk_edildi"
            talep.sevk_tarihi = timezone.now()
            talep.merkez_islem_yapan = request.user
            talep.save(update_fields=["durum", "sevk_tarihi", "merkez_islem_yapan"])

        elif aksiyon == "teslim-al":
            if mod != "ilce" or talep.durum != "sevk_edildi":
                raise PermissionDenied("Bu talep ilçe ambarı teslim aşamasında değil.")
            talep.durum = "teslim_alindi"
            talep.teslim_tarihi = timezone.now()
            talep.save(update_fields=["durum", "teslim_tarihi"])
            sevk_sayac_ids = talep.hareketler.filter(islem="sevk", sayac__isnull=False).values_list("sayac_id", flat=True).distinct()
            for sayac in SayacEnvanteri.objects.select_for_update().filter(pk__in=sevk_sayac_ids):
                kaynak = sayac.ambar
                sayac.ambar = talep.hedef_ambar
                sayac.durum = "stokta"
                sayac.save(update_fields=["ambar", "durum", "guncellenme_tarihi"])
                AmbarHareketi.objects.create(
                    sayac=sayac, talep=talep, kaynak_ambar=kaynak, hedef_ambar=talep.hedef_ambar,
                    islem="teslim", kullanici=request.user, aciklama=f"{talep.talep_no} kapsamında ilçe ambarı fiziksel teslim aldı."
                )
        else:
            raise PermissionDenied("Geçersiz ambar talep işlemi.")

    messages.success(request, f"{talep.talep_no}: {talep.get_durum_display()}.")
    return redirect("abonelik:ambar_yonetimi")


@login_required
@require_POST
def hurdaya_gonder(request, pk):
    yetki, mod = _ambar_erisim(request)
    if mod != "ilce" or not yetki:
        raise PermissionDenied("Hurda Ambar yönlendirmesini yalnız ilçe ambar sorumlusu yapabilir.")
    sayac_qs = SayacEnvanteri.objects.select_related("ambar")
    if mod == "ilce" and yetki:
        sayac_qs = sayac_qs.filter(
            Q(ambar=yetki.ambar) | Q(abone_baglantilari__sozlesme__adres__ilce=yetki.ilce)
        ).distinct()
    sayac = get_object_or_404(sayac_qs, pk=pk)
    if sayac.durum != "kullanim_disi":
        messages.warning(request, "Yalnız kullanım dışı sayaçlar Hurda Ambara yönlendirilebilir.")
        return redirect("abonelik:ambar_yonetimi")
    hurda = get_object_or_404(Ambar, tur="hurda", aktif=True)
    kaynak = sayac.ambar
    neden = (request.POST.get("neden") or "").strip()[:250]
    if len(neden) < 5:
        messages.error(request, "Hurda Ambara gönderim için en az 5 karakterlik gerekçe girilmelidir.")
        return redirect("abonelik:ambar_yonetimi")
    sayac.ambar = hurda
    sayac.durum = "hurda"
    sayac.aktif = False
    sayac.hurda_nedeni = neden
    sayac.save(update_fields=["ambar", "durum", "aktif", "hurda_nedeni", "guncellenme_tarihi"])
    AmbarHareketi.objects.create(
        sayac=sayac, kaynak_ambar=kaynak, hedef_ambar=hurda,
        islem="hurdaya_ayirma", kullanici=request.user, aciklama=neden
    )
    messages.success(request, f"{sayac.sayac_no} Hurda Ambara yönlendirildi; geçmiş hareket kaydı korundu.")
    return redirect("abonelik:ambar_yonetimi")
