"""Tests de la configuració de producció (D2): es carrega settings.py amb cada entorn."""

import os
import runpy
import subprocess
import sys
from pathlib import Path

import environ
import pytest
from django.core.exceptions import ImproperlyConfigured

DIR_BACKEND = Path(__file__).resolve().parent.parent
RUTA_SETTINGS = DIR_BACKEND / "config" / "settings.py"
CLAU_REAL = "x7Kq9-mZ2vLp4Rt8Yw3Nf6Hb1Sd5Gj0Ac-eUoIiPlMnBvCxZaQsWd"
VARIABLES = (
    "DJANGO_SECRET_KEY",
    "DJANGO_DEBUG",
    "DJANGO_ALLOWED_HOSTS",
    "CORS_ALLOWED_ORIGINS",
    "CSRF_TRUSTED_ORIGINS",
    "DJANGO_SECURE_SSL_REDIRECT",
    "DJANGO_SECURE_HSTS_SECONDS",
    "DJANGO_SESSION_COOKIE_SECURE",
    "DJANGO_CSRF_COOKIE_SECURE",
    "DJANGO_COOKIE_SAMESITE",
    "DJANGO_PROXY_HTTPS",
)


@pytest.fixture
def carrega_settings(monkeypatch):
    """Carrega settings.py només amb les variables indicades, sense llegir el .env local."""
    monkeypatch.setattr(environ.Env, "read_env", lambda *args, **kwargs: None)
    monkeypatch.setenv("POSTGRES_PASSWORD", "contrasenya-de-prova")
    for variable in VARIABLES:
        monkeypatch.delenv(variable, raising=False)

    def carrega(**variables):
        for nom, valor in variables.items():
            monkeypatch.setenv(nom, valor)
        return runpy.run_path(str(RUTA_SETTINGS))

    return carrega


def test_sense_variables_debug_queda_desactivat(carrega_settings):
    configuracio = carrega_settings(DJANGO_SECRET_KEY=CLAU_REAL)

    assert configuracio["DEBUG"] is False


def test_en_produccio_s_activen_https_i_cookies_segures(carrega_settings):
    configuracio = carrega_settings(DJANGO_SECRET_KEY=CLAU_REAL, DJANGO_DEBUG="False")

    assert configuracio["SECURE_SSL_REDIRECT"] is True
    assert configuracio["SECURE_HSTS_SECONDS"] > 0
    assert configuracio["SESSION_COOKIE_SECURE"] is True
    assert configuracio["CSRF_COOKIE_SECURE"] is True


def test_en_local_no_es_forca_https(carrega_settings):
    configuracio = carrega_settings(DJANGO_DEBUG="True")

    assert configuracio["DEBUG"] is True
    assert configuracio["SECURE_SSL_REDIRECT"] is False
    assert configuracio["SECURE_HSTS_SECONDS"] == 0
    assert configuracio["SESSION_COOKIE_SECURE"] is False
    assert configuracio["CSRF_COOKIE_SECURE"] is False


@pytest.mark.parametrize(
    "clau",
    ["", "canvieu-aquesta-clau", "django-insecure-nomes-per-desenvolupament"],
)
def test_en_produccio_es_rebutja_una_clau_d_exemple(carrega_settings, clau):
    with pytest.raises(ImproperlyConfigured):
        carrega_settings(DJANGO_SECRET_KEY=clau, DJANGO_DEBUG="False")


def test_en_produccio_es_rebutja_una_clau_absent(carrega_settings):
    with pytest.raises(ImproperlyConfigured):
        carrega_settings()


def test_els_dominis_es_llegeixen_de_l_entorn(carrega_settings):
    configuracio = carrega_settings(
        DJANGO_SECRET_KEY=CLAU_REAL,
        DJANGO_ALLOWED_HOSTS="api.bookit.test",
        CORS_ALLOWED_ORIGINS="https://bookit.test",
        CSRF_TRUSTED_ORIGINS="https://bookit.test,https://www.bookit.test",
    )

    assert configuracio["ALLOWED_HOSTS"] == ["api.bookit.test"]
    assert configuracio["CORS_ALLOWED_ORIGINS"] == ["https://bookit.test"]
    assert configuracio["CSRF_TRUSTED_ORIGINS"] == [
        "https://bookit.test",
        "https://www.bookit.test",
    ]


def test_sense_variables_no_hi_ha_cap_origen_de_confianca(carrega_settings):
    configuracio = carrega_settings(DJANGO_SECRET_KEY=CLAU_REAL)

    assert configuracio["CORS_ALLOWED_ORIGINS"] == []
    assert configuracio["CSRF_TRUSTED_ORIGINS"] == []


def test_les_opcions_es_poden_canviar_amb_l_entorn(carrega_settings):
    configuracio = carrega_settings(
        DJANGO_SECRET_KEY=CLAU_REAL,
        DJANGO_SECURE_SSL_REDIRECT="False",
        DJANGO_SECURE_HSTS_SECONDS="60",
        DJANGO_SESSION_COOKIE_SECURE="False",
        DJANGO_CSRF_COOKIE_SECURE="False",
        DJANGO_COOKIE_SAMESITE="None",
    )

    assert configuracio["SECURE_SSL_REDIRECT"] is False
    assert configuracio["SECURE_HSTS_SECONDS"] == 60
    assert configuracio["SESSION_COOKIE_SECURE"] is False
    assert configuracio["CSRF_COOKIE_SECURE"] is False
    assert configuracio["SESSION_COOKIE_SAMESITE"] == "None"
    assert configuracio["CSRF_COOKIE_SAMESITE"] == "None"


def test_la_capcalera_del_proxy_nomes_s_activa_si_es_demana(carrega_settings):
    assert "SECURE_PROXY_SSL_HEADER" not in carrega_settings(DJANGO_DEBUG="True")

    configuracio = carrega_settings(DJANGO_PROXY_HTTPS="True")

    assert configuracio["SECURE_PROXY_SSL_HEADER"] == (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )


def test_check_deploy_no_avisa_de_la_configuracio_de_d2():
    """HSTS amb subdominis i preload (W005, W021) s'han de decidir amb el domini real."""
    entorn = {
        **os.environ,
        "DJANGO_SECRET_KEY": CLAU_REAL,
        "DJANGO_DEBUG": "False",
        "DJANGO_ALLOWED_HOSTS": "api.bookit.test",
        "DJANGO_SECURE_SSL_REDIRECT": "True",
        "DJANGO_SECURE_HSTS_SECONDS": "3600",
        "DJANGO_SESSION_COOKIE_SECURE": "True",
        "DJANGO_CSRF_COOKIE_SECURE": "True",
        "POSTGRES_PASSWORD": "contrasenya-de-prova",
    }

    resultat = subprocess.run(
        [sys.executable, "manage.py", "check", "--deploy"],
        cwd=DIR_BACKEND,
        env=entorn,
        capture_output=True,
        text=True,
    )

    assert resultat.returncode == 0, resultat.stderr
    for avis in ("W004", "W008", "W009", "W012", "W016", "W018", "W020"):
        assert f"security.{avis}" not in resultat.stderr
