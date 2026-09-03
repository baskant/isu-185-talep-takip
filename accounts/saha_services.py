import secrets
import string
from django.contrib.auth.models import User
from django.utils.text import slugify

from .models import PersonelProfili, Rol
from .saha_blueprint import SAHA_BLUEPRINTS
from adres.models import Ilce
from talepler.models import IsTuru

def _password():
    alphabet = string.ascii_letters + string.digits
    return "Isu#" + "".join(secrets.choice(alphabet) for _ in range(10))

def _username(prefix, ilce_ad):
    base = f"{prefix}_{slugify(ilce_ad).replace('-', '_')}"
    username = base
    n = 2
    while User.objects.filter(username=username).exists():
        username = f"{base}_{n}"
        n += 1
    return username

def create_missing_field_teams(*, password=None):
    """
    Her aktif ilçe için her saha rolünden en az bir aktif hesap olmasını sağlar.
    Var olan hesaplara dokunmaz. Yeni hesapların uzmanlıkları blueprint'e göre atanır.
    """
    generated = []

    field_blueprints = [bp for bp in SAHA_BLUEPRINTS if bp.get("panel_tipi", "saha") == "saha"]
    roles = {
        bp["kod"]: Rol.objects.get(kod=bp["kod"], aktif=True)
        for bp in field_blueprints
    }
    work_types = {x.kod: x for x in IsTuru.objects.filter(aktif=True)}

    for ilce in Ilce.objects.filter(aktif=True).order_by("ad"):
        for bp in field_blueprints:
            role = roles[bp["kod"]]
            if PersonelProfili.objects.filter(
                rol=role,
                yetkili_ilceler=ilce,
                aktif=True,
            ).exists():
                continue

            username = _username(bp["prefix"], ilce.ad)
            pwd = password or _password()
            user = User.objects.create_user(
                username=username,
                password=pwd,
                first_name=ilce.ad,
                last_name=bp["ad"],
            )
            profile = PersonelProfili.objects.create(
                kullanici=user,
                rol=role,
                aktif=True,
                musait=True,
            )
            profile.yetkili_ilceler.add(ilce)

            specs = [
                work_types[kod]
                for kod in bp["is_turleri"]
                if kod in work_types
            ]
            if specs:
                profile.uzmanlik_is_turleri.set(specs)

            generated.append({
                "username": username,
                "password": pwd,
                "rol": role.ad,
                "kanal": role.get_calisma_kanali_display(),
                "ilce": ilce.ad,
                "uzmanlik": ", ".join(x.ad for x in specs) if specs else "Genel / fallback",
            })

    return generated


def create_missing_coordinators(*, password=None):
    """Her aktif ilçede en az bir aktif koordinatör bulunmasını sağlar."""
    generated = []
    role = Rol.objects.get(kod="koordinator", aktif=True)

    for ilce in Ilce.objects.filter(aktif=True).order_by("ad"):
        if PersonelProfili.objects.filter(
            rol=role,
            yetkili_ilceler=ilce,
            aktif=True,
        ).exists():
            continue

        username = _username("koord", ilce.ad)
        pwd = password or _password()
        user = User.objects.create_user(
            username=username,
            password=pwd,
            first_name=ilce.ad,
            last_name="Koordinatör",
        )
        profile = PersonelProfili.objects.create(
            kullanici=user,
            rol=role,
            aktif=True,
            musait=True,
        )
        profile.yetkili_ilceler.add(ilce)

        generated.append({
            "username": username,
            "password": pwd,
            "rol": role.ad,
            "kanal": role.get_calisma_kanali_display(),
            "ilce": ilce.ad,
            "uzmanlik": "İlçe koordinasyonu",
        })

    return generated


def create_missing_organization(*, password=None):
    """
    Tek işlemde eksik ilçe koordinatörlerini ve uzman saha ekiplerini tamamlar.
    Var olan hesaplara dokunmaz.
    """
    return (
        create_missing_coordinators(password=password)
        + create_missing_field_teams(password=password)
    )
