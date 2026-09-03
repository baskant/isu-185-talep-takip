"""
İSU 185 uygulamasındaki operasyonel saha rol şablonları.

Not:
Bu adlar bordro/kadro unvanı iddiası değildir. İSU'nun kamuya açık güncel
organizasyon yapısındaki hizmet alanları ile ALO 185 başvuru kategorilerinin,
talep-atama yazılımında kullanılabilecek operasyon karşılıklarıdır.
"""

SAHA_BLUEPRINTS = [
    {
        "kod": "icme-suyu-saha",
        "ad": "İçmesuyu Arıza Saha",
        "parent": "icme-suyu-sefi",
        "prefix": "su",
        "is_turleri": ["icme-suyu"],
        "aciklama": "Şebeke, basınç, boru, vana ve içmesuyu arızaları.",
    },
    {
        "kod": "kanal-saha",
        "ad": "Kanalizasyon ve Yağmursuyu Saha",
        "parent": "kanal-sefi",
        "prefix": "kanal",
        "is_turleri": ["kanalizasyon", "yagmur-suyu", "vidanjor-kanal-acma"],
        "aciklama": "Kanalizasyon, rögar, yağmursuyu, vidanjör ve kanal açma işleri.",
    },
    {
        "kod": "abone-sayac-saha",
        "ad": "Abonelik ve Sayaç İşlemleri",
        "parent": "koordinator",
        "prefix": "sayac",
        "panel_tipi": "abone",
        "calisma_kanali": "web",
        "is_turleri": ["abone-isleri"],
        "aciklama": "Abonelik ve sayaç işlemlerinin masaüstü Web/PC operasyon ekranı.",
    },
    {
        "kod": "kacak-su-saha",
        "ad": "Kaçak Su ve Su Kayıp Kontrol Saha",
        "parent": "koordinator",
        "prefix": "kacak",
        "is_turleri": ["kacak-su"],
        "aciklama": "Kaçak kullanım, fiziki kaçak ve su kayıp kontrol işleri.",
    },
    {
        "kod": "su-kalitesi-saha",
        "ad": "Su Kalitesi ve Numune Saha",
        "parent": "koordinator",
        "prefix": "kalite",
        "is_turleri": ["su-kalitesi"],
        "aciklama": "Su kirliliği şüphesi, numune ve saha kalite kontrolleri.",
    },
    {
        "kod": "elektromekanik-saha",
        "ad": "Elektromekanik ve Terfi Saha",
        "parent": "koordinator",
        "prefix": "em",
        "is_turleri": ["elektromekanik"],
        "aciklama": "Pompa, terfi, elektrik ve mekanik bakım-onarım işleri.",
    },
    {
        "kod": "ortak-saha",
        "ad": "Ortak İlçe Saha",
        "parent": "koordinator",
        "prefix": "saha",
        "is_turleri": [],
        "aciklama": "İlçe koordinatörünün genel destek/fallback saha ekibi.",
    },
]

SAHA_ROLE_CODES = [x["kod"] for x in SAHA_BLUEPRINTS]

def blueprint_for_role(role_code):
    return next((x for x in SAHA_BLUEPRINTS if x["kod"] == role_code), None)
