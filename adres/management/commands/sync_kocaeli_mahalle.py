from django.core.management.base import BaseCommand, CommandError
from adres.realdata import sync_kocaeli_mahalleleri

class Command(BaseCommand):
    help = "Kocaeli'nin 12 ilçesinin güncel mahallelerini gerçek veri kaynağından senkronlar."

    def handle(self, *args, **options):
        self.stdout.write("Kocaeli mahalle verileri güncelleniyor...")
        try:
            results = sync_kocaeli_mahalleleri()
        except Exception as exc:
            raise CommandError(f"Mahalle senkronu başarısız: {exc}")

        total = 0
        for ilce, info in results:
            count = int(info.get("count") or 0)
            total += count
            self.stdout.write(
                f"  {ilce}: {count} mahalle "
                f"(dataset {info.get('datasetVersion') or '?'}, "
                f"güncelleme {info.get('lastUpdated') or '?'})"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Tamamlandı. Toplam {total} güncel mahalle aktif hale getirildi."
            )
        )
