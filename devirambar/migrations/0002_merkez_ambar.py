from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[('devirambar','0001_initial'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.AlterField(
            model_name='devirbasvurusu',
            name='durum',
            field=models.CharField(choices=[('hazirlaniyor','Başvuru Hazırlanıyor'),('ambara_gonderildi','Ambara Gönderildi'),('teslim_alindi','Ambar Teslim Aldı'),('kontrol_edildi','Sayaç Kontrol Edildi'),('merkez_ambara_gonderildi','Merkez Ambara Gönderildi'),('merkez_teslim_alindi','Merkez Ambar Teslim Aldı'),('merkez_kontrol_edildi','Merkez Ambar Kontrol Etti'),('merkez_ambara_kaydedildi','Merkez Ambara Kaydedildi'),('ambara_kaydedildi','Yerel Ambara Kaydedildi (Eski Akış)'),('iptal','İptal')],db_index=True,default='hazirlaniyor',max_length=30),
        ),
        migrations.AddField('devirbasvurusu','merkeze_gonderim_tarihi',models.DateTimeField(blank=True,null=True)),
        migrations.AddField('devirbasvurusu','merkez_teslim_tarihi',models.DateTimeField(blank=True,null=True)),
        migrations.AddField('devirbasvurusu','merkez_kontrol_tarihi',models.DateTimeField(blank=True,null=True)),
        migrations.AddField('devirbasvurusu','merkez_ambar_kayit_tarihi',models.DateTimeField(blank=True,null=True)),
        migrations.AddField('devirbasvurusu','merkez_depo_konumu',models.CharField(blank=True,max_length=120)),
        migrations.AddField('devirbasvurusu','merkez_ambar_notu',models.CharField(blank=True,max_length=300)),
        migrations.AddField('devirbasvurusu','merkeze_gonderen',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='merkez_ambara_gonderdigi_sayaclar',to=settings.AUTH_USER_MODEL)),
        migrations.AddField('devirbasvurusu','merkez_teslim_alan',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='merkezde_teslim_aldigi_sayaclar',to=settings.AUTH_USER_MODEL)),
        migrations.AddField('devirbasvurusu','merkez_kontrol_eden',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='merkezde_kontrol_ettigi_sayaclar',to=settings.AUTH_USER_MODEL)),
        migrations.AddField('devirbasvurusu','merkez_ambara_kaydeden',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='merkez_ambara_kaydettigi_sayaclar',to=settings.AUTH_USER_MODEL)),
    ]
