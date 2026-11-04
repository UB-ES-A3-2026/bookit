"""Tests dels endpoints per editar, canviar exemplars i retirar llibres del catàleg (US17-T4)."""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from cataleg.models import ExemplarBiblioteca, Llibre
from cataleg.permisos import SENSE_PERMISOS
from cataleg.serializers import CAMPS_OBLIGATORIS
from cataleg.test_cataleg_biblioteca import (
    client_de,
    crear_biblioteca,
    crear_llibre,
    crear_usuari,
)
from cataleg.validacions import PORTADA_MAX_LENGTH
from usuaris.models import Usuari

pytestmark = pytest.mark.django_db


def url_llibre(llibre_id):
    return f"/api/cataleg/biblioteca/llibres/{llibre_id}/"


def url_exemplars(llibre_id):
    return f"/api/cataleg/biblioteca/llibres/{llibre_id}/exemplars/"


@pytest.fixture
def biblioteca():
    return crear_biblioteca()


@pytest.fixture
def client(biblioteca):
    return client_de(biblioteca)


@pytest.fixture
def llibre():
    return crear_llibre(portada="https://example.com/placa.jpg")


@pytest.fixture
def exemplar(llibre, biblioteca):
    return ExemplarBiblioteca.objects.create(
        llibre=llibre, biblioteca=biblioteca, quantitat=3
    )


def resposta_esperada(llibre, **canvis):
    return {
        "id": llibre.id,
        "titol": "La plaça del Diamant",
        "autor": "Mercè Rodoreda",
        "isbn": "9788429740011",
        "portada": "https://example.com/placa.jpg",
        "exemplars": 3,
        **canvis,
    }


# Permisos

PETICIONS = [
    ("patch", url_llibre, {"titol": "Nou títol"}),
    ("patch", url_exemplars, {"exemplars": 5}),
    ("delete", url_llibre, None),
]


@pytest.mark.parametrize(("metode", "url", "dades"), PETICIONS)
def test_sense_token_respon_401(exemplar, metode, url, dades):
    resposta = getattr(APIClient(), metode)(url(exemplar.llibre_id), dades, format="json")

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED
    assert ExemplarBiblioteca.objects.get().quantitat == 3


@pytest.mark.parametrize("rol", [Usuari.Role.USUARI, Usuari.Role.REPARTIDOR])
@pytest.mark.parametrize(("metode", "url", "dades"), PETICIONS)
def test_els_altres_rols_reben_403(exemplar, rol, metode, url, dades):
    client = client_de(crear_usuari(f"{rol}@example.com", role=rol))

    resposta = getattr(client, metode)(url(exemplar.llibre_id), dades, format="json")

    assert resposta.status_code == status.HTTP_403_FORBIDDEN
    assert resposta.data == {"detail": SENSE_PERMISOS}
    assert ExemplarBiblioteca.objects.get().quantitat == 3
    assert Llibre.objects.get().titol == "La plaça del Diamant"


@pytest.mark.parametrize(("metode", "url", "dades"), PETICIONS)
def test_un_llibre_inexistent_rep_404(client, metode, url, dades):
    resposta = getattr(client, metode)(url(999), dades, format="json")

    assert resposta.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(("metode", "url", "dades"), PETICIONS)
def test_un_llibre_que_nomes_te_una_altra_biblioteca_rep_404(client, llibre, metode, url, dades):
    altra = crear_biblioteca("altra@example.com")
    ExemplarBiblioteca.objects.create(llibre=llibre, biblioteca=altra, quantitat=4)

    resposta = getattr(client, metode)(url(llibre.id), dades, format="json")

    assert resposta.status_code == status.HTTP_404_NOT_FOUND
    llibre.refresh_from_db()
    assert llibre.titol == "La plaça del Diamant"
    assert ExemplarBiblioteca.objects.get(biblioteca=altra).quantitat == 4


@pytest.mark.parametrize("metode", ["get", "put", "post"])
def test_els_altres_metodes_del_llibre_reben_405(client, exemplar, metode):
    resposta = getattr(client, metode)(url_llibre(exemplar.llibre_id), {}, format="json")

    assert resposta.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.parametrize("metode", ["get", "put", "post", "delete"])
def test_els_altres_metodes_dels_exemplars_reben_405(client, exemplar, metode):
    resposta = getattr(client, metode)(url_exemplars(exemplar.llibre_id), {}, format="json")

    assert resposta.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# Editar les dades d'un llibre


