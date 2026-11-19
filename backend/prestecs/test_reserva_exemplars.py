"""Tests de la reserva d'exemplars en confirmar una comanda (US6-T3)."""

import threading

import pytest
from django.db import connection
from rest_framework.test import APIClient

from cataleg.models import ExemplarBiblioteca, Llibre
from prestecs.models import Comanda
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


@pytest.mark.django_db
def test_confirmar_descompta_un_exemplar_de_cada_llibre(lector, biblioteca):
    placa = crea_llibre("La plaça del Diamant", "9788429740011", biblioteca, 3)
    solitud = crea_llibre("Solitud", "9788475882574", biblioteca, 1)

    confirma_comanda(lector, biblioteca, [placa, solitud])

    assert exemplars(placa, biblioteca) == 2
    assert exemplars(solitud, biblioteca) == 0


@pytest.mark.django_db
def test_si_falta_estoc_no_es_descompta_cap_exemplar(lector, biblioteca):
    placa = crea_llibre("La plaça del Diamant", "9788429740011", biblioteca, 3)
    esgotat = crea_llibre("Solitud", "9788475882574", biblioteca, 0)

    with pytest.raises(LlibresSenseEstoc):
        confirma_comanda(lector, biblioteca, [placa, esgotat])

    assert exemplars(placa, biblioteca) == 3
    assert not Comanda.objects.exists()


@pytest.mark.django_db
def test_despres_de_l_ultim_exemplar_el_llibre_queda_sense_estoc(lector, biblioteca):
    llibre = crea_llibre("Solitud", "9788475882574", biblioteca, 1)
    confirma_comanda(lector, biblioteca, [llibre])

    with pytest.raises(LlibresSenseEstoc) as error:
        confirma_comanda(crea_usuari("altre@example.com"), biblioteca, [llibre])

    assert error.value.ids_llibres == [llibre.pk]
    assert Comanda.objects.count() == 1


@pytest.mark.django_db
def test_no_toca_els_exemplars_d_altres_biblioteques(lector, biblioteca):
    altra = crea_biblioteca("altra@example.com", "Biblioteca Sant Gervasi")
    llibre = crea_llibre("Solitud", "9788475882574", biblioteca, 2)
    ExemplarBiblioteca.objects.create(llibre=llibre, biblioteca=altra, quantitat=2)

    confirma_comanda(lector, biblioteca, [llibre])

    assert exemplars(llibre, biblioteca) == 1
    assert exemplars(llibre, altra) == 2


@pytest.mark.django_db
def test_l_endpoint_reserva_els_exemplars(lector, biblioteca):
    llibre = crea_llibre("Solitud", "9788475882574", biblioteca, 1)
    client = APIClient()
    client.force_authenticate(lector)

    primera = client.post(URL, {"biblioteca": biblioteca.pk, "llibres": [llibre.pk]}, format="json")
    segona = client.post(URL, {"biblioteca": biblioteca.pk, "llibres": [llibre.pk]}, format="json")

    assert primera.status_code == 201
    assert segona.status_code == 400
    assert segona.json()["sense_estoc"] == [llibre.pk]
    assert exemplars(llibre, biblioteca) == 0


@pytest.mark.django_db(transaction=True)
def test_dues_comandes_alhora_no_poden_agafar_l_ultim_exemplar():
    """Dos fils, cadascun amb la seva connexió, confirmen alhora l'últim exemplar."""
    biblioteca = crea_biblioteca("biblioteca@example.com", "Biblioteca Montbau")
    llibre = crea_llibre("Solitud", "9788475882574", biblioteca, 1)
    usuaris = [crea_usuari("primer@example.com"), crea_usuari("segon@example.com")]
    sortida = threading.Barrier(2)
    resultats = []

    def demana(usuari):
        try:
            sortida.wait()
            confirma_comanda(usuari, biblioteca, [llibre])
            resultats.append("creada")
        except LlibresSenseEstoc:
            resultats.append("sense estoc")
        finally:
            connection.close()

    fils = [threading.Thread(target=demana, args=(usuari,)) for usuari in usuaris]
    for fil in fils:
        fil.start()
    for fil in fils:
        fil.join()

    assert sorted(resultats) == ["creada", "sense estoc"]
    assert Comanda.objects.count() == 1
    assert exemplars(llibre, biblioteca) == 0
