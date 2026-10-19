"""Rutes del projecte. Totes les rutes de l'API van sota /api/."""

from django.contrib import admin
from django.urls import include, path

from config.views import salut

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", salut, name="salut"),
    path("api/usuaris/", include("usuaris.urls")),
    path("api/cataleg/", include("cataleg.urls")),
    path("api/prestecs/", include("prestecs.urls")),
]
