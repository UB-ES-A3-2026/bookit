"""Tests dels validadors de DNI/NIE, telèfon, matrícula i Seguretat Social (US1.1-T2)."""

import pytest
from django.core.exceptions import ValidationError

from usuaris.validacions import (
    DNI_NIE_INVALID,
    MATRICULA_INVALIDA,
    SEGURETAT_SOCIAL_INVALIDA,
    TELEFON_INVALID,
    es_dni_nie_valid,
    es_matricula_valida,
    es_num_seguretat_social_valid,
    es_telefon_valid,
    normalitza,
    valida_dni_nie,
    valida_matricula,
    valida_num_seguretat_social,
    valida_telefon,
)


# Tests de normalització


@pytest.mark.parametrize(
    "entrada, esperat",
    [
        ("123 456", "123456"),
        ("123-456", "123456"),
        ("123/456", "123456"),
        ("  123 - 456 / 789  ", "123456789"),
        ("1234bcd", "1234BCD"),
        ("+34 612 345 678", "+34612345678"),
        ("", ""),
        (None, ""),
        (12345, ""),
    ],
)
def test_normalitza_elimina_separadors_i_passa_a_majuscules(entrada, esperat):
    assert normalitza(entrada) == esperat


# Tests de DNI / NIE


@pytest.mark.parametrize(
    "valor",
    [
        "12345678Z",
        "12345678-Z",
        "12 345 678 Z",
        "12345678/z",
        "12345678z",
        "00000000T",
        "99999999R",
        "X1234567L",
        "X-1234567-L",
        "x 1234567 l",
        "Y1234567X",
        "y-1234567-x",
        "Z1234567R",
        "z/1234567/r",
    ],
)
def test_dni_nie_valid(valor):
    assert es_dni_nie_valid(valor) is True
    # No ha de llançar cap excepció
    valida_dni_nie(valor)


@pytest.mark.parametrize(
    "valor",
    [
        "12345678A",  # Lletra incorrecta (hauria de ser Z)
        "X1234567A",  # Lletra incorrecta (hauria de ser L)
        "Y1234567A",  # Lletra incorrecta (hauria de ser X)
        "Z1234567A",  # Lletra incorrecta (hauria de ser R)
        "1234567Z",  # Falta 1 dígit
        "123456789Z",  # Sobra 1 dígit
        "X123456L",  # NIE amb menys dígits
        "X12345678L",  # NIE amb més dígits
        "K1234567L",  # Lletra inicial no permesa per a NIE (només X, Y, Z)
        "A1234567L",
        "12345678",  # Sense lletra
        "ABCDEFGHI",  # Només lletres
        "",
        None,
        12345678,
    ],
)
def test_dni_nie_invalid(valor):
    assert es_dni_nie_valid(valor) is False
    with pytest.raises(ValidationError) as exc_info:
        valida_dni_nie(valor)
    assert exc_info.value.messages == [DNI_NIE_INVALID]
    assert exc_info.value.code == "invalid"


# Tests de Telèfon


@pytest.mark.parametrize(
    "valor",
    [
        "612345678",
        "712345678",
        "812345678",
        "933123456",
        "+34 612 345 678",
        "+34612345678",
        "+34-933-12-34-56",
        "+34/612/345/678",
        "612-34-56-78",
        " 612 345 678 ",
    ],
)
def test_telefon_valid(valor):
    assert es_telefon_valid(valor) is True
    valida_telefon(valor)


@pytest.mark.parametrize(
    "valor",
    [
        "512345678",  # Comença per 5
        "123456789",  # Comença per 1
        "012345678",  # Comença per 0
        "612345",  # Massa curt
        "61234567",  # 8 dígits
        "6123456789",  # 10 dígits
        "+33 612345678",  # Prefix internacional diferent de +34
        "+1612345678",
        "61234567A",  # Conté lletres
        "telèfon",
        "",
        None,
        612345678,
    ],
)
def test_telefon_invalid(valor):
    assert es_telefon_valid(valor) is False
    with pytest.raises(ValidationError) as exc_info:
        valida_telefon(valor)
    assert exc_info.value.messages == [TELEFON_INVALID]
    assert exc_info.value.code == "invalid"


# Tests de Matrícula


@pytest.mark.parametrize(
    "valor",
    [
        "1234 BCD",
        "1234-BCD",
        "1234/BCD",
        "1234bcd",
        "0000 ZZZ",
        "9999-FGH",
        "5678 JKL",
        " 1234 bcd ",
    ],
)
def test_matricula_valida(valor):
    assert es_matricula_valida(valor) is True
    valida_matricula(valor)


@pytest.mark.parametrize(
    "valor",
    [
        "1234 ABC",  # Conté vocal A
        "1234 BED",  # Conté vocal E
        "1234 BCI",  # Conté vocal I
        "1234 BCO",  # Conté vocal O
        "1234 BCU",  # Conté vocal U
        "1234 BCÑ",  # Conté consonant prohibida Ñ
        "1234 BCQ",  # Conté consonant prohibida Q
        "123 BCD",  # 3 dígits
        "12345 BCD",  # 5 dígits
        "1234 BC",  # 2 lletres
        "1234 BCDE",  # 4 lletres
        "BCD 1234",  # Ordre invertit
        "1234-123",  # Sense lletres
        "",
        None,
        1234,
    ],
)
def test_matricula_invalida(valor):
    assert es_matricula_valida(valor) is False
    with pytest.raises(ValidationError) as exc_info:
        valida_matricula(valor)
    assert exc_info.value.messages == [MATRICULA_INVALIDA]
    assert exc_info.value.code == "invalid"


# Tests de Número de la Seguretat Social


@pytest.mark.parametrize(
    "valor",
    [
        "28/12345678/90",
        "28 12345678 90",
        "28-12345678-90",
        "281234567890",
        "081234567890",
        "  28 / 12345678 / 90  ",
    ],
)
def test_num_seguretat_social_valid(valor):
    assert es_num_seguretat_social_valid(valor) is True
    valida_num_seguretat_social(valor)


@pytest.mark.parametrize(
    "valor",
    [
        "28/1234",  # Massa curt
        "28123456789",  # 11 dígits
        "2812345678901",  # 13 dígits
        "28/1234567A/90",  # Conté lletres
        "seguretat social",
        "",
        None,
        281234567890,
    ],
)
def test_num_seguretat_social_invalid(valor):
    assert es_num_seguretat_social_valid(valor) is False
    with pytest.raises(ValidationError) as exc_info:
        valida_num_seguretat_social(valor)
    assert exc_info.value.messages == [SEGURETAT_SOCIAL_INVALIDA]
    assert exc_info.value.code == "invalid"
