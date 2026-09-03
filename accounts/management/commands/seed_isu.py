from django.core.management.base import BaseCommand
from accounts.models import Rol, RolAtamaKurali
from accounts.saha_blueprint import SAHA_BLUEPRINTS
from adres.models import Ilce, Mahalle, Yol
from talepler.models import IsTuru, IsAltTuru

ILCELER = {
    "Başiskele": (40.7169, 29.9284),
    "Çayırova": (40.8260, 29.3744),
    "Darıca": (40.7696, 29.3803),
    "Derince": (40.7569, 29.8307),
    "Dilovası": (40.7873, 29.5352),
    "Gebze": (40.8028, 29.4307),
    "Gölcük": (40.7167, 29.8280),
    "İzmit": (40.7656, 29.9408),
    "Kandıra": (41.0704, 30.1520),
    "Karamürsel": (40.6917, 29.6161),
    "Kartepe": (40.7534, 30.0236),
    "Körfez": (40.7769, 29.7297),
}

IS_TURLERI = [
    {
        "kod": "icme-suyu",
        "ad": "İçme Suyu",
        "aciklama": "Şebeke, basınç ve içmesuyu arızaları",
        "alt": [
            "Su Kesintisi", "Boru Patlağı", "Su Kaçağı", "Düşük Basınç",
            "Yüksek Basınç", "Vana Arızası", "Şebeke Hattı Arızası",
            "Depo / Hat Kaynaklı Su Sorunu",
        ],
    },
    {
        "kod": "kanalizasyon",
        "ad": "Kanalizasyon",
        "aciklama": "Kanal, rögar ve atık su hattı sorunları",
        "alt": [
            "Kanal Tıkanıklığı", "Rögar Taşması", "Pis Koku", "Kanal Çökmesi",
            "Kanal Bağlantı Sorunu", "Rögar Kapağı Arızası / Eksikliği",
            "Atık Su Geri Tepmesi", "Kanal Hattı Hasarı",
        ],
    },
    {
        "kod": "yagmur-suyu",
        "ad": "Yağmur Suyu",
        "aciklama": "Mazgal ve yağmur suyu hattı talepleri",
        "alt": [
            "Mazgal Tıkanıklığı", "Mazgal Kapağı Arızası / Eksikliği",
            "Yağmur Suyu Hattı Tıkanıklığı", "Yolda Su Birikmesi",
            "Yağmur Suyu Taşkını", "Yağmur Suyu Hattı Hasarı",
        ],
    },
    {
        "kod": "vidanjor-kanal-acma",
        "ad": "Vidanjör ve Kanal Açma",
        "aciklama": "Vidanjör ve kanal temizleme operasyonları",
        "alt": [
            "Vidanjör Talebi", "Fosseptik Çekimi", "Basınçlı Kanal Açma",
            "Kanal Yıkama / Temizleme", "Rögar Temizliği",
        ],
    },
    {
        "kod": "abone-isleri",
        "ad": "Abone ve Sayaç İşleri",
        "aciklama": "Abonelik, sayaç ve yerinde abone hizmetleri",
        "alt": [
            "Yeni Abonelik", "Abonelik Açma", "Abonelik Kapatma",
            "Abone Bilgisi Güncelleme", "Sayaç Arızası", "Sayaç Değişimi",
            "Sayaç Okuma / Endeks Sorunu", "Fatura İtirazı",
            "Yüksek Fatura Şikâyeti", "Su Açma Talebi", "Su Kapama Talebi",
            "Abonelik Devir İşlemi",
        ],
    },
    {
        "kod": "kacak-su",
        "ad": "Kaçak Su ve Su Kayıpları",
        "aciklama": "Kaçak kullanım ve su kayıp kontrol ihbarları",
        "alt": [
            "Kaçak Su Kullanımı İhbarı", "Fiziki Kaçak Şüphesi",
            "İzinsiz Bağlantı Şüphesi", "Sayaç By-pass Şüphesi",
            "Bölgesel Su Kayıp İncelemesi", "Şebeke Kaçak Tespiti",
        ],
    },
    {
        "kod": "su-kalitesi",
        "ad": "Su Kalitesi ve Kirlilik",
        "aciklama": "Su kirliliği, renk, koku, tat ve numune talepleri",
        "alt": [
            "Su Kirliliği Şüphesi", "Bulanık / Renkli Su",
            "Kokulu Su", "Tat Değişikliği", "Tortu / Partikül Şikâyeti",
            "Numune Alma Talebi",
        ],
    },
    {
        "kod": "elektromekanik",
        "ad": "Elektromekanik ve Terfi",
        "aciklama": "Pompa, terfi, pano ve mekanik ekipman arızaları",
        "alt": [
            "Pompa Arızası", "Elektrik Panosu Arızası", "Terfi Merkezi Arızası",
            "Jeneratör Arızası", "Elektrik / Enerji Kaynaklı Arıza",
            "Mekanik Ekipman Arızası",
        ],
    },
    {
        "kod": "teknik-inceleme",
        "ad": "Teknik İnceleme",
        "aciklama": "Yerinde keşif ve teknik değerlendirme talepleri",
        "alt": [
            "Yerinde Keşif Talebi", "Hat Güzergâhı İncelemesi",
            "Teknik Kontrol Talebi", "Altyapı Uygunluk İncelemesi",
            "Teknik Görüş Talebi",
        ],
    },
    {
        "kod": "yol-kazi-onarim",
        "ad": "Yol ve Kazı Onarım",
        "aciklama": "Altyapı çalışması sonrası yol ve zemin düzenleme",
        "alt": [
            "Kazı Sonrası Asfalt Onarımı", "Parke Taşı Onarımı",
            "Kaldırım Onarımı", "Kazı Alanında Çökme",
            "Yol Kaplaması Bozukluğu", "Çalışma Sonrası Zemin Düzenleme",
        ],
    },
]

