from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class VatandasSicili(models.Model):
    sicil_no = models.CharField(max_length=30, unique=True, blank=True, db_index=True)
    tc_kimlik_no = models.CharField(max_length=11, unique=True, db_index=True)
    ad = models.CharField(max_length=100)
    soyad = models.CharField(max_length=100)
    dogum_tarihi = models.DateField(null=True, blank=True)
    aktif = models.BooleanField(default=True, db_index=True)
    olusturan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="olusturdugu_vatandas_sicilleri")
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)
    guncellenme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ad", "soyad", "sicil_no"]
        indexes = [models.Index(fields=["aktif", "tc_kimlik_no"], name="abonelik_vat_aktif_tc_idx")]

    def __str__(self):
        return f"{self.sicil_no} — {self.ad} {self.soyad}"

    def save(self, *args, **kwargs):
        if not self.sicil_no:
            yil = timezone.localdate().year
            son = VatandasSicili.objects.filter(sicil_no__startswith=f"SIC-{yil}-").order_by("-id").first()
            sira = (son.id + 1) if son else 1
            self.sicil_no = f"SIC-{yil}-{sira:06d}"
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Vatandaş sicili silinemez; aktif/pasif durumu kullanılmalıdır.")


class VatandasIletisim(models.Model):
    class IletisimTuru(models.TextChoices):
        CEP_TELEFONU = "cep_telefonu", "Cep Telefonu"
        EPOSTA = "eposta", "E-posta"
        SABIT_TELEFON = "sabit_telefon", "Sabit Telefon"
        DIGER = "diger", "Diğer"

    ILETISIM_TURLERI = IletisimTuru.choices
    sicil = models.ForeignKey(VatandasSicili, on_delete=models.PROTECT, related_name="iletisim_kayitlari")
    tur = models.CharField(max_length=30, choices=ILETISIM_TURLERI)
    deger = models.CharField(max_length=180)
    aktif = models.BooleanField(default=True, db_index=True)
    baslangic_tarihi = models.DateTimeField(default=timezone.now)
    bitis_tarihi = models.DateTimeField(null=True, blank=True)
    kaydeden = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="kaydettigi_vatandas_iletisimleri")
    aciklama = models.CharField(max_length=250, blank=True)

    class Meta:
        ordering = ["-aktif", "-baslangic_tarihi"]
        indexes = [models.Index(fields=["sicil", "tur", "aktif"], name="abonelik_iletisim_idx")]

    def __str__(self):
        return f"{self.sicil.sicil_no} — {self.get_tur_display()}: {self.deger}"

    def delete(self, *args, **kwargs):
        raise ValidationError("İletişim geçmişi silinemez; kayıt pasife alınmalıdır.")


class HizmetAdresi(models.Model):
    adres_kodu = models.CharField(max_length=40, unique=True, db_index=True)
    ilce = models.ForeignKey("adres.Ilce", on_delete=models.PROTECT, related_name="abonelik_hizmet_adresleri")
    mahalle = models.CharField(max_length=120)
    cadde_sokak = models.CharField(max_length=180)
    kapi_no = models.CharField(max_length=30)
    daire_no = models.CharField(max_length=30, blank=True)
    adres_notu = models.CharField(max_length=250, blank=True)
    aktif = models.BooleanField(default=True, db_index=True)
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ilce__ad", "adres_kodu"]
        indexes = [models.Index(fields=["ilce", "aktif"], name="abonelik_adres_ilce_idx")]

    def __str__(self):
        return f"{self.adres_kodu} — {self.tam_adres}"

    @property
    def tam_adres(self):
        parcalar = [self.mahalle, self.cadde_sokak, f"No: {self.kapi_no}"]
        if self.daire_no:
            parcalar.append(f"D: {self.daire_no}")
        parcalar.append(self.ilce.ad)
        return " / ".join(x for x in parcalar if x)


