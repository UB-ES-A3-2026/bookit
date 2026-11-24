from datetime import timedelta

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from cataleg.models import ExemplarBiblioteca, Llibre
from cataleg.views import (
    MISSATGE_ANONIM,
    MISSATGE_SENSE_ADRECA,
    MISSATGE_SENSE_ESTOC,
)
from usuaris.models import Adreca, Biblioteca, Usuari


pytestmark = pytest.mark.django_db


def crear_usuari(email="usuari@example.com", **camps):
    return Usuari.objects.create_user(
        email=email,
        password="una-contrasenya-segura",
        name=camps.pop("name", "Usuari de prova"),
        address="C/ Major 1",
        library_card_number=camps.pop(
            "library_card_number",
            f"carnet-{email}",
        ),
        **camps,
    )


def crear_biblioteca(
    email,
    nom,
    latitud=None,
    longitud=None,
    activa=True,
):
    usuari = crear_usuari(
        email=email,
        role=Usuari.Role.BIBLIOTECA,
        is_active=activa,
    )
    perfil = Biblioteca.objects.create(
        usuari=usuari,
        nom=nom,
        carrer="C/ de la Biblioteca",
        numero_porta="1",
        latitud=latitud,
        longitud=longitud,
    )

    if activa:
        usuari.is_active = True
        usuari.save(update_fields=["is_active"])

    return usuari, perfil


def crear_llibre():
    return Llibre.objects.create(
        titol="La plaça del Diamant",
        autor="Mercè Rodoreda",
        isbn="9788429740011",
    )


def url_llibre(llibre):
    return f"/api/cataleg/llibres/{llibre.id}/biblioteques/"


def client_amb_token(usuari):
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(usuari)}"
    )
    return client


def test_anonym_obte_la_llista_sense_distancies_i_amb_missatge():
    llibre = crear_llibre()
    crear_biblioteca(
        "biblioteca@example.com",
        "Biblioteca Central",
        latitud="41.385064",
        longitud="2.173403",
    )
    biblioteca, _ = crear_biblioteca(
        "biblio2@example.com",
        "Biblioteca Nord",
        latitud="41.400000",
        longitud="2.180000",
    )
    ExemplarBiblioteca.objects.create(
        llibre=llibre,
        biblioteca=biblioteca,
        quantitat=3,
    )

    resposta = APIClient().get(url_llibre(llibre))

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["ordenada_per_distancia"] is False
    assert resposta.data["missatge"] == MISSATGE_ANONIM
    assert "distancia_km" not in resposta.data["biblioteques"][0]
    assert "address" not in resposta.data
    assert "latitud" not in resposta.data
    assert "longitud" not in resposta.data


def test_usuari_amb_adreca_obte_ordenacio_per_distancia():
    llibre = crear_llibre()
    usuari = crear_usuari()
    Adreca.objects.create(
        usuari=usuari,
        municipi="Barcelona",
        carrer="C/ Major",
        pis="1",
        codi_postal="08001",
        latitud="41.385064",
        longitud="2.173403",
        predeterminada=True,
    )

    _, llunyana = crear_biblioteca(
        "llunyana@example.com",
        "Biblioteca Llunyana",
        latitud="41.500000",
        longitud="2.200000",
    )
    _, propera = crear_biblioteca(
        "propera@example.com",
        "Biblioteca Propera",
        latitud="41.390000",
        longitud="2.175000",
    )
    ExemplarBiblioteca.objects.create(
        llibre=llibre,
        biblioteca=llunyana.usuari,
        quantitat=1,
    )
    ExemplarBiblioteca.objects.create(
        llibre=llibre,
        biblioteca=propera.usuari,
        quantitat=2,
    )

    resposta = client_amb_token(usuari).get(url_llibre(llibre))

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["ordenada_per_distancia"] is True
    assert resposta.data["missatge"] is None
    assert [
        biblioteca["nom"]
        for biblioteca in resposta.data["biblioteques"]
    ] == [
        "Biblioteca Propera",
        "Biblioteca Llunyana",
    ]
    assert resposta.data["biblioteques"][0]["distancia_km"] < (
        resposta.data["biblioteques"][1]["distancia_km"]
    )


def test_usuari_sense_adreca_obte_missatge():
    llibre = crear_llibre()
    usuari = crear_usuari()
    biblioteca, _ = crear_biblioteca(
        "biblioteca@example.com",
        "Biblioteca Central",
        latitud="41.385064",
        longitud="2.173403",
    )
    ExemplarBiblioteca.objects.create(
        llibre=llibre,
        biblioteca=biblioteca,
        quantitat=2,
    )

    resposta = client_amb_token(usuari).get(url_llibre(llibre))

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["ordenada_per_distancia"] is False
    assert resposta.data["missatge"] == MISSATGE_SENSE_ADRECA


def test_llibre_sense_estoc_retorna_llista_buida_i_missatge():
    llibre = crear_llibre()
    biblioteca, _ = crear_biblioteca(
        "biblioteca@example.com",
        "Biblioteca Central",
        latitud="41.385064",
        longitud="2.173403",
    )
    ExemplarBiblioteca.objects.create(
        llibre=llibre,
        biblioteca=biblioteca,
        quantitat=0,
    )

    resposta = APIClient().get(url_llibre(llibre))

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["biblioteques"] == []
    assert resposta.data["missatge"] == MISSATGE_SENSE_ESTOC


def test_biblioteca_inactiva_no_apareix():
    llibre = crear_llibre()
    biblioteca, _ = crear_biblioteca(
        "inactiva@example.com",
        "Biblioteca Inactiva",
        latitud="41.385064",
        longitud="2.173403",
        activa=False,
    )
    ExemplarBiblioteca.objects.create(
        llibre=llibre,
        biblioteca=biblioteca,
        quantitat=3,
    )

    resposta = APIClient().get(url_llibre(llibre))

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["biblioteques"] == []


def test_biblioteca_sense_coordenades_no_trenca_la_resposta():
    llibre = crear_llibre()
    usuari = crear_usuari()
    Adreca.objects.create(
        usuari=usuari,
        municipi="Barcelona",
        carrer="C/ Major",
        pis="1",
        codi_postal="08001",
        latitud="41.385064",
        longitud="2.173403",
        predeterminada=True,
    )
    biblioteca, _ = crear_biblioteca(
        "sense-coordenades@example.com",
        "Biblioteca Sense Coordenades",
    )
    ExemplarBiblioteca.objects.create(
        llibre=llibre,
        biblioteca=biblioteca,
        quantitat=2,
    )

    resposta = client_amb_token(usuari).get(url_llibre(llibre))

    assert resposta.status_code == status.HTTP_200_OK
    assert len(resposta.data["biblioteques"]) == 1
    assert "distancia_km" not in resposta.data["biblioteques"][0]


@pytest.mark.parametrize(
    "autoritzacio",
    [
        "Bearer token-invalid",
    ],
)
def test_token_invalid_es_comporta_com_a_anonym(autoritzacio):
    llibre = crear_llibre()
    biblioteca, _ = crear_biblioteca(
        "biblioteca@example.com",
        "Biblioteca Central",
    )
    ExemplarBiblioteca.objects.create(
        llibre=llibre,
        biblioteca=biblioteca,
        quantitat=2,
    )

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=autoritzacio)

    resposta = client.get(url_llibre(llibre))

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["missatge"] == MISSATGE_ANONIM


def test_llibre_inexistent_retorna_404():
    resposta = APIClient().get(
        "/api/cataleg/llibres/999999/biblioteques/"
    )

    assert resposta.status_code == status.HTTP_404_NOT_FOUND
