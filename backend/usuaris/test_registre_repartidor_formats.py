"""Tests dels formats, duplicats i matrícula del registre de repartidor (US1.1-T6)."""

import pytest

from usuaris.models import PerfilRepartidor, Usuari
from usuaris.test_registre_repartidor import (
    JA_REGISTRAT,
    OBLIGATORI,
    URL,
    dades_valides,
)
from usuaris.validacions import (
    DNI_NIE_INVALID,
    MATRICULA_INVALIDA,
    SEGURETAT_SOCIAL_INVALIDA,
    TELEFON_INVALID,
)

CORREU_INVALID = "Introduïu una adreça de correu electrònic vàlida."
VEHICLE_INVALID = '"bici", "moto" o "cotxe" no és una opció vàlida.'


def registra(client, **canvis):
    return client.post(
        URL, dades_valides(**canvis), content_type="application/json"
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "dni",
    [
        "12345678A",  # lletra de control incorrecta
        "1234567Z",  # 7 xifres
        "123456789Z",  # 9 xifres
        "123456789",  # sense lletra
        "A1234567L",  # prefix de NIE que no existeix
        "X1234567A",  # NIE amb lletra de control incorrecta
        "X123456L",  # NIE amb 6 xifres
    ],
)
def test_dni_o_nie_invalid_retorna_400(client, dni):
    resposta = registra(client, dni=dni)

    assert resposta.status_code == 400
    assert resposta.json() == {"dni": [DNI_NIE_INVALID]}
    assert not Usuari.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("dni", "desat"),
    [
        ("00000000T", "00000000T"),
        ("X1234567L", "X1234567L"),
        ("Y1234567X", "Y1234567X"),
        ("Z1234567R", "Z1234567R"),
        ("12345678z", "12345678Z"),  # minúscula
        ("12 345 678-Z", "12345678Z"),  # separadors
        ("x/1234567/l", "X1234567L"),
    ],
)
def test_dni_o_nie_valid_es_desa_normalitzat(client, dni, desat):
    resposta = registra(client, dni=dni)

    assert resposta.status_code == 201
    assert resposta.json()["dni"] == desat


@pytest.mark.django_db
@pytest.mark.parametrize(
    "telefon",
    [
        "512345678",  # no comença per 6, 7, 8 ni 9
        "61234567",  # 8 xifres
        "6123456789",  # 10 xifres
        "61234567a",  # lletra
        "+33612345678",  # prefix d'un altre país
        "+34512345678",  # prefix correcte, però comença per 5
    ],
)
def test_telefon_invalid_retorna_400(client, telefon):
    resposta = registra(client, telefon=telefon)

    assert resposta.status_code == 400
    assert resposta.json() == {"telefon": [TELEFON_INVALID]}
    assert not Usuari.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("telefon", "desat"),
    [
        ("612345678", "612345678"),
        ("712345678", "712345678"),
        ("812345678", "812345678"),
        ("912345678", "912345678"),
        ("+34612345678", "+34612345678"),
        ("612-345/678", "612345678"),
    ],
)
def test_telefon_valid_es_desa_normalitzat(client, telefon, desat):
    resposta = registra(client, telefon=telefon)

    assert resposta.status_code == 201
    assert resposta.json()["telefon"] == desat


@pytest.mark.django_db
@pytest.mark.parametrize(
    "correu",
    [
        "no-es-un-correu",
        "pol@",
        "@example.com",
        "pol@example",
        "pol ferrer@example.com",
    ],
)
def test_correu_invalid_retorna_400(client, correu):
    resposta = registra(client, correu=correu)

    assert resposta.status_code == 400
    assert resposta.json() == {"correu": [CORREU_INVALID]}
    assert not Usuari.objects.exists()


@pytest.mark.django_db
def test_correu_es_desa_en_minuscules(client):
    resposta = registra(client, correu="Pol.Ferrer@Example.com")

    assert resposta.status_code == 201
    assert resposta.json()["correu"] == "pol.ferrer@example.com"


@pytest.mark.django_db
@pytest.mark.parametrize("num_seguretat_social", ["1234", "1234567890123", "12345678901A"])
def test_seguretat_social_invalida_retorna_400(client, num_seguretat_social):
    resposta = registra(client, num_seguretat_social=num_seguretat_social)

    assert resposta.status_code == 400
    assert resposta.json() == {"num_seguretat_social": [SEGURETAT_SOCIAL_INVALIDA]}
    assert not Usuari.objects.exists()


@pytest.mark.django_db
def test_amb_diversos_formats_invalids_es_retornen_tots(client):
    resposta = registra(
        client, correu="no-es-un-correu", dni="12345678A", telefon="512345678"
    )

    assert resposta.status_code == 400
    assert resposta.json() == {
        "correu": [CORREU_INVALID],
        "dni": [DNI_NIE_INVALID],
        "telefon": [TELEFON_INVALID],
    }


