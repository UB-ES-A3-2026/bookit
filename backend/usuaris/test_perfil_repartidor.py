"""Tests del model del perfil de repartidor (US1.1-T1)."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from usuaris.models import PerfilRepartidor, Usuari
from usuaris.validacions import (
    DNI_NIE_INVALID,
    MATRICULA_INVALIDA,
    SEGURETAT_SOCIAL_INVALIDA,
    TELEFON_INVALID,
)

pytestmark = pytest.mark.django_db


def crea_usuari(email="anna@example.com", num_carnet="1234567890"):
    return Usuari.objects.create_user(
        email=email,
        password="contrasenya-segura",
        name="Anna",
        address="C/ Major 1, 08001 Barcelona",
        library_card_number=num_carnet,
        role=Usuari.Role.REPARTIDOR,
    )


def dades_perfil(**canvis):
    dades = {
        "cognoms": "Puig Soler",
        "dni": "12345678Z",
        "telefon": "612345678",
        "vehicle": PerfilRepartidor.Vehicle.MOTO,
        "matricula": "1234BCD",
        "num_seguretat_social": "281234567890",
    }
    return {**dades, **canvis}


def test_crea_perfil_vinculat_a_usuari():
    usuari = crea_usuari()

    perfil = PerfilRepartidor.objects.create(usuari=usuari, **dades_perfil())

    assert usuari.perfil_repartidor == perfil
    assert perfil.cognoms == "Puig Soler"


def test_estat_inicial_es_pendent():
    perfil = PerfilRepartidor.objects.create(usuari=crea_usuari(), **dades_perfil())

    assert perfil.estat == PerfilRepartidor.Estat.PENDENT
    assert perfil.get_estat_display() == "Pendent de validació"


def test_perfil_valid_passa_full_clean():
    perfil = PerfilRepartidor(usuari=crea_usuari(), **dades_perfil())

    perfil.full_clean()


def test_bici_sense_matricula_es_valida():
    dades = dades_perfil(vehicle=PerfilRepartidor.Vehicle.BICI)
    del dades["matricula"]
    perfil = PerfilRepartidor(usuari=crea_usuari(), **dades)

    perfil.full_clean()

    assert perfil.matricula == ""


def test_dni_duplicat_no_es_pot_desar():
    PerfilRepartidor.objects.create(usuari=crea_usuari(), **dades_perfil())
    altre_usuari = crea_usuari("pere@example.com", "9876543210")

    with pytest.raises(IntegrityError):
        PerfilRepartidor.objects.create(usuari=altre_usuari, **dades_perfil())


def test_un_usuari_no_pot_tenir_dos_perfils():
    usuari = crea_usuari()
    PerfilRepartidor.objects.create(usuari=usuari, **dades_perfil())

    with pytest.raises(IntegrityError):
        PerfilRepartidor.objects.create(
            usuari=usuari,
            **dades_perfil(dni="X1234567L"),
        )


def test_esborrar_usuari_esborra_el_perfil():
    usuari = crea_usuari()
    PerfilRepartidor.objects.create(usuari=usuari, **dades_perfil())

    usuari.delete()

    assert not PerfilRepartidor.objects.exists()


@pytest.mark.parametrize(
    "camp, valor, missatge",
    [
        ("dni", "12345678A", DNI_NIE_INVALID),
        ("telefon", "512345678", TELEFON_INVALID),
        ("matricula", "1234AEI", MATRICULA_INVALIDA),
        ("num_seguretat_social", "12345", SEGURETAT_SOCIAL_INVALIDA),
    ],
)
def test_format_invalid_no_passa_full_clean(camp, valor, missatge):
    perfil = PerfilRepartidor(usuari=crea_usuari(), **dades_perfil(**{camp: valor}))

    with pytest.raises(ValidationError) as error:
        perfil.full_clean()

    assert missatge in error.value.message_dict[camp]


@pytest.mark.parametrize("camp", ["vehicle", "estat"])
def test_opcio_invalida_no_passa_full_clean(camp):
    perfil = PerfilRepartidor(usuari=crea_usuari(), **dades_perfil(**{camp: "patinet"}))

    with pytest.raises(ValidationError) as error:
        perfil.full_clean()

    assert camp in error.value.message_dict
