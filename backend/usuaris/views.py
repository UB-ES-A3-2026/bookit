"""Vistes de l'API del mòdul usuaris."""

from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from usuaris.serializers import (
    RepartidorRegistreSerializer,
    UsuariActualSerializer,
    UsuariRegistreSerializer,
)


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


class UsuariActualView(generics.RetrieveAPIView):
    """Retorna les dades i el rol de l'usuari del token (US2). Contracte a `docs/api-auth.md`.

    Retorna 200 amb les dades de l'usuari o 401 si no hi ha un token vàlid.
    """

    serializer_class = UsuariActualSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class RegistreRepartidorView(generics.CreateAPIView):
    """Registra un repartidor nou (US1.1). Contracte a `docs/api-registre-repartidor.md`.

    Retorna 201 amb les dades del repartidor i l'estat del perfil (sense la
    contrasenya) o 400 amb els errors agrupats per camp.
    """

    serializer_class = RepartidorRegistreSerializer
    # Endpoint públic, com el registre d'usuaris: mateixos motius que a RegistreView.
    permission_classes = [AllowAny]
    authentication_classes = []
