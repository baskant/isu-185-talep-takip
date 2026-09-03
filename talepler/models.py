from django.contrib.auth.models import User
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP

class IsTuru(models.Model):
    ad=models.CharField(max_length=120,unique=True)
    kod=models.SlugField(max_length=120,unique=True)
    aktif=models.BooleanField(default=True)
    aciklama=models.CharField(max_length=250,blank=True)
    class Meta: ordering=["ad"]
    def __str__(self): return self.ad

class IsAltTuru(models.Model):
    is_turu=models.ForeignKey(IsTuru,on_delete=models.CASCADE,related_name="alt_turler")
    ad=models.CharField(max_length=160)
    aktif=models.BooleanField(default=True)
    # V42 — Her iş alt türü kendi zorunlu fotoğraf kuralını taşır.
    # 1-8 arası fotoğraf zorunluluğu tanımlanabilir; etiketler satır satır girilir.
    zorunlu_fotograf_sayisi=models.PositiveSmallIntegerField(
        default=2,
        validators=[MinValueValidator(1),MaxValueValidator(8)],
        help_text="İş emri şef onayına gönderilmeden önce tamamlanması gereken fotoğraf adedi.",
    )
    fotograf_etiketleri=models.TextField(
        blank=True,
        help_text="Her satıra bir fotoğraf adı yazın. Örn: Kazı Öncesi / Kazı Sonrası / Yol Geri Kapama Sonrası",
    )
    class Meta:
        ordering=["is_turu__ad","ad"]
        constraints=[models.UniqueConstraint(fields=["is_turu","ad"],name="uq_is_turu_alt_turu")]
    def __str__(self): return f"{self.is_turu.ad} / {self.ad}"

    @property
    def zorunlu_foto_etiketleri(self):
        adet=max(1,min(int(self.zorunlu_fotograf_sayisi or 1),8))
        etiketler=[x.strip() for x in (self.fotograf_etiketleri or "").splitlines() if x.strip()]
        while len(etiketler)<adet:
            etiketler.append(f"Saha Fotoğrafı {len(etiketler)+1}")
        return etiketler[:adet]

