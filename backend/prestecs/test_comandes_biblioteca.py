"""Tests de l'endpoint de comandes pendents de la biblioteca (US10-T1)."""

from datetime import date

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from cataleg.models import ExemplarBiblioteca, Llibre
from prestecs.models import Comanda, LiniaComanda
from usuaris.models import Biblioteca, Usuari

URL = "/api/prestecs/biblioteca/comandes/"
Estat = Comanda.Estat


def crea_usuari(correu, rol=Usuari.Role.USUARI, nom=None):
    return Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {"name": nom or correu.split("@")[0], "address": "C/ Major 1", "library_card_number": correu, "role": rol},
    )


def crea_biblioteca(correu, nom):
    usuari = crea_usuari(correu, Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=usuari, nom=nom)
    usuari.is_active = True
    usuari.save(update_fields=["is_active"])
    return usuari


@pytest.fixture
def biblioteca():
    return crea_biblioteca("biblioteca@example.com", "Biblioteca Montbau")


@pytest.fixture
def lector():
    return crea_usuari("anna@example.com", nom="Anna Puig")


@pytest.fixture
def llibre():
    return Llibre.objects.create(titol="Solitud", autor="Víctor Català", isbn="9788475882574")


@pytest.fixture
def client(biblioteca):
    client = APIClient()
    client.force_authenticate(biblioteca)
    return client


def crea_comanda(usuari, biblioteca, llibres, estat=Estat.REBUDA, data_lliurament=None):
    comanda = Comanda.objects.create(
        usuari=usuari, biblioteca=biblioteca, estat=estat, data_lliurament=data_lliurament
    )
    for llibre in llibres:
        LiniaComanda.objects.create(comanda=comanda, llibre=llibre)
    return comanda


@pytest.mark.django_db
def test_mostra_les_comandes_de_la_biblioteca_amb_l_usuari_i_els_llibres(client, biblioteca, lector, llibre):
    comanda = crea_comanda(lector, biblioteca, [llibre], data_lliurament=date(2026, 11, 20))

    resposta = client.get(URL)

    assert resposta.status_code == 200
    assert resposta.json() == [
        {
            "id": comanda.pk,
            "estat": "rebuda",
            "usuari": {"id": lector.pk, "nom": "Anna Puig"},
            "biblioteca": {"id": biblioteca.pk, "nom": "Biblioteca Montbau"},
            "llibres": [{"id": llibre.pk, "titol": "Solitud", "autor": "Víctor Català", "portada": ""}],
            "data_lliurament": "2026-11-20",
            "creada": resposta.json()[0]["creada"],
        }
    ]


@pytest.mark.django_db
def test_ordena_per_data_de_lliurament_i_deixa_al_final_les_que_no_en_tenen(client, biblioteca, lector, llibre):
    sense_data = crea_comanda(lector, biblioteca, [llibre])
    tard = crea_comanda(lector, biblioteca, [llibre], data_lliurament=date(2026, 11, 25))
    aviat = crea_comanda(lector, biblioteca, [llibre], data_lliurament=date(2026, 11, 18))

    ids = [comanda["id"] for comanda in client.get(URL).json()]

    assert ids == [aviat.pk, tard.pk, sense_data.pk]


@pytest.mark.django_db
def test_amb_la_mateixa_data_surt_primer_la_mes_antiga(client, biblioteca, lector, llibre):
    primera = crea_comanda(lector, biblioteca, [llibre], data_lliurament=date(2026, 11, 20))
    segona = crea_comanda(lector, biblioteca, [llibre], data_lliurament=date(2026, 11, 20))

    ids = [comanda["id"] for comanda in client.get(URL).json()]

    assert ids == [primera.pk, segona.pk]


@pytest.mark.django_db
def test_nomes_surten_les_rebudes_preparades_i_cancellades(client, biblioteca, lector, llibre):
    visibles = {
        estat: crea_comanda(lector, biblioteca, [llibre], estat=estat)
        for estat in (Estat.REBUDA, Estat.PREPARADA, Estat.CANCELLADA)
    }
    for estat in (Estat.EN_CAMI, Estat.LLIURADA):
        crea_comanda(lector, biblioteca, [llibre], estat=estat)

    estats = sorted(comanda["estat"] for comanda in client.get(URL).json())

    assert estats == sorted(visibles)


@pytest.mark.django_db
def test_no_mostra_les_comandes_d_altres_biblioteques(client, biblioteca, lector, llibre):
    altra = crea_biblioteca("altra@example.com", "Biblioteca Sant Gervasi")
    meva = crea_comanda(lector, biblioteca, [llibre])
    crea_comanda(lector, altra, [llibre])

    ids = [comanda["id"] for comanda in client.get(URL).json()]

    assert ids == [meva.pk]


@pytest.mark.django_db
def test_sense_comandes_retorna_una_llista_buida(client):
    resposta = client.get(URL)

    assert resposta.status_code == 200
    assert resposta.json() == []


@pytest.mark.django_db
def test_sense_sessio_rep_401():
    assert APIClient().get(URL).status_code == 401


