"""Tests dels endpoints de les franges de disponibilitat del repartidor (US14-T2)."""

from datetime import time

import pytest
from rest_framework.test import APIClient

from usuaris.models import FranjaDisponibilitat, PerfilRepartidor, Usuari

URL = "/api/usuaris/repartidor/franges/"
Dia = FranjaDisponibilitat.Dia


def crea_repartidor(correu="repartidor@example.com", dni="12345678Z", estat=PerfilRepartidor.Estat.VALIDAT):
    usuari = Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {"name": "Jordi", "address": "C/ Major 1", "library_card_number": correu, "role": Usuari.Role.REPARTIDOR},
    )
    PerfilRepartidor.objects.create(
        usuari=usuari,
        cognoms="Puig",
        dni=dni,
        telefon="612345678",
        vehicle=PerfilRepartidor.Vehicle.BICI,
        num_seguretat_social="281234567840",
        estat=estat,
    )
    return usuari


@pytest.fixture
def repartidor():
    return crea_repartidor()


@pytest.fixture
def client(repartidor):
    client = APIClient()
    client.force_authenticate(repartidor)
    return client


def franja(dia, inici, fi):
    return {"dia": dia, "hora_inici": inici, "hora_fi": fi}


def desa(client, franges):
    return client.put(URL, {"franges": franges}, format="json")


@pytest.mark.django_db
def test_sense_franges_retorna_una_llista_buida(client):
    resposta = client.get(URL)

    assert resposta.status_code == 200
    assert resposta.json() == {"franges": []}


@pytest.mark.django_db
def test_consulta_les_franges_ordenades_per_dia_i_hora(client, repartidor):
    perfil = repartidor.perfil_repartidor
    tarda = perfil.franges.create(dia=Dia.DILLUNS, hora_inici=time(16), hora_fi=time(20))
    dimarts = perfil.franges.create(dia=Dia.DIMARTS, hora_inici=time(9), hora_fi=time(13))
    mati = perfil.franges.create(dia=Dia.DILLUNS, hora_inici=time(9), hora_fi=time(13))

    resposta = client.get(URL)

    assert resposta.json() == {
        "franges": [
            {"id": mati.pk, "dia": 0, "hora_inici": "09:00", "hora_fi": "13:00"},
            {"id": tarda.pk, "dia": 0, "hora_inici": "16:00", "hora_fi": "20:00"},
            {"id": dimarts.pk, "dia": 1, "hora_inici": "09:00", "hora_fi": "13:00"},
        ]
    }


@pytest.mark.django_db
def test_desa_les_franges_i_les_retorna(client, repartidor):
    resposta = desa(client, [franja(4, "16:00", "20:30"), franja(0, "09:00", "13:00")])

    assert resposta.status_code == 200
    franges = resposta.json()["franges"]
    assert [(f["dia"], f["hora_inici"], f["hora_fi"]) for f in franges] == [
        (0, "09:00", "13:00"),
        (4, "16:00", "20:30"),
    ]
    assert repartidor.perfil_repartidor.franges.count() == 2


@pytest.mark.django_db
def test_desar_substitueix_les_franges_que_tenia(client, repartidor):
    repartidor.perfil_repartidor.franges.create(dia=Dia.DIUMENGE, hora_inici=time(10), hora_fi=time(14))

    desa(client, [franja(2, "08:00", "12:00")])

    franges = FranjaDisponibilitat.objects.filter(repartidor__usuari=repartidor)
    assert [(f.dia, f.hora_inici) for f in franges] == [(Dia.DIMECRES, time(8))]


@pytest.mark.django_db
def test_una_llista_buida_esborra_totes_les_franges(client, repartidor):
    repartidor.perfil_repartidor.franges.create(dia=Dia.DILLUNS, hora_inici=time(9), hora_fi=time(13))

    resposta = desa(client, [])

    assert resposta.status_code == 200
    assert resposta.json() == {"franges": []}
    assert not FranjaDisponibilitat.objects.exists()


@pytest.mark.django_db
def test_franges_que_es_toquen_es_poden_desar(client):
    resposta = desa(client, [franja(0, "09:00", "13:00"), franja(0, "13:00", "17:00")])

    assert resposta.status_code == 200


@pytest.mark.django_db
def test_franges_que_es_trepitgen_no_es_desen(client, repartidor):
    repartidor.perfil_repartidor.franges.create(dia=Dia.DIUMENGE, hora_inici=time(10), hora_fi=time(14))

    resposta = desa(client, [franja(0, "12:00", "14:00"), franja(0, "09:00", "13:00")])

    assert resposta.status_code == 400
    assert resposta.json() == {
        "franges": ["Les franges del dilluns de 09:00 a 13:00 i de 12:00 a 14:00 es trepitgen."]
    }
    assert repartidor.perfil_repartidor.franges.count() == 1


