from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="DevirBasvurusu",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("basvuru_no", models.CharField(blank=True, max_length=30, unique=True)),
                ("vatandas_ad_soyad", models.CharField(max_length=160)),
                ("telefon", models.CharField(max_length=20)),
                ("tc_kimlik_no", models.CharField(blank=True, max_length=11)),
                ("ilce", models.CharField(choices=[("Başiskele","Başiskele"),("Çayırova","Çayırova"),("Darıca","Darıca"),("Derince","Derince"),("Dilovası","Dilovası"),("Gebze","Gebze"),("Gölcük","Gölcük"),("İzmit","İzmit"),("Kandıra","Kandıra"),("Karamürsel","Karamürsel"),("Kartepe","Kartepe"),("Körfez","Körfez")], max_length=40)),
                ("adres", models.CharField(max_length=300)),
                ("eski_abone_no", models.CharField(blank=True, max_length=50)),
                ("yeni_abone_no", models.CharField(blank=True, max_length=50)),
                ("sayac_seri_no", models.CharField(max_length=80)),
                ("sayac_marka_model", models.CharField(blank=True, max_length=120)),
                ("sayac_endeks", models.DecimalField(blank=True, decimal_places=3, max_digits=12, null=True)),
                ("devir_nedeni", models.CharField(choices=[("mulk_degisimi","Mülk / kullanıcı değişimi"),("kiraci_degisimi","Kiracı değişimi"),("vefat","Vefat / miras"),("kurum_degisimi","Kurum / şirket değişimi"),("diger","Diğer")], default="diger", max_length=30)),
                ("aciklama", models.TextField(blank=True)),
                ("durum", models.CharField(choices=[("hazirlaniyor","Başvuru Hazırlanıyor"),("ambara_gonderildi","Ambara Gönderildi"),("teslim_alindi","Ambar Teslim Aldı"),("kontrol_edildi","Sayaç Kontrol Edildi"),("ambara_kaydedildi","Ambara Kaydedildi"),("iptal","İptal")], db_index=True, default="hazirlaniyor", max_length=30)),
                ("olusturulma_tarihi", models.DateTimeField(auto_now_add=True)),
                ("guncellenme_tarihi", models.DateTimeField(auto_now=True)),
                ("ambara_gonderim_tarihi", models.DateTimeField(blank=True, null=True)),
                ("teslim_tarihi", models.DateTimeField(blank=True, null=True)),
                ("kontrol_tarihi", models.DateTimeField(blank=True, null=True)),
                ("ambar_kayit_tarihi", models.DateTimeField(blank=True, null=True)),
                ("depo_konumu", models.CharField(blank=True, max_length=120)),
                ("ambar_notu", models.CharField(blank=True, max_length=300)),
                ("ambara_gonderen", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ambara_gonderdigi_devirler", to=settings.AUTH_USER_MODEL)),
                ("ambara_kaydeden", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ambara_kaydettigi_sayaclar", to=settings.AUTH_USER_MODEL)),
                ("kontrol_eden", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="kontrol_ettigi_sayaclar", to=settings.AUTH_USER_MODEL)),
                ("olusturan", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="devir_basvurulari", to=settings.AUTH_USER_MODEL)),
                ("teslim_alan", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="teslim_aldigi_sayaclar", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering":["-olusturulma_tarihi"]},
        ),
        migrations.CreateModel(
            name="DevirHareketi",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("islem", models.CharField(max_length=100)),
                ("aciklama", models.CharField(blank=True, max_length=400)),
                ("onceki_durum", models.CharField(blank=True, max_length=30)),
                ("yeni_durum", models.CharField(blank=True, max_length=30)),
                ("tarih", models.DateTimeField(auto_now_add=True)),
                ("basvuru", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="hareketler", to="devirambar.devirbasvurusu")),
                ("kullanici", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering":["-tarih"]},
        ),
        migrations.AddIndex(model_name="devirbasvurusu", index=models.Index(fields=["durum","olusturulma_tarihi"], name="devirambar_durum_olust_idx")),
        migrations.AddIndex(model_name="devirbasvurusu", index=models.Index(fields=["ilce","durum"], name="devirambar_ilce_durum_idx")),
        migrations.AddIndex(model_name="devirbasvurusu", index=models.Index(fields=["sayac_seri_no"], name="devirambar_sayac_idx")),
        migrations.AddIndex(model_name="devirhareketi", index=models.Index(fields=["basvuru","tarih"], name="devirambar_hareket_idx")),
    ]
