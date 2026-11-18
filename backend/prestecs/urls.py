"""Rutes de l'API del mòdul prestecs."""

from django.urls import path

from prestecs.views import ComandesView, CostEnviamentView

app_name = "prestecs"

urlpatterns = [
    path("comandes/", ComandesView.as_view(), name="comandes"),
    path("comandes/cost-enviament/", CostEnviamentView.as_view(), name="cost-enviament"),
]
