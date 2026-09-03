from django import forms
from talepler.models import Talep
class TalepFiltreForm(forms.Form):
    durum=forms.ChoiceField(required=False,choices=[("","Tüm Durumlar")]+list(Talep.DURUMLAR))
    oncelik=forms.ChoiceField(required=False,choices=[("","Tüm Öncelikler")]+list(Talep.ONCELIKLER))
    ilce=forms.ModelChoiceField(required=False,queryset=None,empty_label="Tüm İlçeler")
    is_turu=forms.ModelChoiceField(required=False,queryset=None,empty_label="Tüm İş Türleri")
    ara=forms.CharField(required=False,max_length=120,widget=forms.TextInput(attrs={"placeholder":"Talep no, telefon, vatandaş..."}))
    def __init__(self,*args,**kwargs):
        from adres.models import Ilce
        from talepler.models import IsTuru
        super().__init__(*args,**kwargs)
        self.fields["ilce"].queryset=Ilce.objects.filter(aktif=True)
        self.fields["is_turu"].queryset=IsTuru.objects.filter(aktif=True)
