from django.urls import path
from . import views

app_name = "abonelik"

urlpatterns = [
    path("", views.izleme, name="izleme"),
    path("<int:pk>/iletisim-ekle/", views.izleme_iletisim_ekle, name="izleme_iletisim_ekle"),
    path("sozlesme/<int:pk>/sayac-ata/", views.sayac_ata, name="sayac_ata"),
    path("sicil/", views.sicil, name="sicil"),
    path("sicil/<int:pk>/toggle/", views.sicil_toggle, name="sicil_toggle"),
    path("sicil/iletisim/<int:pk>/toggle/", views.iletisim_toggle, name="iletisim_toggle"),
    path("sozlesmeler/", views.sozlesmeler, name="sozlesmeler"),
    path("sozlesme/<int:pk>/toggle/", views.sozlesme_toggle, name="sozlesme_toggle"),
    path("sayac/<int:pk>/kullanim-disi/", views.sayac_kullanim_disi, name="sayac_kullanim_disi"),
    path("ambar/", views.ambar_yonetimi, name="ambar_yonetimi"),
    path("ambar/talep/<int:pk>/<str:aksiyon>/", views.ambar_talep_durum, name="ambar_talep_durum"),
    path("ambar/sayac/<int:pk>/hurda/", views.hurdaya_gonder, name="hurdaya_gonder"),
]
