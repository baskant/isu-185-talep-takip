from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Q
from django.db.models.functions import Lower

from adres.models import Ilce
from abonelik.models import (
    AboneSayac,
    AmbarSayacTalebi,
    AmbarYetkisi,
    SayacEnvanteri,
    Sozlesme,
    VatandasIletisim,
    VatandasSicili,
)


class Command(BaseCommand):
    help = "V59: mevcut veritabanında veri bütünlüğü ve rol/ambar tutarlılığı kontrolü yapar."

    def add_arguments(self, parser):
        parser.add_argument("--strict", action="store_true", help="Kritik hata varsa komutu hata koduyla sonlandırır.")

    def handle(self, *args, **options):
        kritik = []
        uyari = []

        aktif_iletisim_coklu = list(
            VatandasIletisim.objects.filter(aktif=True)
            .values("sicil_id", "tur")
            .annotate(n=Count("id"))
            .filter(n__gt=1)
        )
        if aktif_iletisim_coklu:
            kritik.append(f"Aynı sicil/iletişim türünde birden fazla aktif kayıt: {len(aktif_iletisim_coklu)} grup")

        aktif_adres_coklu = list(
            Sozlesme.objects.filter(aktif=True)
            .values("adres_id")
            .annotate(n=Count("id"))
            .filter(n__gt=1)
        )
        if aktif_adres_coklu:
            kritik.append(f"Aynı hizmet adresinde birden fazla aktif sözleşme: {len(aktif_adres_coklu)} adres")

        aktif_sayac_coklu = list(
            AboneSayac.objects.filter(aktif=True)
            .values("sayac_id")
            .annotate(n=Count("id"))
            .filter(n__gt=1)
        )
        if aktif_sayac_coklu:
            kritik.append(f"Aynı fiziksel sayaç birden fazla aktif aboneliğe bağlı: {len(aktif_sayac_coklu)} sayaç")

        seri_case_dupe = list(
            SayacEnvanteri.objects.annotate(norm=Lower("seri_no"))
            .values("norm")
            .annotate(n=Count("id"))
            .filter(n__gt=1)
        )
        if seri_case_dupe:
            kritik.append(f"Büyük/küçük harf farkıyla tekrar eden sayaç seri no: {len(seri_case_dupe)}")

        sayac_case_dupe = list(
            SayacEnvanteri.objects.annotate(norm=Lower("sayac_no"))
            .values("norm")
            .annotate(n=Count("id"))
            .filter(n__gt=1)
        )
        if sayac_case_dupe:
            kritik.append(f"Büyük/küçük harf farkıyla tekrar eden sayaç no: {len(sayac_case_dupe)}")

        bozuk_tc = 0
        for tc in VatandasSicili.objects.values_list("tc_kimlik_no", flat=True):
            if len(tc or "") != 11 or not (tc or "").isdigit():
                bozuk_tc += 1
        if bozuk_tc:
            kritik.append(f"11 rakam formatına uymayan T.C. kaydı: {bozuk_tc}")

        hatali_talep = AmbarSayacTalebi.objects.filter(
            Q(adet__lt=1) | Q(cap_mm__lt=10) | Q(gerekce__isnull=True) | Q(gerekce="")
        ).count()
        if hatali_talep:
            kritik.append(f"Geçersiz adet/çap/gerekçeli ambar talebi: {hatali_talep}")

        negatif_endeks = SayacEnvanteri.objects.filter(son_endeks__lt=0).count()
        if negatif_endeks:
            kritik.append(f"Negatif sayaç endeksi: {negatif_endeks}")

        aktif_soz_pasif_sicil = Sozlesme.objects.filter(aktif=True, sicil__aktif=False).count()
        if aktif_soz_pasif_sicil:
            kritik.append(f"Pasif sicile bağlı aktif sözleşme: {aktif_soz_pasif_sicil}")

        ilce_sayisi = Ilce.objects.filter(aktif=True).count()
        yetkili_ilce = AmbarYetkisi.objects.filter(aktif=True, ilce__aktif=True, ambar__aktif=True, ambar__tur="ilce").values("ilce_id").distinct().count()
        if yetkili_ilce != ilce_sayisi:
            uyari.append(f"Aktif ilçe / aktif ambar yetkisi eşleşmesi: {yetkili_ilce}/{ilce_sayisi}")

        eski_aktif = User.objects.filter(username__in=["devir_personeli", "ambar_personeli"], is_active=True).count()
        if eski_aktif:
            uyari.append(f"Eski ayrı devir/ambar hesabından halen aktif olan: {eski_aktif}")

        if kritik:
            self.stdout.write(self.style.ERROR("Kritik kontroller:"))
            for x in kritik:
                self.stdout.write(self.style.ERROR(f" - {x}"))
        else:
            self.stdout.write(self.style.SUCCESS("Kritik veri bütünlüğü kontrolleri temiz."))

        if uyari:
            self.stdout.write(self.style.WARNING("Uyarılar:"))
            for x in uyari:
                self.stdout.write(self.style.WARNING(f" - {x}"))
        else:
            self.stdout.write(self.style.SUCCESS("Rol/ambar kapsam uyarısı yok."))

        self.stdout.write(f"Kontrol özeti: kritik={len(kritik)} uyarı={len(uyari)}")
        if options["strict"] and kritik:
            raise CommandError("V59 sistem kontrolünde kritik veri bütünlüğü hataları bulundu.")
