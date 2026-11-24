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


def test_ordenacio_amb_quatre_distancies_conegudes():
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

    ubicacions = [
        ("Biblioteca Barcelona", "41.385064", "2.173403"),
        ("Biblioteca Propera", "41.390000", "2.175000"),
        ("Biblioteca Girona", "41.979400", "2.821400"),
        ("Biblioteca Lleida", "41.617600", "0.620000"),
    ]

    for index, (nom, latitud, longitud) in enumerate(ubicacions):
        biblioteca, _ = crear_biblioteca(
            f"biblioteca-{index}@example.com",
            nom,
            latitud=latitud,
            longitud=longitud,
        )
        ExemplarBiblioteca.objects.create(
            llibre=llibre,
            biblioteca=biblioteca,
            quantitat=index + 1,
        )

    resposta = client_amb_token(usuari).get(url_llibre(llibre))

    assert resposta.status_code == status.HTTP_200_OK
    assert [
        biblioteca["nom"]
        for biblioteca in resposta.data["biblioteques"]
    ] == [
        "Biblioteca Barcelona",
        "Biblioteca Propera",
        "Biblioteca Girona",
        "Biblioteca Lleida",
    ]

    distancies = {
        biblioteca["nom"]: biblioteca["distancia_km"]
        for biblioteca in resposta.data["biblioteques"]
    }
    assert distancies["Biblioteca Barcelona"] == 0.0
    assert 0.5 <= distancies["Biblioteca Propera"] <= 0.7
    assert 84.0 <= distancies["Biblioteca Girona"] <= 86.0
    assert 130.0 <= distancies["Biblioteca Lleida"] <= 134.0

    # Distàncies aproximades des de 41.385064, 2.173403:
    # Barcelona: 0,0 km
    # Propera: 0,6 km
    # Girona: 85,1 km
    # Lleida: 132,1 km
    # Fórmula Haversine, radi de la Terra 6371 km.
    assert [
        distancies["Biblioteca Barcelona"],
        distancies["Biblioteca Propera"],
        distancies["Biblioteca Girona"],
        distancies["Biblioteca Lleida"],
    ] == sorted(distancies.values())


def test_dos_usuaris_veuen_ordres_de_distancia_diferents():
    llibre = crear_llibre()

    usuari_barcelona = crear_usuari(
        "barcelona@example.com",
        library_card_number="USR-BAR",
    )
    usuari_girona = crear_usuari(
        "girona@example.com",
        library_card_number="USR-GIR",
    )

    Adreca.objects.create(
        usuari=usuari_barcelona,
        municipi="Barcelona",
        carrer="C/ Barcelona",
        pis="1",
        codi_postal="08001",
        latitud="41.385064",
        longitud="2.173403",
        predeterminada=True,
    )
    Adreca.objects.create(
        usuari=usuari_girona,
        municipi="Girona",
        carrer="C/ Girona",
        pis="1",
        codi_postal="17001",
        latitud="41.979400",
        longitud="2.821400",
        predeterminada=True,
    )

    biblioteca_barcelona, _ = crear_biblioteca(
        "lloc-barcelona@example.com",
        "Biblioteca Barcelona",
        latitud="41.385064",
        longitud="2.173403",
    )
    biblioteca_girona, _ = crear_biblioteca(
        "lloc-girona@example.com",
        "Biblioteca Girona",
        latitud="41.979400",
        longitud="2.821400",
    )

    ExemplarBiblioteca.objects.create(
        llibre=llibre,
        biblioteca=biblioteca_barcelona,
        quantitat=2,
    )
    ExemplarBiblioteca.objects.create(
        llibre=llibre,
        biblioteca=biblioteca_girona,
        quantitat=2,
    )

    resposta_barcelona = client_amb_token(
        usuari_barcelona
    ).get(url_llibre(llibre))
    resposta_girona = client_amb_token(
        usuari_girona
    ).get(url_llibre(llibre))

    assert [
        item["nom"] for item in resposta_barcelona.data["biblioteques"]
    ] == [
        "Biblioteca Barcelona",
        "Biblioteca Girona",
    ]
    assert [
        item["nom"] for item in resposta_girona.data["biblioteques"]
    ] == [
        "Biblioteca Girona",
        "Biblioteca Barcelona",
    ]


