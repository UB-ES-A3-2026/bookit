"""Tests de l'endpoint per confirmar una comanda (US6-T2). Contracte a `docs/api-comandes.md`."""

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from cataleg.models import ExemplarBiblioteca, Llibre
from prestecs.models import Comanda
from usuaris.models import Biblioteca, Usuari

URL = "/api/prestecs/comandes/"
SENSE_ESTOC = "Aquest llibre no te estoc en aquest moment. Pots apuntar-te a la llista d'espera"
LIMIT_SUPERAT = "Has superat el límit de llibres per aquesta comanda, elimina un per continuar"


def crea_usuari(correu, rol=Usuari.Role.USUARI, carnet=None, actiu=True):
    return Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {
            "name": correu.split("@")[0],
            "address": "C/ Major 1",
            "library_card_number": carnet or correu,
            "role": rol,
            "is_active": actiu,
        },
    )


def crea_biblioteca(correu="biblioteca@example.com", nom="Biblioteca Montbau"):
    usuari = crea_usuari(correu, Usuari.Role.BIBLIOTECA)
    # El perfil de biblioteca deixa el compte inactiu fins que es verifica el correu.
    Biblioteca.objects.create(usuari=usuari, nom=nom)
    usuari.is_active = True
    usuari.save(update_fields=["is_active"])
    return usuari


def crea_llibre(titol, isbn, biblioteca=None, exemplars=0):
    llibre = Llibre.objects.create(titol=titol, autor="Autor de prova", isbn=isbn)
    if biblioteca is not None:
        ExemplarBiblioteca.objects.create(llibre=llibre, biblioteca=biblioteca, quantitat=exemplars)
    return llibre


@pytest.fixture
def lector():
    return crea_usuari("lector@example.com")


@pytest.fixture
def client(lector):
    client = APIClient()
    client.force_authenticate(lector)
    return client


@pytest.fixture
def biblioteca():
    return crea_biblioteca()


@pytest.fixture
def llibres(biblioteca):
    return [
        crea_llibre("La plaça del Diamant", "9788429740011", biblioteca, exemplars=2),
        crea_llibre("Solitud", "9788475882574", biblioteca, exemplars=1),
    ]


def confirma(client, biblioteca, llibres):
    return client.post(URL, {"biblioteca": biblioteca, "llibres": llibres}, format="json")


@pytest.mark.django_db
def test_confirma_una_comanda_amb_diversos_llibres(client, lector, biblioteca, llibres):
    resposta = confirma(client, biblioteca.pk, [llibre.pk for llibre in llibres])

    assert resposta.status_code == 201
    dades = resposta.json()
    assert dades["estat"] == "rebuda"
    assert dades["biblioteca"] == {"id": biblioteca.pk, "nom": "Biblioteca Montbau"}
    assert [llibre["titol"] for llibre in dades["llibres"]] == ["La plaça del Diamant", "Solitud"]
    assert set(dades["llibres"][0]) == {"id", "titol", "autor", "portada"}
    assert dades["data_lliurament"] is None
    assert "creada" in dades

    comanda = Comanda.objects.get(pk=dades["id"])
    assert comanda.usuari == lector
    assert comanda.linies.count() == 2


@pytest.mark.django_db
def test_sense_sessio_rep_401(biblioteca, llibres):
    resposta = confirma(APIClient(), biblioteca.pk, [llibres[0].pk])

    assert resposta.status_code == 401


@pytest.mark.django_db
@pytest.mark.parametrize("rol", [Usuari.Role.BIBLIOTECA, Usuari.Role.REPARTIDOR])
def test_una_biblioteca_o_un_repartidor_no_poden_fer_comandes(rol, biblioteca, llibres):
    client = APIClient()
    client.force_authenticate(crea_usuari("altre@example.com", rol))

    resposta = confirma(client, biblioteca.pk, [llibres[0].pk])

    assert resposta.status_code == 403
    assert not Comanda.objects.exists()


@pytest.mark.django_db
def test_un_usuari_inactiu_no_pot_fer_comandes(biblioteca, llibres):
    client = APIClient()
    client.force_authenticate(crea_usuari("inactiu@example.com", actiu=False))

    resposta = confirma(client, biblioteca.pk, [llibres[0].pk])

    assert resposta.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize("cos", [{}, {"biblioteca": None, "llibres": None}])
