"""Vistes de l'API del mòdul usuaris."""

import binascii

from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from usuaris.models import FranjaDisponibilitat, Usuari
from usuaris.permisos import EsRepartidorValidat
from usuaris.serializers import (
    CAMP_OBLIGATORI,
    BibliotecaRegistreSerializer,
    FranjaSerializer,
    FrangesSerializer,
    RepartidorRegistreSerializer,
    UsuariActualSerializer,
    UsuariRegistreSerializer,
    enviar_correu_verificacio,
    missatges_contrasenya,
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


class RegistreBibliotecaView(generics.CreateAPIView):
    """Registra una biblioteca amb el compte inactiu fins a verificar-lo."""

    serializer_class = BibliotecaRegistreSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def perform_create(self, serializer):
        biblioteca = serializer.save()
        enviar_correu_verificacio(biblioteca.usuari)


ENLLAC_INVALID = "L'enllaç de verificació no és vàlid o ha caducat."


class VerificacioBibliotecaView(generics.GenericAPIView):
    """Verificació del compte d'una biblioteca amb l'enllaç del correu.

    El GET només comprova que l'enllaç sigui vàlid. El POST rep la contrasenya
    que tria la biblioteca, la desa i activa el compte. Com que el token de Django
    depèn de la contrasenya, en desar-la l'enllaç deixa de ser vàlid i només es
    pot fer servir una vegada.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def biblioteca_de_l_enllac(self, uidb64, token):
        """Retorna l'usuari de la biblioteca de l'enllaç, o None si no és vàlid."""
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
            return None

        if (
            usuari.role != Usuari.Role.BIBLIOTECA
            or not hasattr(usuari, "biblioteca")
            or not default_token_generator.check_token(usuari, token)
        ):
            return None
        return usuari

    def get(self, request, uidb64, token):
        usuari = self.biblioteca_de_l_enllac(uidb64, token)
        if usuari is None:
            return Response({"detail": ENLLAC_INVALID}, status=HTTP_400_BAD_REQUEST)
        return Response({"correu": usuari.email}, status=HTTP_200_OK)

    def post(self, request, uidb64, token):
        usuari = self.biblioteca_de_l_enllac(uidb64, token)
        if usuari is None:
            return Response({"detail": ENLLAC_INVALID}, status=HTTP_400_BAD_REQUEST)

        contrasenya = request.data.get("contrasenya")
        if not isinstance(contrasenya, str) or not contrasenya:
            return Response(
                {"contrasenya": [CAMP_OBLIGATORI]}, status=HTTP_400_BAD_REQUEST
            )

        try:
            validate_password(contrasenya, user=usuari)
        except DjangoValidationError as error:
            return Response(
                {"contrasenya": missatges_contrasenya(error)},
                status=HTTP_400_BAD_REQUEST,
            )

        usuari.set_password(contrasenya)
        usuari.is_active = True
        usuari.save(update_fields=["password", "is_active"])
        return Response(
            {"detail": "El compte de biblioteca s'ha verificat correctament."},
            status=HTTP_200_OK,
        )


class FrangesRepartidorView(generics.GenericAPIView):
    """Franges de disponibilitat del repartidor autenticat (US14-T2).

    GET les retorna i PUT les substitueix totes per les que s'envien, perquè el
    repartidor desa l'horari de la setmana sencer d'una vegada. Contracte a
    `docs/api-franges.md`.
    """

    serializer_class = FrangesSerializer
    permission_classes = [EsRepartidorValidat]

    def resposta(self, perfil):
        return Response({"franges": FranjaSerializer(perfil.franges.all(), many=True).data})

    def get(self, request):
        return self.resposta(request.user.perfil_repartidor)

    def put(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        perfil = request.user.perfil_repartidor
        with transaction.atomic():
            perfil.franges.all().delete()
            FranjaDisponibilitat.objects.bulk_create(
                FranjaDisponibilitat(repartidor=perfil, **franja)
                for franja in serializer.validated_data["franges"]
            )
        return self.resposta(perfil)