@pytest.mark.django_db
@pytest.mark.parametrize("rol", [Usuari.Role.USUARI, Usuari.Role.REPARTIDOR])
def test_un_lector_o_un_repartidor_reben_403(rol):
    client = APIClient()
    client.force_authenticate(crea_usuari("altre@example.com", rol))

    assert client.get(URL).status_code == 403


@pytest.mark.django_db
def test_nomes_es_pot_consultar(client):
    assert client.post(URL, {}, format="json").status_code == 405


@pytest.mark.django_db
def test_el_nombre_de_consultes_no_creix_amb_les_comandes(client, biblioteca, lector, llibre):
    altre = Llibre.objects.create(titol="Mirall trencat", autor="Mercè Rodoreda", isbn="9788475881355")
    crea_comanda(lector, biblioteca, [llibre, altre])
    with CaptureQueriesContext(connection) as amb_una:
        client.get(URL)

    for _ in range(5):
        crea_comanda(lector, biblioteca, [llibre, altre])
    with CaptureQueriesContext(connection) as amb_sis:
        client.get(URL)

    assert len(amb_sis) == len(amb_una)


@pytest.mark.django_db
def test_les_que_no_tenen_data_surten_de_la_mes_antiga_a_la_mes_nova(client, biblioteca, lector, llibre):
    primera = crea_comanda(lector, biblioteca, [llibre])
    segona = crea_comanda(lector, biblioteca, [llibre])
    amb_data = crea_comanda(lector, biblioteca, [llibre], data_lliurament=date(2026, 12, 1))

    ids = [comanda["id"] for comanda in client.get(URL).json()]

    assert ids == [amb_data.pk, primera.pk, segona.pk]


@pytest.mark.django_db
def test_les_cancellades_s_ordenen_amb_les_altres_per_data(client, biblioteca, lector, llibre):
    preparada = crea_comanda(lector, biblioteca, [llibre], estat=Estat.PREPARADA, data_lliurament=date(2026, 11, 30))
    cancellada = crea_comanda(lector, biblioteca, [llibre], estat=Estat.CANCELLADA, data_lliurament=date(2026, 11, 22))
    rebuda = crea_comanda(lector, biblioteca, [llibre], data_lliurament=date(2026, 11, 25))

    comandes = client.get(URL).json()

    assert [(comanda["id"], comanda["estat"]) for comanda in comandes] == [
        (cancellada.pk, "cancellada"),
        (rebuda.pk, "rebuda"),
        (preparada.pk, "preparada"),
    ]


@pytest.mark.django_db
def test_els_llibres_surten_en_l_ordre_de_la_comanda(client, biblioteca, lector, llibre):
    mirall = Llibre.objects.create(titol="Mirall trencat", autor="Mercè Rodoreda", isbn="9788475881355")
    crea_comanda(lector, biblioteca, [mirall, llibre])

    titols = [del_llistat["titol"] for del_llistat in client.get(URL).json()[0]["llibres"]]

    assert titols == ["Mirall trencat", "Solitud"]


@pytest.mark.django_db
def test_cada_comanda_diu_de_quin_usuari_es(client, biblioteca, lector, llibre):
    altre = crea_usuari("pere@example.com", nom="Pere Vila")
    de_l_anna = crea_comanda(lector, biblioteca, [llibre], data_lliurament=date(2026, 11, 20))
    d_en_pere = crea_comanda(altre, biblioteca, [llibre], data_lliurament=date(2026, 11, 21))

    usuaris = {comanda["id"]: comanda["usuari"] for comanda in client.get(URL).json()}

    assert usuaris == {
        de_l_anna.pk: {"id": lector.pk, "nom": "Anna Puig"},
        d_en_pere.pk: {"id": altre.pk, "nom": "Pere Vila"},
    }


@pytest.mark.django_db
def test_una_comanda_confirmada_surt_a_la_llista_de_la_seva_biblioteca(client, biblioteca, lector, llibre):
    altra = crea_biblioteca("altra@example.com", "Biblioteca Sant Gervasi")
    ExemplarBiblioteca.objects.create(llibre=llibre, biblioteca=biblioteca, quantitat=1)
    usuari = APIClient()
    usuari.force_authenticate(lector)

    confirmada = usuari.post(
        "/api/prestecs/comandes/", {"biblioteca": biblioteca.pk, "llibres": [llibre.pk]}, format="json"
    )

    assert confirmada.status_code == 201
    assert [comanda["id"] for comanda in client.get(URL).json()] == [confirmada.json()["id"]]
    de_l_altra = APIClient()
    de_l_altra.force_authenticate(altra)
    assert de_l_altra.get(URL).json() == []


@pytest.mark.django_db
def test_una_biblioteca_desactivada_rep_403(client, biblioteca):
    biblioteca.is_active = False
    biblioteca.save(update_fields=["is_active"])

    resposta = client.get(URL)

    assert resposta.status_code == 403
    assert resposta.json() == {"detail": "No té permisos per realitzar aquesta acció."}


@pytest.mark.django_db
def test_un_compte_de_biblioteca_sense_perfil_rep_403():
    client = APIClient()
    sense_perfil = crea_usuari("sense-perfil@example.com", Usuari.Role.BIBLIOTECA)
    client.force_authenticate(sense_perfil)

    assert client.get(URL).status_code == 403
