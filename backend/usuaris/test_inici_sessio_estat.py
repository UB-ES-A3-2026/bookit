"""Tests de l'inici de sessió segons l'estat del compte (US2-T3)."""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from usuaris.models import PerfilRepartidor, Usuari

URL_LOGIN = "/api/auth/login/"
CONTRASENYA = "una-contrasenya-segura"
MISSATGE_CREDENCIALS = "El correu o la contrasenya no són correctes."

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


def crea_usuari(email, role=Usuari.Role.USUARI, is_active=True, num_carnet="1234567890"):
    return Usuari.objects.create_user(
        email=email,
        password=CONTRASENYA,
        name="Anna",
        address="C/ Major 1, 08001 Barcelona",
        library_card_number=num_carnet,
        role=role,
        is_active=is_active,
    )


def crea_repartidor(estat):
    usuari = crea_usuari(
        "repartidor@example.com",
        role=Usuari.Role.REPARTIDOR,
        num_carnet="repartidor-12345678Z",
    )
    PerfilRepartidor.objects.create(
        usuari=usuari,
        cognoms="Puig Soler",
        dni="12345678Z",
        telefon="612345678",
        vehicle=PerfilRepartidor.Vehicle.MOTO,
        matricula="1234BCD",
        num_seguretat_social="281234567890",
        estat=estat,
    )
    return usuari


def crea_biblioteca(is_active):
    return crea_usuari(
        "biblioteca@example.com",
        role=Usuari.Role.BIBLIOTECA,
        is_active=is_active,
        num_carnet="biblioteca-1",
    )


def inicia_sessio(client, correu, contrasenya=CONTRASENYA):
    return client.post(
        URL_LOGIN, {"correu": correu, "contrasenya": contrasenya}, format="json"
    )


def test_repartidor_validat_rep_els_tokens(client):
    crea_repartidor(PerfilRepartidor.Estat.VALIDAT)

    resposta = inicia_sessio(client, "repartidor@example.com")

    assert resposta.status_code == status.HTTP_200_OK
    assert set(resposta.data) == {"access", "refresh"}


@pytest.mark.parametrize(
    ("estat", "missatge"),
    [
        (PerfilRepartidor.Estat.PENDENT, "Pendent de validació"),
        (PerfilRepartidor.Estat.REBUTJAT, "Validació incompleta"),
    ],
)
def test_repartidor_no_validat_no_rep_els_tokens(client, estat, missatge):
    crea_repartidor(estat)

    resposta = inicia_sessio(client, "repartidor@example.com")

    assert resposta.status_code == status.HTTP_403_FORBIDDEN
    assert resposta.data == {"detail": missatge}


def test_biblioteca_verificada_rep_els_tokens(client):
    crea_biblioteca(is_active=True)

    resposta = inicia_sessio(client, "biblioteca@example.com")

    assert resposta.status_code == status.HTTP_200_OK
    assert set(resposta.data) == {"access", "refresh"}


def test_biblioteca_sense_verificar_no_rep_els_tokens(client):
    crea_biblioteca(is_active=False)

    resposta = inicia_sessio(client, "biblioteca@example.com")

    assert resposta.status_code == status.HTTP_403_FORBIDDEN
    assert resposta.data == {"detail": "Verifica el teu correu"}


def test_biblioteca_sense_verificar_amb_el_correu_en_majuscules(client):
    crea_biblioteca(is_active=False)

    resposta = inicia_sessio(client, "Biblioteca@Example.com")

    assert resposta.status_code == status.HTTP_403_FORBIDDEN
    assert resposta.data == {"detail": "Verifica el teu correu"}


@pytest.mark.parametrize(
    "crea_compte",
    [
        lambda: crea_repartidor(PerfilRepartidor.Estat.PENDENT),
        lambda: crea_repartidor(PerfilRepartidor.Estat.REBUTJAT),
        lambda: crea_biblioteca(is_active=False),
    ],
    ids=["repartidor-pendent", "repartidor-rebutjat", "biblioteca-sense-verificar"],
)
def test_contrasenya_incorrecta_no_revela_l_estat_del_compte(client, crea_compte):
    usuari = crea_compte()

    resposta = inicia_sessio(client, usuari.email, "contrasenya-incorrecta")

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED
    assert resposta.data == {"detail": MISSATGE_CREDENCIALS}


def test_compte_inactiu_que_no_es_de_biblioteca_rep_el_missatge_generic(client):
    crea_usuari("anna@example.com", is_active=False)

    resposta = inicia_sessio(client, "anna@example.com")

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED
    assert resposta.data == {"detail": MISSATGE_CREDENCIALS}


def test_repartidor_inactiu_rep_el_missatge_generic(client):
    usuari = crea_repartidor(PerfilRepartidor.Estat.VALIDAT)
    usuari.is_active = False
    usuari.save(update_fields=["is_active"])

    resposta = inicia_sessio(client, "repartidor@example.com")

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED
    assert resposta.data == {"detail": MISSATGE_CREDENCIALS}
