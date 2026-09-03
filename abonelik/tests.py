from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import PersonelProfili, Rol
from adres.models import Ilce
from abonelik.forms import AmbarSayacTalepForm, MerkezStokGirisForm, VatandasSicilForm
from abonelik.models import (
    AboneSayac,
    Ambar,
    AmbarSayacTalebi,
    AmbarYetkisi,
    HizmetAdresi,
    SayacEnvanteri,
    Sozlesme,
    VatandasIletisim,
    VatandasSicili,
)


class AbonelikV59Base(TestCase):
    def setUp(self):
        self.client = Client()
        self.ilce = Ilce.objects.create(ad="Test İlçe", aktif=True)
        self.adres = HizmetAdresi.objects.create(
            adres_kodu="TEST-ADR-001",
            ilce=self.ilce,
            mahalle="Merkez Mahallesi",
            cadde_sokak="Test Sokak",
            kapi_no="10",
            daire_no="2",
            aktif=True,
        )
        self.adres2 = HizmetAdresi.objects.create(
            adres_kodu="TEST-ADR-002",
            ilce=self.ilce,
            mahalle="Merkez Mahallesi",
            cadde_sokak="İkinci Sokak",
            kapi_no="20",
            daire_no="1",
            aktif=True,
        )

        self.abone_rol = Rol.objects.create(
            ad="Abonelik ve Sayaç İşlemleri",
            kod="abone-sayac-saha",
            panel_tipi="abone",
            calisma_kanali="web",
            aktif=True,
        )
        self.sef_rol = Rol.objects.create(
            ad="Test Koordinatör",
            kod="test-koordinator",
            panel_tipi="sef",
            calisma_kanali="web",
            aktif=True,
        )
        self.merkez_rol = Rol.objects.create(
            ad="Test Merkez Ambar",
            kod="test-merkez-ambar",
            panel_tipi="merkez_ambar",
            calisma_kanali="web",
            aktif=True,
        )
        self.cagri_rol = Rol.objects.create(
            ad="Test 185",
            kod="test-185",
            panel_tipi="185",
            calisma_kanali="web",
            aktif=True,
        )
        self.saha_rol = Rol.objects.create(
            ad="Test Saha",
            kod="test-saha",
            panel_tipi="saha",
            calisma_kanali="mobil",
            aktif=True,
        )

        self.abone_user = User.objects.create_user("test_abone", password="testpass")
        self.sef_user = User.objects.create_user("test_sef", password="testpass")
        self.merkez_user = User.objects.create_user("test_merkez", password="testpass")
        self.cagri_user = User.objects.create_user("test_185", password="testpass")
        self.saha_user = User.objects.create_user("test_saha", password="testpass")

        self.abone_profil = PersonelProfili.objects.create(kullanici=self.abone_user, rol=self.abone_rol, aktif=True, musait=True)
        self.abone_profil.yetkili_ilceler.add(self.ilce)
        self.sef_profil = PersonelProfili.objects.create(kullanici=self.sef_user, rol=self.sef_rol, aktif=True, musait=True)
        self.sef_profil.yetkili_ilceler.add(self.ilce)
        self.merkez_profil = PersonelProfili.objects.create(kullanici=self.merkez_user, rol=self.merkez_rol, aktif=True, musait=True)
        self.cagri_profil = PersonelProfili.objects.create(kullanici=self.cagri_user, rol=self.cagri_rol, aktif=True, musait=True)
        self.saha_profil = PersonelProfili.objects.create(kullanici=self.saha_user, rol=self.saha_rol, aktif=True, musait=True)

        self.merkez_ambar = Ambar.objects.create(kod="test-merkez", ad="Test Merkez Ambar", tur="merkez", aktif=True)
        self.hurda_ambar = Ambar.objects.create(kod="test-hurda", ad="Test Hurda Ambar", tur="hurda", aktif=True)
        self.ilce_ambar = Ambar.objects.create(kod="test-ilce", ad="Test İlçe Ambarı", tur="ilce", ilce=self.ilce, aktif=True)
        self.yetki = AmbarYetkisi.objects.create(ilce=self.ilce, personel=self.sef_profil, ambar=self.ilce_ambar, aktif=True)

        self.sicil = VatandasSicili.objects.create(
            tc_kimlik_no="90000000001",
            ad="Test",
            soyad="Vatandaş",
            dogum_tarihi=date(1990, 1, 1),
            aktif=True,
            olusturan=self.abone_user,
        )
        self.sozlesme = Sozlesme.objects.create(
            abone_no="TEST-ABN-001",
            sicil=self.sicil,
            adres=self.adres,
            abonelik_turu="mesken",
            kaynak="ilce_sube",
            aktif=True,
            baslangic_tarihi=date(2026, 1, 1),
            olusturan=self.abone_user,
        )

    def stok_sayaci(self, no="TEST-STK-001", seri="TEST-SER-001", *, tip="mekanik", cap=20, ambar=None):
        return SayacEnvanteri.objects.create(
            sayac_no=no,
            seri_no=seri,
            marka_model="Test Sayaç",
            sayac_tipi=tip,
            cap_mm=cap,
            son_endeks=Decimal("0"),
            durum="stokta",
            ambar=ambar or self.ilce_ambar,
            aktif=True,
        )


