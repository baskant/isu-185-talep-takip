from talepler.models import IslemLogu
def global_ui(request):
    if not request.user.is_authenticated:return {}
    try:p=request.user.personel_profili
    except Exception:p=None
    logs=IslemLogu.objects.select_related("kullanici","talep")
    if not request.user.is_superuser and p:
        if p.rol.panel_tipi=="saha":logs=logs.filter(talep__sorumlu_saha=p)
        elif p.rol.panel_tipi=="sef":logs=logs.filter(talep__ilce__in=p.yetkili_ilceler.all())
        elif p.rol.panel_tipi=="185":logs=logs.filter(talep__isnull=False)
    return {"global_profil":p,"global_loglar":logs[:25]}
