"""Tests dels endpoints per llistar i afegir llibres al catàleg de la biblioteca (US17-T3)."""

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from cataleg.models import ExemplarBiblioteca, Llibre
from cataleg.permisos import SENSE_PERMISOS
from cataleg.serializers import CAMPS_OBLIGATORIS, LLIBRE_JA_AL_CATALEG
from cataleg.validacions import ISBN_INVALID, PORTADA_MAX_LENGTH
from usuaris.models import Biblioteca, Usuari

URL = "/api/cataleg/biblioteca/llibres/"

pytestmark = pytest.mark.django_db

LLIBRE_NOU = {
    "titol": "Mecanoscrit del segon origen",
    "autor": "Manuel de Pedrolo",
    "isbn": "978-84-664-2112-6",
    "exemplars": 3,
    "portada": "https://example.com/portades/mecanoscrit.jpg",
}


def crear_usuari(email, role=Usuari.Role.USUARI):
    return Usuari.objects.create_user(
        email=email,
        password="una-contrasenya-segura",
        name="Anna Puig",
        address="C/ Major 1, 08001 Barcelona",
        library_card_number=f"carnet-{email}",
        role=role,
    )


def crear_biblioteca(email="biblioteca@example.com"):
    usuari = crear_usuari(email, role=Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=usuari, nom="Biblioteca Central")
    usuari.is_active = True
    usuari.save(update_fields=["is_active"])
    return usuari


def client_de(usuari):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(usuari)}")
    return client


def crear_llibre(titol="La plaça del Diamant", isbn="9788429740011", **camps):
    return Llibre.objects.create(titol=titol, autor="Mercè Rodoreda", isbn=isbn, **camps)


@pytest.fixture
def biblioteca():
    return crear_biblioteca()


@pytest.fixture
def client(biblioteca):
    return client_de(biblioteca)


# Permisos


@pytest.mark.parametrize("metode", ["get", "post"])
def test_sense_token_respon_401(metode):
    resposta = getattr(APIClient(), metode)(URL, LLIBRE_NOU, format="json")

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("rol", [Usuari.Role.USUARI, Usuari.Role.REPARTIDOR])
@pytest.mark.parametrize("metode", ["get", "post"])
def test_els_altres_rols_reben_403(rol, metode):
    client = client_de(crear_usuari(f"{rol}@example.com", role=rol))

    resposta = getattr(client, metode)(URL, LLIBRE_NOU, format="json")

    assert resposta.status_code == status.HTTP_403_FORBIDDEN
    assert resposta.data == {"detail": SENSE_PERMISOS}
    assert not Llibre.objects.exists()


@pytest.mark.parametrize("metode", ["put", "patch", "delete"])
def test_els_altres_metodes_reben_405(client, metode):
    resposta = getattr(client, metode)(URL, LLIBRE_NOU, format="json")

    assert resposta.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# Llistar el catàleg


def test_un_cataleg_buit_retorna_una_llista_buida(client):
    resposta = client.get(URL)

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data == []


def test_llista_els_llibres_de_la_biblioteca_ordenats_per_titol(client, biblioteca):
    plaça = crear_llibre(portada="https://example.com/placa.jpg")
    mirall = crear_llibre(titol="Mirall trencat", isbn="9788475882475")
    ExemplarBiblioteca.objects.create(llibre=plaça, biblioteca=biblioteca, quantitat=2)
    ExemplarBiblioteca.objects.create(llibre=mirall, biblioteca=biblioteca, quantitat=0)

    resposta = client.get(URL)

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data == [
        {
            "id": plaça.id,
            "titol": "La plaça del Diamant",
            "autor": "Mercè Rodoreda",
            "isbn": "9788429740011",
            "portada": "https://example.com/placa.jpg",
            "exemplars": 2,
        },
        {
            "id": mirall.id,
            "titol": "Mirall trencat",
            "autor": "Mercè Rodoreda",
            "isbn": "9788475882475",
            "portada": "",
            "exemplars": 0,
        },
    ]


