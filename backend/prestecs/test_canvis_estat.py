"""Tests dels canvis d'estat de la comanda (US8-T1)."""

import pytest

from cataleg.models import ExemplarBiblioteca, Llibre
from prestecs.models import CanviEstat, Comanda
from prestecs.serveis import TransicioNoPermesa, canvia_estat, confirma_comanda
from usuaris.models import Biblioteca, Usuari

Estat = Comanda.Estat

PERMESOS = [
    (Estat.REBUDA, Estat.PREPARADA),
    (Estat.REBUDA, Estat.CANCELLADA),
    (Estat.PREPARADA, Estat.EN_CAMI),
    (Estat.PREPARADA, Estat.CANCELLADA),
    (Estat.EN_CAMI, Estat.LLIURADA),
    (Estat.EN_CAMI, Estat.PREPARADA),
]
PROHIBITS = [
    (actual, nou)
    for actual in Estat.values
    for nou in Estat.values
    if (actual, nou) not in PERMESOS
]


def crea_usuari(correu, rol=Usuari.Role.USUARI):
    return Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {"name": correu.split("@")[0], "address": "C/ Major 1", "library_card_number": correu, "role": rol},
    )


@pytest.fixture
def biblioteca():
    usuari = crea_usuari("biblioteca@example.com", Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=usuari, nom="Biblioteca Montbau")
    usuari.is_active = True
    usuari.save(update_fields=["is_active"])
    return usuari


@pytest.fixture
def comanda(biblioteca):
    llibre = Llibre.objects.create(titol="Solitud", autor="Víctor Català", isbn="9788475882574")
    ExemplarBiblioteca.objects.create(llibre=llibre, biblioteca=biblioteca, quantitat=1)
    return confirma_comanda(crea_usuari("lector@example.com"), biblioteca, [llibre])


def historial(comanda):
    return list(comanda.canvis_estat.values_list("estat", flat=True))


def amb_estat(comanda, estat):
    Comanda.objects.filter(pk=comanda.pk).update(estat=estat)
    comanda.refresh_from_db()
    return comanda


@pytest.mark.django_db
def test_en_confirmar_la_comanda_l_historial_comenca_amb_rebuda(comanda):
    assert comanda.estat == Estat.REBUDA
    assert historial(comanda) == [Estat.REBUDA]


@pytest.mark.django_db
def test_el_recorregut_complet_d_una_comanda(comanda):
    for estat in (Estat.PREPARADA, Estat.EN_CAMI, Estat.LLIURADA):
        canvia_estat(comanda, estat)

    comanda.refresh_from_db()
    assert comanda.estat == Estat.LLIURADA
    assert historial(comanda) == ["rebuda", "preparada", "en_cami", "lliurada"]


@pytest.mark.django_db
@pytest.mark.parametrize("actual, nou", PERMESOS)
def test_canvis_permesos(comanda, actual, nou):
    amb_estat(comanda, actual)

    canvia_estat(comanda, nou)

    assert comanda.estat == nou
    assert Comanda.objects.get(pk=comanda.pk).estat == nou
    assert historial(comanda)[-1] == nou


@pytest.mark.django_db
@pytest.mark.parametrize("actual, nou", PROHIBITS)
def test_canvis_no_permesos(comanda, actual, nou):
    amb_estat(comanda, actual)
    registres = CanviEstat.objects.count()

    with pytest.raises(TransicioNoPermesa) as error:
        canvia_estat(comanda, nou)

    assert (error.value.estat_actual, error.value.nou_estat) == (actual, nou)
    assert Comanda.objects.get(pk=comanda.pk).estat == actual
    assert CanviEstat.objects.count() == registres


@pytest.mark.django_db
def test_una_parada_fallida_torna_la_comanda_a_preparada(comanda):
    canvia_estat(comanda, Estat.PREPARADA)
    canvia_estat(comanda, Estat.EN_CAMI)

    canvia_estat(comanda, Estat.PREPARADA)

    assert historial(comanda) == ["rebuda", "preparada", "en_cami", "preparada"]


@pytest.mark.django_db
def test_es_fa_servir_l_estat_de_la_base_de_dades_i_no_el_de_la_copia(comanda):
    """Una còpia antiga de la comanda no permet saltar-se l'estat real."""
    copia_antiga = Comanda.objects.get(pk=comanda.pk)
    canvia_estat(comanda, Estat.CANCELLADA)

    with pytest.raises(TransicioNoPermesa):
        canvia_estat(copia_antiga, Estat.PREPARADA)

    assert Comanda.objects.get(pk=comanda.pk).estat == Estat.CANCELLADA


@pytest.mark.django_db
def test_pot_passar_a(comanda):
    assert comanda.pot_passar_a(Estat.PREPARADA)
    assert not comanda.pot_passar_a(Estat.LLIURADA)


@pytest.mark.django_db
def test_en_esborrar_la_comanda_s_esborra_el_seu_historial(comanda):
    comanda.delete()

    assert not CanviEstat.objects.exists()
