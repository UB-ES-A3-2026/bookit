"""Vistes de l'API del mòdul usuaris."""

from rest_framework import generics
from rest_framework.permissions import AllowAny

from usuaris.serializers import BibliotecaRegistreSerializer, UsuariRegistreSerializer


class RegistreView(generics.CreateAPIView):
    """Registra un usuari nou (US1). Contracte a `docs/api-registre.md`.

    Retorna 201 amb les dades de l'usuari creat (sense la contrasenya) o 400 amb
    els errors agrupats per camp.
    """

    serializer_class = UsuariRegistreSerializer
    # Endpoint públic: qualsevol persona s'ha de poder registrar sense sessió.
    permission_classes = [AllowAny]
    # Sense autenticació: així una sessió oberta (p. ex. de l'admin)
    # no obliga a enviar el token CSRF.
    authentication_classes = []


class RegistreBibliotecaView(generics.CreateAPIView):
    """Registra una biblioteca amb el compte inactiu fins a verificar-lo."""

    serializer_class = BibliotecaRegistreSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