class Command(BaseCommand):
    help = "İSU 185 temel organizasyon, rol, ilçe ve iş türü verilerini kurar/günceller."

    def handle(self, *args, **options):
        roller = {}

        # Behlül Bey'in istediği ana parent/child omurgası korunur.
        base_roles = [
            ("admin", "Admin", "admin", None, "Sistem yönetimi"),
            ("185-personeli", "185 Personeli", "185", "admin", "Çağrı talep girişi"),
            ("icme-suyu-sefi", "İçme Suyu Şefi", "sef", "admin", "İçmesuyu operasyon şefi"),
            ("kanal-sefi", "Kanal Şefi", "sef", "admin", "Kanal operasyon şefi"),
            ("koordinator", "Koordinatör", "sef", "admin", "İlçe operasyon koordinatörü"),
        ]
        for kod, ad, panel, parent_kod, aciklama in base_roles:
            obj, _ = Rol.objects.update_or_create(
                kod=kod,
                defaults={
                    "ad": ad,
                    "panel_tipi": panel,
                    "calisma_kanali": "web",
                    "parent": roller.get(parent_kod),
                    "aktif": True,
                    "aciklama": aciklama,
                },
            )
            roller[kod] = obj

        # Saha rolleri kamuya açık İSU hizmet alanlarının uygulama karşılığıdır.
        for bp in SAHA_BLUEPRINTS:
            parent = roller.get(bp["parent"]) or Rol.objects.get(kod=bp["parent"])
            obj, _ = Rol.objects.update_or_create(
                kod=bp["kod"],
                defaults={
                    "ad": bp["ad"],
                    "panel_tipi": bp.get("panel_tipi", "saha"),
                    "calisma_kanali": bp.get("calisma_kanali", "mobil"),
                    "parent": parent,
                    "aktif": True,
                    "aciklama": bp["aciklama"],
                },
            )
            roller[bp["kod"]] = obj

        # Şeflerin kendi uzman ekipleri.
        for kaynak, hedef in [
            ("icme-suyu-sefi", "icme-suyu-saha"),
            ("kanal-sefi", "kanal-saha"),
        ]:
            RolAtamaKurali.objects.update_or_create(
                kaynak_rol=roller[kaynak],
                hedef_rol=roller[hedef],
                defaults={"aktif": True},
            )

        # İlçe koordinatörü kendi ilçesindeki tüm operasyonel saha türlerine atama yapabilir.
        for bp in SAHA_BLUEPRINTS:
            if bp.get("panel_tipi", "saha") != "saha":
                continue
            RolAtamaKurali.objects.update_or_create(
                kaynak_rol=roller["koordinator"],
                hedef_rol=roller[bp["kod"]],
                defaults={
                    "aktif": True,
                    "aciklama": "İlçe + uzmanlık + müsaitlik kontrolüyle atanır.",
                },
            )

        # Behlül Bey'in belirttiği çapraz ilişki de korunur.
        RolAtamaKurali.objects.update_or_create(
            kaynak_rol=roller["kanal-saha"],
            hedef_rol=roller["ortak-saha"],
            defaults={"aktif": True},
        )

        ilceler = {}
        for ad, (lat, lng) in ILCELER.items():
            ilceler[ad], _ = Ilce.objects.update_or_create(
                ad=ad,
                defaults={"aktif": True, "merkez_lat": lat, "merkez_lng": lng},
            )

        is_turu_map = {}
        for veri in IS_TURLERI:
            tur, _ = IsTuru.objects.update_or_create(
                kod=veri["kod"],
                defaults={
                    "ad": veri["ad"],
                    "aktif": True,
                    "aciklama": veri["aciklama"],
                },
            )
            is_turu_map[veri["kod"]] = tur
            for alt_ad in veri["alt"]:
                IsAltTuru.objects.update_or_create(
                    is_turu=tur,
                    ad=alt_ad,
                    defaults={"aktif": True},
                )

        # Küçük demo yol seti; gerçek mahalleler V3 senkronundan gelir.
        demo = [
            ("Başiskele", "Barbaros Mahallesi", "Atatürk Caddesi", "cadde"),
            ("İzmit", "Karabaş Mahallesi", "Cumhuriyet Bulvarı", "bulvar"),
            ("İzmit", "Yahya Kaptan Mahallesi", "Şehit Ergün Köncü Sokak", "sokak"),
            ("Gölcük", "Merkez Mahallesi", "Amiral Sağlam Caddesi", "cadde"),
        ]
        for ilce_ad, mahalle_ad, yol_ad, yol_tur in demo:
            mahalle, _ = Mahalle.objects.get_or_create(
                ilce=ilceler[ilce_ad], ad=mahalle_ad,
            )
            Yol.objects.get_or_create(
                mahalle=mahalle, ad=yol_ad, defaults={"tur": yol_tur},
            )

        self.stdout.write(
            self.style.SUCCESS(
                "İSU 185 V4 temel verileri, saha rolleri ve atama kuralları güncellendi."
            )
        )
