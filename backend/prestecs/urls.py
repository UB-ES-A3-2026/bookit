"""Rutes de l'API del mòdul prestecs."""

from django.urls import path

from prestecs.views import (
    CancellarComandaView,
    ComandesView,
    NotificacioLlegidaView,
    NotificacionsLlegidesView,
    NotificacionsView,
)

app_name = "prestecs"

urlpatterns = [
    path("comandes/", ComandesView.as_view(), name="comandes"),
    path("comandes/<int:pk>/cancellar/", CancellarComandaView.as_view(), name="cancellar-comanda"),
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
]
