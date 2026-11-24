"""Tests unitaris del serializer de registre de repartidor (US1.1-T3)."""

import pytest

from usuaris.models import PerfilRepartidor, Usuari
from usuaris.serializers import RepartidorRegistreSerializer
from usuaris.validacions import (
    DNI_NIE_INVALID,
    MATRICULA_INVALIDA,
    SEGURETAT_SOCIAL_INVALIDA,
    TELEFON_INVALID,
)

pytestmark = pytest.mark.django_db

OBLIGATORI = "Aquest camp és obligatori."
JA_REGISTRAT = "DNI/correu ja registrat"
CAMPS_OBLIGATORIS = (
    "nom",
    "cognoms",
    "correu",
    "dni",
    "telefon",
    "vehicle",
    "num_seguretat_social",
    "contrasenya",
)


def dades_valides(**canvis):
    """Cos de petició vàlid segons el contracte, amb els canvis indicats."""
    dades = {
        "nom": "Pol",
        "cognoms": "Ferrer Soler",
        "correu": "repartidor@example.com",
        "dni": "12345678Z",
        "telefon": "+34 612 345 678",
        "vehicle": "moto",
        "matricula": "1234 BCD",
        "num_seguretat_social": "28/12345678/90",
        "contrasenya": "Llibres-de-tardor-24",
    }
    dades.update(canvis)
    return dades


def dades_bici(**canvis):
    dades = dades_valides(vehicle="bici", **canvis)
    if "matricula" not in canvis:
        del dades["matricula"]
    return dades


def registra(**canvis):
    serializer = RepartidorRegistreSerializer(data=dades_valides(**canvis))
    assert serializer.is_valid(), serializer.errors
    return serializer.save()


def errors_de(dades):
    serializer = RepartidorRegistreSerializer(data=dades)
    assert not serializer.is_valid()
    return serializer.errors


def test_crea_l_usuari_amb_rol_repartidor_i_contrasenya_xifrada():
    usuari = registra()

    assert usuari.role == Usuari.Role.REPARTIDOR
    assert usuari.name == "Pol"
    assert usuari.email == "repartidor@example.com"
    assert usuari.check_password("Llibres-de-tardor-24")


def test_crea_el_perfil_pendent_amb_les_dades_normalitzades():
    perfil = registra().perfil_repartidor

    assert perfil.estat == PerfilRepartidor.Estat.PENDENT
    assert perfil.cognoms == "Ferrer Soler"
    assert perfil.dni == "12345678Z"
    assert perfil.telefon == "+34612345678"
    assert perfil.vehicle == PerfilRepartidor.Vehicle.MOTO
    assert perfil.matricula == "1234BCD"
    assert perfil.num_seguretat_social == "281234567890"


def test_el_perfil_compleix_els_validadors_i_mides_del_model():
    registra().perfil_repartidor.full_clean()


def test_la_representacio_segueix_el_contracte_sense_contrasenya():
    usuari = registra()

    assert RepartidorRegistreSerializer(usuari).data == {
        "id": usuari.id,
        "nom": "Pol",
        "cognoms": "Ferrer Soler",
        "correu": "repartidor@example.com",
        "dni": "12345678Z",
        "telefon": "+34612345678",
        "vehicle": "moto",
        "matricula": "1234BCD",
        "num_seguretat_social": "281234567890",
        "rol": "repartidor",
        "estat": "pendent",
    }


def test_el_rol_i_l_estat_no_es_poden_triar():
    usuari = registra(rol="biblioteca", estat="validat", is_staff=True)

    assert usuari.role == Usuari.Role.REPARTIDOR
    assert usuari.perfil_repartidor.estat == PerfilRepartidor.Estat.PENDENT
    assert not usuari.is_staff


def test_es_poden_registrar_diversos_repartidors():
    primer = registra()
    segon = registra(correu="laia@example.com", dni="00000000T")

    assert primer.library_card_number != segon.library_card_number


def test_accepta_un_nie():
    assert registra(dni="x-1234567-l").perfil_repartidor.dni == "X1234567L"


def test_desa_el_correu_en_minuscules():
    assert registra(correu="Repartidor@Example.com").email == "repartidor@example.com"


@pytest.mark.parametrize("camp", CAMPS_OBLIGATORIS)
def test_camp_absent_es_obligatori(camp):
    dades = dades_valides()
    del dades[camp]

    assert errors_de(dades)[camp] == [OBLIGATORI]


@pytest.mark.parametrize("camp", CAMPS_OBLIGATORIS)
@pytest.mark.parametrize("valor", ["", None])
def test_camp_buit_es_obligatori(camp, valor):
    assert errors_de(dades_valides(**{camp: valor}))[camp] == [OBLIGATORI]


