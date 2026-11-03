"""Rutes d'autenticació del mòdul usuaris, sota /api/auth/.

El contracte de l'endpoint de registre és a `docs/api-registre.md` i el de
l'usuari autenticat, a `docs/api-auth.md`.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from usuaris.views import RegistreView, UsuariActualView

app_name = "auth"

urlpatterns = [
    path("register/", RegistreView.as_view(), name="registre"),
    # Les vistes de simplejwt són públiques i no autentiquen la petició: un token
    # caducat a la capçalera no impedeix iniciar sessió ni renovar l'accés.
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("me/", UsuariActualView.as_view(), name="me"),
]