def test_camps_obligatoris(client, cos):
    resposta = client.post(URL, cos, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {
        "biblioteca": ["Aquest camp és obligatori."],
        "llibres": ["Aquest camp és obligatori."],
    }


@pytest.mark.django_db
def test_una_comanda_sense_llibres(client, biblioteca):
    resposta = confirma(client, biblioteca.pk, [])

    assert resposta.status_code == 400
    assert resposta.json() == {"llibres": ["Afegeix almenys un llibre a la comanda."]}


@pytest.mark.django_db
def test_un_llibre_repetit(client, biblioteca, llibres):
    resposta = confirma(client, biblioteca.pk, [llibres[0].pk, llibres[0].pk])

    assert resposta.status_code == 400
    assert resposta.json() == {
        "llibres": ["Un llibre no pot sortir dues vegades a la mateixa comanda."]
    }


@pytest.mark.django_db
def test_un_llibre_que_no_existeix(client, biblioteca, llibres):
    resposta = confirma(client, biblioteca.pk, [llibres[0].pk, 999999])

    assert resposta.status_code == 400
    assert resposta.json() == {"llibres": ["Algun dels llibres no existeix."]}


@pytest.mark.django_db
@pytest.mark.parametrize("llibres_enviats", [["set"], [True], "7", [1.5]])
def test_llibres_que_no_son_identificadors(client, biblioteca, llibres_enviats):
    resposta = confirma(client, biblioteca.pk, llibres_enviats)

    assert resposta.status_code == 400
    assert resposta.json() == {"llibres": ["Algun dels llibres no existeix."]}


@pytest.mark.django_db
def test_la_biblioteca_ha_de_ser_una_biblioteca_activa(client, lector, llibres):
    inactiva = crea_biblioteca("inactiva@example.com", "Biblioteca inactiva")
    inactiva.is_active = False
    inactiva.save(update_fields=["is_active"])

    for id_biblioteca in (999999, lector.pk, inactiva.pk, "abc"):
        resposta = confirma(client, id_biblioteca, [llibres[0].pk])

        assert resposta.status_code == 400
        assert resposta.json() == {"biblioteca": ["La biblioteca no existeix."]}


@pytest.mark.django_db
@override_settings(LIMIT_LLIBRES_COMANDA=2)
def test_no_es_pot_superar_el_limit_de_llibres(client, biblioteca, llibres):
    tercer = crea_llibre("Mirall trencat", "9788475881355", biblioteca, exemplars=1)

    resposta = confirma(client, biblioteca.pk, [llibres[0].pk, llibres[1].pk, tercer.pk])

    assert resposta.status_code == 400
    assert resposta.json() == {"llibres": [LIMIT_SUPERAT]}
    assert not Comanda.objects.exists()


@pytest.mark.django_db
@override_settings(LIMIT_LLIBRES_COMANDA=2)
def test_es_pot_arribar_just_al_limit(client, biblioteca, llibres):
    resposta = confirma(client, biblioteca.pk, [llibre.pk for llibre in llibres])

    assert resposta.status_code == 201


@pytest.mark.django_db
def test_un_llibre_sense_exemplars_no_crea_la_comanda(client, biblioteca, llibres):
    esgotat = crea_llibre("Mirall trencat", "9788475881355", biblioteca, exemplars=0)

    resposta = confirma(client, biblioteca.pk, [llibres[0].pk, esgotat.pk])

    assert resposta.status_code == 400
    assert resposta.json() == {"llibres": [SENSE_ESTOC], "sense_estoc": [esgotat.pk]}
    assert not Comanda.objects.exists()


@pytest.mark.django_db
def test_un_llibre_que_la_biblioteca_no_te_compta_com_a_sense_estoc(client, biblioteca, llibres):
    altra = crea_biblioteca("altra@example.com", "Biblioteca Sant Gervasi")
    d_una_altra = crea_llibre("Mirall trencat", "9788475881355", altra, exemplars=3)

    resposta = confirma(client, biblioteca.pk, [llibres[0].pk, d_una_altra.pk])

    assert resposta.status_code == 400
    assert resposta.json()["sense_estoc"] == [d_una_altra.pk]


@pytest.mark.django_db
@override_settings(LIMIT_LLIBRES_COMANDA=1)
def test_el_limit_es_comprova_abans_que_l_estoc(client, biblioteca, llibres):
    esgotat = crea_llibre("Mirall trencat", "9788475881355", biblioteca, exemplars=0)

    resposta = confirma(client, biblioteca.pk, [llibres[0].pk, esgotat.pk])

    assert resposta.json() == {"llibres": [LIMIT_SUPERAT]}


@pytest.mark.django_db
def test_nomes_es_pot_fer_post(client):
    assert client.get(URL).status_code == 405
