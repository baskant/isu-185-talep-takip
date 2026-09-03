from django.db.models import Q, Case, When, IntegerField, Count
from accounts.models import PersonelProfili, RolAtamaKurali
from .models import GeriBildirim, IslemLogu, Talep

def kullanici_ip(request):
    raw=request.META.get("HTTP_X_FORWARDED_FOR")
    return raw.split(",")[0].strip() if raw else request.META.get("REMOTE_ADDR")

def log_yaz(request,islem,aciklama,talep=None,varlik_turu="",varlik_id="",eski="",yeni=""):
    IslemLogu.objects.create(
        talep=talep,kullanici=request.user if request and request.user.is_authenticated else None,
        islem=islem,aciklama=aciklama,varlik_turu=varlik_turu,varlik_id=str(varlik_id or ""),
        eski_deger=str(eski or ""),yeni_deger=str(yeni or ""),ip_adresi=kullanici_ip(request) if request else None
    )

def akisa_yaz(talep,kullanici,mesaj,durum="",request=None,sistem=True,islem="STATUS"):
    """
    Talep yaşam döngüsündeki okunabilir hareket kaydı.
    Bu kayıtlar kullanıcı tarafından yazılmaz; buton/iş akışı olaylarından sistem üretir.
    `sistem` parametresi eski çağrılarla uyumluluk için tutulur, ancak kayıt daima sistem mesajıdır.
    """
    GeriBildirim.objects.create(
        talep=talep,kullanici=kullanici,mesaj=mesaj,durum=durum,sistem_mesaji=True
    )
    if request:
        log_yaz(request,islem,mesaj,talep,"Talep",talep.pk)

def koordinator_bul(talep):
    base=PersonelProfili.objects.filter(
        aktif=True,
        kullanici__is_active=True,
        yetkili_ilceler=talep.ilce,
        rol__aktif=True,
        rol__panel_tipi="sef",
    ).select_related("kullanici","rol").prefetch_related("uzmanlik_is_turleri")

    adaylar=list(base.filter(rol__kod="koordinator").distinct()) or list(base.distinct())
    uygun=[p for p in adaylar if p.is_turune_yetkili_mi(talep.is_turu)]
    uygun.sort(
        key=lambda p:p.koordinator_talepleri.exclude(
            durum__in=["tamamlandi","iptal"]
        ).count()
    )
    return uygun[0] if uygun else None

def bolge_saha_personelleri(atan_kisi, talep):
    """
    Atama yapan rolün kural olarak erişebildiği ve talebin ilçesinde bulunan
    tüm aktif saha hesaplarını döndürür. Müsaitlik/uzmanlık filtrelenmez;
    atama ekranında neden seçilemediği görülebilsin.
    """
    if not atan_kisi:
        return PersonelProfili.objects.none()

    hedef_roller = RolAtamaKurali.objects.filter(
        kaynak_rol=atan_kisi.rol,
        aktif=True,
        hedef_rol__aktif=True,
        hedef_rol__panel_tipi="saha",
    ).values_list("hedef_rol_id", flat=True)

    return PersonelProfili.objects.filter(
        aktif=True,
        kullanici__is_active=True,
        rol_id__in=hedef_roller,
        yetkili_ilceler=talep.ilce,
    ).select_related("kullanici","rol").prefetch_related(
        "uzmanlik_is_turleri","yetkili_ilceler"
    ).distinct().order_by("rol__ad","kullanici__username")

def uygun_saha_personelleri(atan_kisi,talep):
    """
    Manuel saha ataması için uygun hesaplar:
    1. Parent/child atama kuralı
    2. Aynı ilçe
    3. Aktif kullanıcı/profil
    4. Yeni görev kabulü açık (musait=True)
    5. İş türü uzmanlığı

    V35: Bir saha ekibine birden fazla iş emri atanabilir.
    Mevcut açık iş sayısı atamayı ENGELLEMEZ; yalnızca listede daha az
    yüklü ekipleri önce göstermek için sıralama verisi olarak kullanılır.
    Aynı anda yalnız bir işi operasyonel olarak ilerletme kuralı
    durum_guncelle() içinde korunur.
    """
    qs = bolge_saha_personelleri(atan_kisi, talep).filter(musait=True)

    candidates = []
    for p in qs:
        specs = list(p.uzmanlik_is_turleri.all())
        exact = any(x.pk == talep.is_turu_id for x in specs)
        general = not specs
        if exact or general:
            open_jobs = p.saha_talepleri.exclude(
                durum__in=["tamamlandi","iptal"]
            ).count()
            candidates.append((p, exact, open_jobs))

    # Tam uzman > ortak/fallback, sonra daha az bekleyen/açık işi olan.
    candidates.sort(
        key=lambda x: (
            0 if x[1] else 1,
            x[2],
            x[0].rol.ad,
            x[0].kullanici.username,
        )
    )
    ids = [p.pk for p, _, _ in candidates]
    if not ids:
        return PersonelProfili.objects.none()

    preserved = Case(
        *[When(pk=pk, then=pos) for pos, pk in enumerate(ids)],
        output_field=IntegerField(),
    )
    return PersonelProfili.objects.filter(pk__in=ids).select_related(
        "kullanici","rol"
    ).prefetch_related(
        "uzmanlik_is_turleri","yetkili_ilceler"
    ).order_by(preserved)

def talep_erisim_var_mi(user,talep):
    if user.is_superuser:
        return True
    try:
        p=user.personel_profili
    except PersonelProfili.DoesNotExist:
        return False
    if not p.aktif:
        return False
    if p.rol.panel_tipi in ["admin","185"]:
        return True
    if p.rol.panel_tipi=="sef":
        return (
            talep.sorumlu_koordinator_id==p.id or
            (p.ilceye_yetkili_mi(talep.ilce) and p.is_turune_yetkili_mi(talep.is_turu))
        )
    if p.rol.panel_tipi=="saha":
        return talep.sorumlu_saha_id==p.id
    return False

def kullanici_talepleri(user):
    if user.is_superuser:
        return Talep.objects.all()
    try:
        p=user.personel_profili
    except PersonelProfili.DoesNotExist:
        return Talep.objects.none()

    if p.rol.panel_tipi in ["admin","185"]:
        return Talep.objects.all()

    if p.rol.panel_tipi=="sef":
        ids=p.yetkili_ilceler.values_list("id",flat=True)
        qs=Talep.objects.filter(Q(sorumlu_koordinator=p)|Q(ilce_id__in=ids))
        uz=p.uzmanlik_is_turleri.all()
        if uz.exists():
            qs=qs.filter(is_turu__in=uz)
        return qs.distinct()

    if p.rol.panel_tipi=="saha":
        return Talep.objects.filter(sorumlu_saha=p)

    return Talep.objects.none()
