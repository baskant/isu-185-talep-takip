import re

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, validate_email
from django.utils import timezone

from .models import (
    AmbarSayacTalebi,
    SayacEnvanteri,
    Sozlesme,
    VatandasIletisim,
    VatandasSicili,
)


def _sadece_rakam(value):
    return re.sub(r"\D", "", value or "")


class VatandasSicilForm(forms.ModelForm):
    tc_kimlik_no = forms.CharField(
        min_length=11,
        max_length=11,
        validators=[RegexValidator(r"^\d{11}$", "T.C. Kimlik No 11 rakam olmalıdır.")],
        widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "off"}),
    )
    cep_telefonu = forms.CharField(
        required=False,
        max_length=30,
        widget=forms.TextInput(attrs={"autocomplete": "off", "placeholder": "Örn. 05xx xxx xx xx"}),
        label="Cep Telefonu",
    )
    eposta = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={"autocomplete": "off", "placeholder": "ornek@eposta.com"}),
        label="E-posta",
    )

    class Meta:
        model = VatandasSicili
        fields = ["tc_kimlik_no", "ad", "soyad", "dogum_tarihi", "aktif"]
        widgets = {
            "dogum_tarihi": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_tc_kimlik_no(self):
        value = (self.cleaned_data.get("tc_kimlik_no") or "").strip()
        if not value.isdigit() or len(value) != 11:
            raise ValidationError("T.C. Kimlik No 11 rakam olmalıdır.")
        qs = VatandasSicili.objects.filter(tc_kimlik_no=value)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Bu T.C. Kimlik No ile daha önce vatandaş sicili oluşturulmuş.")
        return value

    def clean_ad(self):
        value = (self.cleaned_data.get("ad") or "").strip()
        if not value:
            raise ValidationError("Ad alanı boş bırakılamaz.")
        return value

    def clean_soyad(self):
        value = (self.cleaned_data.get("soyad") or "").strip()
        if not value:
            raise ValidationError("Soyad alanı boş bırakılamaz.")
        return value

    def clean_dogum_tarihi(self):
        value = self.cleaned_data.get("dogum_tarihi")
        if value and value > timezone.localdate():
            raise ValidationError("Doğum tarihi ileri bir tarih olamaz.")
        return value

    def clean_cep_telefonu(self):
        value = (self.cleaned_data.get("cep_telefonu") or "").strip()
        if value:
            digits = _sadece_rakam(value)
            if len(digits) < 10 or len(digits) > 15:
                raise ValidationError("Telefon numarası 10-15 rakam arasında olmalıdır.")
        return value


class IletisimForm(forms.ModelForm):
    class Meta:
        model = VatandasIletisim
        fields = ["tur", "deger", "aciklama"]
        widgets = {
            "deger": forms.TextInput(attrs={"autocomplete": "off", "placeholder": "Yeni iletişim bilgisi"}),
            "aciklama": forms.TextInput(attrs={"placeholder": "Opsiyonel açıklama"}),
        }

    def clean_deger(self):
        deger = (self.cleaned_data.get("deger") or "").strip()
        tur = self.cleaned_data.get("tur")
        if not deger:
            raise ValidationError("İletişim bilgisi boş bırakılamaz.")
        if tur == VatandasIletisim.IletisimTuru.EPOSTA:
            try:
                validate_email(deger)
            except ValidationError:
                raise
            except Exception:
                raise ValidationError("Geçerli bir e-posta adresi girin.")
        elif tur in {
            VatandasIletisim.IletisimTuru.CEP_TELEFONU,
            VatandasIletisim.IletisimTuru.SABIT_TELEFON,
        }:
            digits = _sadece_rakam(deger)
            if len(digits) < 10 or len(digits) > 15:
                raise ValidationError("Telefon numarası 10-15 rakam arasında olmalıdır.")
        return deger

    def clean_aciklama(self):
        return (self.cleaned_data.get("aciklama") or "").strip()


class SozlesmeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Devir akışı aktif modülden çıkarıldı; tarihsel kayıt değeri modelde korunur.
        self.fields["kaynak"].choices = [x for x in self.fields["kaynak"].choices if x[0] != "devir"]

    class Meta:
        model = Sozlesme
        fields = ["adres", "abonelik_turu", "kaynak", "baslangic_tarihi", "aciklama"]
        widgets = {
            "baslangic_tarihi": forms.DateInput(attrs={"type": "date"}),
            "aciklama": forms.TextInput(attrs={"placeholder": "Opsiyonel sözleşme notu"}),
        }

    def clean_adres(self):
        adres = self.cleaned_data.get("adres")
        if not adres or not adres.aktif:
            raise ValidationError("Aktif bir hizmet adresi seçilmelidir.")
        return adres

    def clean_baslangic_tarihi(self):
        value = self.cleaned_data.get("baslangic_tarihi")
        if not value:
            raise ValidationError("Başlangıç tarihi zorunludur.")
        return value

    def clean_aciklama(self):
        return (self.cleaned_data.get("aciklama") or "").strip()


class AmbarSayacTalepForm(forms.ModelForm):
    class Meta:
        model = AmbarSayacTalebi
        fields = ["sayac_tipi", "cap_mm", "adet", "gerekce"]
        widgets = {
            "cap_mm": forms.NumberInput(attrs={"min": 10, "max": 200}),
            "adet": forms.NumberInput(attrs={"min": 1, "max": 200}),
            "gerekce": forms.TextInput(attrs={"placeholder": "Örn. İlçe sayaç değişim stoğu için"}),
        }

    def clean_cap_mm(self):
        cap = self.cleaned_data.get("cap_mm")
        if cap is None or cap < 10 or cap > 200:
            raise ValidationError("Sayaç çapı 10 ile 200 mm arasında olmalıdır.")
        return cap

    def clean_adet(self):
        adet = self.cleaned_data.get("adet")
        if adet is None or adet < 1 or adet > 200:
            raise ValidationError("Talep adedi 1 ile 200 arasında olmalıdır.")
        return adet

    def clean_gerekce(self):
        value = (self.cleaned_data.get("gerekce") or "").strip()
        if len(value) < 5:
            raise ValidationError("Talep gerekçesi en az 5 karakter olmalıdır.")
        return value


class SayacAtamaForm(forms.Form):
    sayac = forms.ModelChoiceField(
        queryset=SayacEnvanteri.objects.none(),
        label="Stoktaki Sayaç",
        empty_label="Sayaç seçin",
    )
    takilma_tarihi = forms.DateField(
        label="Takılma Tarihi",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    ilk_endeks = forms.DecimalField(
        label="İlk Endeks",
        required=False,
        max_digits=12,
        decimal_places=3,
        min_value=0,
        widget=forms.NumberInput(attrs={"step": "0.001", "min": "0"}),
    )
    aciklama = forms.CharField(
        label="İşlem Notu",
        required=False,
        max_length=250,
        widget=forms.TextInput(attrs={"placeholder": "Örn. Yeni abonelik / sayaç değişimi"}),
    )

    def __init__(self, *args, sayac_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if sayac_queryset is not None:
            self.fields["sayac"].queryset = sayac_queryset

    def clean_takilma_tarihi(self):
        value = self.cleaned_data.get("takilma_tarihi")
        if value and value > timezone.localdate():
            raise ValidationError("Sayaç takılma tarihi ileri bir tarih olamaz.")
        return value


class MerkezStokGirisForm(forms.ModelForm):
    class Meta:
        model = SayacEnvanteri
        fields = ["sayac_no", "seri_no", "marka_model", "sayac_tipi", "cap_mm", "son_endeks"]
        widgets = {
            "sayac_no": forms.TextInput(attrs={"autocomplete": "off", "placeholder": "Sayaç numarası"}),
            "seri_no": forms.TextInput(attrs={"autocomplete": "off", "placeholder": "Üretici seri numarası"}),
            "marka_model": forms.TextInput(attrs={"placeholder": "Marka / model"}),
            "cap_mm": forms.NumberInput(attrs={"min": 10, "max": 200}),
            "son_endeks": forms.NumberInput(attrs={"step": "0.001", "min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["marka_model"].required = True

    def clean_sayac_no(self):
        value = (self.cleaned_data.get("sayac_no") or "").strip()
        if not value:
            raise ValidationError("Sayaç numarası zorunludur.")
        qs = SayacEnvanteri.objects.filter(sayac_no__iexact=value)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Bu sayaç numarası sistemde zaten kayıtlı.")
        return value

    def clean_seri_no(self):
        value = (self.cleaned_data.get("seri_no") or "").strip()
        if not value:
            raise ValidationError("Seri numarası zorunludur.")
        qs = SayacEnvanteri.objects.filter(seri_no__iexact=value)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Bu seri numarası sistemde zaten kayıtlı.")
        return value

    def clean_marka_model(self):
        value = (self.cleaned_data.get("marka_model") or "").strip()
        if not value:
            raise ValidationError("Marka / model bilgisi zorunludur.")
        return value

    def clean_cap_mm(self):
        cap = self.cleaned_data.get("cap_mm")
        if cap is None or cap < 10 or cap > 200:
            raise ValidationError("Sayaç çapı 10 ile 200 mm arasında olmalıdır.")
        return cap

    def clean_son_endeks(self):
        value = self.cleaned_data.get("son_endeks")
        if value is not None and value < 0:
            raise ValidationError("Sayaç endeksi negatif olamaz.")
        return value
