"""Tests de l'endpoint de salut de l'API (C16)."""

from django.urls import reverse

URL = "/api/health/"


def test_get_retorna_200_i_status_ok(client):
    resposta = client.get(URL)
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_es_accessible_sense_autenticacio(client):
    resposta = client.get(URL)
    assert resposta.status_code not in (401, 403)


def test_la_ruta_es_correspon_amb_el_nom(client):
    assert reverse("salut") == URL


def test_post_retorna_405(client):
    resposta = client.post(URL)
    assert resposta.status_code == 405


def test_altres_metodes_retornen_405(client):
    assert client.put(URL).status_code == 405
    assert client.delete(URL).status_code == 405
