from django.contrib import admin

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


class TarihceSilinemezAdmin(admin.ModelAdmin):
    """Sicil/sözleşme geçmişi fiziksel olarak silinmez; aktif-pasif tutulur."""

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(VatandasSicili)
class VatandasSiciliAdmin(TarihceSilinemezAdmin):
    list_display = ("sicil_no", "tc_kimlik_no", "ad", "soyad", "dogum_tarihi", "aktif")
    search_fields = ("sicil_no", "tc_kimlik_no", "ad", "soyad")
    list_filter = ("aktif",)


@admin.register(VatandasIletisim)
class VatandasIletisimAdmin(TarihceSilinemezAdmin):
    list_display = ("sicil", "tur", "deger", "aktif", "baslangic_tarihi", "bitis_tarihi")
    list_filter = ("tur", "aktif")
    search_fields = ("sicil__sicil_no", "sicil__tc_kimlik_no", "deger")


@admin.register(Sozlesme)
class SozlesmeAdmin(TarihceSilinemezAdmin):
    list_display = ("sozlesme_no", "abone_no", "sicil", "adres", "abonelik_turu", "aktif")
    list_filter = ("aktif", "abonelik_turu", "kaynak")
    search_fields = ("sozlesme_no", "abone_no", "sicil__tc_kimlik_no", "sicil__sicil_no")


@admin.register(HizmetAdresi)
class HizmetAdresiAdmin(admin.ModelAdmin):
    list_display = ("adres_kodu", "ilce", "mahalle", "cadde_sokak", "kapi_no", "daire_no", "aktif")
    list_filter = ("ilce", "aktif")
    search_fields = ("adres_kodu", "mahalle", "cadde_sokak", "kapi_no", "daire_no")


@admin.register(SayacEnvanteri)
class SayacEnvanteriAdmin(admin.ModelAdmin):
    list_display = ("sayac_no", "seri_no", "marka_model", "sayac_tipi", "cap_mm", "durum", "ambar", "aktif")
    list_filter = ("durum", "sayac_tipi", "cap_mm", "ambar", "aktif")
    search_fields = ("sayac_no", "seri_no", "marka_model")


@admin.register(AboneSayac)
class AboneSayacAdmin(TarihceSilinemezAdmin):
    list_display = ("sozlesme", "sayac", "aktif", "takilma_tarihi", "sokulme_tarihi")
    list_filter = ("aktif",)
    search_fields = ("sozlesme__abone_no", "sayac__sayac_no", "sayac__seri_no")


@admin.register(Ambar)
class AmbarAdmin(admin.ModelAdmin):
    list_display = ("kod", "ad", "tur", "ilce", "aktif")
    list_filter = ("tur", "aktif", "ilce")


@admin.register(AmbarYetkisi)
class AmbarYetkisiAdmin(admin.ModelAdmin):
    list_display = ("ilce", "personel", "ambar", "aktif", "atanma_tarihi")
    list_filter = ("aktif", "ilce")


@admin.register(AmbarSayacTalebi)
class AmbarSayacTalebiAdmin(admin.ModelAdmin):
    list_display = ("talep_no", "yetki", "sayac_tipi", "cap_mm", "adet", "durum", "talep_tarihi")
    list_filter = ("durum", "sayac_tipi", "cap_mm")
    search_fields = ("talep_no", "yetki__ilce__ad", "gerekce")


@admin.register(AmbarHareketi)
class AmbarHareketiAdmin(TarihceSilinemezAdmin):
    list_display = ("tarih", "islem", "sayac", "kaynak_ambar", "hedef_ambar", "kullanici")
    list_filter = ("islem", "kaynak_ambar", "hedef_ambar")
    search_fields = ("sayac__sayac_no", "sayac__seri_no", "talep__talep_no", "aciklama")
