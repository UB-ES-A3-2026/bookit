"""Tests dels models de comanda (US6-T1)."""

import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from cataleg.models import Llibre
from prestecs.models import Comanda, LiniaComanda
from usuaris.models import Usuari


def crea_usuari(correu, rol=Usuari.Role.USUARI, carnet="0000000001"):
    return Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {"name": correu.split("@")[0], "address": "C/ Major 1", "library_card_number": carnet, "role": rol},
    )


@pytest.fixture
def lector():
    return crea_usuari("lector@example.com")


@pytest.fixture
def biblioteca():
    return crea_usuari("biblioteca@example.com", Usuari.Role.BIBLIOTECA, "biblioteca-1")


@pytest.fixture
def llibres():
    return [
        Llibre.objects.create(titol="La plaça del Diamant", autor="Mercè Rodoreda", isbn="9788429740011"),
        Llibre.objects.create(titol="Solitud", autor="Víctor Català", isbn="9788475882574"),
    ]


@pytest.fixture
def comanda(lector, biblioteca):
    return Comanda.objects.create(usuari=lector, biblioteca=biblioteca)


@pytest.mark.django_db
def test_una_comanda_nova_queda_en_estat_rebuda(comanda):
    assert comanda.estat == Comanda.Estat.REBUDA
    assert comanda.data_lliurament is None
    assert comanda.creada is not None


@pytest.mark.django_db
def test_una_comanda_pot_tenir_diversos_llibres(comanda, llibres):
    for llibre in llibres:
        LiniaComanda.objects.create(comanda=comanda, llibre=llibre)

    assert comanda.linies.count() == 2
    assert {linia.llibre for linia in comanda.linies.all()} == set(llibres)


@pytest.mark.django_db
def test_un_llibre_no_pot_sortir_dues_vegades_a_la_mateixa_comanda(comanda, llibres):
    LiniaComanda.objects.create(comanda=comanda, llibre=llibres[0])

    with pytest.raises(IntegrityError), transaction.atomic():
        LiniaComanda.objects.create(comanda=comanda, llibre=llibres[0])


@pytest.mark.django_db
def test_el_mateix_llibre_pot_ser_a_comandes_diferents(lector, biblioteca, llibres):
    primera = Comanda.objects.create(usuari=lector, biblioteca=biblioteca)
    segona = Comanda.objects.create(usuari=lector, biblioteca=biblioteca)

    LiniaComanda.objects.create(comanda=primera, llibre=llibres[0])
    LiniaComanda.objects.create(comanda=segona, llibre=llibres[0])

    assert llibres[0].linies_comanda.count() == 2


@pytest.mark.django_db
def test_hi_ha_els_estats_de_la_comanda():
    assert set(Comanda.Estat.values) == {"rebuda", "preparada", "en_cami", "lliurada", "cancellada"}


@pytest.mark.django_db
def test_en_esborrar_una_comanda_s_esborren_les_seves_linies(comanda, llibres):
    LiniaComanda.objects.create(comanda=comanda, llibre=llibres[0])

    comanda.delete()

    assert not LiniaComanda.objects.exists()


@pytest.mark.django_db
def test_no_es_pot_esborrar_un_llibre_que_ha_estat_en_una_comanda(comanda, llibres):
    LiniaComanda.objects.create(comanda=comanda, llibre=llibres[0])

    with pytest.raises(ProtectedError):
        llibres[0].delete()


@pytest.mark.django_db
def test_no_es_pot_esborrar_una_biblioteca_amb_comandes(comanda, biblioteca):
    with pytest.raises(ProtectedError):
        biblioteca.delete()


@pytest.mark.django_db
def test_les_comandes_d_un_usuari_i_d_una_biblioteca(comanda, lector, biblioteca):
    assert list(lector.comandes.all()) == [comanda]
    assert list(biblioteca.comandes_biblioteca.all()) == [comanda]


@pytest.mark.django_db
def test_les_comandes_surten_de_la_mes_nova_a_la_mes_antiga(lector, biblioteca):
    antiga = Comanda.objects.create(usuari=lector, biblioteca=biblioteca)
    nova = Comanda.objects.create(usuari=lector, biblioteca=biblioteca)

    assert list(Comanda.objects.all()) == [nova, antiga]


@pytest.mark.django_db
def test_el_text_de_la_comanda_diu_l_usuari_i_l_estat(comanda):
    assert str(comanda) == f"Comanda {comanda.pk} de {comanda.usuari} (Rebuda)"
