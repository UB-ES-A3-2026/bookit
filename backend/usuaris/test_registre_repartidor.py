"""Tests de l'endpoint POST /api/auth/register/repartidor/ (US1.1-T4)."""

import pytest
from django.test import Client

from usuaris.models import PerfilRepartidor, Usuari

URL = "/api/auth/register/repartidor/"
OBLIGATORI = "Aquest camp és obligatori."
JA_REGISTRAT = "DNI/correu ja registrat"


def dades_valides(**canvis):
    """Cos de petició vàlid segons el contracte, amb els canvis indicats."""
    dades = {
        "nom": "Pol",
        "cognoms": "Ferrer Soler",
        "correu": "repartidor@example.com",
        "dni": "12345678Z",
        "telefon": "+34 612 345 678",
        "vehicle": "moto",
        "matricula": "1234 BCD",
        "num_seguretat_social": "28/12345678/90",
        "contrasenya": "Llibres-de-tardor-24",
    }
    dades.update(canvis)
    return dades


@pytest.mark.django_db
def test_registre_correcte_retorna_201_amb_les_dades_i_l_estat(client):
    resposta = client.post(URL, dades_valides(), content_type="application/json")

    assert resposta.status_code == 201
    cos = resposta.json()
    assert cos == {
        "id": cos["id"],
        "nom": "Pol",
        "cognoms": "Ferrer Soler",
        "correu": "repartidor@example.com",
        "dni": "12345678Z",
        "telefon": "+34612345678",
        "vehicle": "moto",
        "matricula": "1234BCD",
        "num_seguretat_social": "281234567890",
        "rol": "repartidor",
        "estat": "pendent",
    }


@pytest.mark.django_db
def test_registre_correcte_crea_l_usuari_i_el_perfil_pendent(client):
    client.post(URL, dades_valides(), content_type="application/json")

    usuari = Usuari.objects.get(email="repartidor@example.com")
    assert usuari.role == Usuari.Role.REPARTIDOR
    assert usuari.check_password("Llibres-de-tardor-24")
    assert usuari.perfil_repartidor.estat == PerfilRepartidor.Estat.PENDENT


@pytest.mark.django_db
def test_registre_amb_bici_no_necessita_matricula(client):
    dades = dades_valides(vehicle="bici")
    del dades["matricula"]

    resposta = client.post(URL, dades, content_type="application/json")

    assert resposta.status_code == 201
    assert resposta.json()["matricula"] == ""


@pytest.mark.django_db
def test_la_resposta_no_inclou_la_contrasenya(client):
    resposta = client.post(URL, dades_valides(), content_type="application/json")

    assert "contrasenya" not in resposta.json()
    assert "password" not in resposta.json()


@pytest.mark.django_db
def test_el_client_no_pot_triar_el_rol_ni_l_estat(client):
    resposta = client.post(
        URL,
        dades_valides(rol="admin", estat="aprovat"),
        content_type="application/json",
    )

    assert resposta.status_code == 201
    assert resposta.json()["rol"] == "repartidor"
    assert resposta.json()["estat"] == "pendent"


@pytest.mark.django_db
def test_camps_invalids_retornen_400_amb_els_errors_per_camp(client):
    resposta = client.post(
        URL,
        dades_valides(nom="", correu="no-es-un-correu", matricula=""),
        content_type="application/json",
    )

    assert resposta.status_code == 400
    assert resposta.json() == {
        "nom": [OBLIGATORI],
        "correu": ["Introduïu una adreça de correu electrònic vàlida."],
    }
    assert not Usuari.objects.exists()


@pytest.mark.django_db
def test_moto_sense_matricula_retorna_400(client):
    resposta = client.post(
        URL, dades_valides(matricula=""), content_type="application/json"
    )

    assert resposta.status_code == 400
    assert resposta.json() == {"matricula": [OBLIGATORI]}
    assert not Usuari.objects.exists()


@pytest.mark.django_db
def test_correu_i_dni_ja_registrats_retornen_400(client):
    client.post(URL, dades_valides(), content_type="application/json")

    resposta = client.post(URL, dades_valides(), content_type="application/json")

    assert resposta.status_code == 400
    assert resposta.json() == {"correu": [JA_REGISTRAT], "dni": [JA_REGISTRAT]}
    assert Usuari.objects.count() == 1


@pytest.mark.django_db
def test_cos_buit_retorna_400_amb_tots_els_camps_obligatoris(client):
    resposta = client.post(URL, {}, content_type="application/json")

    assert resposta.status_code == 400
    assert set(resposta.json()) == {
        "nom",
        "cognoms",
        "correu",
        "dni",
        "telefon",
        "vehicle",
        "num_seguretat_social",
        "contrasenya",
    }


@pytest.mark.django_db
def test_no_cal_autenticacio(client):
    # El client de proves no té cap sessió iniciada.
    resposta = client.post(URL, dades_valides(), content_type="application/json")

    assert resposta.status_code not in (401, 403)


@pytest.mark.django_db
def test_una_sessio_oberta_no_obliga_a_enviar_el_token_csrf():
    admin = Usuari.objects.create_superuser(
        email="admin@example.com",
        password="Llibres-de-tardor-24",
        name="Admin",
        address="C/ Major 1",
        library_card_number="0000000001",
    )
    client = Client(enforce_csrf_checks=True)
    client.force_login(admin)

    resposta = client.post(URL, dades_valides(), content_type="application/json")

    assert resposta.status_code == 201


def test_get_no_esta_permes(client):
    resposta = client.get(URL)

    assert resposta.status_code == 405
