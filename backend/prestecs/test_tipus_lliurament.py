"""Tests del tipus de lliurament i del cost d'enviament de la comanda (US7-T1)."""

from decimal import Decimal

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from cataleg.models import ExemplarBiblioteca, Llibre
from prestecs.models import Comanda
from prestecs.serveis import confirma_comanda, cost_enviament
from usuaris.models import Biblioteca, Usuari

URL = "/api/prestecs/comandes/"
URL_COST = "/api/prestecs/comandes/cost-enviament/"


def crea_usuari(correu, rol=Usuari.Role.USUARI, adreca="C/ Major 1"):
    return Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {"name": correu.split("@")[0], "address": adreca, "library_card_number": correu, "role": rol},
    )


@pytest.fixture
def lector():
    return crea_usuari("lector@example.com", adreca="C/ de la Muntanya 12, Barcelona")


@pytest.fixture
def client(lector):
    client = APIClient()
    client.force_authenticate(lector)
    return client


@pytest.fixture
def biblioteca():
    usuari = crea_usuari("biblioteca@example.com", Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=usuari, nom="Biblioteca Montbau")
    usuari.is_active = True
    usuari.save(update_fields=["is_active"])
    return usuari


@pytest.fixture
def llibre(biblioteca):
    llibre = Llibre.objects.create(titol="Solitud", autor="Víctor Català", isbn="9788475882574")
    ExemplarBiblioteca.objects.create(llibre=llibre, biblioteca=biblioteca, quantitat=3)
    return llibre


def confirma(client, biblioteca, llibre, **dades):
    return client.post(URL, {"biblioteca": biblioteca.pk, "llibres": [llibre.pk], **dades}, format="json")


@pytest.mark.django_db
@override_settings(COST_ENVIAMENT_DOMICILI=Decimal("2.50"))
def test_a_domicili_es_porta_a_l_adreca_indicada_i_te_cost(client, biblioteca, llibre):
    resposta = confirma(
        client, biblioteca, llibre, tipus_lliurament="domicili", adreca_lliurament="Pg. de Gràcia 5, Barcelona"
    )

    assert resposta.status_code == 201
    dades = resposta.json()
    assert dades["tipus_lliurament"] == "domicili"
    assert dades["adreca_lliurament"] == "Pg. de Gràcia 5, Barcelona"
    assert dades["cost_enviament"] == "2.50"


@pytest.mark.django_db
def test_la_recollida_es_gratuita_i_no_porta_adreca(client, biblioteca, llibre):
    resposta = confirma(
        client, biblioteca, llibre, tipus_lliurament="recollida", adreca_lliurament="Pg. de Gràcia 5, Barcelona"
    )

    assert resposta.status_code == 201
    dades = resposta.json()
    assert dades["tipus_lliurament"] == "recollida"
    assert dades["adreca_lliurament"] == ""
    assert dades["cost_enviament"] == "0.00"


@pytest.mark.django_db
@override_settings(COST_ENVIAMENT_DOMICILI=Decimal("2.50"))
def test_per_defecte_es_a_domicili_amb_l_adreca_del_perfil(client, biblioteca, llibre):
    resposta = confirma(client, biblioteca, llibre)

    assert resposta.status_code == 201
    dades = resposta.json()
    assert dades["tipus_lliurament"] == "domicili"
    assert dades["adreca_lliurament"] == "C/ de la Muntanya 12, Barcelona"
    assert dades["cost_enviament"] == "2.50"


@pytest.mark.django_db
def test_una_adreca_buida_fa_servir_la_del_perfil(client, biblioteca, llibre):
    resposta = confirma(client, biblioteca, llibre, adreca_lliurament="   ")

    assert resposta.json()["adreca_lliurament"] == "C/ de la Muntanya 12, Barcelona"


@pytest.mark.django_db
def test_a_domicili_sense_cap_adreca_dona_error(biblioteca, llibre):
    client = APIClient()
    client.force_authenticate(crea_usuari("sense@example.com", adreca=""))

    resposta = confirma(client, biblioteca, llibre, tipus_lliurament="domicili")

    assert resposta.status_code == 400
    assert resposta.json() == {"adreca_lliurament": ["Indica l'adreça de lliurament."]}
    assert not Comanda.objects.exists()
    assert ExemplarBiblioteca.objects.get(llibre=llibre).quantitat == 3


@pytest.mark.django_db
def test_sense_adreca_es_pot_recollir_a_la_biblioteca(biblioteca, llibre):
    client = APIClient()
    client.force_authenticate(crea_usuari("sense@example.com", adreca=""))

    resposta = confirma(client, biblioteca, llibre, tipus_lliurament="recollida")

    assert resposta.status_code == 201


@pytest.mark.django_db
@pytest.mark.parametrize("tipus", ["correu", "", None, 3])
def test_un_tipus_de_lliurament_que_no_existeix(client, biblioteca, llibre, tipus):
    resposta = confirma(client, biblioteca, llibre, tipus_lliurament=tipus)

    assert resposta.status_code == 400
    assert resposta.json() == {"tipus_lliurament": ["Tria lliurament a domicili o recollida a la biblioteca."]}


@pytest.mark.django_db
@override_settings(COST_ENVIAMENT_DOMICILI=Decimal("2.50"))
def test_el_cost_es_desa_a_la_comanda_i_no_canvia_amb_la_tarifa(lector, biblioteca, llibre):
    comanda = confirma_comanda(lector, biblioteca, [llibre], "domicili", "C/ Major 1")

    with override_settings(COST_ENVIAMENT_DOMICILI=Decimal("4.00")):
        comanda.refresh_from_db()
        assert comanda.cost_enviament == Decimal("2.50")