class V59ValidationTests(AbonelikV59Base):
    def test_duplicate_tc_is_blocked(self):
        form = VatandasSicilForm(data={
            "tc_kimlik_no": "90000000001",
            "ad": "Başka",
            "soyad": "Kişi",
            "dogum_tarihi": "1991-01-01",
            "aktif": True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("tc_kimlik_no", form.errors)

    def test_duplicate_meter_serial_is_blocked(self):
        self.stok_sayaci(no="MER-001", seri="SERI-ABC", ambar=self.merkez_ambar)
        form = MerkezStokGirisForm(data={
            "sayac_no": "MER-002",
            "seri_no": "seri-abc",
            "marka_model": "Baylan TK-5",
            "sayac_tipi": "mekanik",
            "cap_mm": 20,
            "son_endeks": 0,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("seri_no", form.errors)

    def test_negative_or_empty_warehouse_request_is_blocked(self):
        form = AmbarSayacTalepForm(data={
            "sayac_tipi": "mekanik",
            "cap_mm": -20,
            "adet": -5,
            "gerekce": "",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("cap_mm", form.errors)
        self.assertIn("adet", form.errors)
        self.assertIn("gerekce", form.errors)


class V59AuthorizationTests(AbonelikV59Base):
    def test_abone_personeli_only_abone_screens(self):
        self.client.force_login(self.abone_user)
        self.assertEqual(self.client.get(reverse("abonelik:izleme")).status_code, 200)
        self.assertEqual(self.client.get(reverse("abonelik:ambar_yonetimi")).status_code, 403)

    def test_ambar_yetkili_sef_only_warehouse_screen(self):
        self.client.force_login(self.sef_user)
        self.assertEqual(self.client.get(reverse("abonelik:ambar_yonetimi")).status_code, 200)
        self.assertEqual(self.client.get(reverse("abonelik:izleme")).status_code, 403)

    def test_merkez_ambar_only_warehouse_screen(self):
        self.client.force_login(self.merkez_user)
        self.assertEqual(self.client.get(reverse("abonelik:ambar_yonetimi")).status_code, 200)
        self.assertEqual(self.client.get(reverse("abonelik:izleme")).status_code, 403)

    def test_185_and_saha_cannot_open_abone_or_warehouse(self):
        for user in [self.cagri_user, self.saha_user]:
            self.client.force_login(user)
            self.assertEqual(self.client.get(reverse("abonelik:izleme")).status_code, 403)
            self.assertEqual(self.client.get(reverse("abonelik:ambar_yonetimi")).status_code, 403)
            self.client.logout()


class V59EndToEndTests(AbonelikV59Base):
    def test_citizen_contract_meter_flow(self):
        self.client.force_login(self.abone_user)

        response = self.client.post(reverse("abonelik:sicil"), {
            "islem": "sicil_ekle",
            "tc_kimlik_no": "90000000002",
            "ad": "Yeni",
            "soyad": "Abone",
            "dogum_tarihi": "1995-05-05",
            "cep_telefonu": "05551112233",
            "eposta": "yeni.abone@example.com",
            "aktif": "on",
        })
        self.assertEqual(response.status_code, 302)
        yeni_sicil = VatandasSicili.objects.get(tc_kimlik_no="90000000002")

        response = self.client.post(reverse("abonelik:sozlesmeler"), {
            "islem": "sozlesme_ekle",
            "sicil_id": yeni_sicil.pk,
            "adres": self.adres2.pk,
            "abonelik_turu": "isyeri",
            "kaynak": "e_devlet",
            "baslangic_tarihi": "2026-02-01",
            "aciklama": "V59 uçtan uca test sözleşmesi",
        })
        self.assertEqual(response.status_code, 302)
        yeni_sozlesme = Sozlesme.objects.get(sicil=yeni_sicil, adres=self.adres2, aktif=True)

        stok = self.stok_sayaci(no="TEST-STK-E2E", seri="TEST-SER-E2E")
        response = self.client.post(reverse("abonelik:sayac_ata", args=[yeni_sozlesme.pk]), {
            "sayac": stok.pk,
            "takilma_tarihi": "2026-02-01",
            "ilk_endeks": "0",
            "aciklama": "Yeni abonelik sayaç ataması",
        })
        self.assertEqual(response.status_code, 302)
        bag = AboneSayac.objects.get(sozlesme=yeni_sozlesme, aktif=True)
        bag.sayac.refresh_from_db()
        self.assertEqual(bag.sayac.durum, "aboneye_takili")
        self.assertIsNone(bag.sayac.ambar)

    def test_communication_history_keeps_old_value(self):
        old = VatandasIletisim.objects.create(
            sicil=self.sicil,
            tur="cep_telefonu",
            deger="05321112233",
            aktif=True,
            kaydeden=self.abone_user,
        )
        self.client.force_login(self.abone_user)
        response = self.client.post(reverse("abonelik:izleme_iletisim_ekle", args=[self.sozlesme.pk]), {
            "tur": "cep_telefonu",
            "deger": "05559998877",
            "aciklama": "Numara değişikliği",
        })
        self.assertEqual(response.status_code, 302)
        old.refresh_from_db()
        self.assertFalse(old.aktif)
        self.assertIsNotNone(old.bitis_tarihi)
        self.assertTrue(VatandasIletisim.objects.filter(sicil=self.sicil, tur="cep_telefonu", deger="05559998877", aktif=True).exists())

    def test_warehouse_request_prepare_ship_receive_flow(self):
        self.stok_sayaci(no="MER-STK-01", seri="MER-SER-01", ambar=self.merkez_ambar)
        self.stok_sayaci(no="MER-STK-02", seri="MER-SER-02", ambar=self.merkez_ambar)

        self.client.force_login(self.sef_user)
        response = self.client.post(reverse("abonelik:ambar_yonetimi"), {
            "islem": "sayac_talebi",
            "sayac_tipi": "mekanik",
            "cap_mm": 20,
            "adet": 2,
            "gerekce": "İlçe yeni abonelik stoğunu tamamlamak için",
        })
        self.assertEqual(response.status_code, 302)
        talep = AmbarSayacTalebi.objects.get(yetki=self.yetki, durum="talep_edildi")

        self.client.force_login(self.merkez_user)
        response = self.client.post(reverse("abonelik:ambar_talep_durum", args=[talep.pk, "hazirla"]))
        self.assertEqual(response.status_code, 302)
        talep.refresh_from_db()
        self.assertEqual(talep.durum, "hazirlaniyor")

        response = self.client.post(reverse("abonelik:ambar_talep_durum", args=[talep.pk, "sevk-et"]))
        self.assertEqual(response.status_code, 302)
        talep.refresh_from_db()
        self.assertEqual(talep.durum, "sevk_edildi")
        self.assertEqual(talep.hareketler.filter(islem="sevk").count(), 2)

        self.client.force_login(self.sef_user)
        response = self.client.post(reverse("abonelik:ambar_talep_durum", args=[talep.pk, "teslim-al"]))
        self.assertEqual(response.status_code, 302)
        talep.refresh_from_db()
        self.assertEqual(talep.durum, "teslim_alindi")
        self.assertEqual(SayacEnvanteri.objects.filter(ambar=self.ilce_ambar, durum="stokta", sayac_no__in=["MER-STK-01", "MER-STK-02"]).count(), 2)

    def test_usage_out_to_scrap_flow(self):
        mounted = SayacEnvanteri.objects.create(
            sayac_no="ABN-MTR-01",
            seri_no="ABN-MTR-SER-01",
            marka_model="Baylan TK-5",
            sayac_tipi="mekanik",
            cap_mm=20,
            durum="aboneye_takili",
            ambar=None,
            aktif=True,
        )
        bag = AboneSayac.objects.create(
            sozlesme=self.sozlesme,
            sayac=mounted,
            aktif=True,
            takilma_tarihi=date(2026, 1, 1),
            ilk_endeks=Decimal("0"),
        )

        self.client.force_login(self.abone_user)
        response = self.client.post(reverse("abonelik:sayac_kullanim_disi", args=[bag.pk]))
        self.assertEqual(response.status_code, 302)
        mounted.refresh_from_db()
        bag.refresh_from_db()
        self.assertEqual(mounted.durum, "kullanim_disi")
        self.assertFalse(bag.aktif)

        self.client.force_login(self.sef_user)
        response = self.client.post(reverse("abonelik:hurdaya_gonder", args=[mounted.pk]), {
            "neden": "Mekanik arıza nedeniyle yeniden kullanılamaz",
        })
        self.assertEqual(response.status_code, 302)
        mounted.refresh_from_db()
        self.assertEqual(mounted.durum, "hurda")
        self.assertEqual(mounted.ambar, self.hurda_ambar)
        self.assertIn("Mekanik arıza", mounted.hurda_nedeni)
