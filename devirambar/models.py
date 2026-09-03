from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


KOCAELI_ILCELERI = [
    ("Başiskele", "Başiskele"), ("Çayırova", "Çayırova"), ("Darıca", "Darıca"),
    ("Derince", "Derince"), ("Dilovası", "Dilovası"), ("Gebze", "Gebze"),
    ("Gölcük", "Gölcük"), ("İzmit", "İzmit"), ("Kandıra", "Kandıra"),
    ("Karamürsel", "Karamürsel"), ("Kartepe", "Kartepe"), ("Körfez", "Körfez"),
]


class AbonelikKaydi(models.Model):
    """Devir ekranının sorguladığı mevcut abonelik kaydı.

    Gerçek kurum entegrasyonunda bu model, İSU'nun ana abonelik sistemi/veritabanı
    ile değiştirilebilir. Projede akışı uçtan uca göstermek için yerel kayıt tutulur.
    """

    abone_no = models.CharField(max_length=50, unique=True, db_index=True)
    abone_ad_soyad = models.CharField(max_length=160)
    telefon = models.CharField(max_length=20, blank=True)
    tc_kimlik_no = models.CharField(max_length=11, blank=True)
    ilce = models.CharField(max_length=40, choices=KOCAELI_ILCELERI)
    adres = models.CharField(max_length=300)
    sayac_seri_no = models.CharField(max_length=80, blank=True, db_index=True)
    sayac_marka_model = models.CharField(max_length=120, blank=True)
    sayac_endeks = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    aktif = models.BooleanField(default=True, db_index=True)
    onceki_abonelik = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="devam_abonelikleri"
    )
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)
    kapanis_tarihi = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-aktif", "abone_no"]
        indexes = [models.Index(fields=["aktif", "ilce"])]

    def __str__(self):
        return f"{self.abone_no} — {self.abone_ad_soyad}"

    @classmethod
    def yeni_abone_no_uret(cls):
        """Demo/proje formatında yeni ve benzersiz abone numarası üretir."""
        yil = timezone.localdate().year
        prefix = f"ABN-{yil}-"
        son_no = (
            cls.objects.filter(abone_no__startswith=prefix)
            .order_by("-abone_no")
            .values_list("abone_no", flat=True)
            .first()
        )
        try:
            sira = int((son_no or "").split("-")[-1]) + 1
        except (TypeError, ValueError):
            sira = 1
        while True:
            aday = f"{prefix}{sira:06d}"
            if not cls.objects.filter(abone_no=aday).exists():
                return aday
            sira += 1


