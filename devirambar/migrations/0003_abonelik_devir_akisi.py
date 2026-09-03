from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("devirambar", "0002_merkez_ambar"),
    ]

    operations = [
        migrations.CreateModel(
            name="AbonelikKaydi",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("abone_no", models.CharField(db_index=True, max_length=50, unique=True)),
                ("abone_ad_soyad", models.CharField(max_length=160)),
                ("telefon", models.CharField(blank=True, max_length=20)),
                ("tc_kimlik_no", models.CharField(blank=True, max_length=11)),
                ("ilce", models.CharField(choices=[("Başiskele", "Başiskele"), ("Çayırova", "Çayırova"), ("Darıca", "Darıca"), ("Derince", "Derince"), ("Dilovası", "Dilovası"), ("Gebze", "Gebze"), ("Gölcük", "Gölcük"), ("İzmit", "İzmit"), ("Kandıra", "Kandıra"), ("Karamürsel", "Karamürsel"), ("Kartepe", "Kartepe"), ("Körfez", "Körfez")], max_length=40)),
                ("adres", models.CharField(max_length=300)),
                ("sayac_seri_no", models.CharField(blank=True, db_index=True, max_length=80)),
                ("sayac_marka_model", models.CharField(blank=True, max_length=120)),
                ("sayac_endeks", models.DecimalField(blank=True, decimal_places=3, max_digits=12, null=True)),
                ("aktif", models.BooleanField(db_index=True, default=True)),
                ("olusturulma_tarihi", models.DateTimeField(auto_now_add=True)),
                ("kapanis_tarihi", models.DateTimeField(blank=True, null=True)),
                ("onceki_abonelik", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="devam_abonelikleri", to="devirambar.abonelikkaydi")),
            ],
            options={"ordering": ["-aktif", "abone_no"]},
        ),
        migrations.AddIndex(
            model_name="abonelikkaydi",
            index=models.Index(fields=["aktif", "ilce"], name="devir_abone_aktif_ilce_idx"),
        ),
        migrations.AddField(
            model_name="devirbasvurusu",
            name="eski_abone_ad_soyad",
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name="devirbasvurusu",
            name="eski_abonelik",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="devir_basvurulari", to="devirambar.abonelikkaydi"),
        ),
        migrations.AddField(
            model_name="devirbasvurusu",
            name="yeni_abonelik",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="olusturan_devirler", to="devirambar.abonelikkaydi"),
        ),
        migrations.AlterField(
            model_name="devirbasvurusu",
            name="durum",
            field=models.CharField(choices=[("hazirlaniyor", "Devir Kaydı Oluşturuldu"), ("ambara_gonderildi", "Ambara Gönderildi"), ("teslim_alindi", "Ambar Teslim Aldı"), ("kontrol_edildi", "Sayaç Kontrol Edildi"), ("merkez_ambara_gonderildi", "Merkez Ambara Gönderildi"), ("merkez_teslim_alindi", "Merkez Ambar Teslim Aldı"), ("merkez_kontrol_edildi", "Merkez Ambar Kontrol Etti"), ("merkez_ambara_kaydedildi", "Merkez Ambara Kaydedildi"), ("ambara_kaydedildi", "Yerel Ambara Kaydedildi (Eski Akış)"), ("iptal", "İptal")], db_index=True, default="hazirlaniyor", max_length=30),
        ),
        migrations.AlterField(
            model_name="devirbasvurusu",
            name="devir_nedeni",
            field=models.CharField(choices=[("mulk_degisimi", "Mülk sahibi değişikliği"), ("kiraci_degisimi", "Kiracı değişimi"), ("vefat", "Vefat / miras"), ("kurum_degisimi", "Kurum / şirket değişikliği"), ("diger", "Diğer")], default="diger", max_length=30),
        ),
    ]
