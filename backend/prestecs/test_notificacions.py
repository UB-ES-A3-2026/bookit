"""Tests de les notificacions de cada canvi d'estat de la comanda (US8-T2)."""

import pytest

from cataleg.models import ExemplarBiblioteca, Llibre
from prestecs.models import Comanda, LiniaComanda, Notificacio
from prestecs.serveis import LlibresSenseEstoc, TransicioNoPermesa, canvia_estat, confirma_comanda
from usuaris.models import Biblioteca, Usuari

Estat = Comanda.Estat

REBUDA = "La teva comanda s'ha rebut correctament. La biblioteca ja l'està preparant"
PREPARADA = "La teva comanda ja està preparada i aviat sortirà cap a casa teva"
LLIURADA = "La teva comanda s'ha lliurat correctament. Gaudeix del teu llibre!"


def crea_usuari(correu, rol=Usuari.Role.USUARI, nom=None):
    return Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {"name": nom or correu.split("@")[0], "address": "C/ Major 1", "library_card_number": correu, "role": rol},
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
def repartidor():
    return crea_usuari("repartidor@example.com", Usuari.Role.REPARTIDOR, nom="Jordi")


@pytest.fixture
def comanda(lector, biblioteca):
    comanda = Comanda.objects.create(usuari=lector, biblioteca=biblioteca)
    llibre = Llibre.objects.create(titol="Solitud", autor="Víctor Català", isbn="9788475882574")
    LiniaComanda.objects.create(comanda=comanda, llibre=llibre)
    return comanda


def textos(comanda):
    return list(comanda.notificacions.order_by("creada", "id").values_list("text", flat=True))


@pytest.mark.django_db
def test_confirmar_la_comanda_avisa_que_s_ha_rebut(lector, biblioteca):
    llibre = Llibre.objects.create(titol="Solitud", autor="Víctor Català", isbn="9788475882574")
    ExemplarBiblioteca.objects.create(llibre=llibre, biblioteca=biblioteca, quantitat=1)

    comanda = confirma_comanda(lector, biblioteca, [llibre])

    notificacio = Notificacio.objects.get()
    assert notificacio.usuari == lector
    assert notificacio.comanda == comanda
    assert notificacio.text == REBUDA
    assert not notificacio.llegida


@pytest.mark.django_db
def test_cada_canvi_d_estat_crea_la_seva_notificacio(comanda, repartidor):
    canvia_estat(comanda, Estat.PREPARADA)
    canvia_estat(comanda, Estat.EN_CAMI, repartidor=repartidor)
    canvia_estat(comanda, Estat.LLIURADA)

    assert textos(comanda) == [
        PREPARADA,
        "En/Na Jordi ja porta la teva comanda. Està en camí!",
        LLIURADA,
    ]


@pytest.mark.django_db
def test_la_notificacio_es_per_a_l_usuari_de_la_comanda(comanda, lector):
    canvia_estat(comanda, Estat.PREPARADA)

    assert list(lector.notificacions.values_list("text", flat=True)) == [PREPARADA]


@pytest.mark.django_db
def test_en_cami_sense_repartidor_no_en_diu_el_nom(comanda):
    canvia_estat(comanda, Estat.PREPARADA)
    canvia_estat(comanda, Estat.EN_CAMI)

    assert textos(comanda)[-1] == "El repartidor ja porta la teva comanda. Està en camí!"


@pytest.mark.django_db
def test_cancellar_avisa_l_usuari(comanda):
    canvia_estat(comanda, Estat.CANCELLADA)

    assert textos(comanda) == ["La teva comanda s'ha cancel·lat."]


@pytest.mark.django_db
def test_si_la_parada_falla_torna_a_avisar_que_esta_preparada(comanda, repartidor):
    canvia_estat(comanda, Estat.PREPARADA)
    canvia_estat(comanda, Estat.EN_CAMI, repartidor=repartidor)
    canvia_estat(comanda, Estat.PREPARADA)

    assert textos(comanda)[-1] == PREPARADA
    assert comanda.notificacions.count() == 3


@pytest.mark.django_db
def test_un_canvi_no_permes_no_crea_cap_notificacio(comanda):
    with pytest.raises(TransicioNoPermesa):
        canvia_estat(comanda, Estat.LLIURADA)

    assert not comanda.notificacions.exists()


@pytest.mark.django_db
def test_si_falta_estoc_no_es_crea_cap_notificacio(lector, biblioteca):
    llibre = Llibre.objects.create(titol="Solitud", autor="Víctor Català", isbn="9788475882574")
    ExemplarBiblioteca.objects.create(llibre=llibre, biblioteca=biblioteca, quantitat=0)

    with pytest.raises(LlibresSenseEstoc):
        confirma_comanda(lector, biblioteca, [llibre])

    assert not Notificacio.objects.exists()


@pytest.mark.django_db
def test_les_notificacions_surten_de_la_mes_nova_a_la_mes_antiga(comanda, lector):
    canvia_estat(comanda, Estat.PREPARADA)
    canvia_estat(comanda, Estat.CANCELLADA)

    assert list(lector.notificacions.values_list("text", flat=True)) == [
        "La teva comanda s'ha cancel·lat.",
        PREPARADA,
    ]


@pytest.mark.django_db
def test_en_esborrar_la_comanda_s_esborren_les_notificacions(comanda):
    canvia_estat(comanda, Estat.PREPARADA)

    comanda.delete()

    assert not Notificacio.objects.exists()


@pytest.mark.django_db
def test_el_text_de_la_notificacio_diu_l_usuari_i_el_missatge(comanda):
    canvia_estat(comanda, Estat.PREPARADA)

    assert str(comanda.notificacions.get()) == f"lector: {PREPARADA}"
