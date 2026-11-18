"""Tests de l'endpoint per marcar una comanda com a llesta per a recollida (US15-T1)."""

import pytest
from rest_framework.test import APIClient

from cataleg.models import Llibre
from prestecs.models import Comanda, LiniaComanda
from usuaris.models import Biblioteca, Usuari

Estat = Comanda.Estat


def url(comanda_id):
    return f"/api/prestecs/biblioteca/comandes/{comanda_id}/preparada/"


def crea_usuari(correu, rol=Usuari.Role.USUARI):
    return Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {"name": correu.split("@")[0], "address": "C/ Major 1", "library_card_number": correu, "role": rol},
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
def client(biblioteca):
    client = APIClient()
    client.force_authenticate(biblioteca)
    return client


@pytest.fixture
def comanda(biblioteca):
    comanda = Comanda.objects.create(usuari=crea_usuari("lector@example.com"), biblioteca=biblioteca)
    llibre = Llibre.objects.create(titol="Solitud", autor="Víctor Català", isbn="9788475882574")
    LiniaComanda.objects.create(comanda=comanda, llibre=llibre)
    return comanda


@pytest.mark.django_db
def test_marca_una_comanda_rebuda_com_a_llesta(client, comanda):
    resposta = client.post(url(comanda.pk))

    assert resposta.status_code == 200
    assert resposta.json()["id"] == comanda.pk
    assert resposta.json()["estat"] == "preparada"
    comanda.refresh_from_db()
    assert comanda.estat == Estat.PREPARADA


@pytest.mark.django_db
def test_el_canvi_queda_a_l_historial_de_la_comanda(client, comanda):
    client.post(url(comanda.pk))

    assert list(comanda.canvis_estat.values_list("estat", flat=True)) == [Estat.PREPARADA]


@pytest.mark.django_db
def test_una_comanda_que_ja_esta_llesta_dona_409(client, comanda):
    comanda.estat = Estat.PREPARADA
    comanda.save()

    resposta = client.post(url(comanda.pk))

    assert resposta.status_code == 409
    assert resposta.json() == {"detail": "Aquesta comanda ja està llesta per a recollida."}
    assert not comanda.canvis_estat.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("estat", "text"),
    [(Estat.EN_CAMI, "en camí"), (Estat.LLIURADA, "lliurada"), (Estat.CANCELLADA, "cancel·lada")],
)
def test_una_comanda_que_ja_ha_sortit_o_s_ha_cancellat_no_es_pot_marcar(client, comanda, estat, text):
    comanda.estat = estat
    comanda.save()

    resposta = client.post(url(comanda.pk))

    assert resposta.status_code == 409
    assert resposta.json() == {"detail": f"Aquesta comanda no es pot marcar com a llesta perquè està {text}."}
    comanda.refresh_from_db()
    assert comanda.estat == estat


@pytest.mark.django_db
def test_una_comanda_d_una_altra_biblioteca_dona_404(comanda):
    client = APIClient()
    client.force_authenticate(crea_biblioteca("altra@example.com", "Biblioteca Sant Gervasi"))

    resposta = client.post(url(comanda.pk))

    assert resposta.status_code == 404
    comanda.refresh_from_db()
    assert comanda.estat == Estat.REBUDA


@pytest.mark.django_db
def test_una_comanda_que_no_existeix_dona_404(client):
    assert client.post(url(999999)).status_code == 404


@pytest.mark.django_db
def test_sense_sessio_rep_401(comanda):
    assert APIClient().post(url(comanda.pk)).status_code == 401


@pytest.mark.django_db
@pytest.mark.parametrize("rol", [Usuari.Role.USUARI, Usuari.Role.REPARTIDOR])
def test_un_lector_o_un_repartidor_reben_403(comanda, rol):
    client = APIClient()
    client.force_authenticate(crea_usuari("altre@example.com", rol))

    assert client.post(url(comanda.pk)).status_code == 403


@pytest.mark.django_db
def test_una_biblioteca_inactiva_rep_403(client, biblioteca, comanda):
    biblioteca.is_active = False
    biblioteca.save(update_fields=["is_active"])

    assert client.post(url(comanda.pk)).status_code == 403


@pytest.mark.django_db
def test_nomes_es_pot_fer_post(client, comanda):
    assert client.get(url(comanda.pk)).status_code == 405
