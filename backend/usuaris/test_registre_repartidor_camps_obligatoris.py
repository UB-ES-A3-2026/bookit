"""Tests dels camps obligatoris de l'endpoint de registre de repartidor (US1.1-T6).

Si en falta algun o és buit, la resposta és 400 amb "Aquest camp és obligatori." al
camp (`docs/api-registre-repartidor.md`). La matrícula depèn del vehicle: es prova a
`test_registre_repartidor_formats.py`.
"""

import pytest

from usuaris.models import Usuari
from usuaris.test_registre_repartidor import OBLIGATORI, URL, dades_valides

CAMPS = [
    "nom",
    "cognoms",
    "correu",
    "dni",
    "telefon",
    "vehicle",
    "num_seguretat_social",
    "contrasenya",
]


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
@pytest.mark.parametrize("valor", ["", None])
def test_camp_buit_retorna_400(client, camp, valor):
    resposta = client.post(
        URL, dades_valides(**{camp: valor}), content_type="application/json"
    )

    assert resposta.status_code == 400
    assert resposta.json() == {camp: [OBLIGATORI]}
    assert not Usuari.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "camp", ["nom", "cognoms", "correu", "dni", "telefon", "num_seguretat_social"]
)
def test_camp_amb_nomes_espais_es_considera_buit(client, camp):
    resposta = client.post(
        URL, dades_valides(**{camp: "   "}), content_type="application/json"
    )

    assert resposta.status_code == 400
    assert resposta.json() == {camp: [OBLIGATORI]}
    assert not Usuari.objects.exists()


@pytest.mark.django_db
def test_diversos_camps_buits_es_retornen_tots(client):
    resposta = client.post(
        URL,
        dades_valides(nom="", dni="", telefon=""),
        content_type="application/json",
    )

    assert resposta.status_code == 400
    assert resposta.json() == {
        "nom": [OBLIGATORI],
        "dni": [OBLIGATORI],
        "telefon": [OBLIGATORI],
    }
