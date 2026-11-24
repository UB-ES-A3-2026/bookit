"""Rutes de l'API del mòdul prestecs."""

from django.urls import path

from prestecs.views import ComandaLlestaView, ComandesView, RutaAvuiView

app_name = "prestecs"

urlpatterns = [
    path("comandes/", ComandesView.as_view(), name="comandes"),
    path(
        "biblioteca/comandes/<int:pk>/preparada/",
        ComandaLlestaView.as_view(),
        name="comanda-llesta",
    ),
    path(
        "repartidor/ruta-avui/",
        RutaAvuiView.as_view(),
        name="ruta-avui-repartidor",
    ),
]
