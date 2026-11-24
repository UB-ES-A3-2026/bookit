"""Tests del model d'adreça de lliurament (US3-T1)."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from usuaris.models import Adreca, Usuari


def crear_usuari(**camps):
    dades = {
        "email": "anna@example.com",
        "password": "una-contrasenya-segura",
        "name": "Anna Puig",
        "address": "C/ Major 1, 08001 Barcelona",
        "library_card_number": "1234567890",
    }
    return Usuari.objects.create_user(**(dades | camps))


@pytest.mark.django_db
def test_es_pot_crear_una_adreca_associada_a_un_usuari():
    usuari = crear_usuari()

    adreca = Adreca.objects.create(
        usuari=usuari,
        municipi="Barcelona",
        carrer="C/ Major 1",
        pis="2n A",
    )

    assert adreca.pk is not None
    assert adreca.usuari == usuari
    assert adreca.predeterminada is False
    assert str(adreca) == "C/ Major 1, pis 2n A, Barcelona"


@pytest.mark.django_db
def test_un_usuari_pot_tenir_diverses_adreces_no_predeterminades():
    usuari = crear_usuari()

    primera = Adreca.objects.create(
        usuari=usuari,
        municipi="Barcelona",
        carrer="C/ Major 1",
        pis="1r",
    )
    segona = Adreca.objects.create(
        usuari=usuari,
        municipi="Sabadell",
        carrer="C/ Nova 20",
        pis="3t",
        predeterminada=False,
    )

    assert usuari.adreces.count() == 2
    assert set(usuari.adreces.values_list("pk", flat=True)) == {
        primera.pk,
        segona.pk,
    }
    assert usuari.adreces.filter(predeterminada=True).count() == 0


@pytest.mark.django_db
def test_un_usuari_no_pot_tenir_dues_adreces_predeterminades():
    usuari = crear_usuari()

    Adreca.objects.create(
        usuari=usuari,
        municipi="Barcelona",
        carrer="C/ Major 1",
        pis="1r",
        predeterminada=True,
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Adreca.objects.create(
                usuari=usuari,
                municipi="Girona",
                carrer="C/ Nou 5",
                pis="2n",
                predeterminada=True,
            )


@pytest.mark.django_db
def test_usuaris_diferents_poden_tenir_cadascun_una_adreca_predeterminada():
    usuari = crear_usuari()
    altre_usuari = crear_usuari(
        email="pere@example.com",
        name="Pere Vila",
        library_card_number="0987654321",
    )

    Adreca.objects.create(
        usuari=usuari,
        municipi="Barcelona",
        carrer="C/ Major 1",
        pis="1r",
        predeterminada=True,
    )
    Adreca.objects.create(
        usuari=altre_usuari,
        municipi="Girona",
        carrer="C/ Nou 5",
        pis="2n",
        predeterminada=True,
    )

    assert usuari.adreces.filter(predeterminada=True).count() == 1
    assert altre_usuari.adreces.filter(predeterminada=True).count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize("camp", ["municipi", "carrer", "pis"])
def test_camps_obligatoris_buits_es_rebutgen(camp):
    usuari = crear_usuari()
    dades = {
        "usuari": usuari,
        "municipi": "Barcelona",
        "carrer": "C/ Major 1",
        "pis": "1r",
    }
    dades[camp] = ""

    adreca = Adreca(**dades)

    with pytest.raises(ValidationError):
        adreca.full_clean()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("camp", "longitud_maxima"),
    [
        ("municipi", 100),
        ("carrer", 255),
        ("pis", 20),
    ],
)
def test_camps_amb_longitud_excessiva_es_rebutgen(camp, longitud_maxima):
    usuari = crear_usuari()
    dades = {
        "usuari": usuari,
        "municipi": "Barcelona",
        "carrer": "C/ Major 1",
        "pis": "1r",
    }
    dades[camp] = "X" * (longitud_maxima + 1)

    adreca = Adreca(**dades)

    with pytest.raises(ValidationError):
        adreca.full_clean()

@pytest.mark.django_db
@pytest.mark.parametrize(
    "camp",
    ["municipi", "carrer", "pis", "codi_postal"],
)
def test_camps_obligatoris_buits_es_rebutgen(camp):
    usuari = crear_usuari()
    dades = {
        "usuari": usuari,
        "municipi": "Barcelona",
        "carrer": "C/ Major 1",
        "pis": "1r",
        "codi_postal": "08001",
    }
    dades[camp] = ""

    adreca = Adreca(**dades)

    with pytest.raises(ValidationError):
        adreca.full_clean()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("camp", "longitud_maxima"),
    [
        ("municipi", 100),
        ("carrer", 255),
        ("pis", 20),
        ("codi_postal", 5),
    ],
)
def test_camps_amb_longitud_excessiva_es_rebutgen(camp, longitud_maxima):
    usuari = crear_usuari()
    dades = {
        "usuari": usuari,
        "municipi": "Barcelona",
        "carrer": "C/ Major 1",
        "pis": "1r",
        "codi_postal": "08001",
    }
    dades[camp] = "X" * (longitud_maxima + 1)

    adreca = Adreca(**dades)

    with pytest.raises(ValidationError):
        adreca.full_clean()
