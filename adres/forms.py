from django import forms
class AdresCsvForm(forms.Form):
    dosya = forms.FileField(help_text="CSV kolonları: ilce,mahalle,yol,tur,lat,lng")
