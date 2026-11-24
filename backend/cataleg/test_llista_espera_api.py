from datetime import timedelta

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from cataleg.models import LlistaEspera, Llibre
from usuaris.models import Usuari


pytestmark = pytest.mark.django_db


def crear_usuari(email="usuari@example.com", carnet="USR-001"):
    return Usuari.objects.create_user(
        email=email,
        password="una-contrasenya-segura",
        name="Usuari de prova",
        address="C/ Major 1",
        library_card_number=carnet,
    )


def client_amb_token(usuari):
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(usuari)}"
    )
    return client


def crear_llibre():
    return Llibre.objects.create(
        titol="La plaça del Diamant",
        autor="Mercè Rodoreda",
        isbn="9788429740011",
    )


def url_llista(llibre):
    return f"/api/cataleg/llibres/{llibre.id}/llista-espera/"


@pytest.mark.parametrize("metode", ["post", "delete"])
def test_sense_autenticacio_retorna_401(metode, db):
    llibre = crear_llibre()

    resposta = getattr(APIClient(), metode)(url_llista(llibre))

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("autoritzacio", [
    "Bearer token-invalid",
])
@pytest.mark.parametrize("metode", ["post", "delete"])
def test_token_invalid_retorna_401(metode, autoritzacio):
    llibre = crear_llibre()
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=autoritzacio)

    resposta = getattr(client, metode)(url_llista(llibre))

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("metode", ["post", "delete"])
def test_token_caducat_retorna_401(metode):
    llibre = crear_llibre()
    usuari = crear_usuari()
    token = AccessToken.for_user(usuari)
    token.set_exp(lifetime=timedelta(seconds=-1))

    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {token}"
    )

    resposta = getattr(client, metode)(url_llista(llibre))

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


def test_post_crea_lentrada_per_lusuari_autenticat():
    usuari = crear_usuari()
    llibre = crear_llibre()

    resposta = client_amb_token(usuari).post(url_llista(llibre))

    assert resposta.status_code == status.HTTP_201_CREATED
    assert resposta.data["llibre"] == llibre.id
    assert resposta.data["data_alta"] is not None

    entrada = LlistaEspera.objects.get()
    assert entrada.usuari == usuari
    assert entrada.llibre == llibre


def test_post_repetit_es_idempotent_i_no_duplica():
    usuari = crear_usuari()
    llibre = crear_llibre()
    client = client_amb_token(usuari)

    primera = client.post(url_llista(llibre))
    segona = client.post(url_llista(llibre))

    assert primera.status_code == status.HTTP_201_CREATED
    assert segona.status_code == status.HTTP_200_OK
    assert LlistaEspera.objects.filter(
        usuari=usuari,
        llibre=llibre,
    ).count() == 1


def test_delete_esborra_només_lentrada_de_lusuari():
    usuari = crear_usuari()
    llibre = crear_llibre()
    LlistaEspera.objects.create(usuari=usuari, llibre=llibre)

    resposta = client_amb_token(usuari).delete(url_llista(llibre))

    assert resposta.status_code == status.HTTP_204_NO_CONTENT
    assert not LlistaEspera.objects.filter(
        usuari=usuari,
        llibre=llibre,
    ).exists()


def test_delete_sense_entrada_retornat_204():
    usuari = crear_usuari()
    llibre = crear_llibre()

    resposta = client_amb_token(usuari).delete(url_llista(llibre))

    assert resposta.status_code == status.HTTP_204_NO_CONTENT


def test_usuari_no_afecta_lentrada_dun_altre_usuari():
    usuari = crear_usuari()
    altre = crear_usuari(
        email="altre@example.com",
        carnet="USR-002",
    )
    llibre = crear_llibre()
    entrada_altra = LlistaEspera.objects.create(
        usuari=altre,
        llibre=llibre,
    )

    resposta = client_amb_token(usuari).post(url_llista(llibre))

    assert resposta.status_code == status.HTTP_201_CREATED
    assert LlistaEspera.objects.filter(
        usuari=altre,
        llibre=llibre,
    ).get() == entrada_altra
    assert LlistaEspera.objects.filter(llibre=llibre).count() == 2

    resposta = client_amb_token(usuari).delete(url_llista(llibre))

    assert resposta.status_code == status.HTTP_204_NO_CONTENT
    assert LlistaEspera.objects.filter(
        usuari=altre,
        llibre=llibre,
    ).exists()


@pytest.mark.parametrize("metode", ["post", "delete"])
def test_llibre_inexistent_retorna_404(metode):
    usuari = crear_usuari()
    client = client_amb_token(usuari)

    resposta = getattr(client, metode)(
        "/api/cataleg/llibres/999999/llista-espera/"
    )

    assert resposta.status_code == status.HTTP_404_NOT_FOUND


def test_camp_usuari_del_cos_no_substitueix_lusuari_autenticat():
    usuari = crear_usuari()
    altre = crear_usuari(
        email="altre@example.com",
        carnet="USR-002",
    )
    llibre = crear_llibre()

    resposta = client_amb_token(usuari).post(
        url_llista(llibre),
        {"usuari": altre.id},
        format="json",
    )

    assert resposta.status_code == status.HTTP_201_CREATED
    entrada = LlistaEspera.objects.get()
    assert entrada.usuari == usuari
    assert entrada.llibre == llibre
