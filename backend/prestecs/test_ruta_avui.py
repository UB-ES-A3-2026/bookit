from datetime import date, timedelta

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone

from cataleg.models import ExemplarBiblioteca, Llibre
from prestecs.models import Comanda, LiniaComanda, Parada, Ruta
from usuaris.models import PerfilRepartidor, Usuari
from rest_framework_simplejwt.tokens import AccessToken


pytestmark = pytest.mark.django_db


def crea_repartidor(
    correu="repartidor@example.com",
    dni="12345678Z",
):
    usuari = Usuari.objects.create_user(
        correu,
        "ContrasenyaSegura123!",
        {
            "name": "Repartidor de prova",
            "address": "",
            "library_card_number": f"repartidor-{dni}",
            "role": Usuari.Role.REPARTIDOR,
        },
    )
    return PerfilRepartidor.objects.create(
        usuari=usuari,
        cognoms="Puig Soler",
        dni=dni,
        telefon="612345678",
        vehicle=PerfilRepartidor.Vehicle.BICI,
        matricula="",
        num_seguretat_social="281234567840",
        estat=PerfilRepartidor.Estat.VALIDAT,
    ).usuari


def crea_usuari(correu="lector@example.com"):
    return Usuari.objects.create_user(
        correu,
        "ContrasenyaSegura123!",
        {
            "name": "Lector de prova",
            "address": "C/ Major 1",
            "library_card_number": f"lector-{correu}",
        },
    )


def crea_biblioteca(correu="biblioteca@example.com"):
    usuari = Usuari.objects.create_user(
        correu,
        "ContrasenyaSegura123!",
        {
            "name": "Biblioteca de prova",
            "address": "C/ Biblioteca 1",
            "library_card_number": f"biblioteca-{correu}",
            "role": Usuari.Role.BIBLIOTECA,
        },
    )
    PerfilBiblioteca = None
    from usuaris.models import Biblioteca
    PerfilBiblioteca = Biblioteca.objects.create(
        usuari=usuari,
        nom="Biblioteca Central",
    )
    usuari.is_active = True
    usuari.save(update_fields=["is_active"])
    return usuari


def client_repartidor(repartidor):
    client = APIClient()
    client.force_authenticate(repartidor)
    return client


URL_RUTA_AVUI = "/api/prestecs/repartidor/ruta-avui/"


def test_repartidor_obte_s_ordre_avui_amb_adreces(monkeypatch):
    avui = date(2026, 11, 24)
    monkeypatch.setattr(
        "prestecs.views.timezone.localdate",
        lambda: avui,
    )

    repartidor = crea_repartidor()
    lector = crea_usuari()
    biblioteca = crea_biblioteca()
    comanda = Comanda.objects.create(
        usuari=lector,
        biblioteca=biblioteca,
        repartidor=repartidor,
        data_lliurament=avui,
    )
    llibre = Llibre.objects.create(
        titol="La plaça del Diamant",
        autor="Mercè Rodoreda",
        isbn="9788429740011",
    )
    LiniaComanda.objects.create(comanda=comanda, llibre=llibre)

    ruta = Ruta.objects.create(repartidor=repartidor, data=avui)
    lliurament = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.LLIVRAMENT,
        ordre=1,
    )
    recollida = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.RECOLLIDA,
        ordre=2,
    )

    resposta = client_repartidor(repartidor).get(URL_RUTA_AVUI)

    assert resposta.status_code == status.HTTP_200_OK
    assert [parada["tipus"] for parada in resposta.data] == [
        "recollida",
        "lliurament",
    ]
    assert resposta.data[0]["ordre"] == 1
    assert resposta.data[1]["ordre"] == 2
    assert resposta.data[0]["adreca"]["biblioteca"]["nom"] == "Biblioteca Central"
    assert resposta.data[1]["adreca"]["text"] == "C/ Major 1"
    assert resposta.data[1]["adreca"]["latitud"] is None
    assert resposta.data[1]["adreca"]["longitud"] is None


def test_no_retorna_ruta_dun_altre_repartidor(monkeypatch):
    avui = date(2026, 11, 24)
    monkeypatch.setattr(
        "prestecs.views.timezone.localdate",
        lambda: avui,
    )

    repartidor = crea_repartidor()
    altre = crea_repartidor("altre@example.com", "87654321X")
    lector = crea_usuari()
    biblioteca = crea_biblioteca()
    comanda = Comanda.objects.create(
        usuari=lector,
        biblioteca=biblioteca,
        repartidor=altre,
    )

    Ruta.objects.create(repartidor=repartidor, data=avui)
    altra_ruta = Ruta.objects.create(
        repartidor=altre,
        data=avui,
    )
    Parada.objects.create(
        ruta=altra_ruta,
        comanda=comanda,
        tipus=Parada.Tipus.RECOLLIDA,
        ordre=1,
    )

    resposta = client_repartidor(repartidor).get(URL_RUTA_AVUI)

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data == []


def test_no_retorna_parades_dahir_ni_dema(monkeypatch):
    avui = date(2026, 11, 24)
    monkeypatch.setattr(
        "prestecs.views.timezone.localdate",
        lambda: avui,
    )

    repartidor = crea_repartidor()
    lector = crea_usuari()
    biblioteca = crea_biblioteca()
    comanda = Comanda.objects.create(
        usuari=lector,
        biblioteca=biblioteca,
        repartidor=repartidor,
    )

    for dia in (avui - timedelta(days=1), avui + timedelta(days=1)):
        ruta = Ruta.objects.create(repartidor=repartidor, data=dia)
        Parada.objects.create(
            ruta=ruta,
            comanda=comanda,
            tipus=Parada.Tipus.RECOLLIDA,
            ordre=1,
        )

    resposta = client_repartidor(repartidor).get(URL_RUTA_AVUI)

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data == []


