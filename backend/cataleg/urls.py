"""Rutes de l'API del mòdul cataleg."""

from django.urls import path

from cataleg.views import (
    CatalegBibliotecaView,
    CercaLlibresView,
    ExemplarsCatalegBibliotecaView,
    LlibreCatalegBibliotecaView,
)

app_name = "cataleg"

urlpatterns = [
    path("llibres/", CercaLlibresView.as_view(), name="cerca-llibres"),
    path(
        "biblioteca/llibres/",
        CatalegBibliotecaView.as_view(),
        name="cataleg-biblioteca",
    ),
    path(
        "biblioteca/llibres/<int:id>/",
        LlibreCatalegBibliotecaView.as_view(),
        name="llibre-cataleg-biblioteca",
    ),
    path(
        "biblioteca/llibres/<int:id>/exemplars/",
        ExemplarsCatalegBibliotecaView.as_view(),
        name="exemplars-cataleg-biblioteca",
    ),
]
