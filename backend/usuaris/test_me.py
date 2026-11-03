"""Tests de l'endpoint de l'usuari autenticat, `GET /api/auth/me/` (US2-T4)."""

from datetime import timedelta

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from usuaris.models import Usuari

URL = "/api/auth/me/"


def crear_usuari(**camps):
    dades = {
        "email": "anna@example.com",
        "password": "una-contrasenya-segura",
        "name": "Anna Puig",
        "address": "C/ Major 1, 08001 Barcelona",
        "library_card_number": "1234567890",
    }
    return Usuari.objects.create_user(**(dades | camps))


def client_amb_token(token):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def usuari(db):
    return crear_usuari()


def test_retorna_les_dades_de_l_usuari_del_token(usuari):
    resposta = client_amb_token(AccessToken.for_user(usuari)).get(URL)

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data == {
        "id": usuari.id,
        "nom": "Anna Puig",
        "correu": "anna@example.com",
        "rol": "usuari",
    }


@pytest.mark.parametrize(
    "rol",
    [Usuari.Role.USUARI, Usuari.Role.REPARTIDOR, Usuari.Role.BIBLIOTECA],
)
def test_retorna_els_mateixos_camps_per_a_cada_rol(db, rol):
    usuari = crear_usuari(role=rol)

    resposta = client_amb_token(AccessToken.for_user(usuari)).get(URL)

    assert resposta.status_code == status.HTTP_200_OK
    assert set(resposta.data) == {"id", "nom", "correu", "rol"}
    assert resposta.data["rol"] == rol


def test_cada_token_retorna_el_seu_usuari(usuari):
    altre = crear_usuari(
        email="pere@example.com", name="Pere Vila", library_card_number="0987654321"
    )

    resposta = client_amb_token(AccessToken.for_user(altre)).get(URL)

    assert resposta.data["id"] == altre.id
    assert resposta.data["correu"] == "pere@example.com"


def test_sense_token_retorna_401(db):
    resposta = APIClient().get(URL)

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


def test_un_token_invalid_retorna_401(db):
    resposta = client_amb_token("no-es-un-token").get(URL)

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED
    assert resposta.data["code"] == "token_not_valid"


def test_un_token_caducat_retorna_401(usuari):
    token = AccessToken.for_user(usuari)
    token.set_exp(lifetime=-timedelta(seconds=1))

    resposta = client_amb_token(token).get(URL)

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED
    assert resposta.data["code"] == "token_not_valid"


def test_un_token_de_refresc_retorna_401(usuari):
    resposta = client_amb_token(RefreshToken.for_user(usuari)).get(URL)

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED
    assert resposta.data["code"] == "token_not_valid"


def test_el_token_d_un_compte_inactiu_retorna_401(usuari):
    token = AccessToken.for_user(usuari)
    usuari.is_active = False
    usuari.save(update_fields=["is_active"])

    resposta = client_amb_token(token).get(URL)

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED
    assert resposta.data["code"] == "user_inactive"


def test_el_token_d_un_compte_esborrat_retorna_401(usuari):
    token = AccessToken.for_user(usuari)
    usuari.delete()

    resposta = client_amb_token(token).get(URL)

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("metode", ["post", "put", "patch", "delete"])
def test_els_altres_metodes_retornen_405(usuari, metode):
    client = client_amb_token(AccessToken.for_user(usuari))

    resposta = getattr(client, metode)(URL)

    assert resposta.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
