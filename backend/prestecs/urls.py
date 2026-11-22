"""Rutes de l'API del mòdul prestecs."""

from django.urls import path

from prestecs.views import ComandaLlestaView, ComandesBibliotecaView, ComandesView

app_name = "prestecs"

urlpatterns = [
    path("comandes/", ComandesView.as_view(), name="comandes"),
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
]
