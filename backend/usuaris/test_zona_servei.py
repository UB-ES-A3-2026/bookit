import pytest
from django.core.exceptions import ValidationError

from usuaris.validacions import (
    ADRECA_FORA_ZONA_SERVEI,
    es_codi_postal_catalunya,
    normalitza_codi_postal,
    valida_codi_postal_zona,
)


@pytest.mark.parametrize(
    "codi_postal",
    ["08001", "08999", "17001", "25001", "43001", " 08001 ", "08 001"],
)
def test_codi_postal_de_catalunya_passa(codi_postal):
    assert es_codi_postal_catalunya(codi_postal)
    valida_codi_postal_zona(codi_postal)


@pytest.mark.parametrize(
    "codi_postal",
    ["01001", "07001", "28001", "50001", "0800", "080001", "08A01", "", "   ", None],
)
def test_codi_postal_fora_de_zona_genera_error_exacte(codi_postal):
    assert not es_codi_postal_catalunya(codi_postal)

    with pytest.raises(ValidationError) as error:
        valida_codi_postal_zona(codi_postal)

    assert error.value.messages == [ADRECA_FORA_ZONA_SERVEI]
    assert error.value.code == "fora_zona_servei"


@pytest.mark.parametrize(
    ("entrada", "esperat"),
    [
        (" 08001 ", "08001"),
        ("08 001", "08001"),
        ("17001", "17001"),
        ("", ""),
        (None, ""),
    ],
)
def test_normalitzacio_del_codi_postal(entrada, esperat):
    assert normalitza_codi_postal(entrada) == esperat


@pytest.mark.parametrize(
    ("codi_postal", "dins_zona"),
    [
        ("08000", True),
        ("08999", True),
        ("17000", True),
        ("17999", True),
        ("25000", True),
        ("25999", True),
        ("43000", True),
        ("43999", True),
        ("07999", False),
        ("09000", False),
    ],
)
def test_fronteres_de_la_zona(codi_postal, dins_zona):
    assert es_codi_postal_catalunya(codi_postal) is dins_zona


def test_missatge_exacte():
    assert ADRECA_FORA_ZONA_SERVEI == ("Aquesta adreça està fora de la zona de servei, introdueix una adreça vàlida")
