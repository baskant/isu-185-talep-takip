from django import forms

from .models import Rol, RolAtamaKurali
from .saha_blueprint import blueprint_for_role


class PersonelOlusturForm(forms.Form):
    kayit_alani = forms.ChoiceField(
        choices=[],
        label="Kayıt Alanı",
        help_text="Önce hangi organizasyon alanına kayıt ekleneceğini seçin.",
    )
    kullanici_adi = forms.CharField(
        max_length=150,
        required=False,
        label="Kullanıcı adı",
    )
    ad = forms.CharField(max_length=100, required=False, label="Ad")
    soyad = forms.CharField(max_length=100, required=False, label="Soyad")
    eposta = forms.EmailField(required=False, label="E-posta")
    gecici_sifre = forms.CharField(
        max_length=128,
        required=False,
        label="Geçici şifre",
        help_text="Boş bırakılırsa güvenli geçici şifre üretilir.",
    )
    yetkili_ilceler = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        label="Yetkili ilçe",
        widget=forms.SelectMultiple(attrs={"size": 6}),
    )
    uzmanlik_is_turleri = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        label="Uzmanlık iş türleri",
        widget=forms.SelectMultiple(attrs={"size": 6}),
    )
    telefon = forms.CharField(max_length=20, required=False, label="Telefon")
    sicil_no = forms.CharField(max_length=50, required=False, label="Sicil no")

    def __init__(self, *args, **kwargs):
        from adres.models import Ilce
        from talepler.models import IsTuru

        super().__init__(*args, **kwargs)

        roles = Rol.objects.filter(aktif=True).exclude(kod="admin").order_by(
            "panel_tipi", "ad"
        )
        choices = [
            ("", "Kayıt alanını seçiniz"),
            (
                "auto",
                "Otomatik Organizasyon — eksik koordinatör ve saha ekiplerini tamamla",
            ),
        ]
        for role in roles:
            panel = role.get_panel_tipi_display()
            kanal = role.get_calisma_kanali_display()
            choices.append((f"rol:{role.pk}", f"{role.ad} — {panel} — {kanal}"))

        self.fields["kayit_alani"].choices = choices
        self.fields["yetkili_ilceler"].queryset = Ilce.objects.filter(
            aktif=True
        ).order_by("ad")
        self.fields["uzmanlik_is_turleri"].queryset = IsTuru.objects.filter(
            aktif=True
        ).order_by("ad")

        self.fields["kullanici_adi"].widget.attrs["placeholder"] = "Örn. 185_personeli_2"
        self.fields["ad"].widget.attrs["placeholder"] = "Ad"
        self.fields["soyad"].widget.attrs["placeholder"] = "Soyad"
        self.fields["eposta"].widget.attrs["placeholder"] = "ornek@isu.gov.tr"
        self.fields["gecici_sifre"].widget.attrs["placeholder"] = "Boş bırakılabilir"
        self.fields["telefon"].widget.attrs["placeholder"] = "05xx xxx xx xx"
        self.fields["sicil_no"].widget.attrs["placeholder"] = "Varsa sicil no"

    def clean(self):
        cleaned = super().clean()
        area = cleaned.get("kayit_alani")

        if not area:
            return cleaned

        if area == "auto":
            cleaned["rol_obj"] = None
            return cleaned

        if not area.startswith("rol:"):
            self.add_error("kayit_alani", "Geçerli bir kayıt alanı seçin.")
            return cleaned

        try:
            role_id = int(area.split(":", 1)[1])
            role = Rol.objects.get(pk=role_id, aktif=True)
        except (ValueError, Rol.DoesNotExist):
            self.add_error("kayit_alani", "Seçilen rol artık aktif değil.")
            return cleaned

        cleaned["rol_obj"] = role

        if not (cleaned.get("kullanici_adi") or "").strip():
            self.add_error("kullanici_adi", "Personel kaydında kullanıcı adı zorunludur.")

        # İlçe bazlı roller mutlaka bölgeyle ilişkilendirilir.
        if (
            role.kod == "koordinator"
            or role.panel_tipi == "saha"
        ) and not cleaned.get("yetkili_ilceler"):
            self.add_error(
                "yetkili_ilceler",
                "Koordinatör ve saha personeli için en az bir yetkili ilçe seçin.",
            )

        return cleaned


class RolForm(forms.ModelForm):
    class Meta:
        model = Rol
        fields = ["ad", "kod", "panel_tipi", "calisma_kanali", "parent", "aktif", "aciklama"]
        help_texts = {
            "calisma_kanali": (
                "Kullanıcı adına göre kural yazılmaz. Bu role bağlı herkes girişte "
                "Web / Mobil / Her İkisi seçimine göre otomatik yönlendirilir."
            ),
        }


class RolAtamaKuraliForm(forms.ModelForm):
    class Meta:
        model = RolAtamaKurali
        fields = ["kaynak_rol", "hedef_rol", "aktif", "aciklama"]
