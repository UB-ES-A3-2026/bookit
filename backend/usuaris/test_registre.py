"""Tests de l'endpoint de registre POST /api/auth/register/ (US1-T4)."""

import pytest

from usuaris.models import Usuari

URL = "/api/auth/register/"


def dades_valides(**canvis):
    """Cos de petició vàlid segons el contracte, amb els canvis indicats."""
    dades = {
        "nom": "Anna Puig",
        "correu": "anna@example.com",
        "adreca": "C/ Major 1, 08001 Barcelona",
        "num_carnet": "1234567890",
        "contrasenya": "una-Contrasenya-segura-9",
    }
    dades.update(canvis)
    return dades


@pytest.mark.django_db
def test_registre_correcte_retorna_201_amb_les_dades_de_l_usuari(client):
    resposta = client.post(URL, dades_valides(), content_type="application/json")

    assert resposta.status_code == 201
    cos = resposta.json()
    assert cos == {
        "id": cos["id"],
        "nom": "Anna Puig",
        "correu": "anna@example.com",
        "adreca": "C/ Major 1, 08001 Barcelona",
        "num_carnet": "1234567890",
        "rol": "usuari",
    }


@pytest.mark.django_db
def test_registre_correcte_crea_l_usuari_amb_la_contrasenya_xifrada(client):
    client.post(URL, dades_valides(), content_type="application/json")

    usuari = Usuari.objects.get(email="anna@example.com")
    assert usuari.role == Usuari.Role.USUARI
    assert usuari.password != "una-Contrasenya-segura-9"
    assert usuari.check_password("una-Contrasenya-segura-9")


@pytest.mark.django_db
def test_la_resposta_no_inclou_la_contrasenya(client):
    resposta = client.post(URL, dades_valides(), content_type="application/json")

    assert "contrasenya" not in resposta.json()
    assert "password" not in resposta.json()


@pytest.mark.django_db
def test_correu_ja_registrat_retorna_400(client):
    client.post(URL, dades_valides(), content_type="application/json")

    resposta = client.post(
        URL, dades_valides(num_carnet="0000000001"), content_type="application/json"
    )

    assert resposta.status_code == 400
    assert resposta.json() == {
        "correu": ["Aquest correu electrònic ja està registrat"]
    }
    assert Usuari.objects.count() == 1


@pytest.mark.django_db
def test_correu_ja_registrat_amb_majuscules_retorna_400(client):
    client.post(URL, dades_valides(), content_type="application/json")

    resposta = client.post(
        URL,
        dades_valides(correu="ANNA@Example.com", num_carnet="0000000001"),
        content_type="application/json",
    )

    assert resposta.status_code == 400
    assert resposta.json() == {
        "correu": ["Aquest correu electrònic ja està registrat"]
    }


@pytest.mark.django_db
def test_el_correu_es_desa_en_minuscules(client):
    client.post(
        URL, dades_valides(correu="Anna@Example.com"), content_type="application/json"
    )

    assert Usuari.objects.filter(email="anna@example.com").exists()


@pytest.mark.django_db
def test_carnet_ja_registrat_retorna_400(client):
    client.post(URL, dades_valides(), content_type="application/json")

    resposta = client.post(
        URL, dades_valides(correu="pere@example.com"), content_type="application/json"
    )

    assert resposta.status_code == 400
    assert resposta.json() == {"num_carnet": ["Aquest usuari ja està registrat"]}
    assert Usuari.objects.count() == 1


@pytest.mark.django_db
def test_no_cal_autenticacio(client):
    # El client de proves no té cap sessió iniciada.
    resposta = client.post(URL, dades_valides(), content_type="application/json")

    assert resposta.status_code not in (401, 403)


def test_get_no_esta_permes(client):
    resposta = client.get(URL)

    assert resposta.status_code == 405
