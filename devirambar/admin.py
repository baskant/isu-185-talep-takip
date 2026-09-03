from django.contrib import admin
from .models import AbonelikKaydi, DevirBasvurusu, DevirHareketi


@admin.register(AbonelikKaydi)
class AbonelikKaydiAdmin(admin.ModelAdmin):
    list_display = ("abone_no", "abone_ad_soyad", "ilce", "sayac_seri_no", "aktif", "olusturulma_tarihi")
    list_filter = ("aktif", "ilce")
    search_fields = ("abone_no", "abone_ad_soyad", "telefon", "sayac_seri_no", "adres")


@admin.register(DevirBasvurusu)
class DevirBasvurusuAdmin(admin.ModelAdmin):
    list_display = ("basvuru_no", "eski_abone_no", "yeni_abone_no", "vatandas_ad_soyad", "ilce", "sayac_seri_no", "durum", "olusturulma_tarihi")
    list_filter = ("durum", "ilce", "devir_nedeni")
    search_fields = ("basvuru_no", "eski_abone_ad_soyad", "vatandas_ad_soyad", "telefon", "sayac_seri_no", "eski_abone_no", "yeni_abone_no")


@admin.register(DevirHareketi)
class DevirHareketiAdmin(admin.ModelAdmin):
    list_display = ("basvuru", "islem", "kullanici", "tarih")
    search_fields = ("basvuru__basvuru_no", "islem", "aciklama")
