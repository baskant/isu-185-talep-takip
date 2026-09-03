from django.urls import path
from . import views

app_name = "devirambar"

urlpatterns = [
    path("", views.panel_yonlendir, name="home"),
    path("devir/", views.devir_paneli, name="devir_paneli"),
    path("devir/<int:pk>/ambara-gonder/", views.ambara_gonder, name="ambara_gonder"),
    path("ambar/", views.ambar_paneli, name="ambar_paneli"),
    path("ambar/<int:pk>/<str:aksiyon>/", views.ambar_durum, name="ambar_durum"),
    path("merkez-ambar/", views.merkez_ambar_paneli, name="merkez_ambar_paneli"),
    path("merkez-ambar/<int:pk>/<str:aksiyon>/", views.merkez_ambar_durum, name="merkez_ambar_durum"),
    path("sistem/", views.sistem_devir_ambar, name="sistem"),
    path("sistem/csv/", views.sistem_csv, name="sistem_csv"),
]
