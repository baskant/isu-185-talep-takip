from django import forms
from .models import DevirBasvurusu


class DevirBasvuruForm(forms.ModelForm):
    """Yalnızca yeni aboneye ait bilgiler kullanıcıdan alınır.

    Eski abonelik, adres ve sökülen sayaç bilgileri sorgulanan mevcut abonelik
    kaydından backend tarafından doldurulur. Yeni abone numarası da sistemce üretilir.
    """

    class Meta:
        model = DevirBasvurusu
        fields = [
            "vatandas_ad_soyad", "telefon", "tc_kimlik_no", "devir_nedeni", "aciklama",
        ]
        widgets = {
            "vatandas_ad_soyad": forms.TextInput(attrs={
                "autocomplete": "name",
                "placeholder": "Yeni abonenin ad soyadı",
            }),
            "telefon": forms.TextInput(attrs={
                "placeholder": "05xx xxx xx xx",
                "autocomplete": "tel",
                "inputmode": "tel",
            }),
            "tc_kimlik_no": forms.TextInput(attrs={
                "maxlength": "11",
                "inputmode": "numeric",
                "autocomplete": "off",
                "placeholder": "11 hane (isteğe bağlı)",
            }),
            "aciklama": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Devir işlemiyle ilgili kısa not",
                "autocomplete": "off",
            }),
        }
        labels = {
            "vatandas_ad_soyad": "Yeni Abone Ad Soyad",
            "telefon": "Yeni Abone Telefon",
            "tc_kimlik_no": "Yeni Abone T.C. Kimlik No",
        }
        error_messages = {
            "vatandas_ad_soyad": {"required": "Yeni abonenin ad soyad bilgisi zorunludur."},
            "telefon": {"required": "Yeni abonenin telefon bilgisi zorunludur."},
            "devir_nedeni": {"required": "Devir nedeni seçimi zorunludur."},
        }

    def clean_vatandas_ad_soyad(self):
        value = (self.cleaned_data.get("vatandas_ad_soyad") or "").strip()
        if not value:
            raise forms.ValidationError("Yeni abonenin ad soyad bilgisi zorunludur.")
        if len(value) < 3:
            raise forms.ValidationError("Ad soyad bilgisi en az 3 karakter olmalıdır.")
        return " ".join(value.split())

    def clean_telefon(self):
        value = (self.cleaned_data.get("telefon") or "").strip()
        if not value:
            raise forms.ValidationError("Telefon bilgisi zorunludur.")
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) < 10 or len(digits) > 11:
            raise forms.ValidationError("Telefon numarası 10 veya 11 rakam içermelidir.")
        return value

    def clean_tc_kimlik_no(self):
        value = (self.cleaned_data.get("tc_kimlik_no") or "").strip()
        if value and (not value.isdigit() or len(value) != 11):
            raise forms.ValidationError("T.C. kimlik numarası girilecekse 11 rakam olmalıdır.")
        return value


class AmbarKayitForm(forms.Form):
    depo_konumu = forms.CharField(
        max_length=120,
        label="Depo / Raf Konumu",
        widget=forms.TextInput(attrs={"placeholder": "Örn. A Blok / Raf 12", "autocomplete": "off"}),
    )
    ambar_notu = forms.CharField(
        max_length=300,
        required=False,
        label="Ambar Notu",
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "İsteğe bağlı kısa not", "autocomplete": "off"}),
    )
