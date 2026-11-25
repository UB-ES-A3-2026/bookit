"""Tests unitaris del serializer de registre, sense passar per l'endpoint (US1-T6)."""

import pytest

from usuaris.models import Usuari
from usuaris.serializers import UsuariRegistreSerializer
from usuaris.test_registre import dades_valides


@pytest.mark.django_db
def test_tradueix_els_camps_publics_als_del_model():
    serializer = UsuariRegistreSerializer(data=dades_valides())
    assert serializer.is_valid(), serializer.errors

    usuari = serializer.save()

    assert usuari.name == "Anna Puig"
    assert usuari.email == "anna@example.com"
    assert usuari.address == "C/ Major 1, 08001 Barcelona"
    assert usuari.library_card_number == "1234567890"


@pytest.mark.django_db
def test_el_rol_sempre_es_usuari_encara_que_n_arribi_un_altre():
    serializer = UsuariRegistreSerializer(data=dades_valides(rol="biblioteca"))
    assert serializer.is_valid(), serializer.errors

    usuari = serializer.save()

    assert usuari.role == Usuari.Role.USUARI


@pytest.mark.django_db
def test_ignora_els_camps_que_no_son_del_contracte():
    serializer = UsuariRegistreSerializer(
        data=dades_valides(is_staff=True, is_superuser=True)
    )
    assert serializer.is_valid(), serializer.errors

    usuari = serializer.save()

    assert not usuari.is_staff
    assert not usuari.is_superuser


@pytest.mark.django_db
def test_la_representacio_no_inclou_la_contrasenya():
    usuari = Usuari.objects.create_user(
        email="anna@example.com",
        password="ContrasenyaSegura123!",
        name="Anna Puig",
        address="C/ Major 1",
        library_card_number="1234567890",
    )

    dades = UsuariRegistreSerializer(usuari).data

    assert set(dades) == {"id", "nom", "correu", "adreca", "num_carnet", "rol"}
