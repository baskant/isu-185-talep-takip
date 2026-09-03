from django.core.management.base import BaseCommand
from accounts.saha_services import create_missing_field_teams

class Command(BaseCommand):
    help = "Kocaeli'nin aktif ilçeleri için eksik operasyon saha ekiplerini otomatik oluşturur."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default=None,
            help="Demo/test için yeni oluşturulan tüm saha hesaplarına verilecek ortak şifre.",
        )

    def handle(self, *args, **options):
        generated = create_missing_field_teams(password=options.get("password"))
        if not generated:
            self.stdout.write(self.style.SUCCESS("Eksik saha hesabı yok."))
            return

        self.stdout.write(f"{len(generated)} yeni saha hesabı oluşturuldu:")
        for x in generated:
            self.stdout.write(
                f"  {x['username']} | {x['rol']} | {x['ilce']} | "
                f"{x['uzmanlik']} | Şifre: {x['password']}"
            )
        self.stdout.write(self.style.SUCCESS("Saha ekipleri hazır."))
