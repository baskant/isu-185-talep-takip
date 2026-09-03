from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def backfill_is_emirleri(apps, schema_editor):
    Talep=apps.get_model("talepler","Talep")
    IsEmri=apps.get_model("talepler","IsEmri")

    yil=django.utils.timezone.localdate().year
    sira=1
    for talep in Talep.objects.filter(sorumlu_saha__isnull=False).order_by("id"):
        if IsEmri.objects.filter(talep_id=talep.id).exists():
            continue
        while IsEmri.objects.filter(is_emri_no=f"IE-{yil}-{sira:06d}").exists():
            sira += 1

        durum_esleme={
            "sahaya_atandi":"atandi",
            "kabul_edildi":"kabul_edildi",
            "yolda":"yolda",
            "yerinde":"yerinde",
            "islemde":"islemde",
            "onay_bekliyor":"onay_bekliyor",
            "tamamlandi":"tamamlandi",
            "iptal":"iptal",
        }
        gonderen=(getattr(talep.is_turu,"ad","") or "Operasyon") + " Birimi"
        IsEmri.objects.create(
            is_emri_no=f"IE-{yil}-{sira:06d}",
            talep_id=talep.id,
            gonderen_birim=gonderen,
            olusturan_id=talep.olusturan_id,
            atanan_saha_id=talep.sorumlu_saha_id,
            durum=durum_esleme.get(talep.durum,"atandi"),
            atama_tarihi=talep.olusturulma_tarihi,
            saha_tamam_tarihi=talep.saha_tamam_bildirim_tarihi,
            sef_onay_tarihi=talep.sef_onay_tarihi,
            sonuc_notu=talep.saha_sonuc_notu or "",
        )
        sira += 1


class Migration(migrations.Migration):

    dependencies=[
        ("talepler","0004_vatandas_bilgilendirme_akisi"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations=[
        migrations.CreateModel(
            name="Abone",
            fields=[
                ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
                ("abone_no",models.CharField(db_index=True,max_length=40,unique=True)),
                ("ad",models.CharField(max_length=100)),
                ("soyad",models.CharField(blank=True,max_length=100)),
                ("telefon",models.CharField(blank=True,max_length=20)),
                ("eposta",models.EmailField(blank=True,max_length=254)),
                ("sayac_no",models.CharField(blank=True,max_length=60)),
                ("kapi_no",models.CharField(blank=True,max_length=30)),
                ("adres_aciklama",models.CharField(blank=True,max_length=250)),
                ("aktif",models.BooleanField(default=True)),
                ("olusturulma_tarihi",models.DateTimeField(auto_now_add=True)),
                ("guncellenme_tarihi",models.DateTimeField(auto_now=True)),
                ("ilce",models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="aboneler",to="adres.ilce")),
                ("mahalle",models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="aboneler",to="adres.mahalle")),
                ("yol",models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="aboneler",to="adres.yol")),
            ],
            options={"ordering":["abone_no"]},
        ),
        migrations.AddIndex(
            model_name="abone",
            index=models.Index(fields=["aktif","abone_no"],name="talepler_ab_aktif_5b163e_idx"),
        ),
        migrations.AddField(
            model_name="talep",
            name="abone",
            field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="talepler",to="talepler.abone"),
        ),
        migrations.CreateModel(
            name="IsEmri",
            fields=[
                ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
                ("is_emri_no",models.CharField(blank=True,max_length=30,unique=True)),
                ("gonderen_birim",models.CharField(blank=True,max_length=160)),
                ("durum",models.CharField(choices=[
                    ("atandi","Sahaya Atandı"),("kabul_edildi","Kabul Edildi"),
                    ("yolda","Yola Çıkıldı"),("yerinde","Adrese Ulaşıldı"),
                    ("islemde","Müdahale Ediliyor"),("onay_bekliyor","Şef Onayı Bekliyor"),
                    ("tamamlandi","Tamamlandı"),("iptal","İptal"),
                ],default="atandi",max_length=30)),
                ("atama_tarihi",models.DateTimeField(default=django.utils.timezone.now)),
                ("kabul_tarihi",models.DateTimeField(blank=True,null=True)),
                ("yola_cikis_tarihi",models.DateTimeField(blank=True,null=True)),
                ("adrese_ulasma_tarihi",models.DateTimeField(blank=True,null=True)),
                ("mudahale_baslama_tarihi",models.DateTimeField(blank=True,null=True)),
                ("saha_tamam_tarihi",models.DateTimeField(blank=True,null=True)),
                ("sef_onay_tarihi",models.DateTimeField(blank=True,null=True)),
                ("sonuc_notu",models.TextField(blank=True)),
                ("olusturulma_tarihi",models.DateTimeField(auto_now_add=True)),
                ("guncellenme_tarihi",models.DateTimeField(auto_now=True)),
                ("olusturan",models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="olusturdugu_is_emirleri",to=settings.AUTH_USER_MODEL)),
                ("atanan_saha",models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="is_emirleri",to="accounts.personelprofili")),
                ("talep",models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,related_name="is_emri",to="talepler.talep")),
            ],
            options={"ordering":["-olusturulma_tarihi"]},
        ),
        migrations.AddIndex(
            model_name="isemri",
            index=models.Index(fields=["durum","atama_tarihi"],name="talepler_is_durum_21540a_idx"),
        ),
        migrations.AddIndex(
            model_name="isemri",
            index=models.Index(fields=["gonderen_birim","durum"],name="talepler_is_gonder_7e5dc4_idx"),
        ),
        migrations.CreateModel(
            name="MobilToken",
            fields=[
                ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
                ("anahtar",models.CharField(max_length=64,unique=True)),
                ("olusturulma_tarihi",models.DateTimeField(auto_now_add=True)),
                ("son_kullanim",models.DateTimeField(blank=True,null=True)),
                ("aktif",models.BooleanField(default=True)),
                ("kullanici",models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,related_name="mobil_token",to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RunPython(backfill_is_emirleri,migrations.RunPython.noop),
    ]
