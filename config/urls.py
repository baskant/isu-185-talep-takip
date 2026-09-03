from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("_teknik_admin_/", admin.site.urls),
    path("giris/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("cikis/", auth_views.LogoutView.as_view(), name="logout"),
    path("api/adres/", include("adres.urls")),
    path("api/talepler/", include("talepler.urls")),
    path("abonelik/", include("abonelik.urls")),
    path("", include("dashboard.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