class Talep(models.Model):
    DURUMLAR=[
        ("yeni","Yeni"),("sefe_gonderildi","Koordinatöre Gönderildi"),
        ("sahaya_atandi","Sahaya Atandı"),("kabul_edildi","Saha Kabul Etti"),
        ("yolda","Yola Çıkıldı"),("yerinde","Adrese Ulaşıldı"),("islemde","Müdahale Ediliyor"),
        ("onay_bekliyor","Şef Onayı Bekliyor"),("tamamlandi","Tamamlandı"),("iptal","İptal"),
    ]
    ONCELIKLER=[("dusuk","Düşük"),("normal","Normal"),("yuksek","Yüksek"),("acil","Acil")]
    VATANDAS_BILDIRIM_DURUMLARI=[
        ("beklemiyor","Henüz Beklemiyor"),
        ("bekliyor","Geri Bildirim Bekliyor"),
        ("tekrar_aranacak","Tekrar Aranacak"),
        ("bilgilendirildi","Vatandaş Bilgilendirildi"),
    ]
    talep_no=models.CharField(max_length=30,unique=True,blank=True)
    vatandas_ad=models.CharField(max_length=100)
    vatandas_soyad=models.CharField(max_length=100)
    telefon=models.CharField(max_length=20)
    eposta=models.EmailField(blank=True)
    abone=models.ForeignKey("Abone",on_delete=models.SET_NULL,null=True,blank=True,related_name="talepler")
    ilce=models.ForeignKey("adres.Ilce",on_delete=models.PROTECT,related_name="talepler")
    mahalle=models.ForeignKey("adres.Mahalle",on_delete=models.PROTECT,related_name="talepler")
    yol=models.ForeignKey("adres.Yol",on_delete=models.PROTECT,related_name="talepler")
    kapi_no=models.CharField(max_length=30,blank=True)
    adres_aciklama=models.TextField(blank=True)
    lat=models.DecimalField(max_digits=9,decimal_places=6,null=True,blank=True)
    lng=models.DecimalField(max_digits=9,decimal_places=6,null=True,blank=True)
    is_turu=models.ForeignKey(IsTuru,on_delete=models.PROTECT,related_name="talepler")
    is_alt_turu=models.ForeignKey(IsAltTuru,on_delete=models.PROTECT,related_name="talepler")
    aciklama=models.TextField()
    oncelik=models.CharField(max_length=20,choices=ONCELIKLER,default="normal")
    durum=models.CharField(max_length=30,choices=DURUMLAR,default="yeni")
    olusturan=models.ForeignKey(User,on_delete=models.PROTECT,related_name="olusturdugu_talepler")
    sorumlu_koordinator=models.ForeignKey("accounts.PersonelProfili",on_delete=models.SET_NULL,null=True,blank=True,related_name="koordinator_talepleri")
    sorumlu_saha=models.ForeignKey("accounts.PersonelProfili",on_delete=models.SET_NULL,null=True,blank=True,related_name="saha_talepleri")
    olusturulma_tarihi=models.DateTimeField(auto_now_add=True)
    guncellenme_tarihi=models.DateTimeField(auto_now=True)
    tamamlanma_tarihi=models.DateTimeField(null=True,blank=True)
    saha_sonuc_notu=models.TextField(blank=True)
    saha_tamam_bildirim_tarihi=models.DateTimeField(null=True,blank=True)
    sef_onaylayan=models.ForeignKey(
        User,on_delete=models.SET_NULL,null=True,blank=True,
        related_name="onayladigi_talepler"
    )
    sef_onay_tarihi=models.DateTimeField(null=True,blank=True)
    vatandas_bildirim_durumu=models.CharField(
        max_length=30,
        choices=VATANDAS_BILDIRIM_DURUMLARI,
        default="beklemiyor",
    )
    vatandas_bildirim_tarihi=models.DateTimeField(null=True,blank=True)
    vatandas_bildirim_yapan=models.ForeignKey(
        User,on_delete=models.SET_NULL,null=True,blank=True,
        related_name="vatandas_bilgilendirdigi_talepler"
    )
    class Meta:
        ordering=["-olusturulma_tarihi"]
        indexes=[models.Index(fields=["durum","ilce"]),models.Index(fields=["olusturulma_tarihi"])]
    def __str__(self): return self.talep_no
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.mahalle_id and self.ilce_id and self.mahalle.ilce_id!=self.ilce_id:
            raise ValidationError("Seçilen mahalle bu ilçeye ait değil.")
        if self.yol_id and self.mahalle_id and self.yol.mahalle_id!=self.mahalle_id:
            raise ValidationError("Seçilen cadde/sokak bu mahalleye ait değil.")
        if self.is_alt_turu_id and self.is_turu_id and self.is_alt_turu.is_turu_id!=self.is_turu_id:
            raise ValidationError("Seçilen iş alt türü bu iş türüne ait değil.")
    def save(self,*args,**kwargs):
        if not self.talep_no:
            yil=timezone.localdate().year
            son=Talep.objects.filter(talep_no__startswith=f"ISU-{yil}-").order_by("-id").first()
            sira=(son.id+1) if son else 1
            self.talep_no=f"ISU-{yil}-{sira:06d}"
        if self.durum=="tamamlandi" and not self.tamamlanma_tarihi:
            self.tamamlanma_tarihi=timezone.now()

        # Harita servisleri 6'dan fazla ondalık döndürebilir.
        # DecimalField(decimal_places=6) ile uyumlu hale getir.
        if self.lat is not None:
            self.lat=Decimal(str(self.lat)).quantize(
                Decimal("0.000001"),rounding=ROUND_HALF_UP
            )
        if self.lng is not None:
            self.lng=Decimal(str(self.lng)).quantize(
                Decimal("0.000001"),rounding=ROUND_HALF_UP
            )

        self.full_clean()
        super().save(*args,**kwargs)