def test_no_llista_els_llibres_ni_els_exemplars_d_altres_biblioteques(client, biblioteca):
    altra = crear_biblioteca("altra@example.com")
    compartit = crear_llibre()
    nomes_de_l_altra = crear_llibre(titol="Mirall trencat", isbn="9788475882475")
    ExemplarBiblioteca.objects.create(llibre=compartit, biblioteca=biblioteca, quantitat=1)
    ExemplarBiblioteca.objects.create(llibre=compartit, biblioteca=altra, quantitat=5)
    ExemplarBiblioteca.objects.create(llibre=nomes_de_l_altra, biblioteca=altra, quantitat=4)

    resposta = client.get(URL)

    assert [(llibre["id"], llibre["exemplars"]) for llibre in resposta.data] == [
        (compartit.id, 1)
    ]


# Afegir un llibre


def test_afegeix_un_llibre_nou_amb_l_isbn_normalitzat(client, biblioteca):
    resposta = client.post(URL, LLIBRE_NOU, format="json")

    assert resposta.status_code == status.HTTP_201_CREATED
    llibre = Llibre.objects.get()
    assert resposta.data == {
        "id": llibre.id,
        "titol": "Mecanoscrit del segon origen",
        "autor": "Manuel de Pedrolo",
        "isbn": "9788466421126",
        "portada": "https://example.com/portades/mecanoscrit.jpg",
        "exemplars": 3,
    }
    exemplar = ExemplarBiblioteca.objects.get()
    assert (exemplar.llibre, exemplar.biblioteca, exemplar.quantitat) == (llibre, biblioteca, 3)


def test_la_portada_es_opcional(client):
    dades = {camp: valor for camp, valor in LLIBRE_NOU.items() if camp != "portada"}

    resposta = client.post(URL, dades, format="json")

    assert resposta.status_code == status.HTTP_201_CREATED
    assert resposta.data["portada"] == ""


def test_treu_els_espais_del_titol_i_l_autor(client):
    dades = {**LLIBRE_NOU, "titol": "  Mecanoscrit  ", "autor": " Pedrolo "}

    resposta = client.post(URL, dades, format="json")

    assert (resposta.data["titol"], resposta.data["autor"]) == ("Mecanoscrit", "Pedrolo")


def test_accepta_un_isbn_10_i_passa_la_x_a_majuscula(client):
    resposta = client.post(URL, {**LLIBRE_NOU, "isbn": "0-306-40615-2"}, format="json")
    resposta_x = client.post(
        URL, {**LLIBRE_NOU, "isbn": "0 8044 2957 x"}, format="json"
    )

    assert resposta.status_code == status.HTTP_201_CREATED
    assert resposta.data["isbn"] == "0306406152"
    assert resposta_x.status_code == status.HTTP_201_CREATED
    assert resposta_x.data["isbn"] == "080442957X"


def test_reaprofita_un_llibre_que_ja_te_una_altra_biblioteca(client, biblioteca):
    altra = crear_biblioteca("altra@example.com")
    existent = crear_llibre(isbn="9788466421126", titol="Títol desat")
    ExemplarBiblioteca.objects.create(llibre=existent, biblioteca=altra, quantitat=5)

    resposta = client.post(URL, LLIBRE_NOU, format="json")

    assert resposta.status_code == status.HTTP_201_CREATED
    assert Llibre.objects.count() == 1
    assert resposta.data["id"] == existent.id
    # Es mantenen les dades desades (P2 del contracte).
    assert resposta.data["titol"] == "Títol desat"
    assert resposta.data["exemplars"] == 3
    assert ExemplarBiblioteca.objects.get(biblioteca=altra).quantitat == 5
    assert ExemplarBiblioteca.objects.get(biblioteca=biblioteca).quantitat == 3


