"""Tests de l'assignació amb les comandes de recollida (US14-T10).

Les comandes de recollida no les porta cap repartidor: l'usuari les recull a la
biblioteca. Per això l'assignació se les salta.
"""

from datetime import date, time
from io import StringIO

import pytest
from django.core.management import call_command
from django.test import override_settings
from rest_framework.test import APIClient

from prestecs.assignacio import assigna_comanda, assigna_pendents
from prestecs.models import Comanda
from usuaris.models import Biblioteca, FranjaDisponibilitat, PerfilRepartidor, Usuari

Estat = Comanda.Estat
Tipus = Comanda.TipusLliurament
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
def biblioteca():
    usuari = crea_usuari("biblioteca@example.com", Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=usuari, nom="Biblioteca Montbau")
    usuari.is_active = True
    usuari.save(update_fields=["is_active"])
    return usuari


@pytest.fixture
def nova_comanda(biblioteca):
    lector = crea_usuari("lector@example.com")

    def crea(tipus=Tipus.DOMICILI, estat=Estat.PREPARADA):
        return Comanda.objects.create(usuari=lector, biblioteca=biblioteca, estat=estat, tipus_lliurament=tipus)

    return crea


def horari(comanda):
    comanda.refresh_from_db()
    return (comanda.repartidor, comanda.data_lliurament, comanda.hora_inici_lliurament, comanda.hora_fi_lliurament)


@pytest.mark.django_db
def test_una_comanda_de_recollida_no_s_assigna(nova_comanda):
    crea_repartidor([(Dia.DILLUNS, time(9), time(13))])
    comanda = nova_comanda(Tipus.RECOLLIDA)

    assert not assigna_comanda(comanda, primer_dia=DILLUNS)

    assert horari(comanda) == (None, None, None, None)


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_una_comanda_a_domicili_s_assigna_com_sempre(nova_comanda):
    jordi = crea_repartidor([(Dia.DILLUNS, time(9), time(13))])
    comanda = nova_comanda(Tipus.DOMICILI)

    assert assigna_comanda(comanda, primer_dia=DILLUNS)

    assert horari(comanda) == (jordi, DILLUNS, time(9), time(9, 30))


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_les_recollides_no_ocupen_forats_dels_repartidors(nova_comanda):
    jordi = crea_repartidor([(Dia.DILLUNS, time(9), time(9, 30))])
    recollida = nova_comanda(Tipus.RECOLLIDA)
    domicili = nova_comanda(Tipus.DOMICILI)

    assigna_comanda(recollida, primer_dia=DILLUNS)
    assigna_comanda(domicili, primer_dia=DILLUNS)

    assert horari(domicili) == (jordi, DILLUNS, time(9), time(9, 30))


@pytest.mark.django_db
def test_assigna_pendents_no_compta_les_recollides(nova_comanda):
    crea_repartidor([(Dia.DILLUNS, time(9), time(13))])
    recollida = nova_comanda(Tipus.RECOLLIDA)
    domicili = nova_comanda(Tipus.DOMICILI)

    assert assigna_pendents(primer_dia=DILLUNS) == (1, 0)

    assert horari(recollida)[0] is None
    assert horari(domicili)[0] is not None


@pytest.mark.django_db
def test_l_ordre_assigna_comandes_no_compta_les_recollides_com_a_sense_repartidor(nova_comanda):
    nova_comanda(Tipus.RECOLLIDA)
    nova_comanda(Tipus.RECOLLIDA)
    sortida = StringIO()

    call_command("assigna_comandes", stdout=sortida)

    assert sortida.getvalue().strip() == "Comandes assignades: 0. Sense repartidor disponible: 0."


@pytest.mark.django_db
def test_marcar_com_a_llesta_una_recollida_no_li_posa_repartidor(nova_comanda, biblioteca):
    crea_repartidor([(dia, time(8), time(20)) for dia in Dia.values])
    comanda = nova_comanda(Tipus.RECOLLIDA, Estat.REBUDA)
    client = APIClient()
    client.force_authenticate(biblioteca)

    resposta = client.post(f"/api/prestecs/biblioteca/comandes/{comanda.pk}/preparada/")

    assert resposta.status_code == 200
    assert resposta.json()["estat"] == "preparada"
    assert resposta.json()["data_lliurament"] is None
    assert horari(comanda) == (None, None, None, None)


@pytest.mark.django_db
def test_una_recollida_sense_repartidor_es_pot_lliurar_a_la_biblioteca(nova_comanda, biblioteca):
    crea_repartidor([(dia, time(8), time(20)) for dia in Dia.values])
    comanda = nova_comanda(Tipus.RECOLLIDA, Estat.REBUDA)
    client = APIClient()
    client.force_authenticate(biblioteca)

    client.post(f"/api/prestecs/biblioteca/comandes/{comanda.pk}/preparada/")
    resposta = client.post(f"/api/prestecs/biblioteca/comandes/{comanda.pk}/recollida/")

    assert resposta.status_code == 200
    comanda.refresh_from_db()
    assert comanda.estat == Estat.LLIURADA
    assert comanda.repartidor is None
