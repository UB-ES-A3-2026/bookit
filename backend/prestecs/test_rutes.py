from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from prestecs.models import Comanda, Parada, Ruta
from usuaris.models import PerfilRepartidor, Usuari


pytestmark = pytest.mark.django_db


def crea_repartidor(correu="repartidor@example.com", dni="12345678Z"):
    usuari = Usuari.objects.create_user(
        correu,
        "ContrasenyaSegura123!",
        {
            "name": "Repartidor de prova",
            "address": "",
            "library_card_number": f"repartidor-{dni}",
            "role": Usuari.Role.REPARTIDOR,
        },
    )
    return PerfilRepartidor.objects.create(
        usuari=usuari,
        cognoms="Puig Soler",
        dni=dni,
        telefon="612345678",
        vehicle=PerfilRepartidor.Vehicle.BICI,
        matricula="",
        num_seguretat_social="281234567840",
    ).usuari


def crea_usuari(correu="lector@example.com"):
    return Usuari.objects.create_user(
        correu,
        "ContrasenyaSegura123!",
        {
            "name": "Usuari de prova",
            "address": "C/ Major 1",
            "library_card_number": f"lector-{correu}",
        },
    )


def crea_biblioteca(correu="biblioteca@example.com"):
    usuari = Usuari.objects.create_user(
        correu,
        "ContrasenyaSegura123!",
        {
            "name": "Biblioteca de prova",
            "address": "C/ Biblioteca 1",
            "library_card_number": f"biblioteca-{correu}",
            "role": Usuari.Role.BIBLIOTECA,
        },
    )
    usuari.is_active = True
    usuari.save(update_fields=["is_active"])
    return usuari


@pytest.fixture
def repartidor():
    return crea_repartidor()


@pytest.fixture
def comanda():
    return Comanda.objects.create(
        usuari=crea_usuari(),
        biblioteca=crea_biblioteca(),
    )


def test_es_pot_crear_una_ruta_amb_diverses_parades(repartidor, comanda):
    altra_comanda = Comanda.objects.create(
        usuari=crea_usuari("altre-lector@example.com"),
        biblioteca=comanda.biblioteca,
    )
    ruta = Ruta.objects.create(repartidor=repartidor, data=date(2026, 11, 24))

    primera = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.RECOLLIDA,
        ordre=1,
    )
    segona = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.LLIVRAMENT,
        ordre=2,
    )
    tercera = Parada.objects.create(
        ruta=ruta,
        comanda=altra_comanda,
        tipus=Parada.Tipus.RECOLLIDA,
        ordre=3,
    )

    assert ruta.parades.count() == 3
    assert primera.ruta == ruta
    assert segona.comanda == comanda
    assert tercera.ordre == 3


def test_un_repartidor_no_pot_tenir_dues_rutes_el_mateix_dia(repartidor):
    Ruta.objects.create(repartidor=repartidor, data=date(2026, 11, 24))

    with pytest.raises(IntegrityError), transaction.atomic():
        Ruta.objects.create(repartidor=repartidor, data=date(2026, 11, 24))


def test_dos_repartidors_poden_tenir_ruta_i_un_repartidor_varis_dies():
    primer = crea_repartidor()
    segon = crea_repartidor("segon-repartidor@example.com", "87654321X")

    primer_avui = Ruta.objects.create(
        repartidor=primer,
        data=date(2026, 11, 24),
    )
    segon_avui = Ruta.objects.create(
        repartidor=segon,
        data=date(2026, 11, 24),
    )
    primer_dema = Ruta.objects.create(
        repartidor=primer,
        data=date(2026, 11, 25),
    )

    assert primer_avui.repartidor == primer
    assert segon_avui.repartidor == segon
    assert primer_dema.repartidor == primer
    assert Ruta.objects.count() == 3


def test_dues_parades_no_poden_tenir_el_mateix_ordre(repartidor, comanda):
    ruta = Ruta.objects.create(repartidor=repartidor, data=date(2026, 11, 24))
    Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.RECOLLIDA,
        ordre=1,
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        Parada.objects.create(
            ruta=ruta,
            comanda=comanda,
            tipus=Parada.Tipus.LLIVRAMENT,
            ordre=1,
        )


def test_una_comanda_no_pot_repetir_el_mateix_tipus_a_la_ruta(repartidor, comanda):
    ruta = Ruta.objects.create(repartidor=repartidor, data=date(2026, 11, 24))
    Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.RECOLLIDA,
        ordre=1,
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        Parada.objects.create(
            ruta=ruta,
            comanda=comanda,
            tipus=Parada.Tipus.RECOLLIDA,
            ordre=2,
        )


def test_la_mateixa_comanda_pot_tenir_recollida_i_lliurament(repartidor, comanda):
    ruta = Ruta.objects.create(repartidor=repartidor, data=date(2026, 11, 24))

    recollida = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.RECOLLIDA,
        ordre=1,
    )
    lliurament = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.LLIVRAMENT,
        ordre=2,
    )

    assert recollida.comanda == comanda
    assert lliurament.comanda == comanda
    assert Parada.objects.filter(comanda=comanda).count() == 2


def test_les_parades_surten_ordenades_per_ordre(repartidor, comanda):
    ruta = Ruta.objects.create(repartidor=repartidor, data=date(2026, 11, 24))

    tercera = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.LLIVRAMENT,
        ordre=3,
    )
    primera = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.RECOLLIDA,
        ordre=1,
    )
    segona_comanda = Comanda.objects.create(
        usuari=crea_usuari("segona@example.com"),
        biblioteca=comanda.biblioteca,
    )
    segona = Parada.objects.create(
        ruta=ruta,
        comanda=segona_comanda,
        tipus=Parada.Tipus.RECOLLIDA,
        ordre=2,
    )

    assert list(ruta.parades.all()) == [primera, segona, tercera]


def test_un_tipus_de_parada_no_valid_es_rebutjat_per_full_clean(repartidor, comanda):
    ruta = Ruta.objects.create(repartidor=repartidor, data=date(2026, 11, 24))
    parada = Parada(
        ruta=ruta,
        comanda=comanda,
        tipus="indefinida",
        ordre=1,
    )

    with pytest.raises(ValidationError) as error:
        parada.full_clean()

    assert "tipus" in error.value.message_dict
