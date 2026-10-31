import pytest

from usuaris.models import Biblioteca, Usuari


def dades_usuari():
    return {
        "name": "Biblioteca Central",
        "address": "C/ Major 1",
        "library_card_number": "1234567890",
    }


@pytest.mark.django_db
def test_biblioteca_crea_un_usuari_inactiu_amb_rol_biblioteca():
    usuari = Usuari.objects.create_user(
        "biblioteca@example.com",
        "ContrasenyaSegura123!",
        dades_usuari(),
    )

    biblioteca = Biblioteca.objects.create(usuari=usuari, nom="Biblioteca Central")

    usuari.refresh_from_db()
    assert biblioteca.nom == "Biblioteca Central"
    assert usuari.role == Usuari.Role.BIBLIOTECA
    assert usuari.is_active is False


@pytest.mark.django_db
def test_biblioteca_es_pot_activar_despres_de_verificar_el_correu():
    usuari = Usuari.objects.create_user(
        "biblioteca@example.com",
        "ContrasenyaSegura123!",
        dades_usuari(),
    )
    Biblioteca.objects.create(usuari=usuari, nom="Biblioteca Central")

    usuari.is_active = True
    usuari.save(update_fields=["is_active"])

    assert Usuari.objects.get(pk=usuari.pk).is_active is True
