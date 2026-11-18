"""Rutes de l'API del mòdul prestecs."""

from django.urls import path

from prestecs.views import ComandesBibliotecaView, ComandesView

app_name = "prestecs"

urlpatterns = [
    path("comandes/", ComandesView.as_view(), name="comandes"),
    path(
        "biblioteca/comandes/",
        ComandesBibliotecaView.as_view(),
        name="comandes-biblioteca",
    ),
]
