from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.test import override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from usuaris.models import Biblioteca, Usuari


URL = "/api/auth/verify/biblioteca/{uid}/{token}/"
CONTRASENYA = "Llibres-de-tardor-24"
ENLLAC_INVALID = {"detail": "L'enllaç de verificació no és vàlid o ha caducat."}


@pytest.fixture
def usuari_biblioteca():
    """Biblioteca acabada de registrar: compte inactiu i sense contrasenya."""
    usuari = Usuari.objects.create_user(
        "biblioteca@example.com",
        None,
        {
            "name": "Biblioteca Central",
            "address": "",
            "library_card_number": "biblioteca-test",
            "role": Usuari.Role.BIBLIOTECA,
            "is_active": False,
        },
    )
    Biblioteca.objects.create(usuari=usuari, nom="Biblioteca Central")
    return usuari


def url_verificacio(usuari):
    uid = urlsafe_base64_encode(force_bytes(usuari.pk))
    token = default_token_generator.make_token(usuari)
    return URL.format(uid=uid, token=token)


def verifica(client, url, contrasenya=CONTRASENYA):
    return client.post(url, {"contrasenya": contrasenya}, content_type="application/json")


@pytest.mark.django_db
def test_el_get_comprova_l_enllac_sense_activar_el_compte(client, usuari_biblioteca):
    resposta = client.get(url_verificacio(usuari_biblioteca))

    assert resposta.status_code == 200
    assert resposta.json() == {"correu": "biblioteca@example.com"}
    usuari_biblioteca.refresh_from_db()
    assert not usuari_biblioteca.is_active


@pytest.mark.django_db
def test_triar_la_contrasenya_activa_el_compte(client, usuari_biblioteca):
    resposta = verifica(client, url_verificacio(usuari_biblioteca))

    assert resposta.status_code == 200
    assert resposta.json() == {
        "detail": "El compte de biblioteca s'ha verificat correctament."
    }
    usuari_biblioteca.refresh_from_db()
    assert usuari_biblioteca.is_active
    assert usuari_biblioteca.check_password(CONTRASENYA)


@pytest.mark.django_db
def test_despres_de_verificar_la_biblioteca_pot_iniciar_sessio(client, usuari_biblioteca):
    verifica(client, url_verificacio(usuari_biblioteca))

    resposta = client.post(
        "/api/auth/login/",
        {"correu": "biblioteca@example.com", "contrasenya": CONTRASENYA},
        content_type="application/json",
    )

    assert resposta.status_code == 200
    assert "access" in resposta.json()


@pytest.mark.django_db
def test_l_enllac_nomes_es_pot_fer_servir_una_vegada(client, usuari_biblioteca):
    url = url_verificacio(usuari_biblioteca)
    verifica(client, url)

    resposta = verifica(client, url, "Una-altra-contrasenya-99")

    assert resposta.status_code == 400
    assert resposta.json() == ENLLAC_INVALID
    usuari_biblioteca.refresh_from_db()
    assert usuari_biblioteca.check_password(CONTRASENYA)


@pytest.mark.django_db
@pytest.mark.parametrize("cos", [{}, {"contrasenya": ""}, {"contrasenya": None}])
def test_sense_contrasenya_no_s_activa_el_compte(client, usuari_biblioteca, cos):
    resposta = client.post(
        url_verificacio(usuari_biblioteca), cos, content_type="application/json"
    )

    assert resposta.status_code == 400
    assert resposta.json() == {"contrasenya": ["Aquest camp és obligatori."]}
    usuari_biblioteca.refresh_from_db()
    assert not usuari_biblioteca.is_active


@pytest.mark.django_db
def test_una_contrasenya_massa_curta_no_s_accepta(client, usuari_biblioteca):
    resposta = verifica(client, url_verificacio(usuari_biblioteca), "curta1")

    assert resposta.status_code == 400
    assert "contrasenya" in resposta.json()
    assert any("massa curta" in missatge for missatge in resposta.json()["contrasenya"])
    usuari_biblioteca.refresh_from_db()
    assert not usuari_biblioteca.is_active


@pytest.mark.django_db
def test_una_contrasenya_massa_comuna_no_s_accepta(client, usuari_biblioteca):
    resposta = verifica(client, url_verificacio(usuari_biblioteca), "password123")

    assert resposta.status_code == 400
    assert "contrasenya" in resposta.json()
    usuari_biblioteca.refresh_from_db()
    assert not usuari_biblioteca.is_active


@pytest.mark.django_db
@pytest.mark.parametrize("metode", ["get", "post"])
def test_rebutja_un_token_invalid(client, usuari_biblioteca, metode):
    uid = urlsafe_base64_encode(force_bytes(usuari_biblioteca.pk))
    url = URL.format(uid=uid, token="token-invalid")

    resposta = client.get(url) if metode == "get" else verifica(client, url)

    assert resposta.status_code == 400
    assert resposta.json() == ENLLAC_INVALID
    usuari_biblioteca.refresh_from_db()
    assert not usuari_biblioteca.is_active


@pytest.mark.django_db
@override_settings(PASSWORD_RESET_TIMEOUT=0)
def test_rebutja_un_token_caducat(client, usuari_biblioteca):
    url = url_verificacio(usuari_biblioteca)

    with patch.object(
        default_token_generator,
        "_now",
        return_value=default_token_generator._now() + timedelta(seconds=1),
    ):
        resposta = verifica(client, url)

    assert resposta.status_code == 400
    assert resposta.json() == ENLLAC_INVALID
    usuari_biblioteca.refresh_from_db()
    assert not usuari_biblioteca.is_active


@pytest.mark.django_db
@pytest.mark.parametrize("metode", ["get", "post"])
def test_rebutja_un_uid_invalid(client, metode):
    url = URL.format(uid="invalid", token="token-invalid")

    resposta = client.get(url) if metode == "get" else verifica(client, url)

    assert resposta.status_code == 400
    assert resposta.json() == ENLLAC_INVALID


@pytest.mark.django_db
def test_no_verifica_comptes_que_no_son_de_biblioteca(client):
    lector = Usuari.objects.create_user(
        "lector@example.com",
        CONTRASENYA,
        {
            "name": "Anna Puig",
            "address": "C/ Major 1",
            "library_card_number": "1234567890",
            "is_active": False,
        },
    )

    resposta = verifica(client, url_verificacio(lector), "Una-altra-contrasenya-99")

    assert resposta.status_code == 400
    assert resposta.json() == ENLLAC_INVALID
    lector.refresh_from_db()
    assert not lector.is_active


@pytest.mark.django_db
def test_compte_biblioteca_sense_verificar_no_pot_autenticar(usuari_biblioteca):
    assert authenticate(email=usuari_biblioteca.email, password=CONTRASENYA) is None
