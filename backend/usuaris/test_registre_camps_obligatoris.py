"""Tests dels camps obligatoris de l'endpoint de registre (US1-T6).

Tots els camps de la petició són obligatoris (`docs/api-registre.md`): si n'hi falta
algun o és buit, la resposta és 400 amb "Aquest camp és obligatori." al camp.
"""

import pytest

from usuaris.models import Usuari
from usuaris.test_registre import URL, dades_valides

CAMPS = ["nom", "correu", "adreca", "num_carnet", "contrasenya"]
OBLIGATORI = "Aquest camp és obligatori."


@pytest.mark.django_db
@pytest.mark.parametrize("camp", CAMPS)
def test_camp_absent_retorna_400(client, camp):
    dades = dades_valides()
    del dades[camp]

    resposta = client.post(URL, dades, content_type="application/json")

    assert resposta.status_code == 400
    assert resposta.json() == {camp: [OBLIGATORI]}
    assert not Usuari.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("camp", CAMPS)
def test_camp_buit_retorna_400(client, camp):
    resposta = client.post(
        URL, dades_valides(**{camp: ""}), content_type="application/json"
    )

    assert resposta.status_code == 400
    assert resposta.json() == {camp: [OBLIGATORI]}
    assert not Usuari.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("camp", ["nom", "adreca"])
def test_camp_amb_nomes_espais_es_considera_buit(client, camp):
    resposta = client.post(
        URL, dades_valides(**{camp: "   "}), content_type="application/json"
    )

    assert resposta.status_code == 400
    assert resposta.json() == {camp: [OBLIGATORI]}


@pytest.mark.django_db
def test_peticio_sense_cap_camp_retorna_tots_els_errors(client):
    resposta = client.post(URL, {}, content_type="application/json")

    assert resposta.status_code == 400
    assert resposta.json() == {camp: [OBLIGATORI] for camp in CAMPS}
