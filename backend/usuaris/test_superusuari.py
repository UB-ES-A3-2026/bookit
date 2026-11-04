"""Tests de la creació de superusuaris (administradors de l'admin de Django)."""

import pytest
from django.contrib.auth import authenticate
from django.core.management import call_command

from usuaris.models import Usuari

CONTRASENYA = "Llibres-de-tardor-24"
DADES = {
    "name": "Admin",
    "address": "C/ Major 1",
    "library_card_number": "admin-bookit",
}


def comprova_superusuari(usuari):
    assert usuari.is_staff
    assert usuari.is_superuser
    assert usuari.is_active
    assert usuari.check_password(CONTRASENYA)


@pytest.mark.django_db
def test_la_contrasenya_es_desa_quan_arriba_amb_el_nom():
    """És com la passa l'ordre createsuperuser de Django."""
    usuari = Usuari.objects.create_superuser(
        email="admin@example.com", password=CONTRASENYA, **DADES
    )

    comprova_superusuari(usuari)


@pytest.mark.django_db
def test_la_contrasenya_es_desa_quan_arriba_com_a_argument():
    usuari = Usuari.objects.create_superuser("admin@example.com", CONTRASENYA, DADES)

    comprova_superusuari(usuari)


@pytest.mark.django_db
def test_l_ordre_createsuperuser_crea_un_administrador_que_pot_entrar(monkeypatch):
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", CONTRASENYA)

    call_command("createsuperuser", interactive=False, email="admin@example.com", **DADES)

    usuari = Usuari.objects.get(email="admin@example.com")
    comprova_superusuari(usuari)
    assert authenticate(email="admin@example.com", password=CONTRASENYA) == usuari


@pytest.mark.django_db
def test_l_administrador_pot_entrar_a_l_admin(client):
    Usuari.objects.create_superuser(email="admin@example.com", password=CONTRASENYA, **DADES)

    assert client.login(email="admin@example.com", password=CONTRASENYA)
    resposta = client.get("/admin/", HTTP_HOST="localhost")

    assert resposta.status_code == 200
