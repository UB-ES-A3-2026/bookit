"""Tests del validador d'ISBN-10 i ISBN-13 (US17-T2)."""

import pytest
from django.core.exceptions import ValidationError

from cataleg.validacions import (
    ISBN_INVALID,
    es_isbn_valid,
    normalitza_isbn,
    valida_isbn,
)


# Tests de normalització


@pytest.mark.parametrize(
    "entrada, esperat",
    [
        ("978-84-376-0494-7", "9788437604947"),
        ("978 84 376 0494 7", "9788437604947"),
        ("0-8044-2957-x", "080442957X"),
        ("", ""),
        (None, ""),
        (9788437604947, ""),
    ],
)
def test_normalitza_isbn_elimina_guions_i_espais(entrada, esperat):
    assert normalitza_isbn(entrada) == esperat


# Casos correctes


@pytest.mark.parametrize(
    "valor",
    [
        "9788437604947",
        "978-84-376-0494-7",
        "978 84 376 0494 7",
        "9780306406157",
        "979-10-90636-07-1",
        "0306406152",
        "0-306-40615-2",
        "0-8044-2957-X",
        "080442957x",
    ],
)
def test_isbn_valid(valor):
    assert es_isbn_valid(valor)
    valida_isbn(valor)


# Casos d'error


@pytest.mark.parametrize(
    "valor",
    [
        "9788437604948",  # dígit de control incorrecte
        "978-84-376-0494-0",
        "0306406153",  # dígit de control incorrecte
        "0-8044-2957-9",
        "9771234567898",  # ISBN-13 que no comença per 978 ni 979
        "X306406152",  # la X només pot anar al final
        "978030640615X",  # l'ISBN-13 no admet X
        "030640615",  # massa curt
        "03064061522",  # 11 caràcters
        "97803064061577",  # massa llarg
        "978-0-306-4O615-7",  # lletra O en lloc d'un zero
        "978.0.306.40615.7",  # separadors no admesos
        "",
        "   ",
        None,
        9780306406157,
    ],
)
def test_isbn_invalid(valor):
    assert not es_isbn_valid(valor)
    with pytest.raises(ValidationError) as error:
        valida_isbn(valor)
    assert error.value.messages == [ISBN_INVALID]
    assert error.value.code == "invalid"


def test_missatge_d_error():
    assert ISBN_INVALID == "L'ISBN introduït no és vàlid"
