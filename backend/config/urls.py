"""Rutes del projecte. Totes les rutes de l'API van sota /api/."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/usuaris/", include("usuaris.urls")),
    path("api/cataleg/", include("cataleg.urls")),
    path("api/prestecs/", include("prestecs.urls")),
]
