"""Rutes de l'API del mòdul prestecs."""

from django.urls import path

from prestecs.views import (
    ComandesView,
    NotificacioLlegidaView,
    NotificacionsLlegidesView,
    NotificacionsView,
    PrestecsView,
)

app_name = "prestecs"

urlpatterns = [
    path("comandes/", ComandesView.as_view(), name="comandes"),
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
]
