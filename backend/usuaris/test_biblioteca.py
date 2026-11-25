import pytest

from usuaris.models import Biblioteca, Usuari
from decimal import Decimal
from django.core.exceptions import ValidationError

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

@pytest.mark.django_db
def test_biblioteca_pot_tenir_carrer_numero_i_coordenades():
    usuari = Usuari.objects.create_user(
        "ubicada@example.com",
        "ContrasenyaSegura123!",
        dades_usuari(),
    )

    biblioteca = Biblioteca.objects.create(
        usuari=usuari,
        nom="Biblioteca Central",
        carrer="Carrer Major",
        numero_porta="12 bis",
        latitud=Decimal("41.979400"),
        longitud=Decimal("2.821400"),
    )

    biblioteca.full_clean()
    biblioteca.refresh_from_db()

    assert biblioteca.carrer == "Carrer Major"
    assert biblioteca.numero_porta == "12 bis"
    assert biblioteca.latitud == Decimal("41.979400")
    assert biblioteca.longitud == Decimal("2.821400")


@pytest.mark.django_db
def test_biblioteca_sense_coordenades_es_valida():
    usuari = Usuari.objects.create_user(
        "sense-ubicacio@example.com",
        "ContrasenyaSegura123!",
        dades_usuari(),
    )

    biblioteca = Biblioteca.objects.create(
        usuari=usuari,
        nom="Biblioteca sense ubicació",
    )

    biblioteca.full_clean()

    assert biblioteca.carrer == ""
    assert biblioteca.numero_porta == ""
    assert biblioteca.latitud is None
    assert biblioteca.longitud is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("camp", "valor"),
    [
        ("latitud", Decimal("-90.000001")),
        ("latitud", Decimal("90.000001")),
        ("longitud", Decimal("-180.000001")),
        ("longitud", Decimal("180.000001")),
    ],
)
def test_coordenada_fora_de_rang_es_rebutjada(camp, valor):
    usuari = Usuari.objects.create_user(
        f"{camp}-{valor}@example.com",
        "ContrasenyaSegura123!",
        dades_usuari(),
    )
    biblioteca = Biblioteca(
        usuari=usuari,
        nom="Biblioteca amb coordenada invàlida",
        **{camp: valor},
    )

    with pytest.raises(ValidationError):
        biblioteca.full_clean()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("latitud", "longitud"),
    [
        (Decimal("-90"), Decimal("-180")),
        (Decimal("90"), Decimal("180")),
    ],
)
def test_valors_limite_de_coordenades_s_accepten(latitud, longitud):
    usuari = Usuari.objects.create_user(
        f"limits-{latitud}-{longitud}@example.com",
        "ContrasenyaSegura123!",
        dades_usuari(),
    )
    biblioteca = Biblioteca(
        usuari=usuari,
        nom="Biblioteca als límits",
        latitud=latitud,
        longitud=longitud,
    )

    biblioteca.full_clean()


@pytest.mark.django_db
def test_biblioteca_existent_queda_sense_ubicacio_obligatoria():
    usuari = Usuari.objects.create_user(
        "existent@example.com",
        "ContrasenyaSegura123!",
        dades_usuari(),
    )
    Biblioteca.objects.create(usuari=usuari, nom="Biblioteca existent")

    biblioteca = Biblioteca.objects.get(usuari=usuari)

    assert biblioteca.carrer == ""
    assert biblioteca.numero_porta == ""
    assert biblioteca.latitud is None
    assert biblioteca.longitud is None
