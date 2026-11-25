"""Tests del model de préstec i de la creació dels préstecs d'una comanda (US19-T1)."""

from datetime import date

import pytest
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.test import override_settings

from cataleg.models import Llibre
from prestecs.models import Comanda, LiniaComanda, Prestec
from prestecs.serveis import crea_prestecs
from usuaris.models import Biblioteca, Usuari


def crea_usuari(correu, rol=Usuari.Role.USUARI):
    return Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {"name": correu.split("@")[0], "address": "C/ Major 1", "library_card_number": correu, "role": rol},
    )


@pytest.fixture
def lector():
    return crea_usuari("lector@example.com")


@pytest.fixture
def biblioteca():
    usuari = crea_usuari("biblioteca@example.com", Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=usuari, nom="Biblioteca Montbau")
    return usuari


@pytest.fixture
def llibres():
    return [
        Llibre.objects.create(titol="La plaça del Diamant", autor="Mercè Rodoreda", isbn="9788429740011"),
        Llibre.objects.create(titol="Solitud", autor="Víctor Català", isbn="9788475882574"),
    ]


@pytest.fixture
def comanda(lector, biblioteca, llibres):
    comanda = Comanda.objects.create(usuari=lector, biblioteca=biblioteca, estat=Comanda.Estat.LLIURADA)
    for llibre in llibres:
        LiniaComanda.objects.create(comanda=comanda, llibre=llibre)
    return comanda


def crea_prestec(comanda, data_limit, data_devolucio=None, data_inici=date(2026, 11, 1)):
    linia = comanda.linies.first()
    return Prestec.objects.create(
        linia=linia,
        usuari=comanda.usuari,
        llibre=linia.llibre,
        biblioteca=comanda.biblioteca,
        data_inici=data_inici,
        data_limit=data_limit,
        data_devolucio=data_devolucio,
    )


@pytest.mark.django_db
@override_settings(DURADA_PRESTEC_DIES=30)
def test_crea_un_prestec_per_cada_llibre_de_la_comanda(comanda, lector, biblioteca, llibres):
    prestecs = crea_prestecs(comanda, data_inici=date(2026, 11, 18))

    assert [prestec.llibre for prestec in prestecs] == llibres
    for prestec in prestecs:
        assert prestec.usuari == lector
        assert prestec.biblioteca == biblioteca
        assert prestec.data_inici == date(2026, 11, 18)
        assert prestec.data_limit == date(2026, 12, 18)
        assert not prestec.retornat


@pytest.mark.django_db
@override_settings(DURADA_PRESTEC_DIES=14)
def test_la_durada_del_prestec_es_configurable(comanda):
    prestecs = crea_prestecs(comanda, data_inici=date(2026, 12, 25))

    assert prestecs[0].data_limit == date(2027, 1, 8)


@pytest.mark.django_db
def test_sense_data_el_prestec_comenca_avui(comanda, monkeypatch):
    avui = date(2026, 11, 18)
    monkeypatch.setattr("prestecs.serveis.timezone.localdate", lambda: avui)

    prestecs = crea_prestecs(comanda)

    assert prestecs[0].data_inici == avui


@pytest.mark.django_db
def test_crear_els_prestecs_dues_vegades_no_els_duplica(comanda):
    primers = crea_prestecs(comanda, data_inici=date(2026, 11, 18))
    segons = crea_prestecs(comanda, data_inici=date(2026, 11, 20))

    assert Prestec.objects.count() == 2
    assert {prestec.pk for prestec in segons} == {prestec.pk for prestec in primers}
    assert segons[0].data_inici == date(2026, 11, 18)


@pytest.mark.django_db
def test_una_linia_nomes_pot_tenir_un_prestec(comanda):
    crea_prestec(comanda, data_limit=date(2026, 12, 1))

    with pytest.raises(IntegrityError):
        crea_prestec(comanda, data_limit=date(2026, 12, 1))


@pytest.mark.django_db
def test_la_data_limit_no_pot_ser_anterior_a_l_inici(comanda):
    with pytest.raises(IntegrityError):
        crea_prestec(comanda, data_inici=date(2026, 11, 18), data_limit=date(2026, 11, 17))


@pytest.mark.django_db
def test_el_termini_esta_superat_si_ha_passat_la_data_limit(comanda):
    prestec = crea_prestec(comanda, data_limit=date(2026, 11, 17))

    assert prestec.termini_superat(avui=date(2026, 11, 18))


@pytest.mark.django_db
def test_el_dia_de_la_data_limit_encara_no_esta_superat(comanda):
    prestec = crea_prestec(comanda, data_limit=date(2026, 11, 18))

    assert not prestec.termini_superat(avui=date(2026, 11, 18))


@pytest.mark.django_db
def test_un_llibre_retornat_no_te_el_termini_superat(comanda):
    prestec = crea_prestec(comanda, data_limit=date(2026, 11, 10), data_devolucio=date(2026, 11, 12))

    assert prestec.retornat
    assert not prestec.termini_superat(avui=date(2026, 11, 18))


@pytest.mark.django_db
def test_els_prestecs_surten_per_data_limit(lector, biblioteca, llibres):
    comandes = []
    for _ in range(3):
        comanda = Comanda.objects.create(usuari=lector, biblioteca=biblioteca)
        LiniaComanda.objects.create(comanda=comanda, llibre=llibres[0])
        comandes.append(comanda)
    tard = crea_prestec(comandes[0], data_limit=date(2026, 12, 20))
    aviat = crea_prestec(comandes[1], data_limit=date(2026, 11, 25))
    mig = crea_prestec(comandes[2], data_limit=date(2026, 12, 5))

    assert list(lector.prestecs.all()) == [aviat, mig, tard]


@pytest.mark.django_db
def test_no_es_pot_esborrar_una_linia_amb_prestec(comanda):
    prestec = crea_prestec(comanda, data_limit=date(2026, 12, 1))

    with pytest.raises(ProtectedError):
        prestec.linia.delete()


@pytest.mark.django_db
def test_el_text_del_prestec_diu_el_llibre_l_usuari_i_la_data_limit(comanda):
    prestec = crea_prestec(comanda, data_limit=date(2026, 12, 1))

    assert str(prestec) == "La plaça del Diamant a lector fins al 01/12/2026"
