from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def queue_existing_completed(apps, schema_editor):
    Talep = apps.get_model("talepler", "Talep")
    # This feature did not exist before V12; completed jobs have no tracked citizen call.
    Talep.objects.filter(
        durum="tamamlandi",
        vatandas_bildirim_durumu="beklemiyor",
    ).update(vatandas_bildirim_durumu="bekliyor")


class Migration(migrations.Migration):

    dependencies = [
        ("talepler", "0003_global_sef_onay_durum_duzeltme"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="talep",
            name="vatandas_bildirim_durumu",
            field=models.CharField(
                choices=[
                    ("beklemiyor","Henüz Beklemiyor"),
                    ("bekliyor","Geri Bildirim Bekliyor"),
                    ("tekrar_aranacak","Tekrar Aranacak"),
                    ("bilgilendirildi","Vatandaş Bilgilendirildi"),
                ],
                default="beklemiyor",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="talep",
            name="vatandas_bildirim_tarihi",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="talep",
            name="vatandas_bildirim_yapan",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="vatandas_bilgilendirdigi_talepler",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.CreateModel(
            name="VatandasAramaKaydi",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sonuc", models.CharField(
                    choices=[
                        ("bilgilendirildi","Vatandaş Bilgilendirildi"),
                        ("ulasilamadi","Vatandaşa Ulaşılamadı"),
                        ("tekrar_aranacak","Tekrar Aranacak"),
                    ],
                    max_length=30,
                )),
                ("not_metni", models.CharField(blank=True, max_length=300)),
                ("tarih", models.DateTimeField(auto_now_add=True)),
                ("kullanici", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="vatandas_arama_kayitlari",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("talep", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="vatandas_arama_kayitlari",
                    to="talepler.talep",
                )),
            ],
            options={"ordering": ["-tarih"]},
        ),
        migrations.AddIndex(
            model_name="vatandasaramakaydi",
            index=models.Index(fields=["talep","tarih"], name="talepler_va_talep_i_2d6f3b_idx"),
        ),
        migrations.AddIndex(
            model_name="vatandasaramakaydi",
            index=models.Index(fields=["sonuc","tarih"], name="talepler_va_sonuc_i_193aa5_idx"),
        ),
        migrations.RunPython(queue_existing_completed, migrations.RunPython.noop),
    ]
