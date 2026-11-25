"""Tests de la ruta del dia que es crea en assignar una comanda (US12-T12).

Quan `assigna_comanda` assigna una comanda a un repartidor, la comanda entra a
la ruta d'aquell dia del repartidor amb la recollida i el lliurament.
"""

from datetime import date, time
from unittest import mock

import pytest
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from prestecs.assignacio import assigna_comanda, assigna_pendents
from prestecs.models import Comanda, Parada, Ruta
from usuaris.models import Biblioteca, FranjaDisponibilitat, PerfilRepartidor, Usuari

Estat = Comanda.Estat
Dia = FranjaDisponibilitat.Dia
Tipus = Parada.Tipus
# El 23 de novembre de 2026 és dilluns.
DILLUNS = date(2026, 11, 23)
DIMARTS = date(2026, 11, 24)
TOT_EL_DIA = [(dia, time(8), time(20)) for dia in Dia.values]


def crea_usuari(correu, rol=Usuari.Role.USUARI, nom=None):
    return Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {"name": nom or correu.split("@")[0], "address": "C/ Major 1", "library_card_number": correu, "role": rol},
    )


def crea_repartidor(nom, dni, franges=()):
    usuari = crea_usuari(f"{nom.lower()}@example.com", Usuari.Role.REPARTIDOR, nom=nom)
    perfil = PerfilRepartidor.objects.create(
        usuari=usuari,
        cognoms="Puig",
        dni=dni,
        telefon="612345678",
        vehicle=PerfilRepartidor.Vehicle.BICI,
        num_seguretat_social="281234567840",
        estat=PerfilRepartidor.Estat.VALIDAT,
    )
    for dia, inici, fi in franges:
        perfil.franges.create(dia=dia, hora_inici=inici, hora_fi=fi)
    return usuari


def crea_biblioteca():
    usuari = crea_usuari("biblioteca@example.com", Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=usuari, nom="Biblioteca Montbau")
    usuari.is_active = True
    usuari.save(update_fields=["is_active"])
    return usuari


@pytest.fixture
def biblioteca():
    return crea_biblioteca()


@pytest.fixture
def lector():
    return crea_usuari("lector@example.com")


@pytest.fixture
def nova_comanda(lector, biblioteca):
    def crea(estat=Estat.PREPARADA):
        return Comanda.objects.create(usuari=lector, biblioteca=biblioteca, estat=estat)

    return crea


def parades(ruta):
    """Les parades de la ruta en ordre, com a parelles (comanda, tipus)."""
    return [(parada.comanda_id, parada.tipus) for parada in ruta.parades.order_by("ordre")]


@pytest.mark.django_db
def test_en_assignar_la_comanda_es_crea_la_ruta_amb_la_recollida_i_el_lliurament(nova_comanda):
    jordi = crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(13))])
    comanda = nova_comanda()

    assert assigna_comanda(comanda, primer_dia=DILLUNS)

    ruta = Ruta.objects.get()
    assert (ruta.repartidor, ruta.data) == (jordi, DILLUNS)
    assert parades(ruta) == [(comanda.pk, Tipus.RECOLLIDA), (comanda.pk, Tipus.LLIVRAMENT)]
    assert list(ruta.parades.order_by("ordre").values_list("ordre", flat=True)) == [1, 2]


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_les_comandes_del_mateix_repartidor_i_dia_van_a_la_mateixa_ruta_per_hora(nova_comanda):
    crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(13))])
    primera, segona = nova_comanda(), nova_comanda()

    assigna_comanda(primera, primer_dia=DILLUNS)
    assigna_comanda(segona, primer_dia=DILLUNS)

    ruta = Ruta.objects.get()
    assert parades(ruta) == [
        (primera.pk, Tipus.RECOLLIDA),
        (primera.pk, Tipus.LLIVRAMENT),
        (segona.pk, Tipus.RECOLLIDA),
        (segona.pk, Tipus.LLIVRAMENT),
    ]
    assert list(ruta.parades.order_by("ordre").values_list("ordre", flat=True)) == [1, 2, 3, 4]


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_l_ordre_segueix_l_hora_de_lliurament_i_no_l_ordre_d_assignacio(nova_comanda):
    jordi = crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(13))])
    primera, segona = nova_comanda(), nova_comanda()
    assigna_comanda(primera, primer_dia=DILLUNS)
    assigna_comanda(segona, primer_dia=DILLUNS)

    # La segona comanda passa a ser la primera del matí.
    Comanda.objects.filter(pk=segona.pk).update(hora_inici_lliurament=time(8), hora_fi_lliurament=time(8, 30))
    tercera = nova_comanda()
    assigna_comanda(tercera, primer_dia=DILLUNS)

    ruta = Ruta.objects.get(repartidor=jordi)
    ordenades = parades(ruta)
    assert ordenades[:2] == [(segona.pk, Tipus.RECOLLIDA), (segona.pk, Tipus.LLIVRAMENT)]
    assert len(ordenades) == 6


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_cada_dia_te_la_seva_ruta(nova_comanda):
    crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(9, 30)), (Dia.DIMARTS, time(9), time(13))])
    dilluns, dimarts = nova_comanda(), nova_comanda()

    assigna_comanda(dilluns, primer_dia=DILLUNS)
    assigna_comanda(dimarts, primer_dia=DILLUNS)

    assert parades(Ruta.objects.get(data=DILLUNS)) == [
        (dilluns.pk, Tipus.RECOLLIDA),
        (dilluns.pk, Tipus.LLIVRAMENT),
    ]
    assert parades(Ruta.objects.get(data=DIMARTS)) == [
        (dimarts.pk, Tipus.RECOLLIDA),
        (dimarts.pk, Tipus.LLIVRAMENT),
    ]


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_cada_repartidor_te_la_seva_ruta(nova_comanda):
    jordi = crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(9, 30))])
    marta = crea_repartidor("Marta", "87654321X", [(Dia.DILLUNS, time(9), time(9, 30))])
    primera, segona = nova_comanda(), nova_comanda()

    assigna_comanda(primera, primer_dia=DILLUNS)
    assigna_comanda(segona, primer_dia=DILLUNS)

    rutes = {ruta.repartidor: parades(ruta) for ruta in Ruta.objects.all()}
    assert rutes == {
        jordi: [(primera.pk, Tipus.RECOLLIDA), (primera.pk, Tipus.LLIVRAMENT)],
        marta: [(segona.pk, Tipus.RECOLLIDA), (segona.pk, Tipus.LLIVRAMENT)],
    }


