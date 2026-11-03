"""Tests de la configuració de l'autenticació amb JWT."""

from datetime import timedelta

import pytest
from rest_framework import status
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from usuaris.models import Usuari


class VistaProtegida(APIView):
    def get(self, request):
        return Response({"correu": request.user.email})


def peticio_amb_token(token):
    peticio = APIRequestFactory().get(
        "/api/protegida/", HTTP_AUTHORIZATION=f"Bearer {token}"
    )
    return VistaProtegida.as_view()(peticio)


@pytest.fixture
def usuari(db):
    return Usuari.objects.create_user(
        email="anna@example.com",
        password="una-contrasenya-segura",
        name="Anna Puig",
        address="C/ Major 1, 08001 Barcelona",
        library_card_number="1234567890",
    )


def test_jwt_es_l_autenticacio_per_defecte():
    assert api_settings.DEFAULT_AUTHENTICATION_CLASSES == [JWTAuthentication]


def test_durada_dels_tokens():
    assert jwt_settings.ACCESS_TOKEN_LIFETIME == timedelta(minutes=15)
    assert jwt_settings.REFRESH_TOKEN_LIFETIME == timedelta(days=1)


def test_la_vista_de_simplejwt_fa_servir_el_correu_i_la_contrasenya(usuari):
    peticio = APIRequestFactory().post(
        "/api/inici-sessio/",
        {"correu": "anna@example.com", "contrasenya": "una-contrasenya-segura"},
        format="json",
    )

    resposta = TokenObtainPairView.as_view()(peticio)

    assert resposta.status_code == status.HTTP_200_OK
    assert set(resposta.data) == {"access", "refresh"}


def test_un_token_valid_autentica_l_usuari(usuari):
    resposta = peticio_amb_token(AccessToken.for_user(usuari))

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data == {"correu": "anna@example.com"}


def test_un_token_invalid_es_rebutja():
    resposta = peticio_amb_token("no-es-un-token")

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


def test_un_token_caducat_es_rebutja(usuari):
    token = AccessToken.for_user(usuari)
    token.set_exp(lifetime=-timedelta(seconds=1))

    resposta = peticio_amb_token(token)

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


def test_un_token_de_refresc_no_serveix_per_autenticar(usuari):
    resposta = peticio_amb_token(RefreshToken.for_user(usuari))

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


def test_el_token_d_un_compte_inactiu_es_rebutja(usuari):
    token = AccessToken.for_user(usuari)
    usuari.is_active = False
    usuari.save(update_fields=["is_active"])

    resposta = peticio_amb_token(token)

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


def test_salut_funciona_amb_un_token_invalid():
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer no-es-un-token")

    resposta = client.get("/api/health/")

    assert resposta.status_code == status.HTTP_200_OK
