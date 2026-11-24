"""Tests de la portada dels llibres del catàleg (US17-T5).

La portada és un enllaç http o https a la imatge, es desa al llibre i l'API la retorna tal com està desada.
"""

import pytest
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.test import APIClient

from cataleg.models import Llibre
from cataleg.validacions import PORTADA_INVALIDA, PORTADA_MAX_LENGTH

pytestmark = pytest.mark.django_db

PORTADA = "https://covers.openlibrary.org/b/isbn/9788429740011-L.jpg"


def nou_llibre(**camps):
    dades = {
        "titol": "La plaça del Diamant",
        "autor": "Mercè Rodoreda",
        "isbn": "9788429740011",
    }
    dades.update(camps)
    return Llibre(**dades)


class LlibrePortadaSerializer(serializers.ModelSerializer):
    """Serializer mínim per comprovar que els serializers del catàleg hereten la validació del model."""

    class Meta:
        model = Llibre
        fields = ["titol", "autor", "isbn", "portada"]


# Casos correctes


@pytest.mark.parametrize(
    "portada",
    [
        PORTADA,
        "http://example.com/portades/mecanoscrit.jpg",
        "https://example.com/portada?mida=gran",
        "",
    ],
)
def test_accepta_enllacos_http_i_https_o_cap_portada(portada):
    nou_llibre(portada=portada).full_clean()


def test_accepta_un_enllac_de_la_mida_maxima():
    prefix = "https://example.com/"
    portada = prefix + "a" * (PORTADA_MAX_LENGTH - len(prefix))

    nou_llibre(portada=portada).full_clean()


def test_desa_la_portada_i_sense_portada_queda_buida():
    amb_portada = nou_llibre(portada=PORTADA)
    amb_portada.save()
    sense_portada = nou_llibre(isbn="9788499302515")
    sense_portada.save()

    assert Llibre.objects.get(pk=amb_portada.pk).portada == PORTADA
    assert Llibre.objects.get(pk=sense_portada.pk).portada == ""


def test_la_cerca_retorna_la_portada_desada():
    nou_llibre(portada=PORTADA).save()
    nou_llibre(titol="La plaça sense portada", isbn="9788499302515").save()

    resposta = APIClient().get("/api/cataleg/llibres/", {"q": "plaça"})

    assert resposta.status_code == 200
    portades = {resultat["titol"]: resultat["portada"] for resultat in resposta.data["results"]}
    assert portades == {
        "La plaça del Diamant": PORTADA,
        "La plaça sense portada": "",
    }


def test_el_serializer_desa_la_portada_sense_espais_del_voltant():
    serializer = LlibrePortadaSerializer(
        data={
            "titol": "La plaça del Diamant",
            "autor": "Mercè Rodoreda",
            "isbn": "9788429740011",
            "portada": f"  {PORTADA}  ",
        }
    )

    assert serializer.is_valid(), serializer.errors
    assert serializer.save().portada == PORTADA


# Casos d'error


@pytest.mark.parametrize(
    "portada",
    [
        "no és un enllaç",
        "example.com/portada.jpg",
        "ftp://example.com/portada.jpg",
        "javascript:alert(1)",
        "data:image/png;base64,iVBORw0KGgo=",
        "file:///etc/passwd",
    ],
)
def test_rebutja_el_que_no_es_un_enllac_http_o_https(portada):
    with pytest.raises(ValidationError) as error:
        nou_llibre(portada=portada).full_clean()

    assert error.value.message_dict["portada"] == [str(PORTADA_INVALIDA)]


def test_rebutja_un_enllac_mes_llarg_que_la_mida_maxima():
    prefix = "https://example.com/"
    portada = prefix + "a" * (PORTADA_MAX_LENGTH - len(prefix) + 1)

    with pytest.raises(ValidationError) as error:
        nou_llibre(portada=portada).full_clean()

    assert "portada" in error.value.message_dict


@pytest.mark.parametrize("portada", ["ftp://example.com/portada.jpg", "javascript:alert(1)"])
def test_el_serializer_rebutja_una_portada_invalida(portada):
    serializer = LlibrePortadaSerializer(
        data={
            "titol": "La plaça del Diamant",
            "autor": "Mercè Rodoreda",
            "isbn": "9788429740011",
            "portada": portada,
        }
    )

    assert not serializer.is_valid()
    assert serializer.errors["portada"] == [str(PORTADA_INVALIDA)]
    assert not Llibre.objects.exists()