@pytest.mark.django_db
def test_el_mateix_horari_en_dies_diferents_no_es_trepitja(client):
    resposta = desa(client, [franja(0, "09:00", "13:00"), franja(1, "09:00", "13:00")])

    assert resposta.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize(("inici", "fi"), [("13:00", "09:00"), ("09:00", "09:00")])
def test_una_franja_ha_d_acabar_despres_de_comencar(client, inici, fi):
    resposta = desa(client, [franja(0, "08:00", "09:00"), franja(0, inici, fi)])

    assert resposta.status_code == 400
    assert resposta.json() == {"franges": {"1": {"hora_fi": ["La franja ha d'acabar després de començar."]}}}


@pytest.mark.django_db
@pytest.mark.parametrize("dia", [7, -1, "dilluns", None])
def test_un_dia_que_no_existeix(client, dia):
    resposta = desa(client, [franja(dia, "09:00", "13:00")])

    assert resposta.status_code == 400
    error = resposta.json()["franges"]["0"]["dia"]
    assert error in (
        ["Tria un dia de la setmana, del 0 (dilluns) al 6 (diumenge)."],
        ["Aquest camp és obligatori."],
    )


@pytest.mark.django_db
@pytest.mark.parametrize("hora", ["9", "25:00", "09:00:00", "nou"])
def test_una_hora_amb_un_format_incorrecte(client, hora):
    resposta = desa(client, [franja(0, hora, "13:00")])

    assert resposta.status_code == 400
    assert resposta.json() == {"franges": {"0": {"hora_inici": ["Escriu l'hora amb el format HH:MM."]}}}


@pytest.mark.django_db
def test_falten_camps_de_la_franja(client):
    resposta = desa(client, [{"dia": 0}])

    assert resposta.status_code == 400
    assert resposta.json() == {
        "franges": {"0": {"hora_inici": ["Aquest camp és obligatori."], "hora_fi": ["Aquest camp és obligatori."]}}
    }


@pytest.mark.django_db
@pytest.mark.parametrize("cos", [{}, {"franges": None}])
def test_falta_la_llista_de_franges(client, cos):
    resposta = client.put(URL, cos, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {"franges": ["Aquest camp és obligatori."]}


@pytest.mark.django_db
def test_les_franges_han_d_anar_en_una_llista(client):
    resposta = client.put(URL, {"franges": "dilluns"}, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {"franges": ["Envia les franges en una llista."]}


@pytest.mark.django_db
def test_cada_repartidor_nomes_veu_i_canvia_les_seves(client, repartidor):
    altre = crea_repartidor("altre@example.com", dni="87654321X")
    altre.perfil_repartidor.franges.create(dia=Dia.DILLUNS, hora_inici=time(9), hora_fi=time(13))

    assert client.get(URL).json() == {"franges": []}
    desa(client, [])
    assert altre.perfil_repartidor.franges.count() == 1


@pytest.mark.django_db
def test_sense_sessio_rep_401():
    assert APIClient().get(URL).status_code == 401
    assert APIClient().put(URL, {"franges": []}, format="json").status_code == 401


@pytest.mark.django_db
@pytest.mark.parametrize("rol", [Usuari.Role.USUARI, Usuari.Role.BIBLIOTECA])
def test_un_usuari_o_una_biblioteca_reben_403(rol):
    client = APIClient()
    client.force_authenticate(
        Usuari.objects.create_user(
            "altre@example.com",
            "Llibres-de-tardor-24",
            {"name": "Anna", "address": "C/ Major 1", "library_card_number": "x", "role": rol},
        )
    )

    assert client.get(URL).status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize("estat", [PerfilRepartidor.Estat.PENDENT, PerfilRepartidor.Estat.REBUTJAT])
def test_un_repartidor_sense_validar_rep_403(estat):
    client = APIClient()
    client.force_authenticate(crea_repartidor("nou@example.com", dni="87654321X", estat=estat))

    assert client.get(URL).status_code == 403
    assert client.put(URL, {"franges": []}, format="json").status_code == 403


@pytest.mark.django_db
def test_un_repartidor_desactivat_rep_403(client, repartidor):
    repartidor.is_active = False
    repartidor.save(update_fields=["is_active"])

    assert client.get(URL).status_code == 403
