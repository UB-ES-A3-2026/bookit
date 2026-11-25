"""Tests dels registres simultanis amb el mateix correu o carnet (US1-T22, US1-T27).

Dos registres alhora poden passar tots dos els validadors de duplicats. La base de
dades rebutja el segon, i aquest ha de rebre el missatge de duplicat, no un 500.
"""

import threading
from unittest.mock import patch

import pytest
from django.db import IntegrityError, connection
from django.test import Client

from usuaris.models import Usuari
from usuaris.test_registre import URL, dades_valides

CORREU_JA_REGISTRAT = "Aquest correu electrònic ja està registrat"
CARNET_JA_REGISTRAT = "Aquest usuari ja està registrat"


def un_altre_registre_guanya(correu="altre@example.com", carnet="9999999999"):
    """Simula que un altre registre ha desat l'usuari mentre aquest es validava.

    L'altre usuari ja és a la base de dades, però els validadors de duplicats no el
    veuen, com passa quan els dos registres es validen alhora.
    """
    Usuari.objects.create_user(
        correu,
        "una-Contrasenya-segura-9",
        {"name": "Un altre", "address": "C/ Major 2", "library_card_number": carnet},
    )
    return patch("rest_framework.validators.UniqueValidator.__call__", return_value=None)


@pytest.mark.django_db
def test_si_un_altre_registre_desa_el_mateix_correu_abans_rep_el_missatge_de_duplicat(client):
    with un_altre_registre_guanya(correu="anna@example.com"):
        resposta = client.post(URL, dades_valides(), content_type="application/json")

    assert resposta.status_code == 400
    assert resposta.json() == {"correu": [CORREU_JA_REGISTRAT]}
    assert Usuari.objects.filter(email="anna@example.com").count() == 1


@pytest.mark.django_db
def test_si_un_altre_registre_desa_el_mateix_carnet_abans_rep_el_missatge_de_duplicat(client):
    with un_altre_registre_guanya(carnet="1234567890"):
        resposta = client.post(URL, dades_valides(), content_type="application/json")

    assert resposta.status_code == 400
    assert resposta.json() == {"num_carnet": [CARNET_JA_REGISTRAT]}


@pytest.mark.django_db
def test_el_correu_es_compara_sense_majuscules(client):
    with un_altre_registre_guanya(correu="anna@example.com"):
        resposta = client.post(URL, dades_valides(correu="Anna@Example.com"), content_type="application/json")

    assert resposta.json() == {"correu": [CORREU_JA_REGISTRAT]}


@pytest.mark.django_db
def test_un_altre_error_de_la_base_de_dades_no_s_amaga(client):
    error = IntegrityError("una altra restricció")
    with patch("usuaris.serializers.Usuari.objects.create_user", side_effect=error):
        with pytest.raises(IntegrityError):
            client.post(URL, dades_valides(), content_type="application/json")


@pytest.mark.django_db(transaction=True)
def test_dos_registres_alhora_amb_el_mateix_correu_nomes_en_creen_un():
    sortida = threading.Barrier(2)
    respostes = []

    def registra(carnet):
        try:
            sortida.wait()
            resposta = Client().post(
                URL, dades_valides(num_carnet=carnet), content_type="application/json"
            )
            respostes.append((resposta.status_code, resposta.json()))
        finally:
            connection.close()

    fils = [threading.Thread(target=registra, args=(carnet,)) for carnet in ("1234567890", "0987654321")]
    for fil in fils:
        fil.start()
    for fil in fils:
        fil.join()

    assert sorted(codi for codi, _ in respostes) == [201, 400]
    assert [cos for codi, cos in respostes if codi == 400] == [{"correu": [CORREU_JA_REGISTRAT]}]
    assert Usuari.objects.filter(email="anna@example.com").count() == 1
