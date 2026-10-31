import pytest
from django.contrib.auth.tokens import default_token_generator
from django.test import override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from usuaris.models import Biblioteca, Usuari


URL = "/api/auth/verify/biblioteca/{uid}/{token}/"


@pytest.fixture
def usuari_biblioteca():
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


@pytest.mark.django_db
def test_verificacio_biblioteca_activa_el_compte(client, usuari_biblioteca):
    resposta = client.get(url_verificacio(usuari_biblioteca))

    assert resposta.status_code == 200
    assert resposta.json() == {
        "detail": "El compte de biblioteca s'ha verificat correctament."
    }
    usuari_biblioteca.refresh_from_db()
    assert usuari_biblioteca.is_active


@pytest.mark.django_db
def test_verificacio_biblioteca_rebutja_token_invalid(client, usuari_biblioteca):
    uid = urlsafe_base64_encode(force_bytes(usuari_biblioteca.pk))

    resposta = client.get(URL.format(uid=uid, token="token-invalid"))

    assert resposta.status_code == 400
    assert resposta.json() == {
        "detail": "L'enllaç de verificació no és vàlid o ha caducat."
    }
    usuari_biblioteca.refresh_from_db()
    assert not usuari_biblioteca.is_active


@pytest.mark.django_db
@override_settings(PASSWORD_RESET_TIMEOUT=0)
def test_verificacio_biblioteca_rebutja_token_caducat(client, usuari_biblioteca):
    resposta = client.get(url_verificacio(usuari_biblioteca))

    assert resposta.status_code == 400
    assert resposta.json() == {
        "detail": "L'enllaç de verificació no és vàlid o ha caducat."
    }
    usuari_biblioteca.refresh_from_db()
    assert not usuari_biblioteca.is_active


@pytest.mark.django_db
def test_verificacio_biblioteca_rebutja_uid_invalid(client):
    resposta = client.get(URL.format(uid="invalid", token="token-invalid"))

    assert resposta.status_code == 400
    assert resposta.json() == {
        "detail": "L'enllaç de verificació no és vàlid o ha caducat."
    }
