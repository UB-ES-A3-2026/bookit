"""Tests de la configuració del projecte: pytest-django i connexió a la base de dades."""

import pytest
from django.conf import settings
from django.db import connection


def test_carrega_la_configuracio_de_django():
    assert settings.ROOT_URLCONF == "config.urls"
    assert "rest_framework" in settings.INSTALLED_APPS


@pytest.mark.django_db
def test_es_connecta_a_postgresql():
    connection.ensure_connection()
    assert connection.is_usable()
    assert connection.vendor == "postgresql"


@pytest.mark.django_db
def test_fa_servir_una_base_de_dades_de_proves():
    assert connection.settings_dict["NAME"].startswith("test_")


def test_ruta_inexistent_retorna_404(client):
    resposta = client.get("/api/no-existeix/")
    assert resposta.status_code == 404
