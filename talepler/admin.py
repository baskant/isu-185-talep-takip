from django.contrib import admin
from .models import IsTuru,IsAltTuru,Talep,GeriBildirim,IslemLogu,VatandasAramaKaydi,IsEmri,IsEmriFotograf
for m in [IsTuru,IsAltTuru,Talep,GeriBildirim,IslemLogu,VatandasAramaKaydi,IsEmri,IsEmriFotograf]: admin.site.register(m)
