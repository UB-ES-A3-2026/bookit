"""Tests del serializer d'inici de sessió (US2-T1)."""

import pytest
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken

from usuaris.models import Usuari
from usuaris.serializers import IniciSessioSerializer

CONTRASENYA = "una-contrasenya-segura"
MISSATGE_CREDENCIALS = "El correu o la contrasenya no són correctes."


@pytest.fixture
def usuari(db):
    return Usuari.objects.create_user(
        email="anna@example.com",
        password=CONTRASENYA,
        name="Anna Puig",
        address="C/ Major 1, 08001 Barcelona",
        library_card_number="1234567890",
    )


def inicia_sessio(correu, contrasenya):
    serializer = IniciSessioSerializer(
        data={"correu": correu, "contrasenya": contrasenya}
    )
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def test_retorna_tokens_amb_credencials_correctes(usuari):
    dades = inicia_sessio("anna@example.com", CONTRASENYA)

    assert set(dades) == {"access", "refresh"}
    assert AccessToken(dades["access"])["user_id"] == str(usuari.pk)


def test_el_correu_no_distingeix_majuscules(usuari):
    dades = inicia_sessio("ANNA@Example.com", CONTRASENYA)

    assert AccessToken(dades["access"])["user_id"] == str(usuari.pk)


def test_ignora_els_espais_al_voltant_del_correu(usuari):
    dades = inicia_sessio("  anna@example.com  ", CONTRASENYA)

    assert AccessToken(dades["access"])["user_id"] == str(usuari.pk)


@pytest.mark.parametrize(
    ("correu", "contrasenya"),
    [
        ("anna@example.com", "contrasenya-incorrecta"),
        ("ningu@example.com", CONTRASENYA),
    ],
)
def test_credencials_incorrectes_donen_el_mateix_missatge(usuari, correu, contrasenya):
    with pytest.raises(AuthenticationFailed) as error:
        inicia_sessio(correu, contrasenya)

    assert error.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert error.value.detail == MISSATGE_CREDENCIALS


def test_un_compte_inactiu_no_rep_tokens(usuari):
    usuari.is_active = False
    usuari.save(update_fields=["is_active"])

    with pytest.raises(AuthenticationFailed) as error:
        inicia_sessio("anna@example.com", CONTRASENYA)

    assert error.value.detail == MISSATGE_CREDENCIALS


@pytest.mark.parametrize(
    "dades",
    [{}, {"correu": "", "contrasenya": ""}],
)
def test_els_dos_camps_son_obligatoris(dades):
    serializer = IniciSessioSerializer(data=dades)

    assert not serializer.is_valid()
    assert serializer.errors == {
        "correu": ["Aquest camp és obligatori."],
        "contrasenya": ["Aquest camp és obligatori."],
    }


def test_no_accepta_els_noms_interns_dels_camps(usuari):
    serializer = IniciSessioSerializer(
        data={"email": "anna@example.com", "password": CONTRASENYA}
    )

    assert not serializer.is_valid()
    assert set(serializer.errors) == {"correu", "contrasenya"}
