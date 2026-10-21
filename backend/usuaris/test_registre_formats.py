"""Tests dels formats invàlids de l'endpoint de registre (US1-T6).

Formats segons `docs/api-registre.md`: correu electrònic vàlid, carnet d'exactament
10 dígits i contrasenya que compleixi els validadors de Django.
"""

import pytest

from usuaris.models import Usuari
from usuaris.test_registre import URL, dades_valides

CORREU_INVALID = "Introduïu una adreça de correu electrònic vàlida."
CARNET_INVALID = "El format d'aquest carnet no és vàlid"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "correu", ["anna", "anna@", "@example.com", "anna@example", "anna puig@example.com"]
)
def test_correu_amb_format_invalid_retorna_400(client, correu):
    resposta = client.post(
        URL, dades_valides(correu=correu), content_type="application/json"
    )

    assert resposta.status_code == 400
    assert resposta.json() == {"correu": [CORREU_INVALID]}
    assert not Usuari.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "num_carnet",
    [
        "123456789",  # 9 dígits
        "12345678901",  # 11 dígits
        "12345abcde",  # lletres
        "12345 6789",  # espai al mig
        " 1234567890",  # espai davant
        "1234567890\n",  # salt de línia al final
    ],
)
def test_carnet_amb_format_invalid_retorna_400(client, num_carnet):
    resposta = client.post(
        URL, dades_valides(num_carnet=num_carnet), content_type="application/json"
    )

    assert resposta.status_code == 400
    assert resposta.json() == {"num_carnet": [CARNET_INVALID]}
    assert not Usuari.objects.exists()


@pytest.mark.django_db
def test_carnet_que_comenca_per_zero_es_valid(client):
    resposta = client.post(
        URL, dades_valides(num_carnet="0000000001"), content_type="application/json"
    )

    assert resposta.status_code == 201
    assert resposta.json()["num_carnet"] == "0000000001"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "contrasenya",
    [
        "Ab1-",  # massa curta
        "12345678901",  # només números
        "password",  # massa comuna
    ],
)
def test_contrasenya_feble_retorna_400(client, contrasenya):
    resposta = client.post(
        URL, dades_valides(contrasenya=contrasenya), content_type="application/json"
    )

    assert resposta.status_code == 400
    # Els textos els dona Django; només es comprova que l'error és a la contrasenya.
    assert list(resposta.json()) == ["contrasenya"]
    assert not Usuari.objects.exists()


@pytest.mark.django_db
def test_amb_diversos_errors_es_retornen_tots(client):
    resposta = client.post(
        URL,
        dades_valides(correu="anna", num_carnet="123", nom=""),
        content_type="application/json",
    )

    assert resposta.status_code == 400
    assert set(resposta.json()) == {"nom", "correu", "num_carnet"}