def test_edita_nomes_els_camps_enviats(client, exemplar, llibre):
    resposta = client.patch(
        url_llibre(llibre.id), {"titol": "  Nou títol  "}, format="json"
    )

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data == resposta_esperada(llibre, titol="Nou títol")
    llibre.refresh_from_db()
    assert (llibre.titol, llibre.autor, llibre.portada) == (
        "Nou títol",
        "Mercè Rodoreda",
        "https://example.com/placa.jpg",
    )


def test_edita_tots_els_camps_editables(client, exemplar, llibre):
    dades = {
        "titol": "Mirall trencat",
        "autor": "M. Rodoreda",
        "portada": "https://example.com/mirall.jpg",
    }

    resposta = client.patch(url_llibre(llibre.id), dades, format="json")

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data == resposta_esperada(llibre, **dades)


def test_una_portada_buida_treu_la_portada(client, exemplar, llibre):
    resposta = client.patch(url_llibre(llibre.id), {"portada": ""}, format="json")

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["portada"] == ""
    llibre.refresh_from_db()
    assert llibre.portada == ""


def test_ignora_l_isbn_els_exemplars_i_els_camps_desconeguts(client, exemplar, llibre):
    resposta = client.patch(
        url_llibre(llibre.id),
        {"isbn": "0-306-40615-2", "exemplars": 9, "desconegut": "x"},
        format="json",
    )

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data == resposta_esperada(llibre)
    llibre.refresh_from_db()
    assert llibre.isbn == "9788429740011"
    assert ExemplarBiblioteca.objects.get().quantitat == 3


def test_l_edicio_es_veu_a_totes_les_biblioteques_i_a_la_cerca(client, exemplar, llibre):
    altra = crear_biblioteca("altra@example.com")
    ExemplarBiblioteca.objects.create(llibre=llibre, biblioteca=altra, quantitat=1)

    client.patch(url_llibre(llibre.id), {"titol": "Títol editat"}, format="json")

    # Les dades del llibre són compartides (P2 del contracte).
    llista_altra = client_de(altra).get("/api/cataleg/biblioteca/llibres/")
    assert llista_altra.data[0]["titol"] == "Títol editat"
    cerca = APIClient().get("/api/cataleg/llibres/", {"q": "editat"})
    assert cerca.data["count"] == 1


