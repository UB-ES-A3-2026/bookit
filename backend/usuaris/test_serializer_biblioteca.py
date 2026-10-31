import pytest

from usuaris.models import Usuari
from usuaris.serializers import (
    BibliotecaRegistreSerializer,
    CAMPS_BIBLIOTECA_INVALIDS,
    CORREU_BIBLIOTECA_DUPLICAT,
)


def dades_valides():
    return {"nom": "Biblioteca Central", "correu": "biblioteca@example.com"}


def test_serializer_biblioteca_accepta_nom_i_correu():
    serializer = BibliotecaRegistreSerializer(data=dades_valides())

    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data == dades_valides()


@pytest.mark.parametrize("camp", ["nom", "correu"])
def test_serializer_biblioteca_rebutja_camp_absent(camp):
    dades = dades_valides()
    del dades[camp]
    serializer = BibliotecaRegistreSerializer(data=dades)

    assert not serializer.is_valid()
    assert serializer.errors[camp] == [CAMPS_BIBLIOTECA_INVALIDS]


def test_serializer_biblioteca_rebutja_correu_invalid():
    serializer = BibliotecaRegistreSerializer(
        data={"nom": "Biblioteca Central", "correu": "no-es-un-correu"}
    )

    assert not serializer.is_valid()
    assert serializer.errors == {"correu": [CAMPS_BIBLIOTECA_INVALIDS]}


@pytest.mark.django_db
def test_serializer_biblioteca_rebutja_correu_duplicat():
    Usuari.objects.create_user(
        "biblioteca@example.com",
        "ContrasenyaSegura123!",
        {
            "name": "Biblioteca existent",
            "address": "C/ Major 1",
            "library_card_number": "1234567890",
        },
    )

    serializer = BibliotecaRegistreSerializer(data=dades_valides())

    assert not serializer.is_valid()
    assert serializer.errors == {"correu": [CORREU_BIBLIOTECA_DUPLICAT]}