def test_un_isbn_que_ja_es_al_cataleg_dona_error_de_duplicat(client, biblioteca):
    llibre = crear_llibre(isbn="9788466421126")
    ExemplarBiblioteca.objects.create(llibre=llibre, biblioteca=biblioteca, quantitat=2)

    # El mateix ISBN amb un altre format també és un duplicat.
    resposta = client.post(URL, {**LLIBRE_NOU, "isbn": "978 8466421126"}, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data == {"isbn": [LLIBRE_JA_AL_CATALEG]}
    assert ExemplarBiblioteca.objects.get().quantitat == 2


def test_el_missatge_de_duplicat_es_el_literal_dels_criteris():
    assert LLIBRE_JA_AL_CATALEG == (
        "Aquest llibre ja és al teu catàleg, actualitza'n els exemplars"
    )
    assert CAMPS_OBLIGATORIS == "Omple tots els camps obligatoris per continuar"


def test_sense_cap_camp_marca_tots_els_obligatoris(client):
    resposta = client.post(URL, {}, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data == {
        camp: [CAMPS_OBLIGATORIS] for camp in ("titol", "autor", "isbn", "exemplars")
    }
    assert not Llibre.objects.exists()


@pytest.mark.parametrize("camp", ["titol", "autor", "isbn", "exemplars"])
@pytest.mark.parametrize("valor", ["", "   ", None])
def test_un_camp_obligatori_buit_o_nul_dona_el_missatge_d_obligatori(client, camp, valor):
    resposta = client.post(URL, {**LLIBRE_NOU, camp: valor}, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data == {camp: [CAMPS_OBLIGATORIS]}
    assert not ExemplarBiblioteca.objects.exists()


@pytest.mark.parametrize("isbn", ["978-84-664-2112-7", "12345", "abcdefghij"])
def test_un_isbn_invalid_dona_error(client, isbn):
    resposta = client.post(URL, {**LLIBRE_NOU, "isbn": isbn}, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data == {"isbn": [ISBN_INVALID]}


def test_exemplars_ha_de_ser_un_enter(client):
    resposta = client.post(URL, {**LLIBRE_NOU, "exemplars": "tres"}, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data == {"exemplars": ["Es requereix un nombre enter vàlid."]}


@pytest.mark.parametrize("exemplars", [0, -1])
def test_cal_almenys_un_exemplar(client, exemplars):
    resposta = client.post(URL, {**LLIBRE_NOU, "exemplars": exemplars}, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data == {
        "exemplars": ["Aquest valor ha de ser més gran o igual a 1."]
    }


@pytest.mark.parametrize("camp", ["titol", "autor"])
def test_titol_i_autor_tenen_un_maxim_de_255_caracters(client, camp):
    resposta = client.post(URL, {**LLIBRE_NOU, camp: "a" * 256}, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data[camp][0].code == "max_length"


@pytest.mark.parametrize(
    "portada", ["no-es-un-enllac", "ftp://example.com/portada.jpg", "javascript:alert(1)"]
)
def test_una_portada_que_no_es_un_enllac_http_dona_error(client, portada):
    resposta = client.post(URL, {**LLIBRE_NOU, "portada": portada}, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data == {"portada": ["Introduïu una URL vàlida."]}


def test_accepta_una_portada_de_la_mida_maxima_i_rebutja_una_de_mes_llarga(client):
    base = "https://example.com/"
    maxima = base + "a" * (PORTADA_MAX_LENGTH - len(base))

    resposta = client.post(URL, {**LLIBRE_NOU, "portada": maxima}, format="json")
    massa_llarga = client.post(
        URL,
        {**LLIBRE_NOU, "isbn": "0-306-40615-2", "portada": maxima + "a"},
        format="json",
    )

    assert resposta.status_code == status.HTTP_201_CREATED
    assert resposta.data["portada"] == maxima
    assert massa_llarga.status_code == status.HTTP_400_BAD_REQUEST
    assert massa_llarga.data["portada"][0].code == "max_length"


def test_el_llibre_afegit_surt_a_la_cerca_com_a_disponible(client):
    client.post(URL, LLIBRE_NOU, format="json")

    resposta = APIClient().get("/api/cataleg/llibres/", {"q": "Mecanoscrit"})

    assert resposta.data["count"] == 1
    assert resposta.data["results"][0]["disponible"] is True
