"""Tests dels endpoints d'inici de sessió i renovació del token (US2-T2)."""

from datetime import timedelta

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from usuaris.models import Usuari

URL_LOGIN = "/api/auth/login/"
URL_REFRESH = "/api/auth/refresh/"
CONTRASENYA = "una-contrasenya-segura"
MISSATGE_CREDENCIALS = "El correu o la contrasenya no són correctes."


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def usuari(db):
    return Usuari.objects.create_user(
        email="anna@example.com",
        password=CONTRASENYA,
        name="Anna Puig",
        address="C/ Major 1, 08001 Barcelona",
        library_card_number="1234567890",
    )


def inicia_sessio(client, correu="anna@example.com", contrasenya=CONTRASENYA):
    return client.post(
        URL_LOGIN, {"correu": correu, "contrasenya": contrasenya}, format="json"
    )


def renova(client, refresh):
    return client.post(URL_REFRESH, {"refresh": str(refresh)}, format="json")


def test_login_retorna_els_tokens(client, usuari):
    resposta = inicia_sessio(client)

    assert resposta.status_code == status.HTTP_200_OK
    assert set(resposta.data) == {"access", "refresh"}
    assert AccessToken(resposta.data["access"])["user_id"] == str(usuari.pk)


def test_login_funciona_amb_un_token_invalid_a_la_capcalera(client, usuari):
    client.credentials(HTTP_AUTHORIZATION="Bearer no-es-un-token")

    resposta = inicia_sessio(client)

    assert resposta.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    ("correu", "contrasenya"),
    [
        ("anna@example.com", "contrasenya-incorrecta"),
        ("ningu@example.com", CONTRASENYA),
    ],
)
def test_credencials_incorrectes_donen_la_mateixa_resposta(
    client, usuari, correu, contrasenya
):
    resposta = inicia_sessio(client, correu, contrasenya)

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED
    assert resposta.data == {"detail": MISSATGE_CREDENCIALS}


def test_login_rebutja_un_compte_inactiu_amb_el_missatge_generic(client, usuari):
    usuari.is_active = False
    usuari.save(update_fields=["is_active"])

    resposta = inicia_sessio(client)

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED
    assert resposta.data == {"detail": MISSATGE_CREDENCIALS}


@pytest.mark.django_db
@pytest.mark.parametrize("dades", [{}, {"correu": "", "contrasenya": ""}])
def test_login_exigeix_els_dos_camps(client, dades):
    resposta = client.post(URL_LOGIN, dades, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data == {
        "correu": ["Aquest camp és obligatori."],
        "contrasenya": ["Aquest camp és obligatori."],
    }


def test_refresh_retorna_un_token_d_acces_nou(client, usuari):
    refresh = RefreshToken.for_user(usuari)

    resposta = renova(client, refresh)

    assert resposta.status_code == status.HTTP_200_OK
    assert set(resposta.data) == {"access"}
    assert AccessToken(resposta.data["access"])["user_id"] == str(usuari.pk)


def test_refresh_funciona_amb_un_token_caducat_a_la_capcalera(client, usuari):
    caducat = AccessToken.for_user(usuari)
    caducat.set_exp(lifetime=-timedelta(seconds=1))
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {caducat}")

    resposta = renova(client, RefreshToken.for_user(usuari))

    assert resposta.status_code == status.HTTP_200_OK


def test_refresh_rebutja_un_token_invalid(client, db):
    resposta = renova(client, "no-es-un-token")

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


def test_refresh_rebutja_un_token_caducat(client, usuari):
    refresh = RefreshToken.for_user(usuari)
    refresh.set_exp(lifetime=-timedelta(seconds=1))

    resposta = renova(client, refresh)

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


def test_refresh_rebutja_un_token_d_acces(client, usuari):
    resposta = renova(client, AccessToken.for_user(usuari))

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


def test_refresh_rebutja_un_compte_desactivat(client, usuari):
    refresh = RefreshToken.for_user(usuari)
    usuari.is_active = False
    usuari.save(update_fields=["is_active"])

    resposta = renova(client, refresh)

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED
    assert resposta.data["detail"].code == "no_active_account"


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("dades", "missatge"),
    [
        ({}, "Aquest camp és obligatori."),
        ({"refresh": ""}, "Aquest camp no pot estar en blanc."),
    ],
)
def test_refresh_exigeix_el_token(client, dades, missatge):
    resposta = client.post(URL_REFRESH, dades, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data == {"refresh": [missatge]}