def test_canviar_adreca_predeterminada_canvia_l_ordre():
    llibre = crear_llibre()
    usuari = crear_usuari()

    adreca_barcelona = Adreca.objects.create(
        usuari=usuari,
        municipi="Barcelona",
        carrer="C/ Barcelona",
        pis="1",
        codi_postal="08001",
        latitud="41.385064",
        longitud="2.173403",
        predeterminada=True,
    )
    adreca_girona = Adreca.objects.create(
        usuari=usuari,
        municipi="Girona",
        carrer="C/ Girona",
        pis="1",
        codi_postal="17001",
        latitud="41.979400",
        longitud="2.821400",
        predeterminada=False,
    )

    biblioteca_barcelona, _ = crear_biblioteca(
        "lloc-barcelona@example.com",
        "Biblioteca Barcelona",
        latitud="41.385064",
        longitud="2.173403",
    )
    biblioteca_girona, _ = crear_biblioteca(
        "lloc-girona@example.com",
        "Biblioteca Girona",
        latitud="41.979400",
        longitud="2.821400",
    )

    ExemplarBiblioteca.objects.create(
        llibre=llibre,
        biblioteca=biblioteca_barcelona,
        quantitat=2,
    )
    ExemplarBiblioteca.objects.create(
        llibre=llibre,
        biblioteca=biblioteca_girona,
        quantitat=2,
    )

    client = client_amb_token(usuari)
    abans = client.get(url_llibre(llibre))

    resposta_canvi = client.post(
        f"/api/usuaris/adreces/{adreca_girona.id}/predeterminada/",
        format="json",
    )

    despres = client.get(url_llibre(llibre))

    assert resposta_canvi.status_code == status.HTTP_200_OK
    assert adreca_girona.predeterminada is False or (
        Adreca.objects.get(pk=adreca_girona.pk).predeterminada
    )
    assert [
        item["nom"] for item in abans.data["biblioteques"]
    ] == [
        "Biblioteca Barcelona",
        "Biblioteca Girona",
    ]
    assert [
        item["nom"] for item in despres.data["biblioteques"]
    ] == [
        "Biblioteca Girona",
        "Biblioteca Barcelona",
    ]
    adreca_barcelona.refresh_from_db()
    adreca_girona.refresh_from_db()
    assert adreca_barcelona.predeterminada is False
    assert adreca_girona.predeterminada is True


def test_empata_per_distancia_usa_nom_i_id():
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

    for nom in ["Biblioteca Zeta", "Biblioteca Alpha"]:
        biblioteca, _ = crear_biblioteca(
            f"{nom.casefold().replace(' ', '-')}@example.com",
            nom,
            latitud="41.385064",
            longitud="2.173403",
        )
        ExemplarBiblioteca.objects.create(
            llibre=llibre,
            biblioteca=biblioteca,
            quantitat=2,
        )

    resposta = client_amb_token(usuari).get(url_llibre(llibre))

    assert [
        item["nom"] for item in resposta.data["biblioteques"]
    ] == [
        "Biblioteca Alpha",
        "Biblioteca Zeta",
    ]
    assert [
        item["distancia_km"]
        for item in resposta.data["biblioteques"]
    ] == [0.0, 0.0]


@pytest.mark.parametrize("mode", ["anonim", "sense_adreca", "amb_adreca"])
def test_privadesa_no_exposa_adreca_o_coordenades_dusuari(mode):
    llibre = crear_llibre()

    biblioteca, _ = crear_biblioteca(
        "biblioteca-publica@example.com",
        "Biblioteca Pública",
        latitud="41.385064",
        longitud="2.173403",
    )
    ExemplarBiblioteca.objects.create(
        llibre=llibre,
        biblioteca=biblioteca,
        quantitat=2,
    )

    if mode == "anonim":
        client = APIClient()
    else:
        usuari = crear_usuari()
        if mode == "amb_adreca":
            Adreca.objects.create(
                usuari=usuari,
                municipi="Municipi Privat",
                carrer="Carrer Privat",
                pis="Pis Privat",
                codi_postal="99999",
                latitud="10.123456",
                longitud="-20.123456",
                predeterminada=True,
            )
        client = client_amb_token(usuari)

    resposta = client.get(url_llibre(llibre))

    assert resposta.status_code == status.HTTP_200_OK
    resposta_text = str(resposta.data)

    assert "Municipi Privat" not in resposta_text
    assert "Carrer Privat" not in resposta_text
    assert "Pis Privat" not in resposta_text
    assert "99999" not in resposta_text
    assert "10.123456" not in resposta_text
    assert "-20.123456" not in resposta_text

    assert "address" not in resposta.data
    assert "municipi" not in resposta.data
    assert "pis" not in resposta.data
    assert "codi_postal" not in resposta.data
    for item in resposta.data["biblioteques"]:
        assert "municipi" not in item
        assert "address" not in item
        assert "pis" not in item
        assert "codi_postal" not in item


def test_token_caducat_es_comporta_com_anonym():
    llibre = crear_llibre()
    usuari = crear_usuari()
    token = AccessToken.for_user(usuari)
    token.set_exp(lifetime=timedelta(seconds=-1))

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

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    resposta = client.get(url_llibre(llibre))

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["ordenada_per_distancia"] is False
    assert resposta.data["missatge"] == MISSATGE_ANONIM

def test_adreca_predeterminada_sense_coordenades_sense_distancia():
    llibre = crear_llibre()
    usuari = crear_usuari()

    Adreca.objects.create(
        usuari=usuari,
        municipi="Barcelona",
        carrer="C/ Sense Coordenades",
        pis="1",
        codi_postal="08001",
        latitud=None,
        longitud=None,
        predeterminada=True,
    )

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
    assert "distancia_km" not in resposta.data["biblioteques"][0]
