"""Rutes de l'API del mòdul usuaris."""

from django.urls import path

from usuaris.views import (
    AdrecaDetailView,
    AdrecaListCreateView,
    AdrecaPredeterminadaView,
    FrangesRepartidorView,
)

app_name = "usuaris"

urlpatterns = [
    path("adreces/", AdrecaListCreateView.as_view(), name="adreces"),
    path("adreces/<int:id>/", AdrecaDetailView.as_view(), name="adreca"),
    path(
        "adreces/<int:id>/predeterminada/",
        AdrecaPredeterminadaView.as_view(),
        name="adreca-predeterminada",
    ),
    path("repartidor/franges/", FrangesRepartidorView.as_view(), name="franges-repartidor"),
]
