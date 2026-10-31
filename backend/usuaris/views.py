"""Vistes de l'API del mòdul usuaris."""

import binascii

from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from usuaris.models import Usuari
from usuaris.serializers import (
    BibliotecaRegistreSerializer,
    UsuariRegistreSerializer,
    enviar_correu_verificacio,
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


class RegistreBibliotecaView(generics.CreateAPIView):
    """Registra una biblioteca amb el compte inactiu fins a verificar-lo."""

    serializer_class = BibliotecaRegistreSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def perform_create(self, serializer):
        biblioteca = serializer.save()
        enviar_correu_verificacio(biblioteca.usuari)


class VerificacioBibliotecaView(generics.GenericAPIView):
    """Activa el compte d'una biblioteca amb el token del correu."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            usuari = Usuari.objects.get(pk=uid)
        except (
            TypeError,
            ValueError,
            OverflowError,
            UnicodeDecodeError,
            binascii.Error,
            Usuari.DoesNotExist,
        ):
            return Response(
                {"detail": "L'enllaç de verificació no és vàlid o ha caducat."},
                status=HTTP_400_BAD_REQUEST,
            )

        if (
            usuari.role != Usuari.Role.BIBLIOTECA
            or not hasattr(usuari, "biblioteca")
            or not default_token_generator.check_token(usuari, token)
        ):
            return Response(
                {"detail": "L'enllaç de verificació no és vàlid o ha caducat."},
                status=HTTP_400_BAD_REQUEST,
            )

        usuari.is_active = True
        usuari.save(update_fields=["is_active"])
        return Response(
            {"detail": "El compte de biblioteca s'ha verificat correctament."},
            status=HTTP_200_OK,
        )
