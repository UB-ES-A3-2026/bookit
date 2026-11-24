from datetime import date, timedelta

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone

from cataleg.models import ExemplarBiblioteca, Llibre
from prestecs.models import Comanda, LiniaComanda, Parada, Ruta
from usuaris.models import PerfilRepartidor, Usuari


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