class Abone(models.Model):
    abone_no=models.CharField(max_length=40,unique=True,db_index=True)
    ad=models.CharField(max_length=100)
    soyad=models.CharField(max_length=100,blank=True)
    telefon=models.CharField(max_length=20,blank=True)
    eposta=models.EmailField(blank=True)
    sayac_no=models.CharField(max_length=60,blank=True)
    ilce=models.ForeignKey("adres.Ilce",on_delete=models.SET_NULL,null=True,blank=True,related_name="aboneler")
    mahalle=models.ForeignKey("adres.Mahalle",on_delete=models.SET_NULL,null=True,blank=True,related_name="aboneler")
    yol=models.ForeignKey("adres.Yol",on_delete=models.SET_NULL,null=True,blank=True,related_name="aboneler")
    kapi_no=models.CharField(max_length=30,blank=True)
    adres_aciklama=models.CharField(max_length=250,blank=True)
    aktif=models.BooleanField(default=True)
    olusturulma_tarihi=models.DateTimeField(auto_now_add=True)
    guncellenme_tarihi=models.DateTimeField(auto_now=True)

    class Meta:
        ordering=["abone_no"]
        indexes=[models.Index(fields=["aktif","abone_no"])]

    def __str__(self):
        return f"{self.abone_no} — {self.ad} {self.soyad}".strip()

    @property
    def tam_adres(self):
        parcalar=[
            self.ilce.ad if self.ilce_id else "",
            self.mahalle.ad if self.mahalle_id else "",
            self.yol.ad if self.yol_id else "",
            f"No: {self.kapi_no}" if self.kapi_no else "",
            self.adres_aciklama or "",
        ]
        return " / ".join(x for x in parcalar if x)


class IsEmri(models.Model):
    DURUMLAR=[
        ("atandi","Sahaya Atandı"),
        ("kabul_edildi","Kabul Edildi"),
        ("yolda","Yola Çıkıldı"),
        ("yerinde","Adrese Ulaşıldı"),
        ("islemde","Müdahale Ediliyor"),
        ("onay_bekliyor","Şef Onayı Bekliyor"),
        ("tamamlandi","Tamamlandı"),
        ("iptal","İptal"),
    ]
    is_emri_no=models.CharField(max_length=30,unique=True,blank=True)
    talep=models.OneToOneField(Talep,on_delete=models.CASCADE,related_name="is_emri")
    gonderen_birim=models.CharField(max_length=160,blank=True)
    olusturan=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name="olusturdugu_is_emirleri")
    atanan_saha=models.ForeignKey("accounts.PersonelProfili",on_delete=models.SET_NULL,null=True,blank=True,related_name="is_emirleri")
    durum=models.CharField(max_length=30,choices=DURUMLAR,default="atandi")
    atama_tarihi=models.DateTimeField(default=timezone.now)
    kabul_tarihi=models.DateTimeField(null=True,blank=True)
    yola_cikis_tarihi=models.DateTimeField(null=True,blank=True)
    adrese_ulasma_tarihi=models.DateTimeField(null=True,blank=True)
    mudahale_baslama_tarihi=models.DateTimeField(null=True,blank=True)
    saha_tamam_tarihi=models.DateTimeField(null=True,blank=True)
    sef_onay_tarihi=models.DateTimeField(null=True,blank=True)
    sonuc_notu=models.TextField(blank=True)

    # V31 — Mobil saha kanıtı ve GPS doğrulaması.
    once_foto=models.ImageField(upload_to="is_emri/once/%Y/%m/",null=True,blank=True)
    sonra_foto=models.ImageField(upload_to="is_emri/sonra/%Y/%m/",null=True,blank=True)
    gps_lat=models.DecimalField(max_digits=9,decimal_places=6,null=True,blank=True)
    gps_lng=models.DecimalField(max_digits=9,decimal_places=6,null=True,blank=True)
    gps_mesafe_m=models.PositiveIntegerField(null=True,blank=True)
    gps_dogrulandi=models.BooleanField(default=False)
    gps_dogrulama_tarihi=models.DateTimeField(null=True,blank=True)

    olusturulma_tarihi=models.DateTimeField(auto_now_add=True)
    guncellenme_tarihi=models.DateTimeField(auto_now=True)

    class Meta:
        ordering=["-olusturulma_tarihi"]
        indexes=[
            models.Index(fields=["durum","atama_tarihi"]),
            models.Index(fields=["gonderen_birim","durum"]),
        ]

    def __str__(self):
        return self.is_emri_no or f"İş Emri #{self.pk}"

    def save(self,*args,**kwargs):
        if not self.is_emri_no:
            yil=timezone.localdate().year
            son=IsEmri.objects.filter(is_emri_no__startswith=f"IE-{yil}-").order_by("-id").first()
            sira=(son.id+1) if son else 1
            self.is_emri_no=f"IE-{yil}-{sira:06d}"
        super().save(*args,**kwargs)


