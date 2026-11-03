"""Tests del flux complet d'inici de sessió contra el contracte `docs/api-auth.md` (US2-T5).

Els casos de cada endpoint per separat són a `test_inici_sessio.py` (US2-T2),
`test_inici_sessio_estat.py` (US2-T3) i `test_me.py` (US2-T4). Aquí es fan servir
els tokens que retorna l'API, com el frontend, i es cobreixen els casos del
contracte que no hi eren.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from usuaris.models import PerfilRepartidor, Usuari

URL_LOGIN = "/api/auth/login/"
URL_REFRESH = "/api/auth/refresh/"
URL_ME = "/api/auth/me/"
CONTRASENYA = "una-contrasenya-segura"
MISSATGE_CREDENCIALS = "El correu o la contrasenya no són correctes."
CAMP_OBLIGATORI = "Aquest camp és obligatori."

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


def crea_usuari(email="anna@example.com", role=Usuari.Role.USUARI, num_carnet="1234567890"):
    return Usuari.objects.create_user(
        email=email,
        password=CONTRASENYA,
        name="Anna Puig",
        address="C/ Major 1, 08001 Barcelona",
        library_card_number=num_carnet,
        role=role,
    )


def crea_repartidor_validat():
    usuari = crea_usuari(
        "repartidor@example.com",
        role=Usuari.Role.REPARTIDOR,
        num_carnet="repartidor-12345678Z",
    )
    PerfilRepartidor.objects.create(
        usuari=usuari,
        cognoms="Puig Soler",
        dni="12345678Z",
        telefon="612345678",
        vehicle=PerfilRepartidor.Vehicle.MOTO,
        matricula="1234BCD",
        num_seguretat_social="281234567890",
        estat=PerfilRepartidor.Estat.VALIDAT,
    )
    return usuari


def crea_biblioteca():
    return crea_usuari(
        "biblioteca@example.com", role=Usuari.Role.BIBLIOTECA, num_carnet="biblioteca-1"
    )


def inicia_sessio(client, correu="anna@example.com", contrasenya=CONTRASENYA):
    return client.post(
        URL_LOGIN, {"correu": correu, "contrasenya": contrasenya}, format="json"
    )


def renova(client, refresh):
    return client.post(URL_REFRESH, {"refresh": refresh}, format="json")


def me(access):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return client.get(URL_ME)


# Flux complet: login, /me i renovació.


@pytest.mark.parametrize(
    ("crea_compte", "rol"),
    [
        (crea_usuari, "usuari"),
        (crea_repartidor_validat, "repartidor"),
        (crea_biblioteca, "biblioteca"),
    ],
    ids=["usuari", "repartidor-validat", "biblioteca-verificada"],
)
def test_el_token_del_login_dona_les_dades_i_el_rol(client, crea_compte, rol):
    usuari = crea_compte()

    tokens = inicia_sessio(client, usuari.email).data
    resposta = me(tokens["access"])

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data == {
        "id": usuari.id,
        "nom": "Anna Puig",
        "correu": usuari.email,
        "rol": rol,
    }


def test_el_token_renovat_serveix_per_a_me(client):
    usuari = crea_usuari()
    tokens = inicia_sessio(client).data

    renovat = renova(client, tokens["refresh"])
    resposta = me(renovat.data["access"])

    assert renovat.status_code == status.HTTP_200_OK
    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["id"] == usuari.id


def test_el_token_de_refresc_es_pot_fer_servir_mes_d_una_vegada(client):
    crea_usuari()
    refresh = inicia_sessio(client).data["refresh"]

    primera = renova(client, refresh)
    segona = renova(client, refresh)

    assert primera.status_code == status.HTTP_200_OK
    assert segona.status_code == status.HTTP_200_OK


def test_el_token_d_acces_no_serveix_per_renovar(client):
    crea_usuari()
    access = inicia_sessio(client).data["access"]

    resposta = renova(client, access)

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED
    assert resposta.data["code"] == "token_not_valid"


def test_el_token_de_refresc_no_serveix_per_a_me(client):
    crea_usuari()
    refresh = inicia_sessio(client).data["refresh"]

    resposta = me(refresh)

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED
    assert resposta.data["code"] == "token_not_valid"


def test_desactivar_el_compte_talla_la_sessio_oberta(client):
    usuari = crea_usuari()
    tokens = inicia_sessio(client).data
    usuari.is_active = False
    usuari.save(update_fields=["is_active"])

    assert me(tokens["access"]).status_code == status.HTTP_401_UNAUTHORIZED
    assert renova(client, tokens["refresh"]).status_code == status.HTTP_401_UNAUTHORIZED


# Inici de sessió: casos del contracte.


@pytest.mark.parametrize(
    "correu",
    ["ANNA@EXAMPLE.COM", "  anna@example.com  ", " Anna@Example.com "],
)
def test_el_correu_no_distingeix_majuscules_ni_espais(client, correu):
    crea_usuari()

    resposta = inicia_sessio(client, correu)

    assert resposta.status_code == status.HTTP_200_OK
    assert set(resposta.data) == {"access", "refresh"}


def test_la_contrasenya_distingeix_majuscules(client):
    crea_usuari()

    resposta = inicia_sessio(client, contrasenya=CONTRASENYA.upper())

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED
    assert resposta.data == {"detail": MISSATGE_CREDENCIALS}


@pytest.mark.parametrize("correu", ["no-es-un-correu", "anna@", "@example.com"])
def test_un_correu_mal_format_rep_el_missatge_generic(client, correu):
    crea_usuari()

    resposta = inicia_sessio(client, correu)

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED
    assert resposta.data == {"detail": MISSATGE_CREDENCIALS}


def test_correu_inexistent_i_contrasenya_incorrecta_responen_igual(client):
    crea_usuari()

    inexistent = inicia_sessio(client, "ningu@example.com")
    incorrecta = inicia_sessio(client, contrasenya="contrasenya-incorrecta")

    assert inexistent.status_code == incorrecta.status_code == status.HTTP_401_UNAUTHORIZED
    assert inexistent.data == incorrecta.data == {"detail": MISSATGE_CREDENCIALS}


@pytest.mark.parametrize(
    ("dades", "camp"),
    [
        ({"contrasenya": CONTRASENYA}, "correu"),
        ({"correu": "", "contrasenya": CONTRASENYA}, "correu"),
        ({"correu": "   ", "contrasenya": CONTRASENYA}, "correu"),
        ({"correu": "anna@example.com"}, "contrasenya"),
        ({"correu": "anna@example.com", "contrasenya": ""}, "contrasenya"),
    ],
    ids=[
        "correu-absent",
        "correu-buit",
        "correu-nomes-espais",
        "contrasenya-absent",
        "contrasenya-buida",
    ],
)
def test_un_camp_buit_nomes_marca_aquest_camp(client, dades, camp):
    crea_usuari()

    resposta = client.post(URL_LOGIN, dades, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data == {camp: [CAMP_OBLIGATORI]}


def test_un_error_de_login_no_retorna_cap_token(client):
    crea_usuari()

    resposta = inicia_sessio(client, contrasenya="contrasenya-incorrecta")

    assert "access" not in resposta.data
    assert "refresh" not in resposta.data


def test_la_resposta_del_login_no_inclou_la_contrasenya(client):
    crea_usuari()

    resposta = inicia_sessio(client)

    assert CONTRASENYA not in resposta.content.decode()


# /me sense token i mètodes no permesos.


def test_me_sense_capcalera_retorna_el_missatge_del_contracte(client):
    resposta = client.get(URL_ME)

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED
    assert resposta.data == {"detail": "Credencials d'autenticació no disponibles."}


@pytest.mark.parametrize("url", [URL_LOGIN, URL_REFRESH])
@pytest.mark.parametrize("metode", ["get", "put", "patch", "delete"])
def test_login_i_refresh_nomes_accepten_post(client, url, metode):
    resposta = getattr(client, metode)(url)

    assert resposta.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
