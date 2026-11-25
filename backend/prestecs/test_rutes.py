from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from datetime import date, time

from prestecs.models import Comanda, Parada, Ruta
from usuaris.models import PerfilRepartidor, Usuari


from prestecs.rutes import (
    DadesRutaInconsistents,
    calcula_i_desaa_ordre_ruta,
    ordena_parades,
)


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

def test_la_recollida_surt_abans_del_lliurament(repartidor, comanda):
    ruta = Ruta.objects.create(
        repartidor=repartidor,
        data=date(2026, 11, 24),
    )
    lliurament = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.LLIVRAMENT,
        ordre=1,
    )
    recollida = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.RECOLLIDA,
        ordre=2,
    )

    resultat = calcula_i_desaa_ordre_ruta(ruta)
    recollida.refresh_from_db()
    lliurament.refresh_from_db()

    assert resultat == [recollida, lliurament]
    assert recollida.ordre == 1
    assert lliurament.ordre == 2


def test_una_ruta_buida_retorna_llista_buida(repartidor):
    ruta = Ruta.objects.create(
        repartidor=repartidor,
        data=date(2026, 11, 24),
    )

    assert calcula_i_desaa_ordre_ruta(ruta) == []


@pytest.mark.parametrize(
    "tipus",
    [
        Parada.Tipus.RECOLLIDA,
        Parada.Tipus.LLIVRAMENT,
    ],
)
def test_ruta_amb_un_sol_tipus_de_parada_s_ordena(repartidor, comanda, tipus):
    ruta = Ruta.objects.create(
        repartidor=repartidor,
        data=date(2026, 11, 24),
    )
    primera = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=tipus,
        ordre=4,
    )
    altra = Comanda.objects.create(
        usuari=crea_usuari("altre@example.com"),
        biblioteca=comanda.biblioteca,
    )
    segona = Parada.objects.create(
        ruta=ruta,
        comanda=altra,
        tipus=tipus,
        ordre=2,
    )

    resultat = calcula_i_desaa_ordre_ruta(ruta)

    assert set(resultat) == {primera, segona}
    assert sorted(parada.ordre for parada in resultat) == [1, 2]


def test_multiples_llibre_intercalats_repecten_la_precedencia(
    repartidor,
    comanda,
):
    ruta = Ruta.objects.create(
        repartidor=repartidor,
        data=date(2026, 11, 24),
    )
    altre = Comanda.objects.create(
        usuari=crea_usuari("altre@example.com"),
        biblioteca=comanda.biblioteca,
    )

    lliurament_un = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.LLIVRAMENT,
        ordre=1,
    )
    recollida_dos = Parada.objects.create(
        ruta=ruta,
        comanda=altre,
        tipus=Parada.Tipus.RECOLLIDA,
        ordre=2,
    )
    recollida_un = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.RECOLLIDA,
        ordre=3,
    )
    lliurament_dos = Parada.objects.create(
        ruta=ruta,
        comanda=altre,
        tipus=Parada.Tipus.LLIVRAMENT,
        ordre=4,
    )

    resultat = calcula_i_desaa_ordre_ruta(ruta)

    posicions = {
        parada.id: index
        for index, parada in enumerate(resultat, start=1)
    }

    assert posicions[recollida_un.id] < posicions[lliurament_un.id]
    assert posicions[recollida_dos.id] < posicions[lliurament_dos.id]


def test_l_algoritme_es_determinista_repetit(repartidor, comanda):
    ruta = Ruta.objects.create(
        repartidor=repartidor,
        data=date(2026, 11, 24),
    )
    recollida = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.RECOLLIDA,
        ordre=8,
    )
    lliurament = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.LLIVRAMENT,
        ordre=3,
    )

    primer_resultat = [
        parada.id
        for parada in calcula_i_desaa_ordre_ruta(ruta)
    ]
    segon_resultat = [
        parada.id
        for parada in calcula_i_desaa_ordre_ruta(ruta)
    ]

    assert primer_resultat == segon_resultat
    assert primer_resultat == [recollida.id, lliurament.id]