class DevirBasvurusu(models.Model):
    DURUMLAR = [
        ("hazirlaniyor", "Devir Kaydı Oluşturuldu"),
        ("ambara_gonderildi", "Ambara Gönderildi"),
        ("teslim_alindi", "Ambar Teslim Aldı"),
        ("kontrol_edildi", "Sayaç Kontrol Edildi"),
        ("merkez_ambara_gonderildi", "Merkez Ambara Gönderildi"),
        ("merkez_teslim_alindi", "Merkez Ambar Teslim Aldı"),
        ("merkez_kontrol_edildi", "Merkez Ambar Kontrol Etti"),
        ("merkez_ambara_kaydedildi", "Merkez Ambara Kaydedildi"),
        ("ambara_kaydedildi", "Yerel Ambara Kaydedildi (Eski Akış)"),
        ("iptal", "İptal"),
    ]
    DEVIR_NEDENLERI = [
        ("mulk_degisimi", "Mülk sahibi değişikliği"),
        ("kiraci_degisimi", "Kiracı değişimi"),
        ("vefat", "Vefat / miras"),
        ("kurum_degisimi", "Kurum / şirket değişikliği"),
        ("diger", "Diğer"),
    ]

    basvuru_no = models.CharField(max_length=30, unique=True, blank=True)
    # Bu alanlar yeni abonenin/vatandaşın bilgilerini temsil eder.
    vatandas_ad_soyad = models.CharField(max_length=160)
    telefon = models.CharField(max_length=20)
    tc_kimlik_no = models.CharField(max_length=11, blank=True)

    # İlçe/adres/sayaç alanları seçilen mevcut abonelikten snapshot olarak kopyalanır.
    ilce = models.CharField(max_length=40, choices=KOCAELI_ILCELERI)
    adres = models.CharField(max_length=300)
    eski_abone_no = models.CharField(max_length=50, blank=True)
    eski_abone_ad_soyad = models.CharField(max_length=160, blank=True)
    yeni_abone_no = models.CharField(max_length=50, blank=True)
    eski_abonelik = models.ForeignKey(
        AbonelikKaydi, on_delete=models.PROTECT, null=True, blank=True, related_name="devir_basvurulari"
    )
    yeni_abonelik = models.ForeignKey(
        AbonelikKaydi, on_delete=models.SET_NULL, null=True, blank=True, related_name="olusturan_devirler"
    )
    sayac_seri_no = models.CharField(max_length=80)
    sayac_marka_model = models.CharField(max_length=120, blank=True)
    sayac_endeks = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    devir_nedeni = models.CharField(max_length=30, choices=DEVIR_NEDENLERI, default="diger")
    aciklama = models.TextField(blank=True)

    durum = models.CharField(max_length=30, choices=DURUMLAR, default="hazirlaniyor", db_index=True)
    olusturan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="devir_basvurulari")
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)
    guncellenme_tarihi = models.DateTimeField(auto_now=True)

    ambara_gonderen = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="ambara_gonderdigi_devirler")
    ambara_gonderim_tarihi = models.DateTimeField(null=True, blank=True)
    teslim_alan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="teslim_aldigi_sayaclar")
    teslim_tarihi = models.DateTimeField(null=True, blank=True)
    kontrol_eden = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="kontrol_ettigi_sayaclar")
    kontrol_tarihi = models.DateTimeField(null=True, blank=True)
    ambara_kaydeden = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="ambara_kaydettigi_sayaclar")
    ambar_kayit_tarihi = models.DateTimeField(null=True, blank=True)
    depo_konumu = models.CharField(max_length=120, blank=True)
    ambar_notu = models.CharField(max_length=300, blank=True)

    merkeze_gonderen = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="merkez_ambara_gonderdigi_sayaclar")
    merkeze_gonderim_tarihi = models.DateTimeField(null=True, blank=True)
    merkez_teslim_alan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="merkezde_teslim_aldigi_sayaclar")
    merkez_teslim_tarihi = models.DateTimeField(null=True, blank=True)
    merkez_kontrol_eden = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="merkezde_kontrol_ettigi_sayaclar")
    merkez_kontrol_tarihi = models.DateTimeField(null=True, blank=True)
    merkez_ambara_kaydeden = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="merkez_ambara_kaydettigi_sayaclar")
    merkez_ambar_kayit_tarihi = models.DateTimeField(null=True, blank=True)
    merkez_depo_konumu = models.CharField(max_length=120, blank=True)
    merkez_ambar_notu = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-olusturulma_tarihi"]
        indexes = [
            models.Index(fields=["durum", "olusturulma_tarihi"]),
            models.Index(fields=["ilce", "durum"]),
            models.Index(fields=["sayac_seri_no"]),
        ]

    def __str__(self):
        return self.basvuru_no or f"Devir #{self.pk}"

    def eksik_zorunlu_alanlar(self):
        kontroller = [
            ("Yeni Abone Ad Soyad", self.vatandas_ad_soyad),
            ("Telefon", self.telefon),
            ("İlçe", self.ilce),
            ("Adres", self.adres),
            ("Eski Abone No", self.eski_abone_no),
            ("Yeni Abone No", self.yeni_abone_no),
            ("Sayaç Seri No", self.sayac_seri_no),
            ("Devir Nedeni", self.devir_nedeni),
        ]
        return [etiket for etiket, deger in kontroller if not str(deger or "").strip()]

    @property
    def ambar_gonderime_hazir(self):
        return not self.eksik_zorunlu_alanlar()

    def save(self, *args, **kwargs):
        if not self.basvuru_no:
            yil = timezone.localdate().year
            son = DevirBasvurusu.objects.filter(basvuru_no__startswith=f"DV-{yil}-").order_by("-id").first()
            sira = (son.id + 1) if son else 1
            self.basvuru_no = f"DV-{yil}-{sira:06d}"
        super().save(*args, **kwargs)


class DevirHareketi(models.Model):
    basvuru = models.ForeignKey(DevirBasvurusu, on_delete=models.CASCADE, related_name="hareketler")
    kullanici = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    islem = models.CharField(max_length=100)
    aciklama = models.CharField(max_length=400, blank=True)
    onceki_durum = models.CharField(max_length=30, blank=True)
    yeni_durum = models.CharField(max_length=30, blank=True)
    tarih = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-tarih"]
        indexes = [models.Index(fields=["basvuru", "tarih"])]

    def __str__(self):
        return f"{self.basvuru.basvuru_no} — {self.islem}"
