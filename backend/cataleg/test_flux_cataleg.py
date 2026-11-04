"""Tests del backend del catàleg de la biblioteca (US17-T6).

Complementen els tests de cada endpoint (`test_cataleg_biblioteca.py` i
`test_editar_retirar_cataleg.py`) amb el recorregut sencer: que cada canvi al
catàleg es veu a la cerca pública, que una biblioteca no pot tocar el catàleg
d'una altra i que cap altre compte pot fer servir els endpoints.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from cataleg.models import ExemplarBiblioteca, Llibre
from cataleg.permisos import SENSE_PERMISOS
from cataleg.serializers import CAMPS_OBLIGATORIS, LLIBRE_JA_AL_CATALEG
from cataleg.test_cataleg_biblioteca import (
    LLIBRE_NOU,
    client_de,
    crear_biblioteca,
    crear_usuari,
)
from cataleg.validacions import ISBN_INVALID
from usuaris.models import Usuari

pytestmark = pytest.mark.django_db

URL_CATALEG = "/api/cataleg/biblioteca/llibres/"
URL_CERCA = "/api/cataleg/llibres/"


def url_llibre(llibre_id):
    return f"{URL_CATALEG}{llibre_id}/"


def url_exemplars(llibre_id):
    return f"{URL_CATALEG}{llibre_id}/exemplars/"


def cerca(text):
    """Resultats de la cerca pública, sense autenticació."""
    return APIClient().get(URL_CERCA, {"q": text}).data["results"]


def afegeix(client, **canvis):
    resposta = client.post(URL_CATALEG, {**LLIBRE_NOU, **canvis}, format="json")
    assert resposta.status_code == status.HTTP_201_CREATED, resposta.data
    return resposta.data["id"]


@pytest.fixture
def biblioteca():
    return crear_biblioteca()


@pytest.fixture
def client(biblioteca):
    return client_de(biblioteca)


@pytest.fixture
def altra():
    return crear_biblioteca("altra@example.com")


@pytest.fixture
def client_altra(altra):
    return client_de(altra)


# Recorregut sencer i cerca


def test_cada_canvi_del_cataleg_es_veu_a_la_cerca(client):
    assert cerca("Mecanoscrit") == []

    llibre_id = afegeix(client)
    [resultat] = cerca("Mecanoscrit")
    assert (resultat["id"], resultat["disponible"]) == (llibre_id, True)

    client.patch(url_llibre(llibre_id), {"titol": "Segon origen"}, format="json")
    assert cerca("Mecanoscrit") == []
    assert [r["titol"] for r in cerca("Segon origen")] == ["Segon origen"]

    client.patch(url_exemplars(llibre_id), {"exemplars": 0}, format="json")
    assert cerca("Segon origen")[0]["disponible"] is False

    client.patch(url_exemplars(llibre_id), {"exemplars": 2}, format="json")
    assert cerca("Segon origen")[0]["disponible"] is True

    resposta = client.delete(url_llibre(llibre_id))
    assert resposta.status_code == status.HTTP_204_NO_CONTENT
    assert client.get(URL_CATALEG).data == []
    # El llibre es manté (P4 del contracte), però ja no és disponible enlloc.
    [resultat] = cerca("Segon origen")
    assert (resultat["id"], resultat["disponible"]) == (llibre_id, False)


def test_la_cerca_troba_el_llibre_afegit_per_autor_i_per_isbn(client):
    llibre_id = afegeix(client)

    assert [r["id"] for r in cerca("pedrolo")] == [llibre_id]
    assert [r["id"] for r in cerca("9788466421126")] == [llibre_id]


def test_la_portada_editada_es_veu_a_la_cerca(client):
    llibre_id = afegeix(client)

    client.patch(
        url_llibre(llibre_id),
        {"portada": "https://example.com/portades/nova.jpg"},
        format="json",
    )

    assert cerca("Mecanoscrit")[0]["portada"] == "https://example.com/portades/nova.jpg"


@pytest.mark.parametrize(
    ("canvis", "error"),
    [
        ({"isbn": "978-84-664-2112-7"}, {"isbn": [ISBN_INVALID]}),
        ({"titol": ""}, {"titol": [CAMPS_OBLIGATORIS]}),
        ({"exemplars": None}, {"exemplars": [CAMPS_OBLIGATORIS]}),
    ],
)
def test_un_llibre_rebutjat_no_surt_a_la_cerca(client, canvis, error):
    resposta = client.post(URL_CATALEG, {**LLIBRE_NOU, **canvis}, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data == error
    assert cerca("Pedrolo") == []
    assert not Llibre.objects.exists()


def test_un_error_en_editar_no_canvia_el_que_mostra_la_cerca(client):
    llibre_id = afegeix(client)

    resposta = client.patch(url_llibre(llibre_id), {"titol": "  "}, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert cerca("Mecanoscrit")[0]["titol"] == "Mecanoscrit del segon origen"


def test_l_isbn_duplicat_es_detecta_encara_que_s_hagi_editat_el_llibre(client):
    llibre_id = afegeix(client)
    client.patch(url_llibre(llibre_id), {"titol": "Un altre títol"}, format="json")

    resposta = client.post(URL_CATALEG, LLIBRE_NOU, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data == {"isbn": [LLIBRE_JA_AL_CATALEG]}
    assert ExemplarBiblioteca.objects.get().quantitat == 3


# Una biblioteca no pot tocar el catàleg d'una altra


def test_una_biblioteca_no_pot_tocar_un_llibre_que_nomes_te_una_altra(
    client, client_altra
):
    llibre_id = afegeix(client_altra)

    respostes = [
        client.patch(url_llibre(llibre_id), {"titol": "Pirata"}, format="json"),
        client.patch(url_exemplars(llibre_id), {"exemplars": 0}, format="json"),
        client.delete(url_llibre(llibre_id)),
    ]

    assert [r.status_code for r in respostes] == [status.HTTP_404_NOT_FOUND] * 3
    assert client.get(URL_CATALEG).data == []
    assert client_altra.get(URL_CATALEG).data[0]["exemplars"] == 3
    [resultat] = cerca("Mecanoscrit")
    assert (resultat["titol"], resultat["disponible"]) == (
        "Mecanoscrit del segon origen",
        True,
    )


def test_amb_un_llibre_compartit_cada_biblioteca_gestiona_els_seus_exemplars(
    client, client_altra, biblioteca, altra
):
    llibre_id = afegeix(client, exemplars=3)
    assert afegeix(client_altra, exemplars=5, titol="Ignorat") == llibre_id

    client.patch(url_exemplars(llibre_id), {"exemplars": 0}, format="json")

    assert ExemplarBiblioteca.objects.get(biblioteca=biblioteca).quantitat == 0
    assert ExemplarBiblioteca.objects.get(biblioteca=altra).quantitat == 5
    # L'altra biblioteca encara en té, i per tant és disponible.
    assert cerca("Mecanoscrit")[0]["disponible"] is True

    client_altra.delete(url_llibre(llibre_id))

    assert cerca("Mecanoscrit")[0]["disponible"] is False
    assert client.get(URL_CATALEG).data[0]["id"] == llibre_id
    assert client_altra.get(URL_CATALEG).data == []


def test_el_duplicat_nomes_es_compta_dins_del_cataleg_propi(client, client_altra):
    afegeix(client_altra)

    resposta = client.post(URL_CATALEG, LLIBRE_NOU, format="json")

    assert resposta.status_code == status.HTTP_201_CREATED
    assert ExemplarBiblioteca.objects.count() == 2


# Permisos a tots els endpoints


def peticions(llibre_id):
    return [
        ("get", URL_CATALEG, None),
        ("post", URL_CATALEG, {**LLIBRE_NOU, "isbn": "0-306-40615-2"}),
        ("patch", url_llibre(llibre_id), {"titol": "Nou títol"}),
        ("patch", url_exemplars(llibre_id), {"exemplars": 0}),
        ("delete", url_llibre(llibre_id), None),
    ]


NOMS_PETICIONS = ["llistar", "afegir", "editar", "exemplars", "retirar"]


@pytest.fixture
def llibre_id(client):
    return afegeix(client)


def comprova_cataleg_intacte(llibre_id):
    assert Llibre.objects.count() == 1
    assert Llibre.objects.get(id=llibre_id).titol == "Mecanoscrit del segon origen"
    assert ExemplarBiblioteca.objects.get().quantitat == 3


@pytest.mark.parametrize("index", range(5), ids=NOMS_PETICIONS)
@pytest.mark.parametrize("rol", [Usuari.Role.USUARI, Usuari.Role.REPARTIDOR])
def test_un_usuari_que_no_es_biblioteca_rep_403(llibre_id, index, rol):
    usuari = crear_usuari(f"{rol}@example.com", role=rol)
    metode, url, dades = peticions(llibre_id)[index]

    resposta = getattr(client_de(usuari), metode)(url, dades, format="json")

    assert resposta.status_code == status.HTTP_403_FORBIDDEN
    assert resposta.data == {"detail": SENSE_PERMISOS}
    comprova_cataleg_intacte(llibre_id)


@pytest.mark.parametrize("index", range(5), ids=NOMS_PETICIONS)
def test_un_compte_biblioteca_sense_perfil_rep_403(llibre_id, index):
    usuari = crear_usuari("sense-perfil@example.com", role=Usuari.Role.BIBLIOTECA)
    metode, url, dades = peticions(llibre_id)[index]

    resposta = getattr(client_de(usuari), metode)(url, dades, format="json")

    assert resposta.status_code == status.HTTP_403_FORBIDDEN
    assert resposta.data == {"detail": SENSE_PERMISOS}
    comprova_cataleg_intacte(llibre_id)


@pytest.mark.parametrize("index", range(5), ids=NOMS_PETICIONS)
def test_una_biblioteca_desactivada_ja_no_hi_te_acces(biblioteca, llibre_id, index):
    client = client_de(biblioteca)
    biblioteca.is_active = False
    biblioteca.save(update_fields=["is_active"])
    metode, url, dades = peticions(llibre_id)[index]

    resposta = getattr(client, metode)(url, dades, format="json")

    # La JWT rebutja el compte inactiu abans de comprovar els permisos.
    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED
    comprova_cataleg_intacte(llibre_id)


@pytest.mark.parametrize("index", range(5), ids=NOMS_PETICIONS)
def test_un_token_invalid_rep_401(llibre_id, index):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer no-es-un-token")
    metode, url, dades = peticions(llibre_id)[index]

    resposta = getattr(client, metode)(url, dades, format="json")

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED
    comprova_cataleg_intacte(llibre_id)