@pytest.mark.django_db
def test_sense_forat_no_es_crea_cap_ruta(nova_comanda):
    crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(9, 10))])

    assert not assigna_comanda(nova_comanda(), primer_dia=DILLUNS)

    assert not Ruta.objects.exists()
    assert not Parada.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("estat", [Estat.REBUDA, Estat.EN_CAMI, Estat.LLIURADA, Estat.CANCELLADA])
def test_una_comanda_que_no_esta_preparada_no_entra_a_cap_ruta(nova_comanda, estat):
    crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(13))])

    assert not assigna_comanda(nova_comanda(estat), primer_dia=DILLUNS)

    assert not Parada.objects.exists()


@pytest.mark.django_db
def test_assignar_dues_vegades_la_mateixa_comanda_no_duplica_les_parades(nova_comanda):
    crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(13))])
    comanda = nova_comanda()
    assigna_comanda(comanda, primer_dia=DILLUNS)

    assert not assigna_comanda(comanda, primer_dia=DILLUNS)

    assert Parada.objects.filter(comanda=comanda).count() == 2


@pytest.mark.django_db
def test_si_es_torna_a_assignar_al_mateix_repartidor_i_dia_reaprofita_les_parades(nova_comanda):
    """Si la comanda es torna a planificar sense treure les parades, no es dupliquen."""
    crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(13))])
    comanda = nova_comanda()
    assigna_comanda(comanda, primer_dia=DILLUNS)
    Comanda.objects.filter(pk=comanda.pk).update(
        repartidor=None, data_lliurament=None, hora_inici_lliurament=None, hora_fi_lliurament=None
    )

    assert assigna_comanda(comanda, primer_dia=DILLUNS)

    assert parades(Ruta.objects.get()) == [(comanda.pk, Tipus.RECOLLIDA), (comanda.pk, Tipus.LLIVRAMENT)]


@pytest.mark.django_db
def test_si_no_es_pot_crear_la_ruta_la_comanda_no_queda_assignada(nova_comanda):
    crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(13))])
    comanda = nova_comanda()

    with mock.patch("prestecs.assignacio.calcula_i_desaa_ordre_ruta", side_effect=RuntimeError("error de prova")):
        with pytest.raises(RuntimeError):
            assigna_comanda(comanda, primer_dia=DILLUNS)

    comanda.refresh_from_db()
    assert comanda.repartidor is None
    assert comanda.data_lliurament is None
    assert not Ruta.objects.exists()
    assert not Parada.objects.exists()


@pytest.mark.django_db
def test_assigna_pendents_tambe_crea_les_rutes(nova_comanda):
    crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(13))])
    primera, segona = nova_comanda(), nova_comanda()

    assert assigna_pendents(primer_dia=DILLUNS) == (2, 0)

    assert Parada.objects.filter(comanda__in=[primera, segona]).count() == 4


@pytest.mark.django_db
def test_marcar_la_comanda_com_a_llesta_la_posa_a_la_ruta(nova_comanda, biblioteca):
    crea_repartidor("Jordi", "12345678Z", TOT_EL_DIA)
    comanda = nova_comanda(Estat.REBUDA)
    client = APIClient()
    client.force_authenticate(biblioteca)

    resposta = client.post(f"/api/prestecs/biblioteca/comandes/{comanda.pk}/preparada/")

    assert resposta.status_code == 200
    assert parades(Ruta.objects.get()) == [(comanda.pk, Tipus.RECOLLIDA), (comanda.pk, Tipus.LLIVRAMENT)]


@pytest.mark.django_db
def test_el_repartidor_veu_la_comanda_a_la_ruta_del_dia(nova_comanda, biblioteca):
    jordi = crea_repartidor("Jordi", "12345678Z", TOT_EL_DIA)
    comanda = nova_comanda()
    assigna_comanda(comanda, primer_dia=timezone.localdate())
    client = APIClient()
    client.force_authenticate(jordi)

    ruta = client.get("/api/prestecs/repartidor/ruta-avui/").json()

    assert [(parada["ordre"], parada["tipus"], parada["comanda"]) for parada in ruta] == [
        (1, "recollida", comanda.pk),
        (2, "lliurament", comanda.pk),
    ]
    assert ruta[0]["adreca"]["biblioteca"]["nom"] == "Biblioteca Montbau"
