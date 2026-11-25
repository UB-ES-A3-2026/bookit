"""Tests del gestor d'usuaris: create_user, create_superuser i l'ordre createsuperuser."""

import pytest
from django.core.management import call_command

from usuaris.models import Usuari

CAMPS = {
    "name": "Anna Puig",
    "address": "C/ Major 1",
    "library_card_number": "1234567890",
}


@pytest.mark.django_db
def test_create_user_accepta_els_camps_en_un_diccionari():
    usuari = Usuari.objects.create_user(
        "anna@example.com", "una-Contrasenya-segura-9", CAMPS
    )

    assert usuari.name == "Anna Puig"
    assert usuari.check_password("una-Contrasenya-segura-9")


@pytest.mark.django_db
def test_create_user_accepta_els_camps_amb_nom():
    usuari = Usuari.objects.create_user(
        email="anna@example.com", password="una-Contrasenya-segura-9", **CAMPS
    )

    assert usuari.library_card_number == "1234567890"
    assert usuari.check_password("una-Contrasenya-segura-9")


@pytest.mark.django_db
def test_create_superuser_dona_permisos_d_administrador():
    usuari = Usuari.objects.create_superuser(
        "admin@example.com", "una-Contrasenya-segura-9", CAMPS
    )

    assert usuari.is_staff
    assert usuari.is_superuser


@pytest.mark.django_db
def test_create_superuser_sense_is_staff_dona_error():
    with pytest.raises(ValueError):
        Usuari.objects.create_superuser(
            "admin@example.com", "una-Contrasenya-segura-9", is_staff=False, **CAMPS
        )


@pytest.mark.django_db
def test_l_ordre_createsuperuser_crea_l_administrador():
    call_command("createsuperuser", interactive=False, email="admin@example.com", **CAMPS)

    usuari = Usuari.objects.get(email="admin@example.com")
    assert usuari.is_superuser
