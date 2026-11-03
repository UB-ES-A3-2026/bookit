"""Rutes de l'API del mòdul cataleg."""

from django.urls import path

from cataleg.views import CatalegBibliotecaView, CercaLlibresView

app_name = "cataleg"

urlpatterns = [
    path("llibres/", CercaLlibresView.as_view(), name="cerca-llibres"),
    path(
        "biblioteca/llibres/",
        CatalegBibliotecaView.as_view(),
        name="cataleg-biblioteca",
    ),
]
