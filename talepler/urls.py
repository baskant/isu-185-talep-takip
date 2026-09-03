from django.urls import path
from . import views

app_name="talepler"

urlpatterns=[
    path("alt-turler/",views.alt_turler,name="alt_turler"),
    path("<int:pk>/timeline/",views.timeline,name="timeline"),
    path("operasyon-ozet/",views.operasyon_ozet,name="operasyon_ozet"),
]
