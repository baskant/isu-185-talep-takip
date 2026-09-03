import time

from django.core.management.base import BaseCommand
from talepler.models import Talep
from adres.geocoding import talep_konumla

class Command(BaseCommand):
    help = "Haritada görünmeyen eski taleplerin konumlarını adreslerinden doldurur."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Koordinatı olan kayıtları da adres üzerinden yeniden konumlandır.",
        )

    def handle(self, *args, **options):
        force = bool(options.get("force"))
        qs = Talep.objects.select_related("ilce", "mahalle", "yol").order_by("id")
        if not force:
            qs = qs.filter(lat__isnull=True) | qs.filter(lng__isnull=True)

        tickets = list(qs.distinct())
        if not tickets:
            self.stdout.write(self.style.SUCCESS("Harita konumu eksik talep yok."))
            return

        self.stdout.write(f"{len(tickets)} talebin harita konumu tamamlanıyor...")
        counts = {}
        for index, talep in enumerate(tickets, start=1):
            result = talep_konumla(talep, force=force, save=True)
            source = result["source"]
            counts[source] = counts.get(source, 0) + 1
            self.stdout.write(
                f"  [{index}/{len(tickets)}] {talep.talep_no}: "
                f"{result['lat']:.6f}, {result['lng']:.6f} ({source})"
            )
            # Nominatim'e toplu işlemde nazik davran.
            if source in {"adres", "mahalle"}:
                time.sleep(1.05)

        summary = ", ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
        self.stdout.write(self.style.SUCCESS(f"Tamamlandı. {summary}"))
