from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies=[
        ("talepler","0005_abone_isemri_mobil"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations=[
        migrations.AddField(
            model_name="isemri",
            name="once_foto",
            field=models.ImageField(blank=True,null=True,upload_to="is_emri/once/%Y/%m/"),
        ),
        migrations.AddField(
            model_name="isemri",
            name="sonra_foto",
            field=models.ImageField(blank=True,null=True,upload_to="is_emri/sonra/%Y/%m/"),
        ),
        migrations.AddField(
            model_name="isemri",
            name="gps_lat",
            field=models.DecimalField(blank=True,decimal_places=6,max_digits=9,null=True),
        ),
        migrations.AddField(
            model_name="isemri",
            name="gps_lng",
            field=models.DecimalField(blank=True,decimal_places=6,max_digits=9,null=True),
        ),
        migrations.AddField(
            model_name="isemri",
            name="gps_mesafe_m",
            field=models.PositiveIntegerField(blank=True,null=True),
        ),
        migrations.AddField(
            model_name="isemri",
            name="gps_dogrulandi",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="isemri",
            name="gps_dogrulama_tarihi",
            field=models.DateTimeField(blank=True,null=True),
        ),
        migrations.CreateModel(
            name="MobilBildirim",
            fields=[
                ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
                ("tip",models.CharField(
                    choices=[
                        ("yeni_is","Yeni İş Emri"),
                        ("geri_gonderildi","Şef Geri Gönderdi"),
                        ("acil","Acil İş"),
                        ("bilgi","Bilgilendirme"),
                    ],
                    default="bilgi",max_length=30,
                )),
                ("baslik",models.CharField(max_length=140)),
                ("mesaj",models.CharField(max_length=400)),
                ("okundu",models.BooleanField(default=False)),
                ("olusturulma_tarihi",models.DateTimeField(auto_now_add=True)),
                ("is_emri",models.ForeignKey(
                    blank=True,null=True,on_delete=django.db.models.deletion.CASCADE,
                    related_name="mobil_bildirimler",to="talepler.isemri",
                )),
                ("kullanici",models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="mobil_bildirimler",to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={"ordering":["-olusturulma_tarihi"]},
        ),
        migrations.AddIndex(
            model_name="mobilbildirim",
            index=models.Index(
                fields=["kullanici","okundu","olusturulma_tarihi"],
                name="talepler_mo_kullani_b24c88_idx",
            ),
        ),
    ]
