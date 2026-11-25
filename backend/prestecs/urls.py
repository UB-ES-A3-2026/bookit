"""Rutes de l'API del mòdul prestecs."""

from django.urls import path

from prestecs.views import (
    CancellarComandaView,
    CompletarParadaView,
    ComandaLlestaView,
    ComandaRecollidaView,
    ComandesBibliotecaView,
    ComandesView,
    CostEnviamentView,
    FallarParadaView,
    NotificacioLlegidaView,
    NotificacionsLlegidesView,
    NotificacionsView,
    PrestecsView,
    RutaAvuiView,
)

app_name = "prestecs"

urlpatterns = [
    path("comandes/", ComandesView.as_view(), name="comandes"),
    path("comandes/cost-enviament/", CostEnviamentView.as_view(), name="cost-enviament"),
    path("comandes/<int:pk>/cancellar/", CancellarComandaView.as_view(), name="cancellar-comanda"),
    path("prestecs/", PrestecsView.as_view(), name="prestecs"),
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
        "biblioteca/comandes/",
        ComandesBibliotecaView.as_view(),
        name="comandes-biblioteca",
    ),
    path(
        "biblioteca/comandes/<int:pk>/preparada/",
        ComandaLlestaView.as_view(),
        name="comanda-llesta",
    ),
    path(
        "biblioteca/comandes/<int:pk>/recollida/",
        ComandaRecollidaView.as_view(),
        name="comanda-recollida",
    ),
    path(
        "repartidor/ruta-avui/",
        RutaAvuiView.as_view(),
        name="ruta-avui-repartidor",
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
