"""Rutes de l'API del mòdul usuaris."""
from django.urls import path
from usuaris.views import AdrecaDetailView, AdrecaListCreateView


app_name = "usuaris"

urlpatterns = [path("adreces/", AdrecaListCreateView.as_view(), name="adreces"),
    path("adreces/<int:id>/", AdrecaDetailView.as_view(), name="adreca"),
    ]
