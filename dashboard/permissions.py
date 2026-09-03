from functools import wraps
from django.core.exceptions import PermissionDenied
def get_profile(user):
    try:return user.personel_profili
    except Exception:return None
def panel_required(*tipler):
    def deco(view):
        @wraps(view)
        def inner(request,*args,**kwargs):
            if not request.user.is_authenticated:raise PermissionDenied
            if request.user.is_superuser:return view(request,*args,**kwargs)
            p=get_profile(request.user)
            if not p or not p.aktif or p.rol.panel_tipi not in tipler:raise PermissionDenied
            return view(request,*args,**kwargs)
        return inner
    return deco


def operational_profile(request, panel_tipi):
    """
    Operasyon işlemleri sistem yöneticisi tarafından yapılamaz.
    Sistem yöneticisi denetler; 185/koordinatör/saha kendi görevini yürütür.
    """
    if request.user.is_superuser:
        raise PermissionDenied(
            "Sistem yöneticisi operasyonel işlem yapamaz; bu ekran ilgili operasyon rolüne aittir."
        )
    p=get_profile(request.user)
    if not p or not p.aktif or p.rol.panel_tipi!=panel_tipi:
        raise PermissionDenied("Bu işlem için uygun operasyon rolünüz bulunmuyor.")
    return p
