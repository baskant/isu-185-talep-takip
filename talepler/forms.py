from django import forms
from adres.models import Mahalle, Yol
from .models import Talep, IsAltTuru, IsTuru, Abone

class TalepForm(forms.ModelForm):
    abone_no = forms.CharField(
        required=False,
        max_length=40,
        label="Abone No",
        widget=forms.TextInput(attrs={"placeholder":"Abone no (isteğe bağlı)","autocomplete":"off"})
    )

    yol_serbest = forms.CharField(
        required=False,
        max_length=200,
        label="Cadde / Sokak listede yoksa yazınız",
        widget=forms.TextInput(attrs={
            "placeholder": "Örn. Atatürk Caddesi, 1024. Sokak..."
        }),
        help_text="Listede yol bulunamazsa buraya gerçek cadde/sokak adını yazabilirsiniz."
    )

    class Meta:
        model = Talep
        fields = [
            "abone_no", "vatandas_ad", "vatandas_soyad", "telefon", "eposta",
            "ilce", "mahalle", "yol", "yol_serbest",
            "kapi_no", "adres_aciklama", "lat", "lng",
            "is_turu", "is_alt_turu", "aciklama", "oncelik",
        ]
        widgets = {
            "lat": forms.HiddenInput(),
            "lng": forms.HiddenInput(),
            "vatandas_ad": forms.TextInput(attrs={"placeholder": "Vatandaşın adı"}),
            "vatandas_soyad": forms.TextInput(attrs={"placeholder": "Vatandaşın soyadı"}),
            "telefon": forms.TextInput(attrs={"placeholder": "05xx xxx xx xx"}),
            "eposta": forms.EmailInput(attrs={"placeholder": "ornek@eposta.com"}),
            "kapi_no": forms.TextInput(attrs={"placeholder": "Kapı no"}),
            "adres_aciklama": forms.Textarea(attrs={
                "rows": 2,
                "placeholder": "Bina, site, yakınındaki bilinen yer veya ek adres tarifi..."
            }),
            "aciklama": forms.Textarea(attrs={
                "rows": 5,
                "placeholder": "Arızayı ayrıntılı şekilde açıklayın..."
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["ilce"].empty_label = "İlçe seçiniz"
        self.fields["mahalle"].empty_label = "Önce ilçe seçiniz"
        self.fields["yol"].empty_label = "Önce mahalle seçiniz"
        self.fields["is_turu"].empty_label = "İş türü seçiniz"
        self.fields["is_alt_turu"].empty_label = "Önce iş türü seçiniz"

        # OSM/kurum yol listesi eksik olduğunda manuel yol girişi kullanılabilsin.
        self.fields["yol"].required = False

        self.fields["mahalle"].queryset = Mahalle.objects.none()
        self.fields["yol"].queryset = Yol.objects.none()
        self.fields["is_alt_turu"].queryset = IsAltTuru.objects.none()

        if self.instance and self.instance.pk:
            self.fields["mahalle"].queryset = Mahalle.objects.filter(
                ilce=self.instance.ilce, aktif=True
            ).order_by("ad")
            self.fields["yol"].queryset = Yol.objects.filter(
                mahalle=self.instance.mahalle, aktif=True
            ).order_by("ad")
            self.fields["is_alt_turu"].queryset = IsAltTuru.objects.filter(
                is_turu=self.instance.is_turu, aktif=True
            ).order_by("ad")

        data = self.data or None
        if data:
            try:
                self.fields["mahalle"].queryset = Mahalle.objects.filter(
                    ilce_id=int(data.get("ilce")), aktif=True
                ).order_by("ad")
            except (TypeError, ValueError):
                pass
            try:
                self.fields["yol"].queryset = Yol.objects.filter(
                    mahalle_id=int(data.get("mahalle")), aktif=True
                ).order_by("ad")
            except (TypeError, ValueError):
                pass
            try:
                self.fields["is_alt_turu"].queryset = IsAltTuru.objects.filter(
                    is_turu_id=int(data.get("is_turu")), aktif=True
                ).order_by("ad")
            except (TypeError, ValueError):
                pass

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("mahalle") and not cleaned.get("yol") and not (cleaned.get("yol_serbest") or "").strip():
            self.add_error(
                "yol_serbest",
                "Cadde/sokak listeden seçilemiyorsa gerçek yol adını bu alana yazın."
            )

        # Haritada yanlışlıkla başka şehir/ülke noktası seçildiyse o koordinatı
        # kaydetmeyiz. View adresi yeniden geocode ederek Kocaeli içi konum bulur.
        lat=cleaned.get("lat"); lng=cleaned.get("lng")
        if (lat is None) != (lng is None):
            cleaned["lat"]=None; cleaned["lng"]=None
        elif lat is not None and lng is not None:
            try:
                latf=float(lat); lngf=float(lng)
            except (TypeError, ValueError):
                cleaned["lat"]=None; cleaned["lng"]=None
            else:
                if not (40.35 <= latf <= 41.35 and 29.00 <= lngf <= 30.90):
                    cleaned["lat"]=None; cleaned["lng"]=None
        return cleaned


class IsTuruForm(forms.ModelForm):
    class Meta:
        model = IsTuru
        fields = ["ad", "kod", "aktif", "aciklama"]


class IsAltTuruForm(forms.ModelForm):
    class Meta:
        model = IsAltTuru
        fields = ["is_turu", "ad", "aktif", "zorunlu_fotograf_sayisi", "fotograf_etiketleri"]
        widgets={
            "zorunlu_fotograf_sayisi":forms.NumberInput(attrs={"min":1,"max":8}),
            "fotograf_etiketleri":forms.Textarea(attrs={
                "rows":4,
                "placeholder":"Her satıra bir zorunlu fotoğraf adı yazın.\nÖrn. Müdahale Öncesi\nMüdahale Sonrası",
            }),
        }
        labels={
            "zorunlu_fotograf_sayisi":"Zorunlu Fotoğraf Sayısı",
            "fotograf_etiketleri":"Fotoğraf Adları",
        }



class AboneForm(forms.ModelForm):
    class Meta:
        model=Abone
        fields=[
            "abone_no","ad","soyad","telefon","eposta","sayac_no",
            "ilce","mahalle","yol","kapi_no","adres_aciklama","aktif",
        ]
        widgets={
            "abone_no":forms.TextInput(attrs={"placeholder":"Abone No"}),
            "ad":forms.TextInput(attrs={"placeholder":"Ad"}),
            "soyad":forms.TextInput(attrs={"placeholder":"Soyad"}),
            "telefon":forms.TextInput(attrs={"placeholder":"05xx xxx xx xx"}),
            "sayac_no":forms.TextInput(attrs={"placeholder":"Sayaç No"}),
            "adres_aciklama":forms.TextInput(attrs={"placeholder":"Ek adres tarifi"}),
        }

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        from adres.models import Ilce, Mahalle, Yol
        self.fields["ilce"].required=False
        self.fields["mahalle"].required=False
        self.fields["yol"].required=False
        self.fields["ilce"].queryset=Ilce.objects.filter(aktif=True).order_by("ad")
        self.fields["mahalle"].queryset=Mahalle.objects.filter(aktif=True).order_by("ad")
        self.fields["yol"].queryset=Yol.objects.filter(aktif=True).order_by("ad")
