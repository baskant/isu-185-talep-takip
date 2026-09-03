from django.contrib.auth.models import User
from django.db import models

class Rol(models.Model):
    PANEL=[("admin","Sistem Yönetimi"),("185","185 Çağrı Merkezi"),("sef","Şef / Koordinatör"),("saha","Saha"),("abone","Abone İşlemleri"),("merkez_ambar","Merkez Ambar")]
    CALISMA_KANALLARI=[
        ("web","Web / PC"),
        ("mobil","Mobil Saha"),
        ("her_ikisi","Web + Mobil"),
    ]
    ad=models.CharField(max_length=100,unique=True)
    kod=models.SlugField(max_length=100,unique=True)
    panel_tipi=models.CharField(max_length=20,choices=PANEL,default="saha")
    calisma_kanali=models.CharField(
        max_length=20,
        choices=CALISMA_KANALLARI,
        default="web",
        help_text="Bu role bağlı kullanıcıların operasyon ekranına hangi kanaldan gireceğini belirler.",
    )
    parent=models.ForeignKey("self",on_delete=models.SET_NULL,null=True,blank=True,related_name="child_roller")
    aktif=models.BooleanField(default=True)
    aciklama=models.CharField(max_length=250,blank=True)
    class Meta: ordering=["ad"]
    def __str__(self): return self.ad

    def mobil_erisim_var_mi(self):
        return self.calisma_kanali in ("mobil","her_ikisi")

    def web_erisim_var_mi(self):
        return self.calisma_kanali in ("web","her_ikisi")

class RolAtamaKurali(models.Model):
    kaynak_rol=models.ForeignKey(Rol,on_delete=models.CASCADE,related_name="kaynak_kurallari")
    hedef_rol=models.ForeignKey(Rol,on_delete=models.CASCADE,related_name="hedef_kurallari")
    aktif=models.BooleanField(default=True)
    aciklama=models.CharField(max_length=250,blank=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=["kaynak_rol","hedef_rol"],name="uq_rol_atama_kurali")]
    def __str__(self): return f"{self.kaynak_rol} → {self.hedef_rol}"

class PersonelProfili(models.Model):
    kullanici=models.OneToOneField(User,on_delete=models.CASCADE,related_name="personel_profili")
    rol=models.ForeignKey(Rol,on_delete=models.PROTECT,related_name="personeller")
    yetkili_ilceler=models.ManyToManyField("adres.Ilce",blank=True,related_name="yetkili_personeller")
    uzmanlik_is_turleri=models.ManyToManyField("talepler.IsTuru",blank=True,related_name="uzman_personeller")
    telefon=models.CharField(max_length=20,blank=True)
    sicil_no=models.CharField(max_length=50,blank=True,null=True,unique=True)
    aktif=models.BooleanField(default=True)
    musait=models.BooleanField(default=True)
    son_aktivite=models.DateTimeField(null=True,blank=True)
    def __str__(self):
        return f"{self.kullanici.get_full_name() or self.kullanici.username} — {self.rol.ad}"
    def ilceye_yetkili_mi(self,ilce):
        return self.kullanici.is_superuser or self.rol.panel_tipi=="admin" or self.yetkili_ilceler.filter(pk=ilce.pk).exists()
    def is_turune_yetkili_mi(self,is_turu):
        if self.kullanici.is_superuser or self.rol.panel_tipi=="admin": return True
        qs=self.uzmanlik_is_turleri.all()
        return (not qs.exists()) or qs.filter(pk=is_turu.pk).exists()