@pytest.mark.parametrize("camp", ["titol", "autor"])
@pytest.mark.parametrize("valor", ["", "   ", None])
def test_un_titol_o_autor_buit_o_nul_dona_el_missatge_d_obligatori(
    client, exemplar, llibre, camp, valor
):
    resposta = client.patch(url_llibre(llibre.id), {camp: valor}, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data == {camp: [CAMPS_OBLIGATORIS]}
    llibre.refresh_from_db()
    assert getattr(llibre, camp) == resposta_esperada(llibre)[camp]


@pytest.mark.parametrize("camp", ["titol", "autor"])
def test_titol_i_autor_tenen_un_maxim_de_255_caracters(client, exemplar, llibre, camp):
    resposta = client.patch(url_llibre(llibre.id), {camp: "a" * 256}, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data[camp][0].code == "max_length"


@pytest.mark.parametrize(
    "portada", ["no-es-un-enllac", "ftp://example.com/portada.jpg", "javascript:alert(1)"]
)
def test_una_portada_que_no_es_un_enllac_http_dona_error(client, exemplar, llibre, portada):
    resposta = client.patch(url_llibre(llibre.id), {"portada": portada}, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data == {"portada": ["Introduïu una URL vàlida."]}
    llibre.refresh_from_db()
    assert llibre.portada == "https://example.com/placa.jpg"


def test_una_portada_massa_llarga_dona_error(client, exemplar, llibre):
    base = "https://example.com/"
    portada = base + "a" * (PORTADA_MAX_LENGTH - len(base) + 1)

    resposta = client.patch(url_llibre(llibre.id), {"portada": portada}, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data["portada"][0].code == "max_length"


# Canviar el nombre d'exemplars


@pytest.mark.parametrize("exemplars", [5, 1])
def test_canvia_el_nombre_total_d_exemplars(client, exemplar, llibre, exemplars):
    resposta = client.patch(
        url_exemplars(llibre.id), {"exemplars": exemplars}, format="json"
    )

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data == resposta_esperada(llibre, exemplars=exemplars)
    assert ExemplarBiblioteca.objects.get().quantitat == exemplars


def test_amb_0_exemplars_el_llibre_continua_al_cataleg_pero_no_es_disponible(
    client, exemplar, llibre
):
    resposta = client.patch(url_exemplars(llibre.id), {"exemplars": 0}, format="json")

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["exemplars"] == 0
    assert client.get("/api/cataleg/biblioteca/llibres/").data[0]["exemplars"] == 0
    cerca = APIClient().get("/api/cataleg/llibres/", {"q": "Diamant"})
    assert cerca.data["results"][0]["disponible"] is False


def test_nomes_canvia_els_exemplars_de_la_biblioteca_autenticada(client, exemplar, llibre):
    altra = crear_biblioteca("altra@example.com")
    ExemplarBiblioteca.objects.create(llibre=llibre, biblioteca=altra, quantitat=4)

    client.patch(url_exemplars(llibre.id), {"exemplars": 7}, format="json")

    assert ExemplarBiblioteca.objects.get(biblioteca=exemplar.biblioteca).quantitat == 7
    assert ExemplarBiblioteca.objects.get(biblioteca=altra).quantitat == 4


@pytest.mark.parametrize("dades", [{}, {"exemplars": ""}, {"exemplars": "  "}, {"exemplars": None}])
def test_exemplars_absent_buit_o_nul_dona_el_missatge_d_obligatori(
    client, exemplar, llibre, dades
):
    resposta = client.patch(url_exemplars(llibre.id), dades, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data == {"exemplars": [CAMPS_OBLIGATORIS]}
    assert ExemplarBiblioteca.objects.get().quantitat == 3


def test_exemplars_ha_de_ser_un_enter(client, exemplar, llibre):
    resposta = client.patch(url_exemplars(llibre.id), {"exemplars": "tres"}, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data == {"exemplars": ["Es requereix un nombre enter vàlid."]}


def test_exemplars_no_pot_ser_negatiu(client, exemplar, llibre):
    resposta = client.patch(url_exemplars(llibre.id), {"exemplars": -1}, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data == {
        "exemplars": ["Aquest valor ha de ser més gran o igual a 0."]
    }
    assert ExemplarBiblioteca.objects.get().quantitat == 3


def test_els_exemplars_ignoren_els_altres_camps(client, exemplar, llibre):
    resposta = client.patch(
        url_exemplars(llibre.id), {"exemplars": 2, "titol": "Un altre"}, format="json"
    )

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data == resposta_esperada(llibre, exemplars=2)


# Retirar un llibre


def test_retira_el_llibre_i_en_mante_les_dades(client, exemplar, llibre):
    resposta = client.delete(url_llibre(llibre.id))

    assert resposta.status_code == status.HTTP_204_NO_CONTENT
    assert not resposta.content
    assert not ExemplarBiblioteca.objects.exists()
    assert Llibre.objects.get() == llibre
    assert client.get("/api/cataleg/biblioteca/llibres/").data == []


def test_retirar_no_toca_el_cataleg_de_les_altres_biblioteques(client, exemplar, llibre):
    altra = crear_biblioteca("altra@example.com")
    ExemplarBiblioteca.objects.create(llibre=llibre, biblioteca=altra, quantitat=4)

    client.delete(url_llibre(llibre.id))

    assert ExemplarBiblioteca.objects.get().biblioteca == altra
    cerca = APIClient().get("/api/cataleg/llibres/", {"q": "Diamant"})
    assert cerca.data["results"][0]["disponible"] is True


def test_retirar_un_llibre_ja_retirat_rep_404(client, exemplar, llibre):
    client.delete(url_llibre(llibre.id))

    resposta = client.delete(url_llibre(llibre.id))

    assert resposta.status_code == status.HTTP_404_NOT_FOUND


def test_un_llibre_retirat_es_pot_tornar_a_afegir(client, exemplar, llibre):
    client.delete(url_llibre(llibre.id))

    resposta = client.post(
        "/api/cataleg/biblioteca/llibres/",
        {"titol": "Ignorat", "autor": "Ignorat", "isbn": llibre.isbn, "exemplars": 2},
        format="json",
    )

    assert resposta.status_code == status.HTTP_201_CREATED
    assert resposta.data == resposta_esperada(llibre, exemplars=2)
    assert Llibre.objects.count() == 1
