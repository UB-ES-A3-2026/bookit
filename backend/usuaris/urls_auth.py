"""Rutes d'autenticació del mòdul usuaris, sota /api/auth/.

El contracte de l'endpoint de registre és a `docs/api-registre.md`.
"""

from django.urls import path

from usuaris.views import RegistreBibliotecaView, RegistreView

app_name = "auth"

urlpatterns = [
    path("register/", RegistreView.as_view(), name="registre"),
    path(
        "register/biblioteca/",
        RegistreBibliotecaView.as_view(),
        name="registre-biblioteca",
    ),
]
