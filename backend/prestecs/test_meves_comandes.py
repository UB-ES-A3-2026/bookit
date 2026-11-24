"""Tests de l'endpoint de les meves comandes (US8-T3)."""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from cataleg.models import Llibre
from prestecs.models import Comanda, LiniaComanda
from prestecs.serveis import canvia_estat
from usuaris.models import Biblioteca, Usuari

URL = "/api/prestecs/comandes/"
Estat = Comanda.Estat


def crea_usuari(correu, rol=Usuari.Role.USUARI):
    return Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {"name": correu.split("@")[0], "address": "C/ Major 1", "library_card_number": correu, "role": rol},
    )


def crea_biblioteca(correu, nom):
    usuari = crea_usuari(correu, Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=usuari, nom=nom)
    return usuari


@pytest.fixture
def lector():
    return crea_usuari("lector@example.com")


@pytest.fixture
def client(lector):
    client = APIClient()
    client.force_authenticate(lector)
    return client


@pytest.fixture
def biblioteca():
    return crea_biblioteca("biblioteca@example.com", "Biblioteca Montbau")


@pytest.fixture
def llibres():
    return [
        Llibre.objects.create(titol="La plaça del Diamant", autor="Mercè Rodoreda", isbn="9788429740011"),
        Llibre.objects.create(titol="Solitud", autor="Víctor Català", isbn="9788475882574"),
    ]


def crea_comanda(usuari, biblioteca, llibres, estat=Estat.REBUDA):
    comanda = Comanda.objects.create(usuari=usuari, biblioteca=biblioteca, estat=estat)
    for llibre in llibres:
        LiniaComanda.objects.create(comanda=comanda, llibre=llibre)
    return comanda


@pytest.mark.django_db
def test_mostra_les_comandes_amb_l_estat_la_biblioteca_i_els_llibres(client, lector, biblioteca, llibres):
    comanda = crea_comanda(lector, biblioteca, llibres)

    resposta = client.get(URL)

    assert resposta.status_code == 200
    assert resposta.json() == [
        {
            "id": comanda.pk,
            "estat": "rebuda",
            "biblioteca": {"id": biblioteca.pk, "nom": "Biblioteca Montbau"},
            "llibres": [
                {"id": llibres[0].pk, "titol": "La plaça del Diamant", "autor": "Mercè Rodoreda", "portada": ""},
                {"id": llibres[1].pk, "titol": "Solitud", "autor": "Víctor Català", "portada": ""},
            ],
            "data_lliurament": None,
            "creada": resposta.json()[0]["creada"],
        }
    ]


@pytest.mark.django_db
def test_l_estat_canvia_quan_canvia_la_comanda(client, lector, biblioteca, llibres):
    comanda = crea_comanda(lector, biblioteca, llibres)
    canvia_estat(comanda, Estat.PREPARADA)

    assert client.get(URL).json()[0]["estat"] == "preparada"


@pytest.mark.django_db
def test_surten_de_la_mes_nova_a_la_mes_antiga(client, lector, biblioteca, llibres):
    primera = crea_comanda(lector, biblioteca, llibres[:1])
    segona = crea_comanda(lector, biblioteca, llibres[1:])

    ids = [comanda["id"] for comanda in client.get(URL).json()]

    assert ids == [segona.pk, primera.pk]


@pytest.mark.django_db
def test_surten_totes_tambe_les_lliurades_i_les_cancellades(client, lector, biblioteca, llibres):
    for estat in Estat.values:
        crea_comanda(lector, biblioteca, llibres, estat=estat)

    estats = sorted(comanda["estat"] for comanda in client.get(URL).json())

    assert estats == sorted(Estat.values)


@pytest.mark.django_db
def test_no_surten_les_comandes_d_altres_usuaris(client, lector, biblioteca, llibres):
    meva = crea_comanda(lector, biblioteca, llibres)
    crea_comanda(crea_usuari("altre@example.com"), biblioteca, llibres)

    ids = [comanda["id"] for comanda in client.get(URL).json()]

    assert ids == [meva.pk]


@pytest.mark.django_db
def test_sense_comandes_retorna_una_llista_buida(client):
    resposta = client.get(URL)

    assert resposta.status_code == 200
    assert resposta.json() == []


@pytest.mark.django_db
def test_el_nombre_de_consultes_no_creix_amb_les_comandes(client, lector, biblioteca, llibres):
    crea_comanda(lector, biblioteca, llibres)
    with CaptureQueriesContext(connection) as amb_una:
        client.get(URL)

    altra = crea_biblioteca("altra@example.com", "Biblioteca Sant Gervasi")
    for _ in range(4):
        crea_comanda(lector, altra, llibres)
    with CaptureQueriesContext(connection) as amb_cinc:
        client.get(URL)

    assert len(amb_cinc) == len(amb_una)


@pytest.mark.django_db
def test_sense_sessio_rep_401():
    assert APIClient().get(URL).status_code == 401


@pytest.mark.django_db
@pytest.mark.parametrize("rol", [Usuari.Role.BIBLIOTECA, Usuari.Role.REPARTIDOR])
def test_una_biblioteca_o_un_repartidor_reben_403(rol):
    client = APIClient()
    client.force_authenticate(crea_usuari("altre@example.com", rol))

    assert client.get(URL).status_code == 403


@pytest.mark.django_db
def test_un_usuari_desactivat_rep_403(client, lector):
    lector.is_active = False
    lector.save(update_fields=["is_active"])

    assert client.get(URL).status_code == 403
