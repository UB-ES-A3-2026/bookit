"""Tests de la creació dels préstecs quan es lliura una comanda (US19-T9).

Quan una comanda passa a "lliurada", `canvia_estat` crea un préstec per cada
llibre, en la mateixa transacció que el canvi d'estat.
"""

from datetime import timedelta
from unittest import mock

import pytest
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from cataleg.models import ExemplarBiblioteca, Llibre
from prestecs.models import TRANSICIONS, Comanda, Prestec
from prestecs.serveis import TransicioNoPermesa, canvia_estat, confirma_comanda, text_notificacio
from usuaris.models import Biblioteca, Usuari

Estat = Comanda.Estat


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
    usuari.is_active = True
    usuari.save(update_fields=["is_active"])
    return usuari


@pytest.fixture
def llibres(biblioteca):
    llibres = [
        Llibre.objects.create(titol="La plaça del Diamant", autor="Mercè Rodoreda", isbn="9788429740011"),
        Llibre.objects.create(titol="Solitud", autor="Víctor Català", isbn="9788475882574"),
    ]
    for llibre in llibres:
        ExemplarBiblioteca.objects.create(llibre=llibre, biblioteca=biblioteca, quantitat=3)
    return llibres


@pytest.fixture
def comanda(lector, biblioteca, llibres):
    return confirma_comanda(lector, biblioteca, llibres)


def porta_fins_a_en_cami(comanda):
    canvia_estat(comanda, Estat.PREPARADA)
    canvia_estat(comanda, Estat.EN_CAMI)


@pytest.mark.django_db
def test_en_lliurar_la_comanda_es_crea_un_prestec_per_cada_llibre(comanda, lector, biblioteca, llibres):
    porta_fins_a_en_cami(comanda)

    canvia_estat(comanda, Estat.LLIURADA)

    prestecs = list(Prestec.objects.filter(linia__comanda=comanda).order_by("pk"))
    assert [prestec.llibre for prestec in prestecs] == llibres
    assert all(prestec.usuari == lector for prestec in prestecs)
    assert all(prestec.biblioteca == biblioteca for prestec in prestecs)
    assert all(prestec.data_devolucio is None for prestec in prestecs)


@pytest.mark.django_db
@override_settings(DURADA_PRESTEC_DIES=30)
def test_el_prestec_comenca_el_dia_del_lliurament(comanda):
    porta_fins_a_en_cami(comanda)

    canvia_estat(comanda, Estat.LLIURADA)

    avui = timezone.localdate()
    prestec = Prestec.objects.filter(linia__comanda=comanda).first()
    assert prestec.data_inici == avui
    assert prestec.data_limit == avui + timedelta(days=30)


@pytest.mark.django_db
@override_settings(DURADA_PRESTEC_DIES=14)
def test_la_durada_surt_de_la_configuracio(comanda):
    porta_fins_a_en_cami(comanda)

    canvia_estat(comanda, Estat.LLIURADA)

    prestec = Prestec.objects.filter(linia__comanda=comanda).first()
    assert prestec.data_limit == prestec.data_inici + timedelta(days=14)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("actual", "nou"),
    [
        (actual, nou)
        for actual in Estat.values
        for nou in TRANSICIONS[actual]
        if nou != Estat.LLIURADA
    ],
)
def test_cap_altre_canvi_d_estat_crea_prestecs(comanda, actual, nou):
    Comanda.objects.filter(pk=comanda.pk).update(estat=actual)

    canvia_estat(comanda, nou)

    assert not Prestec.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("actual", [Estat.REBUDA, Estat.PREPARADA, Estat.CANCELLADA])
def test_un_lliurament_no_permes_no_crea_prestecs(comanda, actual):
    Comanda.objects.filter(pk=comanda.pk).update(estat=actual)

    with pytest.raises(TransicioNoPermesa):
        canvia_estat(comanda, Estat.LLIURADA)

    assert not Prestec.objects.exists()


@pytest.mark.django_db
def test_una_comanda_lliurada_no_es_pot_tornar_a_lliurar_ni_duplica_prestecs(comanda, llibres):
    porta_fins_a_en_cami(comanda)
    canvia_estat(comanda, Estat.LLIURADA)

    with pytest.raises(TransicioNoPermesa):
        canvia_estat(comanda, Estat.LLIURADA)

    assert Prestec.objects.filter(linia__comanda=comanda).count() == len(llibres)


@pytest.mark.django_db
def test_si_no_es_poden_crear_els_prestecs_la_comanda_no_queda_lliurada(comanda):
    porta_fins_a_en_cami(comanda)
    canvis_abans = comanda.canvis_estat.count()
    notificacions_abans = comanda.notificacions.count()

    with mock.patch("prestecs.serveis.Prestec.objects.create", side_effect=RuntimeError("error de prova")):
        with pytest.raises(RuntimeError):
            canvia_estat(comanda, Estat.LLIURADA)

    comanda.refresh_from_db()
    assert comanda.estat == Estat.EN_CAMI
    assert comanda.canvis_estat.count() == canvis_abans
    assert comanda.notificacions.count() == notificacions_abans
    assert not Prestec.objects.exists()


@pytest.mark.django_db
def test_cada_comanda_crea_nomes_els_seus_prestecs(lector, biblioteca, llibres):
    primera = confirma_comanda(lector, biblioteca, [llibres[0]])
    segona = confirma_comanda(lector, biblioteca, [llibres[1]])
    porta_fins_a_en_cami(primera)
    porta_fins_a_en_cami(segona)

    canvia_estat(primera, Estat.LLIURADA)

    assert list(Prestec.objects.values_list("llibre", flat=True)) == [llibres[0].pk]


@pytest.mark.django_db
def test_el_recorregut_complet_a_traves_de_l_api(lector, biblioteca, llibres):
    client = APIClient()
    client.force_authenticate(lector)
    confirmada = client.post(
        "/api/prestecs/comandes/",
        {"biblioteca": biblioteca.pk, "llibres": [llibre.pk for llibre in llibres]},
        format="json",
    )
    comanda = Comanda.objects.get(pk=confirmada.json()["id"])
    porta_fins_a_en_cami(comanda)
    assert client.get("/api/prestecs/prestecs/").json() == []

    canvia_estat(comanda, Estat.LLIURADA)

    prestecs = client.get("/api/prestecs/prestecs/").json()
    assert [prestec["llibre"]["titol"] for prestec in prestecs] == ["La plaça del Diamant", "Solitud"]
    assert all(prestec["biblioteca"]["nom"] == "Biblioteca Montbau" for prestec in prestecs)
    assert all(prestec["termini_superat"] is False for prestec in prestecs)
    assert client.get("/api/prestecs/notificacions/").json()[0]["text"] == text_notificacio(Estat.LLIURADA)