@pytest.mark.django_db
@override_settings(COST_ENVIAMENT_DOMICILI=Decimal("3.75"))
def test_el_cost_a_domicili_es_configurable():
    assert cost_enviament(Comanda.TipusLliurament.DOMICILI) == Decimal("3.75")
    assert cost_enviament(Comanda.TipusLliurament.RECOLLIDA) == Decimal("0.00")


@pytest.mark.django_db
@override_settings(COST_ENVIAMENT_DOMICILI=Decimal("2.50"))
def test_l_endpoint_de_cost_dona_el_cost_de_cada_tipus(client):
    resposta = client.get(URL_COST)

    assert resposta.status_code == 200
    assert resposta.json() == {"domicili": "2.50", "recollida": "0.00"}


@pytest.mark.django_db
def test_el_cost_d_enviament_sense_sessio_rep_401():
    assert APIClient().get(URL_COST).status_code == 401


@pytest.mark.django_db
def test_una_biblioteca_no_pot_consultar_el_cost_d_enviament(biblioteca):
    client = APIClient()
    client.force_authenticate(biblioteca)

    assert client.get(URL_COST).status_code == 403


@pytest.mark.django_db
def test_una_adreca_null_fa_servir_la_del_perfil(client, biblioteca, llibre):
    resposta = confirma(client, biblioteca, llibre, adreca_lliurament=None)

    assert resposta.status_code == 201
    assert resposta.json()["adreca_lliurament"] == "C/ de la Muntanya 12, Barcelona"


@pytest.mark.django_db
def test_l_adreca_es_desa_sense_espais_als_extrems(client, biblioteca, llibre):
    resposta = confirma(client, biblioteca, llibre, adreca_lliurament="  Pg. de Gràcia 5, Barcelona  ")

    assert resposta.json()["adreca_lliurament"] == "Pg. de Gràcia 5, Barcelona"


@pytest.mark.django_db
def test_la_resposta_coincideix_amb_el_que_es_desa(client, biblioteca, llibre):
    resposta = confirma(client, biblioteca, llibre, tipus_lliurament="recollida")

    comanda = Comanda.objects.get(pk=resposta.json()["id"])
    assert comanda.tipus_lliurament == Comanda.TipusLliurament.RECOLLIDA
    assert comanda.adreca_lliurament == ""
    assert comanda.cost_enviament == Decimal("0.00")


@pytest.mark.django_db
@override_settings(COST_ENVIAMENT_DOMICILI=Decimal("3.5"))
def test_el_cost_sempre_surt_amb_dos_decimals(client, biblioteca, llibre):
    assert confirma(client, biblioteca, llibre).json()["cost_enviament"] == "3.50"


@pytest.mark.django_db
def test_una_recollida_sense_biblioteca_dona_error(client, llibre):
    resposta = client.post(URL, {"llibres": [llibre.pk], "tipus_lliurament": "recollida"}, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {"biblioteca": ["Aquest camp és obligatori."]}


@pytest.mark.django_db
def test_sense_adreca_i_amb_un_tipus_incorrecte_nomes_surt_l_error_del_tipus(biblioteca, llibre):
    client = APIClient()
    client.force_authenticate(crea_usuari("sense@example.com", adreca=""))

    resposta = confirma(client, biblioteca, llibre, tipus_lliurament="correu")

    assert resposta.json() == {"tipus_lliurament": ["Tria lliurament a domicili o recollida a la biblioteca."]}


@pytest.mark.django_db
def test_sense_adreca_i_sense_llibres_nomes_surt_l_error_dels_llibres(biblioteca):
    client = APIClient()
    client.force_authenticate(crea_usuari("sense@example.com", adreca=""))

    resposta = client.post(URL, {"biblioteca": biblioteca.pk, "llibres": []}, format="json")

    assert resposta.json() == {"llibres": ["Afegeix almenys un llibre a la comanda."]}


@pytest.mark.django_db
def test_l_error_de_l_adreca_surt_abans_que_el_de_l_estoc(biblioteca, llibre):
    ExemplarBiblioteca.objects.filter(llibre=llibre).update(quantitat=0)
    client = APIClient()
    client.force_authenticate(crea_usuari("sense@example.com", adreca=""))

    resposta = confirma(client, biblioteca, llibre)

    assert resposta.json() == {"adreca_lliurament": ["Indica l'adreça de lliurament."]}


@pytest.mark.django_db
def test_una_recollida_sense_estoc_tambe_dona_l_error_d_estoc(client, biblioteca, llibre):
    ExemplarBiblioteca.objects.filter(llibre=llibre).update(quantitat=0)

    resposta = confirma(client, biblioteca, llibre, tipus_lliurament="recollida")

    assert resposta.status_code == 400
    assert resposta.json()["sense_estoc"] == [llibre.pk]
    assert not Comanda.objects.exists()


@pytest.mark.django_db
def test_un_repartidor_no_pot_consultar_el_cost_d_enviament():
    client = APIClient()
    client.force_authenticate(crea_usuari("repartidor@example.com", Usuari.Role.REPARTIDOR))

    assert client.get(URL_COST).status_code == 403


@pytest.mark.django_db
def test_el_cost_d_enviament_nomes_es_pot_consultar(client):
    assert client.post(URL_COST, {}, format="json").status_code == 405
