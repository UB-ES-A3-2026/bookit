"""Tests de la cancel·lació d'una comanda que ja tenia repartidor (US20-T8).

En cancel·lar-la, la comanda deixa de tenir repartidor, dia i hora de lliurament.
"""

from datetime import date, time

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from cataleg.models import ExemplarBiblioteca, Llibre
from prestecs.assignacio import assigna_comanda
from prestecs.models import Comanda
from prestecs.serveis import TransicioNoPermesa, cancella_comanda, confirma_comanda
from usuaris.models import Biblioteca, FranjaDisponibilitat, PerfilRepartidor, Usuari

Estat = Comanda.Estat
Dia = FranjaDisponibilitat.Dia
# El 23 de novembre de 2026 és dilluns.
DILLUNS = date(2026, 11, 23)


def crea_usuari(correu, rol=Usuari.Role.USUARI, nom=None):
    return Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {"name": nom or correu.split("@")[0], "address": "C/ Major 1", "library_card_number": correu, "role": rol},
    )


def crea_repartidor(franges):
    usuari = crea_usuari("jordi@example.com", Usuari.Role.REPARTIDOR, nom="Jordi")
    perfil = PerfilRepartidor.objects.create(
        usuari=usuari,
        cognoms="Puig",
        dni="12345678Z",
        telefon="612345678",
        vehicle=PerfilRepartidor.Vehicle.BICI,
        num_seguretat_social="281234567840",
        estat=PerfilRepartidor.Estat.VALIDAT,
    )
    for dia, inici, fi in franges:
        perfil.franges.create(dia=dia, hora_inici=inici, hora_fi=fi)
    return usuari


@pytest.fixture
def lector():
    return crea_usuari("lector@example.com")


@pytest.fixture
def biblioteca():
    usuari = crea_usuari("biblioteca@example.com", Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=usuari, nom="Biblioteca Montbau")
    usuari.is_active = True
    usuari.save(update_fields=["is_active"])
    return usuari


@pytest.fixture
def llibre(biblioteca):
    llibre = Llibre.objects.create(titol="Solitud", autor="Víctor Català", isbn="9788475882574")
    ExemplarBiblioteca.objects.create(llibre=llibre, biblioteca=biblioteca, quantitat=3)
    return llibre


@pytest.fixture
def jordi():
    return crea_repartidor([(Dia.DILLUNS, time(9), time(9, 30))])


@pytest.fixture
def assignada(lector, biblioteca, llibre, jordi):
    comanda = confirma_comanda(lector, biblioteca, [llibre])
    Comanda.objects.filter(pk=comanda.pk).update(estat=Estat.PREPARADA)
    comanda.refresh_from_db()
    assert assigna_comanda(comanda, primer_dia=DILLUNS)
    return comanda


def lliurament(comanda):
    comanda.refresh_from_db()
    return (comanda.repartidor, comanda.data_lliurament, comanda.hora_inici_lliurament, comanda.hora_fi_lliurament)


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_cancellar_una_comanda_assignada_li_treu_el_repartidor_i_l_horari(assignada, jordi):
    assert lliurament(assignada) == (jordi, DILLUNS, time(9), time(9, 30))

    cancella_comanda(assignada)

    assert lliurament(assignada) == (None, None, None, None)
    assert assignada.estat == Estat.CANCELLADA


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_la_resposta_de_l_api_ja_no_porta_la_data_de_lliurament(assignada, lector):
    client = APIClient()
    client.force_authenticate(lector)

    resposta = client.post(f"/api/prestecs/comandes/{assignada.pk}/cancellar/")

    assert resposta.status_code == 200
    assert resposta.json()["estat"] == "cancellada"
    assert resposta.json()["data_lliurament"] is None
    assert lliurament(assignada) == (None, None, None, None)


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_el_forat_queda_lliure_per_a_una_altra_comanda(assignada, lector, biblioteca, llibre, jordi):
    cancella_comanda(assignada)
    altra = confirma_comanda(lector, biblioteca, [llibre])
    Comanda.objects.filter(pk=altra.pk).update(estat=Estat.PREPARADA)

    assert assigna_comanda(altra, primer_dia=DILLUNS)

    assert lliurament(altra) == (jordi, DILLUNS, time(9), time(9, 30))


@pytest.mark.django_db
def test_cancellar_una_comanda_sense_repartidor_continua_funcionant(lector, biblioteca, llibre):
    comanda = confirma_comanda(lector, biblioteca, [llibre])

    cancella_comanda(comanda)

    assert lliurament(comanda) == (None, None, None, None)
    assert comanda.estat == Estat.CANCELLADA


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_si_la_comanda_ja_ha_sortit_no_es_toca_el_repartidor(assignada, jordi):
    Comanda.objects.filter(pk=assignada.pk).update(estat=Estat.EN_CAMI)

    with pytest.raises(TransicioNoPermesa):
        cancella_comanda(assignada)

    assert lliurament(assignada) == (jordi, DILLUNS, time(9), time(9, 30))


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_la_llista_de_la_biblioteca_mostra_la_cancellada_sense_data(assignada, biblioteca):
    cancella_comanda(assignada)
    client = APIClient()
    client.force_authenticate(biblioteca)

    comandes = client.get("/api/prestecs/biblioteca/comandes/").json()

    assert [(comanda["estat"], comanda["data_lliurament"]) for comanda in comandes] == [("cancellada", None)]