@pytest.mark.parametrize("camp", ["nom", "cognoms"])
def test_nom_i_cognoms_tenen_un_maxim_de_150_caracters(camp):
    assert camp in errors_de(dades_valides(**{camp: "a" * 151}))


@pytest.mark.parametrize(
    ("camp", "valor", "missatge"),
    [
        ("correu", "no-es-un-correu", "Introduïu una adreça de correu electrònic vàlida."),
        ("dni", "12345678A", DNI_NIE_INVALID),
        ("telefon", "512345678", TELEFON_INVALID),
        ("vehicle", "patinet", '"bici", "moto" o "cotxe" no és una opció vàlida.'),
        ("matricula", "1234ABC", MATRICULA_INVALIDA),
        ("num_seguretat_social", "1234", SEGURETAT_SOCIAL_INVALIDA),
    ],
)
def test_format_invalid_retorna_el_missatge_del_contracte(camp, valor, missatge):
    assert errors_de(dades_valides(**{camp: valor}))[camp] == [missatge]


@pytest.mark.parametrize("vehicle", ["moto", "cotxe"])
@pytest.mark.parametrize("matricula", ["", None])
def test_matricula_buida_obligatoria_amb_vehicle_de_motor(vehicle, matricula):
    errors = errors_de(dades_valides(vehicle=vehicle, matricula=matricula))

    assert errors["matricula"] == [OBLIGATORI]


@pytest.mark.parametrize("vehicle", ["moto", "cotxe"])
def test_matricula_absent_obligatoria_amb_vehicle_de_motor(vehicle):
    dades = dades_valides(vehicle=vehicle)
    del dades["matricula"]

    assert errors_de(dades)["matricula"] == [OBLIGATORI]


@pytest.mark.parametrize("canvis", [{}, {"matricula": ""}, {"matricula": None}])
def test_bici_no_necessita_matricula(canvis):
    serializer = RepartidorRegistreSerializer(data=dades_bici(**canvis))
    assert serializer.is_valid(), serializer.errors

    assert serializer.save().perfil_repartidor.matricula == ""


def test_bici_descarta_la_matricula_enviada():
    serializer = RepartidorRegistreSerializer(data=dades_bici(matricula="1234BCD"))
    assert serializer.is_valid(), serializer.errors

    assert serializer.save().perfil_repartidor.matricula == ""


def test_correu_repetit_sense_distingir_majuscules():
    registra()

    errors = errors_de(
        dades_valides(correu="REPARTIDOR@example.com", dni="00000000T")
    )

    assert errors["correu"] == [JA_REGISTRAT]


def test_correu_d_un_usuari_que_no_es_repartidor():
    Usuari.objects.create_user(
        email="repartidor@example.com",
        password="una-Contrasenya-segura-9",
        name="Anna",
        address="C/ Major 1",
        library_card_number="1234567890",
    )

    assert errors_de(dades_valides(dni="00000000T"))["correu"] == [JA_REGISTRAT]


def test_dni_repetit_encara_que_s_escrigui_diferent():
    registra()

    errors = errors_de(dades_valides(correu="laia@example.com", dni="12345678-z"))

    assert errors["dni"] == [JA_REGISTRAT]


def test_correu_i_dni_repetits_alhora():
    registra()

    errors = errors_de(dades_valides())

    assert errors["correu"] == [JA_REGISTRAT]
    assert errors["dni"] == [JA_REGISTRAT]


def test_contrasenya_curta_en_catala():
    errors = errors_de(dades_valides(contrasenya="Ll1-b"))

    assert errors["contrasenya"] == [
        "Aquesta contrasenya és massa curta. Ha de tenir com a mínim 8 caràcters."
    ]


def test_contrasenya_massa_semblant_al_correu():
    errors = errors_de(dades_valides(contrasenya="repartidor@example.com"))

    assert "contrasenya" in errors


def test_retorna_alhora_els_errors_de_matricula_i_contrasenya():
    errors = errors_de(dades_valides(matricula="", contrasenya="Ll1-b"))

    assert set(errors) == {"matricula", "contrasenya"}


def test_si_falla_el_perfil_no_queda_cap_usuari(monkeypatch):
    def falla(*args, **kwargs):
        raise RuntimeError

    serializer = RepartidorRegistreSerializer(data=dades_valides())
    assert serializer.is_valid(), serializer.errors
    monkeypatch.setattr(PerfilRepartidor.objects, "create", falla)

    with pytest.raises(RuntimeError):
        serializer.save()

    assert not Usuari.objects.exists()
