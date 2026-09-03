from django.urls import path
from . import views
app_name="adres"
urlpatterns=[
    path("mahalleler/",views.mahalleler,name="mahalleler"),
    path("yollar/",views.yollar,name="yollar"),
    path("ilce/",views.ilce_detay,name="ilce_detay"),
    path("geocode/",views.geocode,name="geocode"),
]
