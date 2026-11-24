"""Tests dels endpoints de les notificacions de l'usuari (US8-T3)."""

import pytest
from rest_framework.test import APIClient

from prestecs.models import Comanda, Notificacio
from usuaris.models import Biblioteca, Usuari

URL = "/api/prestecs/notificacions/"
URL_TOTES_LLEGIDES = "/api/prestecs/notificacions/llegides/"


def url_llegida(notificacio_id):
    return f"/api/prestecs/notificacions/{notificacio_id}/llegida/"


def crea_usuari(correu, rol=Usuari.Role.USUARI):
    return Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {"name": correu.split("@")[0], "address": "C/ Major 1", "library_card_number": correu, "role": rol},
    )


@pytest.fixture
def lector():
    return crea_usuari("lector@example.com")


@pytest.fixture
def client(lector):
    client = APIClient()
    client.force_authenticate(lector)
    return client


@pytest.fixture
def comanda(lector):
    biblioteca = crea_usuari("biblioteca@example.com", Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=biblioteca, nom="Biblioteca Montbau")
    return Comanda.objects.create(usuari=lector, biblioteca=biblioteca)


def notifica(comanda, text, llegida=False, usuari=None):
    return Notificacio.objects.create(
        usuari=usuari or comanda.usuari, comanda=comanda, text=text, llegida=llegida
    )


@pytest.mark.django_db
def test_llista_les_notificacions_de_la_mes_nova_a_la_mes_antiga(client, comanda):
    antiga = notifica(comanda, "La teva comanda s'ha rebut correctament.", llegida=True)
    nova = notifica(comanda, "La teva comanda ja està preparada.")

    resposta = client.get(URL)

    assert resposta.status_code == 200
    dades = resposta.json()
    assert [notificacio["id"] for notificacio in dades] == [nova.pk, antiga.pk]
    assert dades[0] == {
        "id": nova.pk,
        "comanda": comanda.pk,
        "text": "La teva comanda ja està preparada.",
        "llegida": False,
        "creada": dades[0]["creada"],
    }
    assert dades[1]["llegida"] is True


@pytest.mark.django_db
def test_no_surten_les_notificacions_d_altres_usuaris(client, comanda):
    meva = notifica(comanda, "Meva")
    notifica(comanda, "D'un altre", usuari=crea_usuari("altre@example.com"))

    ids = [notificacio["id"] for notificacio in client.get(URL).json()]

    assert ids == [meva.pk]


@pytest.mark.django_db
def test_sense_notificacions_retorna_una_llista_buida(client):
    assert client.get(URL).json() == []


@pytest.mark.django_db
def test_marca_una_notificacio_com_a_llegida(client, comanda):
    notificacio = notifica(comanda, "Nova")
    altra = notifica(comanda, "Una altra")

    resposta = client.post(url_llegida(notificacio.pk))

    assert resposta.status_code == 200
    assert resposta.json()["id"] == notificacio.pk
    assert resposta.json()["llegida"] is True
    notificacio.refresh_from_db()
    altra.refresh_from_db()
    assert notificacio.llegida
    assert not altra.llegida


@pytest.mark.django_db
def test_marcar_una_notificacio_ja_llegida_no_dona_error(client, comanda):
    notificacio = notifica(comanda, "Ja llegida", llegida=True)

    resposta = client.post(url_llegida(notificacio.pk))

    assert resposta.status_code == 200
    assert resposta.json()["llegida"] is True


@pytest.mark.django_db
def test_no_es_pot_marcar_la_notificacio_d_un_altre_usuari(client, comanda):
    d_un_altre = notifica(comanda, "D'un altre", usuari=crea_usuari("altre@example.com"))

    resposta = client.post(url_llegida(d_un_altre.pk))

    assert resposta.status_code == 404
    d_un_altre.refresh_from_db()
    assert not d_un_altre.llegida


@pytest.mark.django_db
def test_una_notificacio_que_no_existeix_dona_404(client):
    assert client.post(url_llegida(999999)).status_code == 404


@pytest.mark.django_db
def test_marca_totes_les_notificacions_com_a_llegides(client, comanda):
    notifica(comanda, "Primera")
    notifica(comanda, "Segona")
    notifica(comanda, "Ja llegida", llegida=True)

    resposta = client.post(URL_TOTES_LLEGIDES)

    assert resposta.status_code == 200
    assert resposta.json() == {"marcades": 2}
    assert not Notificacio.objects.filter(usuari=comanda.usuari, llegida=False).exists()


@pytest.mark.django_db
def test_marcar_totes_no_toca_les_d_altres_usuaris(client, comanda):
    d_un_altre = notifica(comanda, "D'un altre", usuari=crea_usuari("altre@example.com"))

    assert client.post(URL_TOTES_LLEGIDES).json() == {"marcades": 0}
    d_un_altre.refresh_from_db()
    assert not d_un_altre.llegida


@pytest.mark.django_db
def test_sense_sessio_rep_401(comanda):
    notificacio = notifica(comanda, "Nova")

    assert APIClient().get(URL).status_code == 401
    assert APIClient().post(url_llegida(notificacio.pk)).status_code == 401
    assert APIClient().post(URL_TOTES_LLEGIDES).status_code == 401


@pytest.mark.django_db
@pytest.mark.parametrize("rol", [Usuari.Role.BIBLIOTECA, Usuari.Role.REPARTIDOR])
def test_una_biblioteca_o_un_repartidor_reben_403(rol):
    client = APIClient()
    client.force_authenticate(crea_usuari("altre@example.com", rol))

    assert client.get(URL).status_code == 403
    assert client.post(URL_TOTES_LLEGIDES).status_code == 403


@pytest.mark.django_db
def test_la_llista_nomes_es_pot_consultar(client):
    assert client.post(URL, {}, format="json").status_code == 405
