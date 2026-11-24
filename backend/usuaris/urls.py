"""Rutes de l'API del mòdul usuaris."""

from django.urls import path

from usuaris.views import FrangesRepartidorView

app_name = "usuaris"

urlpatterns = [
    path("repartidor/franges/", FrangesRepartidorView.as_view(), name="franges-repartidor"),
]