@pytest.mark.django_db
def test_vehicle_invalid_retorna_400(client):
    resposta = registra(client, vehicle="patinet")

    assert resposta.status_code == 400
    assert resposta.json() == {"vehicle": [VEHICLE_INVALID]}
    assert not Usuari.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("vehicle", ["moto", "cotxe"])
def test_vehicle_de_motor_amb_matricula_es_registra(client, vehicle):
    resposta = registra(client, vehicle=vehicle, matricula="1234-bcd")

    assert resposta.status_code == 201
    assert resposta.json()["vehicle"] == vehicle
    assert resposta.json()["matricula"] == "1234BCD"


@pytest.mark.django_db
@pytest.mark.parametrize("vehicle", ["moto", "cotxe"])
@pytest.mark.parametrize("matricula", ["", None, "   "])
def test_vehicle_de_motor_sense_matricula_retorna_400(client, vehicle, matricula):
    resposta = registra(client, vehicle=vehicle, matricula=matricula)

    assert resposta.status_code == 400
    assert resposta.json() == {"matricula": [OBLIGATORI]}
    assert not Usuari.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("vehicle", ["moto", "cotxe"])
def test_vehicle_de_motor_amb_el_camp_absent_retorna_400(client, vehicle):
    dades = dades_valides(vehicle=vehicle)
    del dades["matricula"]

    resposta = client.post(URL, dades, content_type="application/json")

    assert resposta.status_code == 400
    assert resposta.json() == {"matricula": [OBLIGATORI]}
    assert not Usuari.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "matricula",
    [
        "123BCD",  # 3 xifres
        "12345BCD",  # 5 xifres
        "1234BC",  # 2 lletres
        "BCD1234",  # ordre invertit
        "1234ABC",  # vocal
        "1234BCQ",  # Q
        "1234BCÑ",  # Ñ
    ],
)
def test_matricula_amb_format_invalid_retorna_400(client, matricula):
    resposta = registra(client, matricula=matricula)

    assert resposta.status_code == 400
    assert resposta.json() == {"matricula": [MATRICULA_INVALIDA]}
    assert not Usuari.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("matricula", ["", None, "1234BCD"])
def test_bici_no_desa_cap_matricula(client, matricula):
    resposta = registra(client, vehicle="bici", matricula=matricula)

    assert resposta.status_code == 201
    assert resposta.json()["matricula"] == ""
    assert PerfilRepartidor.objects.get().matricula == ""


@pytest.mark.django_db
def test_correu_ja_registrat_retorna_400(client):
    registra(client)

    resposta = registra(client, dni="00000000T")

    assert resposta.status_code == 400
    assert resposta.json() == {"correu": [JA_REGISTRAT]}
    assert Usuari.objects.count() == 1


@pytest.mark.django_db
def test_correu_ja_registrat_amb_majuscules_retorna_400(client):
    registra(client)

    resposta = registra(client, correu="REPARTIDOR@example.com", dni="00000000T")

    assert resposta.status_code == 400
    assert resposta.json() == {"correu": [JA_REGISTRAT]}


@pytest.mark.django_db
def test_correu_d_un_usuari_que_no_es_repartidor_retorna_400(client):
    Usuari.objects.create_user(
        email="repartidor@example.com",
        password="Llibres-de-tardor-24",
        name="Anna",
        address="C/ Major 1",
        library_card_number="0000000001",
    )

    resposta = registra(client)

    assert resposta.status_code == 400
    assert resposta.json() == {"correu": [JA_REGISTRAT]}
    assert Usuari.objects.count() == 1


@pytest.mark.django_db
def test_dni_ja_registrat_retorna_400(client):
    registra(client)

    resposta = registra(client, correu="laia@example.com")

    assert resposta.status_code == 400
    assert resposta.json() == {"dni": [JA_REGISTRAT]}
    assert Usuari.objects.count() == 1


@pytest.mark.django_db
def test_dni_ja_registrat_escrit_diferent_retorna_400(client):
    registra(client)

    resposta = registra(client, correu="laia@example.com", dni="12345678-z")

    assert resposta.status_code == 400
    assert resposta.json() == {"dni": [JA_REGISTRAT]}


@pytest.mark.django_db
def test_un_registre_rebutjat_no_canvia_el_repartidor_existent(client):
    registra(client)

    registra(client, nom="Laia", telefon="712345678")

    usuari = Usuari.objects.get()
    assert usuari.name == "Pol"
    assert usuari.perfil_repartidor.telefon == "+34612345678"
