import pytest
from django.db import IntegrityError, transaction

from cataleg.models import LlistaEspera, Llibre
from usuaris.models import Usuari


pytestmark = pytest.mark.django_db


@pytest.fixture
def usuari():
    return Usuari.objects.create_user(
        email="usuari@example.com",
        password="ContrasenyaSegura123!",
        name="Usuari de prova",
        address="Carrer Major, 1",
        library_card_number="USR-001",
    )


@pytest.fixture
def llibre():
    return Llibre.objects.create(
        titol="La plaça del Diamant",
        autor="Mercè Rodoreda",
        isbn="9788429740011",
    )


@pytest.fixture
def altre_llibre():
    return Llibre.objects.create(
        titol="Un altre llibre",
        autor="Autor de prova",
        isbn="9788429740028",
    )


def test_es_pot_crear_una_entrada_a_la_llista_despera(usuari, llibre):
    entrada = LlistaEspera.objects.create(usuari=usuari, llibre=llibre)

    assert entrada.usuari == usuari
    assert entrada.llibre == llibre


def test_un_usuari_no_es_pot_apuntar_dues_vegades_al_mateix_llibre(
    usuari,
    llibre,
):
    LlistaEspera.objects.create(usuari=usuari, llibre=llibre)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            LlistaEspera.objects.create(usuari=usuari, llibre=llibre)


def test_un_usuari_es_pot_apuntar_a_llibre_diferents(
    usuari,
    llibre,
    altre_llibre,
):
    LlistaEspera.objects.create(usuari=usuari, llibre=llibre)
    altra_entrada = LlistaEspera.objects.create(
        usuari=usuari,
        llibre=altre_llibre,
    )

    assert LlistaEspera.objects.filter(usuari=usuari).count() == 2
    assert altra_entrada.llibre == altre_llibre


def test_diferents_usuaris_es_poden_apuntar_al_mateix_llibre(llibre):
    primer = Usuari.objects.create_user(
        email="primer@example.com",
        password="ContrasenyaSegura123!",
        name="Primer usuari",
        address="Carrer Primer, 1",
        library_card_number="USR-101",
    )
    segon = Usuari.objects.create_user(
        email="segon@example.com",
        password="ContrasenyaSegura123!",
        name="Segon usuari",
        address="Carrer Segon, 2",
        library_card_number="USR-102",
    )

    LlistaEspera.objects.create(usuari=primer, llibre=llibre)
    LlistaEspera.objects.create(usuari=segon, llibre=llibre)

    assert LlistaEspera.objects.filter(llibre=llibre).count() == 2


def test_la_data_alta_somple_automaticament(usuari, llibre):
    entrada = LlistaEspera.objects.create(usuari=usuari, llibre=llibre)

    assert entrada.data_alta is not None


def test_esborrar_lusuari_esborra_s_entrades_a_la_llista(usuari, llibre):
    entrada = LlistaEspera.objects.create(usuari=usuari, llibre=llibre)

    usuari.delete()

    assert not LlistaEspera.objects.filter(pk=entrada.pk).exists()
