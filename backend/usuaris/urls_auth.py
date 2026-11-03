"""Rutes d'autenticació del mòdul usuaris, sota /api/auth/.

Els contractes dels endpoints de registre són a `docs/api-registre.md` i
`docs/api-registre-repartidor.md`.
"""

from django.urls import path

from usuaris.views import (
    RegistreBibliotecaView,
    RegistreRepartidorView,
    RegistreView,
    VerificacioBibliotecaView,
)

app_name = "auth"

urlpatterns = [
    path("register/", RegistreView.as_view(), name="registre"),
    path(
        "register/repartidor/",
        RegistreRepartidorView.as_view(),
        name="registre-repartidor",
    ),
    path(
        "register/biblioteca/",
        RegistreBibliotecaView.as_view(),
        name="registre-biblioteca",
    ),
    path(
        "verify/biblioteca/<uidb64>/<token>/",
        VerificacioBibliotecaView.as_view(),
        name="verificacio-biblioteca",
    ),
]
