from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


def _norm(s):
    return (s or "").casefold().replace("ı","i").replace("ş","s").replace("ğ","g").replace("ü","u").replace("ö","o").replace("ç","c")


def kurallari_ve_eski_fotolari_tasi(apps, schema_editor):
    IsAltTuru=apps.get_model("talepler","IsAltTuru")
    IsEmri=apps.get_model("talepler","IsEmri")
    IsEmriFotograf=apps.get_model("talepler","IsEmriFotograf")

    for alt in IsAltTuru.objects.select_related("is_turu").all():
        metin=_norm(f"{alt.is_turu.ad} {alt.ad}")
        if "abone" in metin or "sayac" in metin:
            alt.zorunlu_fotograf_sayisi=1
            alt.fotograf_etiketleri="İşlem / Sayaç Sonucu"
        elif ("yol" in metin and ("kazi" in metin or "kaldirim" in metin)) or "yol ve kazi" in metin:
            alt.zorunlu_fotograf_sayisi=3
            alt.fotograf_etiketleri="İşlem Öncesi\nKazı / Müdahale Sonrası\nYol / Kaplama Geri Düzenleme Sonrası"
        else:
            alt.zorunlu_fotograf_sayisi=2
            alt.fotograf_etiketleri="Müdahale Öncesi\nMüdahale Sonrası"
        alt.save(update_fields=["zorunlu_fotograf_sayisi","fotograf_etiketleri"])

    # V31/V34'ten kalan fotoğrafları yeni iş emri galerisine kayıpsız taşı.
    for e in IsEmri.objects.all():
        if getattr(e,"once_foto",None):
            IsEmriFotograf.objects.get_or_create(
                is_emri=e,sira=1,
                defaults={"etiket":"Müdahale Öncesi","foto":e.once_foto.name},
            )
        if getattr(e,"sonra_foto",None):
            IsEmriFotograf.objects.get_or_create(
                is_emri=e,sira=2,
                defaults={"etiket":"Müdahale Sonrası","foto":e.sonra_foto.name},
            )


class Migration(migrations.Migration):
    dependencies=[
        ("talepler","0006_v31_saha_kanit_gps_bildirim"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations=[
        migrations.AddField(
            model_name="isaltturu",
            name="zorunlu_fotograf_sayisi",
            field=models.PositiveSmallIntegerField(
                default=2,
                help_text="İş emri şef onayına gönderilmeden önce tamamlanması gereken fotoğraf adedi.",
                validators=[django.core.validators.MinValueValidator(1),django.core.validators.MaxValueValidator(8)],
            ),
        ),
        migrations.AddField(
            model_name="isaltturu",
            name="fotograf_etiketleri",
            field=models.TextField(
                blank=True,
                help_text="Her satıra bir fotoğraf adı yazın. Örn: Kazı Öncesi / Kazı Sonrası / Yol Geri Kapama Sonrası",
            ),
        ),
        migrations.CreateModel(
            name="IsEmriFotograf",
            fields=[
                ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
                ("sira",models.PositiveSmallIntegerField()),
                ("etiket",models.CharField(max_length=160)),
                ("foto",models.ImageField(upload_to="is_emri/kanit/%Y/%m/")),
                ("yuklenme_tarihi",models.DateTimeField(auto_now_add=True)),
                ("is_emri",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="fotograflar",to="talepler.isemri")),
                ("yukleyen",models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="yukledigi_is_emri_fotograflari",to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering":["sira","yuklenme_tarihi"]},
        ),
        migrations.AddConstraint(
            model_name="isemrifotograf",
            constraint=models.UniqueConstraint(fields=("is_emri","sira"),name="uq_is_emri_foto_slot"),
        ),
        migrations.AddIndex(
            model_name="isemrifotograf",
            index=models.Index(fields=["is_emri","sira"],name="talepler_is_is_emri_27f408_idx"),
        ),
        migrations.RunPython(kurallari_ve_eski_fotolari_tasi,migrations.RunPython.noop),
    ]
