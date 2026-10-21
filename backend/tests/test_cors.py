"""Tests de la configuració de CORS (US1-T17)."""

import pytest
from django.conf import settings as configuracio

ORIGEN_FRONTEND = "http://localhost:5173"
ALTRE_ORIGEN = "http://altre-origen.test"
URL_REGISTRE = "/api/auth/register/"


@pytest.fixture(autouse=True)
def origens_permesos(settings):
    settings.CORS_ALLOWED_ORIGINS = [ORIGEN_FRONTEND]


def preflight(client, origen):
    """Petició OPTIONS que el navegador envia abans d'un POST amb JSON des d'un altre origen."""
    return client.options(
        URL_REGISTRE,
        HTTP_ORIGIN=origen,
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type",
    )


def test_el_preflight_des_del_frontend_es_permet(client):
    resposta = preflight(client, ORIGEN_FRONTEND)

    assert resposta.status_code == 200
    assert resposta["Access-Control-Allow-Origin"] == ORIGEN_FRONTEND
    assert "POST" in resposta["Access-Control-Allow-Methods"]
    assert "content-type" in resposta["Access-Control-Allow-Headers"]


def test_el_preflight_des_d_un_altre_origen_no_es_permet(client):
    resposta = preflight(client, ALTRE_ORIGEN)

    assert "Access-Control-Allow-Origin" not in resposta


def test_sense_origens_configurats_no_es_permet_cap_origen(client, settings):
    settings.CORS_ALLOWED_ORIGINS = []

    resposta = preflight(client, ORIGEN_FRONTEND)

    assert "Access-Control-Allow-Origin" not in resposta


def test_les_respostes_de_l_api_porten_la_capcalera_cors(client):
    resposta = client.get("/api/health/", HTTP_ORIGIN=ORIGEN_FRONTEND)

    assert resposta.status_code == 200
    assert resposta["Access-Control-Allow-Origin"] == ORIGEN_FRONTEND


def test_les_respostes_sense_origen_no_porten_la_capcalera_cors(client):
    resposta = client.get("/api/health/")

    assert "Access-Control-Allow-Origin" not in resposta


def test_el_middleware_de_cors_va_abans_del_common_middleware():
    middleware = configuracio.MIDDLEWARE

    assert middleware.index("corsheaders.middleware.CorsMiddleware") < middleware.index(
        "django.middleware.common.CommonMiddleware"
    )
