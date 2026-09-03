from django.db import migrations


def normalize_unapproved_completed(apps, schema_editor):
    Talep = apps.get_model("talepler", "Talep")

    # Only repair records that clearly went through the V9/V10 field-completion flow:
    # field completion timestamp exists, but there is no chief approval.
    Talep.objects.filter(
        durum="tamamlandi",
        saha_tamam_bildirim_tarihi__isnull=False,
        sef_onaylayan__isnull=True,
    ).update(
        durum="onay_bekliyor",
        tamamlanma_tarihi=None,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("talepler", "0002_sef_onay_akisi"),
    ]

    operations = [
        migrations.RunPython(
            normalize_unapproved_completed,
            migrations.RunPython.noop,
        ),
    ]
