"""Rutes de l'API del mòdul prestecs."""

from django.urls import path

from prestecs.views import CancellarComandaView, ComandesView

app_name = "prestecs"

urlpatterns = [
    path("comandes/", ComandesView.as_view(), name="comandes"),
    path("comandes/<int:pk>/cancellar/", CancellarComandaView.as_view(), name="cancellar-comanda"),
]