class Sozlesme(models.Model):
    ABONELIK_TURLERI = [
        ("mesken", "Mesken"),
        ("isyeri", "İşyeri"),
        ("kurum", "Kurum / Şirket"),
        ("insaat", "İnşaat"),
        ("diger", "Diğer"),
    ]
    KAYNAKLAR = [
        ("ilk_abonelik", "İlk Abonelik"),
        ("devir", "Devir"),
        ("e_devlet", "E-Devlet"),
        ("sanal_sube", "Sanal Şube"),
        ("ilce_sube", "İlçe Şube"),
        ("diger", "Diğer"),
    ]
    sozlesme_no = models.CharField(max_length=40, unique=True, blank=True, db_index=True)
    abone_no = models.CharField(max_length=50, unique=True, db_index=True)
    sicil = models.ForeignKey(VatandasSicili, on_delete=models.PROTECT, related_name="sozlesmeler")
    adres = models.ForeignKey(HizmetAdresi, on_delete=models.PROTECT, related_name="sozlesmeler")
    abonelik_turu = models.CharField(max_length=20, choices=ABONELIK_TURLERI, default="mesken")
    kaynak = models.CharField(max_length=20, choices=KAYNAKLAR, default="ilce_sube")
    aktif = models.BooleanField(default=True, db_index=True)
    baslangic_tarihi = models.DateField(default=timezone.localdate)
    bitis_tarihi = models.DateField(null=True, blank=True)
    aciklama = models.CharField(max_length=300, blank=True)
    devir_basvurusu = models.OneToOneField(
        "devirambar.DevirBasvurusu", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="abonelik_sozlesmesi"
    )
    olusturan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="olusturdugu_sozlesmeler")
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)
    guncellenme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-aktif", "-baslangic_tarihi", "abone_no"]
        indexes = [
            models.Index(fields=["sicil", "aktif"], name="abonelik_soz_sicil_idx"),
            models.Index(fields=["adres", "aktif"], name="abonelik_soz_adres_idx"),
        ]

    def __str__(self):
        return f"{self.abone_no} — {self.sicil.ad} {self.sicil.soyad}"

    @classmethod
    def yeni_abone_no_uret(cls):
        yil = timezone.localdate().year
        prefix = f"ABN-{yil}-"
        son = cls.objects.filter(abone_no__startswith=prefix).order_by("-abone_no").values_list("abone_no", flat=True).first()
        try:
            sira = int((son or "").split("-")[-1]) + 1
        except (TypeError, ValueError):
            sira = 1
        while cls.objects.filter(abone_no=f"{prefix}{sira:06d}").exists():
            sira += 1
        return f"{prefix}{sira:06d}"

    def save(self, *args, **kwargs):
        if not self.abone_no:
            self.abone_no = self.yeni_abone_no_uret()
        if not self.sozlesme_no:
            yil = timezone.localdate().year
            son = Sozlesme.objects.filter(sozlesme_no__startswith=f"SZL-{yil}-").order_by("-id").first()
            sira = (son.id + 1) if son else 1
            self.sozlesme_no = f"SZL-{yil}-{sira:06d}"
        if not self.aktif and not self.bitis_tarihi:
            self.bitis_tarihi = timezone.localdate()
        if self.aktif:
            self.bitis_tarihi = None
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Sözleşme geçmişi silinemez; sözleşme pasife alınmalıdır.")


class Ambar(models.Model):
    TURLER = [
        ("ilce", "İlçe / Yerel Ambar"),
        ("merkez", "Merkez Ambar"),
        ("hurda", "Hurda Ambar"),
    ]
    kod = models.SlugField(max_length=80, unique=True)
    ad = models.CharField(max_length=160)
    tur = models.CharField(max_length=20, choices=TURLER)
    ilce = models.ForeignKey("adres.Ilce", on_delete=models.PROTECT, null=True, blank=True, related_name="ambarlari")
    aktif = models.BooleanField(default=True, db_index=True)
    aciklama = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["tur", "ad"]

    def __str__(self):
        return self.ad


