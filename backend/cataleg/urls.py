"""Rutes de l'API del mòdul cataleg."""

from django.urls import path

from cataleg.views import CercaLlibresView

app_name = "cataleg"

urlpatterns = [
    path("llibres/", CercaLlibresView.as_view(), name="cerca-llibres"),
]
