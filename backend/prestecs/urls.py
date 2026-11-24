"""Rutes de l'API del mòdul prestecs."""

from django.urls import path

from prestecs.views import (
    ComandesView,
    ComandaLlestaView,
    NotificacioLlegidaView,
    NotificacionsLlegidesView,
    NotificacionsView,
    RutaAvuiView,
    CompletarParadaView,
    FallarParadaView,
)

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
    path("notificacions/", NotificacionsView.as_view(), name="notificacions"),
    path(
        "notificacions/<int:pk>/llegida/",
        NotificacioLlegidaView.as_view(),
        name="notificacio-llegida",
    ),
    path(
        "notificacions/llegides/",
        NotificacionsLlegidesView.as_view(),
        name="notificacions-llegides",
    ),
    path(
        "repartidor/parades/<int:pk>/completar/",
        CompletarParadaView.as_view(),
        name="completar-parada",
    ),
    path(
        "repartidor/parades/<int:pk>/fallida/",
        FallarParadaView.as_view(),
        name="fallar-parada",
    ),
]
