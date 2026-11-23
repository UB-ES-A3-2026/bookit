import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from usuaris.models import Adreca, Usuari
from usuaris.validacions import ADRECA_FORA_ZONA_SERVEI

COLLECCIO = "/api/usuaris/adreces/"


def crear_usuari(email="anna@example.com", carnet="1234567890", **camps):
    dades = {
        "email": email,
        "password": "una-contrasenya-segura",
        "name": "Anna Puig",
        "address": "C/ Major 1, 08001 Barcelona",
        "library_card_number": carnet,
    }
    dades.update(camps)
    return Usuari.objects.create_user(**dades)


def client_de(usuari):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(usuari)}")
    return client


def dades_adreca(**canvis):
    dades = {
        "municipi": "Barcelona",
        "carrer": "C/ Major 1",
        "pis": "2n A",
        "codi_postal": "08001",
    }
    dades.update(canvis)
    return dades


@pytest.mark.django_db
@pytest.mark.parametrize("metode", ["get", "post"])
def test_sense_token_colleccio_rebutja_peticio(metode):
    client = APIClient()
    resposta = getattr(client, metode)(
        COLLECCIO,
        dades_adreca(),
        format="json",
    )
    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_sense_token_detall_rebutja_peticio():
    usuari = crear_usuari()
    adreca = Adreca.objects.create(usuari=usuari, **dades_adreca())

    client = APIClient()

    assert client.get(f"{COLLECCIO}{adreca.id}/").status_code == 401
    assert client.patch(
        f"{COLLECCIO}{adreca.id}/",
        {"carrer": "C/ Nova"},
        format="json",
    ).status_code == 401
    assert client.delete(f"{COLLECCIO}{adreca.id}/").status_code == 401


@pytest.mark.django_db
def test_llista_només_retorna_adreces_propies():
    usuari = crear_usuari()
    altre = crear_usuari(
        email="pere@example.com",
        carnet="0987654321",
        name="Pere Vila",
    )
    propria = Adreca.objects.create(usuari=usuari, **dades_adreca())
    Adreca.objects.create(
        usuari=altre,
        **dades_adreca(carrer="C/ Alien 1", codi_postal="17001"),
    )

    resposta = client_de(usuari).get(COLLECCIO)

    assert resposta.status_code == status.HTTP_200_OK
    assert [adreca["id"] for adreca in resposta.data] == [propria.id]


@pytest.mark.django_db
def test_crear_adreca_ignora_usuari_i_l_assigna_al_token():
    usuari = crear_usuari()
    altre = crear_usuari(
        email="pere@example.com",
        carnet="0987654321",
        name="Pere Vila",
    )

    resposta = client_de(usuari).post(
        COLLECCIO,
        dades_adreca() | {"usuari": altre.id},
        format="json",
    )

    assert resposta.status_code == status.HTTP_201_CREATED
    adreca = Adreca.objects.get(pk=resposta.data["id"])
    assert adreca.usuari == usuari


@pytest.mark.django_db
def test_crear_adreca_fora_zona_retorna_error_exacte():
    usuari = crear_usuari()

    resposta = client_de(usuari).post(
        COLLECCIO,
        dades_adreca(codi_postal="28001"),
        format="json",
    )

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data["codi_postal"] == [ADRECA_FORA_ZONA_SERVEI]


@pytest.mark.django_db
def test_editar_adreca_fora_zona_retorna_error_exacte():
    usuari = crear_usuari()
    adreca = Adreca.objects.create(usuari=usuari, **dades_adreca())

    resposta = client_de(usuari).patch(
        f"{COLLECCIO}{adreca.id}/",
        {"codi_postal": "28001"},
        format="json",
    )

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data["codi_postal"] == [ADRECA_FORA_ZONA_SERVEI]


@pytest.mark.django_db
def test_patch_valida_valor_final_sense_reenviar_codi_postal():
    usuari = crear_usuari()
    adreca = Adreca.objects.create(usuari=usuari, **dades_adreca())

    resposta = client_de(usuari).patch(
        f"{COLLECCIO}{adreca.id}/",
        {"carrer": "C/ Nova"},
        format="json",
    )

    assert resposta.status_code == status.HTTP_200_OK
    adreca.refresh_from_db()
    assert adreca.carrer == "C/ Nova"


@pytest.mark.django_db
def test_editar_i_suprimir_adreca_propia():
    usuari = crear_usuari()
    adreca = Adreca.objects.create(usuari=usuari, **dades_adreca())
    client = client_de(usuari)

    resposta_edicio = client.patch(
        f"{COLLECCIO}{adreca.id}/",
        {"pis": "3r B"},
        format="json",
    )
    assert resposta_edicio.status_code == status.HTTP_200_OK

    resposta_esborra = client.delete(f"{COLLECCIO}{adreca.id}/")
    assert resposta_esborra.status_code == status.HTTP_204_NO_CONTENT
    assert not Adreca.objects.filter(pk=adreca.id).exists()


@pytest.mark.django_db
def test_no_pot_editar_ni_suprimir_adreca_aliena():
    usuari = crear_usuari()
    altre = crear_usuari(
        email="pere@example.com",
        carnet="0987654321",
        name="Pere Vila",
    )
    aliena = Adreca.objects.create(usuari=altre, **dades_adreca())

    client = client_de(usuari)

    assert client.patch(
        f"{COLLECCIO}{aliena.id}/",
        {"carrer": "C/ Inaccessible"},
        format="json",
    ).status_code == status.HTTP_404_NOT_FOUND
    assert client.delete(
        f"{COLLECCIO}{aliena.id}/"
    ).status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_predeterminada_no_es_pot_enviar():
    usuari = crear_usuari()
    adreca = Adreca.objects.create(usuari=usuari, **dades_adreca())

    resposta = client_de(usuari).patch(
        f"{COLLECCIO}{adreca.id}/",
        {"predeterminada": True},
        format="json",
    )

    assert resposta.status_code == status.HTTP_200_OK
    adreca.refresh_from_db()
    assert adreca.predeterminada is False
