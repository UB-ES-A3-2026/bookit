"""Rutes d'autenticació del mòdul usuaris, sota /api/auth/.

Els contractes dels endpoints de registre són a `docs/api-registre.md` i
`docs/api-registre-repartidor.md`.
"""

from django.urls import path

from usuaris.views import RegistreRepartidorView, RegistreView

app_name = "auth"

urlpatterns = [
    path("register/", RegistreView.as_view(), name="registre"),
    path(
        "register/repartidor/",
        RegistreRepartidorView.as_view(),
        name="registre-repartidor",
    ),
]