def test_persistencia_desada_a_la_base_de_dades(repartidor, comanda):
    ruta = Ruta.objects.create(
        repartidor=repartidor,
        data=date(2026, 11, 24),
    )
    lliurament = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.LLIVRAMENT,
        ordre=9,
    )
    recollida = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.RECOLLIDA,
        ordre=7,
    )

    calcula_i_desaa_ordre_ruta(ruta)

    recollida.refresh_from_db()
    lliurament.refresh_from_db()
    assert recollida.ordre == 1
    assert lliurament.ordre == 2
    assert list(ruta.parades.all()) == [recollida, lliurament]


def test_llivraments_sense_recollida_no_es_poden_liar(repartidor, comanda):
    ruta = Ruta.objects.create(
        repartidor=repartidor,
        data=date(2026, 11, 24),
    )
    lliurament = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.LLIVRAMENT,
        ordre=1,
    )

    resultat = calcula_i_desaa_ordre_ruta(ruta)

    assert resultat == [lliurament]


def test_recollides_sense_lliurament_no_es_trenca(repartidor, comanda):
    ruta = Ruta.objects.create(
        repartidor=repartidor,
        data=date(2026, 11, 24),
    )
    recollida = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.RECOLLIDA,
        ordre=1,
    )

    resultat = calcula_i_desaa_ordre_ruta(ruta)

    assert resultat == [recollida]


def test_parades_duplicades_del_mateix_tipus_llancen_error_explit(
    comanda,
):
    recollida_un = Parada(
        comanda=comanda,
        tipus=Parada.Tipus.RECOLLIDA,
    )
    recollida_un.id = 1
    recollida_dos = Parada(
        comanda=comanda,
        tipus=Parada.Tipus.RECOLLIDA,
    )
    recollida_dos.id = 2

    with pytest.raises(DadesRutaInconsistents):
        ordena_parades([recollida_un, recollida_dos])

def test_la_precedencia_guanya_al_criteri_secundari(repartidor, comanda):
    ruta = Ruta.objects.create(
        repartidor=repartidor,
        data=date(2026, 11, 24),
    )
    comanda.hora_inici_lliurament = time(8, 0)
    comanda.save(update_fields=["hora_inici_lliurament"])

    lliurament = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.LLIVRAMENT,
        ordre=1,
    )
    recollida = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.RECOLLIDA,
        ordre=2,
    )

    resultat = calcula_i_desaa_ordre_ruta(ruta)

    posicions = {
        parada.id: index
        for index, parada in enumerate(resultat, start=1)
    }
    assert posicions[recollida.id] < posicions[lliurament.id]


def test_tres_comandes_intercalades_tenen_precedencia(repartidor, comanda):
    ruta = Ruta.objects.create(
        repartidor=repartidor,
        data=date(2026, 11, 24),
    )
    altres = [
        Comanda.objects.create(
            usuari=crea_usuari(f"lector-{index}@example.com"),
            biblioteca=comanda.biblioteca,
        )
        for index in range(2)
    ]
    comandes = [comanda, *altres]

    parades = []
    for index, comanda_actual in enumerate(comandes):
        parades.append(
            Parada.objects.create(
                ruta=ruta,
                comanda=comanda_actual,
                tipus=Parada.Tipus.LLIVRAMENT,
                ordre=index + 1,
            )
        )
        parades.append(
            Parada.objects.create(
                ruta=ruta,
                comanda=comanda_actual,
                tipus=Parada.Tipus.RECOLLIDA,
                ordre=index + 4,
            )
        )

    resultat = calcula_i_desaa_ordre_ruta(ruta)
    posicions = {
        parada.id: index
        for index, parada in enumerate(resultat, start=1)
    }

    for comanda_actual in comandes:
        recollida = next(
            parada
            for parada in parades
            if parada.comanda_id == comanda_actual.id
            and parada.tipus == Parada.Tipus.RECOLLIDA
        )
        lliurament = next(
            parada
            for parada in parades
            if parada.comanda_id == comanda_actual.id
            and parada.tipus == Parada.Tipus.LLIVRAMENT
        )
        assert posicions[recollida.id] < posicions[lliurament.id]
