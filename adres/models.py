from django.db import models

class Ilce(models.Model):
    ad = models.CharField(max_length=100, unique=True)
    aktif = models.BooleanField(default=True)
    merkez_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    merkez_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    class Meta:
        ordering = ["ad"]
    def __str__(self): return self.ad

class Mahalle(models.Model):
    ilce = models.ForeignKey(Ilce, on_delete=models.CASCADE, related_name="mahalleler")
    ad = models.CharField(max_length=150)
    aktif = models.BooleanField(default=True)
    merkez_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    merkez_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    class Meta:
        ordering = ["ilce__ad", "ad"]
        constraints = [models.UniqueConstraint(fields=["ilce","ad"], name="uq_ilce_mahalle")]
    def __str__(self): return f"{self.ilce.ad} / {self.ad}"

class Yol(models.Model):
    TUR = [("cadde","Cadde"),("sokak","Sokak"),("bulvar","Bulvar"),("meydan","Meydan"),("diger","Diğer")]
    mahalle = models.ForeignKey(Mahalle, on_delete=models.CASCADE, related_name="yollar")
    ad = models.CharField(max_length=200)
    tur = models.CharField(max_length=20, choices=TUR, default="sokak")
    aktif = models.BooleanField(default=True)
    merkez_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    merkez_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    class Meta:
        ordering = ["mahalle__ilce__ad","mahalle__ad","ad"]
        constraints = [models.UniqueConstraint(fields=["mahalle","ad"], name="uq_mahalle_yol")]
    def __str__(self): return f"{self.mahalle} / {self.ad}"