def test_sense_ruta_avui_retorna_llista_buida(monkeypatch):
    monkeypatch.setattr(
        "prestecs.views.timezone.localdate",
        lambda: date(2026, 11, 24),
    )

    repartidor = crea_repartidor()

    resposta = client_repartidor(repartidor).get(URL_RUTA_AVUI)

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data == []


def test_sense_autenticacio_retorna_401():
    resposta = APIClient().get(URL_RUTA_AVUI)

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


def test_usuari_no_repartidor_retorna_403():
    usuari = crea_usuari()

    resposta = client_repartidor(usuari).get(URL_RUTA_AVUI)

    assert resposta.status_code == status.HTTP_403_FORBIDDEN

def test_cridar_lendpoint_dos_cops_retorna_la_mateixa_seqüencia(monkeypatch):
    avui = date(2026, 11, 24)
    monkeypatch.setattr(
        "prestecs.views.timezone.localdate",
        lambda: avui,
    )

    repartidor = crea_repartidor()
    lector = crea_usuari()
    biblioteca = crea_biblioteca()
    comanda = Comanda.objects.create(
        usuari=lector,
        biblioteca=biblioteca,
        repartidor=repartidor,
        data_lliurament=avui,
    )
    ruta = Ruta.objects.create(repartidor=repartidor, data=avui)

    lliurament = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.LLIVRAMENT,
        ordre=1,
    )
    recollida = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.RECOLLIDA,
        ordre=2,
    )

    client = client_repartidor(repartidor)
    primera = client.get(URL_RUTA_AVUI)
    segona = client.get(URL_RUTA_AVUI)

    assert primera.status_code == status.HTTP_200_OK
    assert segona.status_code == status.HTTP_200_OK
    assert [
        parada["id"] for parada in primera.data
    ] == [
        recollida.id,
        lliurament.id,
    ]
    assert [
        parada["id"] for parada in segona.data
    ] == [
        recollida.id,
        lliurament.id,
    ]


@pytest.mark.parametrize("metode", ["invalid", "caducat"])
def test_token_invalid_o_caducat_retorna_401(metode):
    repartidor = crea_repartidor()
    client = APIClient()

    if metode == "invalid":
        autoritzacio = "Bearer token-invalid"
    else:
        token = AccessToken.for_user(repartidor)
        token.set_exp(lifetime=timedelta(seconds=-1))
        autoritzacio = f"Bearer {token}"

    client.credentials(HTTP_AUTHORIZATION=autoritzacio)

    resposta = client.get(URL_RUTA_AVUI)

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


def test_parametre_repartidor_extra_no_canvia_l_aillament(monkeypatch):
    avui = date(2026, 11, 24)
    monkeypatch.setattr(
        "prestecs.views.timezone.localdate",
        lambda: avui,
    )

    repartidor = crea_repartidor()
    altre = crea_repartidor("altre@example.com", "87654321X")
    lector = crea_usuari()
    biblioteca = crea_biblioteca()

    comanda_propia = Comanda.objects.create(
        usuari=lector,
        biblioteca=biblioteca,
        repartidor=repartidor,
        data_lliurament=avui,
    )
    comanda_aliena = Comanda.objects.create(
        usuari=crea_usuari("lector-altre@example.com"),
        biblioteca=biblioteca,
        repartidor=altre,
        data_lliurament=avui,
    )

    ruta_propia = Ruta.objects.create(
        repartidor=repartidor,
        data=avui,
    )
    ruta_aliena = Ruta.objects.create(
        repartidor=altre,
        data=avui,
    )

    parada_propia = Parada.objects.create(
        ruta=ruta_propia,
        comanda=comanda_propia,
        tipus=Parada.Tipus.RECOLLIDA,
        ordre=1,
    )
    Parada.objects.create(
        ruta=ruta_aliena,
        comanda=comanda_aliena,
        tipus=Parada.Tipus.RECOLLIDA,
        ordre=1,
    )

    resposta = client_repartidor(repartidor).get(
        f"{URL_RUTA_AVUI}?repartidor_id={altre.id}"
    )

    assert resposta.status_code == status.HTTP_200_OK
    assert [parada["id"] for parada in resposta.data] == [parada_propia.id]


def test_la_ruta_inclou_l_estat_i_el_motiu_de_cada_parada(monkeypatch):
    """US13-T5: el frontend necessita saber quines parades ja s'han fet."""
    avui = date(2026, 11, 24)
    monkeypatch.setattr(
        "prestecs.views.timezone.localdate",
        lambda: avui,
    )
    repartidor = crea_repartidor()
    comanda = Comanda.objects.create(
        usuari=crea_usuari(),
        biblioteca=crea_biblioteca(),
        repartidor=repartidor,
        estat=Comanda.Estat.EN_CAMI,
        data_lliurament=avui,
    )
    ruta = Ruta.objects.create(repartidor=repartidor, data=avui)
    Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.RECOLLIDA,
        ordre=1,
        estat=Parada.Estat.COMPLETADA,
    )
    Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.LLIVRAMENT,
        ordre=2,
        estat=Parada.Estat.FALLIDA,
        motiu="No hi havia ningú al domicili.",
    )

    resposta = client_repartidor(repartidor).get(URL_RUTA_AVUI)

    assert resposta.status_code == status.HTTP_200_OK
    assert [parada["estat_parada"] for parada in resposta.data] == [
        "completada",
        "fallida",
    ]
    assert resposta.data[0]["motiu"] == ""
    assert resposta.data[1]["motiu"] == "No hi havia ningú al domicili."
    assert resposta.data[0]["estat"] == "en_cami"
