"""Rutes d'autenticació del mòdul usuaris, sota /api/auth/.

El contracte de l'endpoint de registre és a `docs/api-registre.md` i el de
l'usuari autenticat, a `docs/api-auth.md`.
"""

from django.urls import path

from usuaris.views import RegistreView, UsuariActualView

app_name = "auth"

urlpatterns = [
    path("register/", RegistreView.as_view(), name="registre"),
    path("me/", UsuariActualView.as_view(), name="me"),
]