class SayacEnvanteri(models.Model):
    SAYAC_TIPLERI = [
        ("mekanik", "Mekanik"),
        ("akilli", "Akıllı"),
        ("on_odemeli", "Ön Ödemeli"),
        ("diger", "Diğer"),
    ]
    DURUMLAR = [
        ("stokta", "Stokta"),
        ("aboneye_takili", "Aboneye Takılı"),
        ("sevk_ediliyor", "Sevk Ediliyor"),
        ("kontrol_bekliyor", "Kontrol Bekliyor"),
        ("kullanim_disi", "Kullanım Dışı"),
        ("hurda", "Hurda Ambarda"),
    ]
    sayac_no = models.CharField(max_length=80, unique=True, db_index=True)
    seri_no = models.CharField(max_length=80, unique=True, db_index=True)
    marka_model = models.CharField(max_length=140, blank=True)
    sayac_tipi = models.CharField(max_length=20, choices=SAYAC_TIPLERI, default="mekanik")
    cap_mm = models.PositiveSmallIntegerField(default=20)
    son_endeks = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    durum = models.CharField(max_length=30, choices=DURUMLAR, default="stokta", db_index=True)
    ambar = models.ForeignKey(Ambar, on_delete=models.PROTECT, null=True, blank=True, related_name="sayaclar")
    aktif = models.BooleanField(default=True, db_index=True)
    hurda_nedeni = models.CharField(max_length=250, blank=True)
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)
    guncellenme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sayac_no"]
        indexes = [models.Index(fields=["durum", "ambar"], name="abonelik_sayac_ambar_idx")]

    def __str__(self):
        return f"{self.sayac_no} / {self.seri_no}"


class AboneSayac(models.Model):
    sozlesme = models.ForeignKey(Sozlesme, on_delete=models.PROTECT, related_name="sayac_baglantilari")
    sayac = models.ForeignKey(SayacEnvanteri, on_delete=models.PROTECT, related_name="abone_baglantilari")
    aktif = models.BooleanField(default=True, db_index=True)
    takilma_tarihi = models.DateField(default=timezone.localdate)
    sokulme_tarihi = models.DateField(null=True, blank=True)
    ilk_endeks = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    son_endeks = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    aciklama = models.CharField(max_length=250, blank=True)

    class Meta:
        ordering = ["-aktif", "-takilma_tarihi"]
        constraints = [
            models.UniqueConstraint(fields=["sozlesme", "sayac", "takilma_tarihi"], name="uq_abone_sayac_tarih")
        ]

    def __str__(self):
        return f"{self.sozlesme.abone_no} — {self.sayac.sayac_no}"

    def save(self, *args, **kwargs):
        if not self.aktif and not self.sokulme_tarihi:
            self.sokulme_tarihi = timezone.localdate()
        if self.aktif:
            self.sokulme_tarihi = None
        super().save(*args, **kwargs)


class AmbarYetkisi(models.Model):
    ilce = models.OneToOneField("adres.Ilce", on_delete=models.CASCADE, related_name="ambar_yetkisi")
    personel = models.ForeignKey("accounts.PersonelProfili", on_delete=models.PROTECT, related_name="ambar_yetkileri")
    ambar = models.ForeignKey(Ambar, on_delete=models.PROTECT, related_name="yetkiler")
    aktif = models.BooleanField(default=True)
    atanma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ilce__ad"]

    def __str__(self):
        return f"{self.ilce.ad} — {self.personel.kullanici.username}"

    def clean(self):
        if self.personel_id:
            if self.personel.rol.panel_tipi != "sef":
                raise ValidationError("Ambar yetkisi yalnız şef/koordinatör rolündeki personele verilebilir.")
            if self.ilce_id and not self.personel.yetkili_ilceler.filter(pk=self.ilce_id).exists():
                raise ValidationError("Personelin ambar yetkisi verilen ilçede görev yetkisi bulunmalıdır.")
        if self.ambar_id and self.ambar.tur != "ilce":
            raise ValidationError("İlçe ambar yetkisi bir yerel/ilçe ambarına bağlanmalıdır.")


