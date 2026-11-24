"""Rutes d'autenticació del mòdul usuaris, sota /api/auth/.

Els contractes dels endpoints de registre són a `docs/api-registre.md` i
`docs/api-registre-repartidor.md`, i els d'inici de sessió i de l'usuari
autenticat, a `docs/api-auth.md`.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from usuaris.views import (
    RegistreBibliotecaView,
    RegistreRepartidorView,
    RegistreView,
    UsuariActualView,
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
    # Les vistes de simplejwt són públiques i no autentiquen la petició: un token
    # caducat a la capçalera no impedeix iniciar sessió ni renovar l'accés.
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("me/", UsuariActualView.as_view(), name="me"),
]
