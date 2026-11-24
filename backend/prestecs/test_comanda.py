"""Tests de la comanda de punta a punta (US6-T4).

Completen els de l'endpoint (`test_confirmar_comanda.py`) i els de la reserva
d'exemplars (`test_reserva_exemplars.py`): ordre dels llibres, diverses comandes
del mateix usuari, què passa amb l'estoc quan la comanda no es pot fer i comandes
simultànies amb els mateixos llibres en ordre diferent.
"""

import threading
from unittest import mock

import pytest
from django.db import connection
from django.test import override_settings
from rest_framework.test import APIClient

from cataleg.models import ExemplarBiblioteca, Llibre
from prestecs.models import Comanda, LiniaComanda
from prestecs.serveis import LlibresSenseEstoc, confirma_comanda
from usuaris.models import Biblioteca, Usuari

URL = "/api/prestecs/comandes/"


def crea_usuari(correu, rol=Usuari.Role.USUARI):
    return Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {"name": correu.split("@")[0], "address": "C/ Major 1", "library_card_number": correu, "role": rol},
    )


def crea_biblioteca(correu, nom):
    usuari = crea_usuari(correu, Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=usuari, nom=nom)
    usuari.is_active = True
    usuari.save(update_fields=["is_active"])
    return usuari


def crea_llibre(titol, isbn, biblioteca, exemplars):
    llibre = Llibre.objects.create(titol=titol, autor="Autor de prova", isbn=isbn)
    ExemplarBiblioteca.objects.create(llibre=llibre, biblioteca=biblioteca, quantitat=exemplars)
    return llibre


def exemplars(llibre, biblioteca):
    return ExemplarBiblioteca.objects.get(llibre=llibre, biblioteca=biblioteca).quantitat


@pytest.fixture
def lector():
    return crea_usuari("lector@example.com")


@pytest.fixture
def biblioteca():
    return crea_biblioteca("biblioteca@example.com", "Biblioteca Montbau")


@pytest.fixture
def client(lector):
    client = APIClient()
    client.force_authenticate(lector)
    return client


def confirma(client, biblioteca, llibres):
    return client.post(
        URL, {"biblioteca": biblioteca.pk, "llibres": [llibre.pk for llibre in llibres]}, format="json"
    )


@pytest.mark.django_db
def test_els_llibres_surten_en_l_ordre_en_que_s_han_demanat(client, biblioteca):
    placa = crea_llibre("La plaça del Diamant", "9788429740011", biblioteca, 1)
    solitud = crea_llibre("Solitud", "9788475882574", biblioteca, 1)
    mirall = crea_llibre("Mirall trencat", "9788475881355", biblioteca, 1)

    resposta = confirma(client, biblioteca, [mirall, placa, solitud])

    assert resposta.status_code == 201
    assert [llibre["id"] for llibre in resposta.json()["llibres"]] == [mirall.pk, placa.pk, solitud.pk]


@pytest.mark.django_db
def test_un_usuari_pot_fer_comandes_a_biblioteques_diferents(client, lector, biblioteca):
    altra = crea_biblioteca("altra@example.com", "Biblioteca Sant Gervasi")
    llibre = crea_llibre("Solitud", "9788475882574", biblioteca, 1)
    ExemplarBiblioteca.objects.create(llibre=llibre, biblioteca=altra, quantitat=1)

    primera = confirma(client, biblioteca, [llibre])
    segona = confirma(client, altra, [llibre])

    assert primera.status_code == 201
    assert segona.status_code == 201
    assert segona.json()["biblioteca"] == {"id": altra.pk, "nom": "Biblioteca Sant Gervasi"}
    assert lector.comandes.count() == 2


@pytest.mark.django_db
def test_diu_tots_els_llibres_sense_estoc_en_l_ordre_demanat(client, biblioteca):
    placa = crea_llibre("La plaça del Diamant", "9788429740011", biblioteca, 0)
    solitud = crea_llibre("Solitud", "9788475882574", biblioteca, 2)
    mirall = crea_llibre("Mirall trencat", "9788475881355", biblioteca, 0)

    resposta = confirma(client, biblioteca, [mirall, solitud, placa])

    assert resposta.status_code == 400
    assert resposta.json()["sense_estoc"] == [mirall.pk, placa.pk]
    assert exemplars(solitud, biblioteca) == 2


@pytest.mark.django_db
@override_settings(LIMIT_LLIBRES_COMANDA=1)
def test_si_supera_el_limit_no_es_reserva_cap_exemplar(client, biblioteca):
    placa = crea_llibre("La plaça del Diamant", "9788429740011", biblioteca, 1)
    solitud = crea_llibre("Solitud", "9788475882574", biblioteca, 1)

    resposta = confirma(client, biblioteca, [placa, solitud])

    assert resposta.status_code == 400
    assert exemplars(placa, biblioteca) == 1
    assert exemplars(solitud, biblioteca) == 1


@pytest.mark.django_db
def test_si_falla_en_desar_les_linies_es_desfa_la_reserva(lector, biblioteca):
    llibre = crea_llibre("Solitud", "9788475882574", biblioteca, 1)

    with mock.patch.object(LiniaComanda.objects, "bulk_create", side_effect=RuntimeError("error de prova")):
        with pytest.raises(RuntimeError):
            confirma_comanda(lector, biblioteca, [llibre])

    assert exemplars(llibre, biblioteca) == 1
    assert not Comanda.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_dues_comandes_alhora_amb_els_llibres_creuats_no_es_bloquegen():
    """Una demana A i B, l'altra B i A, i només queda un exemplar de cada.

    Si les files es bloquegessin en l'ordre de la comanda, cadascuna podria
    quedar-se esperant l'altra i PostgreSQL n'aturaria una amb un error.
    """
    biblioteca = crea_biblioteca("biblioteca@example.com", "Biblioteca Montbau")
    placa = crea_llibre("La plaça del Diamant", "9788429740011", biblioteca, 1)
    solitud = crea_llibre("Solitud", "9788475882574", biblioteca, 1)
    peticions = [
        (crea_usuari("primer@example.com"), [placa, solitud]),
        (crea_usuari("segon@example.com"), [solitud, placa]),
    ]
    sortida = threading.Barrier(2)
    resultats = []

    def demana(usuari, llibres):
        try:
            sortida.wait()
            confirma_comanda(usuari, biblioteca, llibres)
            resultats.append("creada")
        except LlibresSenseEstoc:
            resultats.append("sense estoc")
        except Exception as error:
            resultats.append(f"error: {error}")
        finally:
            connection.close()

    fils = [threading.Thread(target=demana, args=peticio) for peticio in peticions]
    for fil in fils:
        fil.start()
    for fil in fils:
        fil.join()

    assert sorted(resultats) == ["creada", "sense estoc"]
    assert Comanda.objects.count() == 1
    assert exemplars(placa, biblioteca) == 0
    assert exemplars(solitud, biblioteca) == 0