class AmbarSayacTalebi(models.Model):
    DURUMLAR = [
        ("talep_edildi", "Talep Edildi"),
        ("hazirlaniyor", "Merkezde Hazırlanıyor"),
        ("sevk_edildi", "İlçe Ambarına Sevk Edildi"),
        ("teslim_alindi", "İlçe Ambarı Teslim Aldı"),
        ("reddedildi", "Reddedildi"),
    ]
    talep_no = models.CharField(max_length=40, unique=True, blank=True, db_index=True)
    yetki = models.ForeignKey(AmbarYetkisi, on_delete=models.PROTECT, related_name="sayac_talepleri")
    kaynak_ambar = models.ForeignKey(Ambar, on_delete=models.PROTECT, related_name="kaynak_sayac_talepleri")
    hedef_ambar = models.ForeignKey(Ambar, on_delete=models.PROTECT, related_name="hedef_sayac_talepleri")
    sayac_tipi = models.CharField(max_length=20, choices=SayacEnvanteri.SAYAC_TIPLERI, default="mekanik")
    cap_mm = models.PositiveSmallIntegerField(default=20)
    adet = models.PositiveSmallIntegerField(default=1)
    gerekce = models.CharField(max_length=300)
    durum = models.CharField(max_length=30, choices=DURUMLAR, default="talep_edildi", db_index=True)
    olusturan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="olusturdugu_ambar_sayac_talepleri")
    merkez_islem_yapan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="islem_yaptigi_ambar_sayac_talepleri")
    talep_tarihi = models.DateTimeField(auto_now_add=True)
    sevk_tarihi = models.DateTimeField(null=True, blank=True)
    teslim_tarihi = models.DateTimeField(null=True, blank=True)
    not_alani = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-talep_tarihi"]
        indexes = [models.Index(fields=["durum", "talep_tarihi"], name="abonelik_talep_durum_idx")]

    def __str__(self):
        return self.talep_no or f"Ambar Talebi #{self.pk}"

    def save(self, *args, **kwargs):
        if not self.talep_no:
            yil = timezone.localdate().year
            son = AmbarSayacTalebi.objects.filter(talep_no__startswith=f"AST-{yil}-").order_by("-id").first()
            sira = (son.id + 1) if son else 1
            self.talep_no = f"AST-{yil}-{sira:06d}"
        super().save(*args, **kwargs)


class AmbarHareketi(models.Model):
    ISLEMLER = [
        ("stok_giris", "Stok Girişi"),
        ("sayac_talebi", "Sayaç Talebi"),
        ("sevk", "Ambarlar Arası Sevk"),
        ("teslim", "Teslim Alma"),
        ("aboneye_takma", "Aboneye Takma"),
        ("aboneden_sokme", "Aboneden Sökme"),
        ("hurdaya_ayirma", "Hurda Ambara Yönlendirme"),
    ]
    sayac = models.ForeignKey(SayacEnvanteri, on_delete=models.PROTECT, null=True, blank=True, related_name="ambar_hareketleri")
    talep = models.ForeignKey(AmbarSayacTalebi, on_delete=models.SET_NULL, null=True, blank=True, related_name="hareketler")
    kaynak_ambar = models.ForeignKey(Ambar, on_delete=models.SET_NULL, null=True, blank=True, related_name="cikis_hareketleri")
    hedef_ambar = models.ForeignKey(Ambar, on_delete=models.SET_NULL, null=True, blank=True, related_name="giris_hareketleri")
    islem = models.CharField(max_length=30, choices=ISLEMLER)
    aciklama = models.CharField(max_length=350, blank=True)
    kullanici = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="ambar_hareketleri")
    tarih = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-tarih"]
        indexes = [models.Index(fields=["tarih", "islem"], name="abonelik_hareket_idx")]

    def __str__(self):
        return f"{self.get_islem_display()} — {self.tarih:%d.%m.%Y %H:%M}"
