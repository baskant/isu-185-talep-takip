from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("talepler", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="talep",
            name="durum",
            field=models.CharField(
                choices=[
                    ("yeni","Yeni"),
                    ("sefe_gonderildi","Koordinatöre Gönderildi"),
                    ("sahaya_atandi","Sahaya Atandı"),
                    ("kabul_edildi","Saha Kabul Etti"),
                    ("yolda","Yola Çıkıldı"),
                    ("yerinde","Adrese Ulaşıldı"),
                    ("islemde","Müdahale Ediliyor"),
                    ("onay_bekliyor","Şef Onayı Bekliyor"),
                    ("tamamlandi","Tamamlandı"),
                    ("iptal","İptal"),
                ],
                default="yeni",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="talep",
            name="saha_sonuc_notu",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="talep",
            name="saha_tamam_bildirim_tarihi",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="talep",
            name="sef_onay_tarihi",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="talep",
            name="sef_onaylayan",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="onayladigi_talepler",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