class IsEmriFotograf(models.Model):
    """V42 — İş alt türünün zorunlu fotoğraf slotlarına bağlı iş emri görselleri."""
    is_emri=models.ForeignKey(IsEmri,on_delete=models.CASCADE,related_name="fotograflar")
    sira=models.PositiveSmallIntegerField()
    etiket=models.CharField(max_length=160)
    foto=models.ImageField(upload_to="is_emri/kanit/%Y/%m/")
    yukleyen=models.ForeignKey(
        User,on_delete=models.SET_NULL,null=True,blank=True,related_name="yukledigi_is_emri_fotograflari"
    )
    yuklenme_tarihi=models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering=["sira","yuklenme_tarihi"]
        constraints=[
            models.UniqueConstraint(fields=["is_emri","sira"],name="uq_is_emri_foto_slot")
        ]
        indexes=[models.Index(fields=["is_emri","sira"],name="talepler_is_is_emri_27f408_idx")]

    def __str__(self):
        return f"{self.is_emri.is_emri_no} — {self.etiket}"


class MobilToken(models.Model):
    kullanici=models.OneToOneField(User,on_delete=models.CASCADE,related_name="mobil_token")
    anahtar=models.CharField(max_length=64,unique=True)
    olusturulma_tarihi=models.DateTimeField(auto_now_add=True)
    son_kullanim=models.DateTimeField(null=True,blank=True)
    aktif=models.BooleanField(default=True)

    def __str__(self):
        return f"{self.kullanici.username} mobil token"


class MobilBildirim(models.Model):
    TIPLER=[
        ("yeni_is","Yeni İş Emri"),
        ("geri_gonderildi","Şef Geri Gönderdi"),
        ("acil","Acil İş"),
        ("bilgi","Bilgilendirme"),
    ]
    kullanici=models.ForeignKey(User,on_delete=models.CASCADE,related_name="mobil_bildirimler")
    is_emri=models.ForeignKey(IsEmri,on_delete=models.CASCADE,null=True,blank=True,related_name="mobil_bildirimler")
    tip=models.CharField(max_length=30,choices=TIPLER,default="bilgi")
    baslik=models.CharField(max_length=140)
    mesaj=models.CharField(max_length=400)
    okundu=models.BooleanField(default=False)
    olusturulma_tarihi=models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering=["-olusturulma_tarihi"]
        indexes=[
            models.Index(fields=["kullanici","okundu","olusturulma_tarihi"]),
        ]

    def __str__(self):
        return f"{self.kullanici.username} — {self.baslik}"



class GeriBildirim(models.Model):
    talep=models.ForeignKey(Talep,on_delete=models.CASCADE,related_name="geri_bildirimler")
    kullanici=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    mesaj=models.TextField()
    durum=models.CharField(max_length=30,blank=True)
    tarih=models.DateTimeField(auto_now_add=True)
    sistem_mesaji=models.BooleanField(default=False)
    class Meta: ordering=["-tarih"]


class VatandasAramaKaydi(models.Model):
    SONUCLAR=[
        ("bilgilendirildi","Vatandaş Bilgilendirildi"),
        ("ulasilamadi","Vatandaşa Ulaşılamadı"),
        ("tekrar_aranacak","Tekrar Aranacak"),
    ]
    talep=models.ForeignKey(
        Talep,on_delete=models.CASCADE,related_name="vatandas_arama_kayitlari"
    )
    kullanici=models.ForeignKey(
        User,on_delete=models.SET_NULL,null=True,blank=True,
        related_name="vatandas_arama_kayitlari"
    )
    sonuc=models.CharField(max_length=30,choices=SONUCLAR)
    not_metni=models.CharField(max_length=300,blank=True)
    tarih=models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering=["-tarih"]
        indexes=[
            models.Index(fields=["talep","tarih"]),
            models.Index(fields=["sonuc","tarih"]),
        ]

    def __str__(self):
        return f"{self.talep.talep_no} / {self.get_sonuc_display()}"

class IslemLogu(models.Model):
    talep=models.ForeignKey(Talep,on_delete=models.CASCADE,related_name="loglar",null=True,blank=True)
    kullanici=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    islem=models.CharField(max_length=80)
    aciklama=models.TextField(blank=True)
    varlik_turu=models.CharField(max_length=80,blank=True)
    varlik_id=models.CharField(max_length=80,blank=True)
    eski_deger=models.TextField(blank=True)
    yeni_deger=models.TextField(blank=True)
    ip_adresi=models.GenericIPAddressField(null=True,blank=True)
    tarih=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=["-tarih"]
        indexes=[models.Index(fields=["tarih","islem"])]
