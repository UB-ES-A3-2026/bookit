"""Tests del pas a "en camí" quan el repartidor completa la recollida (US13-T10).

Completar la recollida a la biblioteca passa la comanda a "en camí" i avisa
l'usuari amb el nom del repartidor (US8). Després, completar el lliurament la
passa a "lliurada".
"""

from unittest import mock

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from prestecs.models import Comanda, Parada, Ruta
from usuaris.models import Biblioteca, PerfilRepartidor, Usuari

Estat = Comanda.Estat
Tipus = Parada.Tipus
EN_CAMI_AMB_JORDI = "En/Na Jordi Vila ja porta la teva comanda. Està en camí!"


def crea_usuari(correu, rol=Usuari.Role.USUARI, nom=None):
    return Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {"name": nom or correu.split("@")[0], "address": "C/ Major 1", "library_card_number": correu, "role": rol},
    )


@pytest.fixture
def repartidor():
    usuari = crea_usuari("jordi@example.com", Usuari.Role.REPARTIDOR, nom="Jordi Vila")
    PerfilRepartidor.objects.create(
        usuari=usuari,
        cognoms="Vila",
        dni="12345678Z",
        telefon="612345678",
        vehicle=PerfilRepartidor.Vehicle.BICI,
        num_seguretat_social="281234567840",
        estat=PerfilRepartidor.Estat.VALIDAT,
    )
    return usuari


@pytest.fixture
def lector():
    return crea_usuari("lector@example.com")


@pytest.fixture
def biblioteca():
    usuari = crea_usuari("biblioteca@example.com", Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=usuari, nom="Biblioteca Montbau")
    usuari.is_active = True
    usuari.save(update_fields=["is_active"])
    return usuari


@pytest.fixture
def comanda(lector, biblioteca, repartidor):
    return Comanda.objects.create(usuari=lector, biblioteca=biblioteca, repartidor=repartidor, estat=Estat.PREPARADA)


@pytest.fixture
def ruta(repartidor):
    return Ruta.objects.create(repartidor=repartidor, data=timezone.localdate())


@pytest.fixture
def recollida(ruta, comanda):
    return Parada.objects.create(ruta=ruta, comanda=comanda, tipus=Tipus.RECOLLIDA, ordre=1)


@pytest.fixture
def lliurament(ruta, comanda):
    return Parada.objects.create(ruta=ruta, comanda=comanda, tipus=Tipus.LLIVRAMENT, ordre=2)


@pytest.fixture
def client_repartidor(repartidor):
    client = APIClient()
    client.force_authenticate(repartidor)
    return client


def completa(client, parada):
    return client.post(f"/api/prestecs/repartidor/parades/{parada.pk}/completar/")


@pytest.mark.django_db
def test_completar_la_recollida_posa_la_comanda_en_cami_i_ho_desa_a_l_historial(
    client_repartidor, recollida, comanda
):
    resposta = completa(client_repartidor, recollida)

    assert resposta.status_code == 200
    comanda.refresh_from_db()
    assert comanda.estat == Estat.EN_CAMI
    assert list(comanda.canvis_estat.values_list("estat", flat=True)) == [Estat.EN_CAMI]


@pytest.mark.django_db
def test_l_usuari_rep_la_notificacio_amb_el_nom_del_repartidor(client_repartidor, recollida, comanda, lector):
    completa(client_repartidor, recollida)

    notificacio = comanda.notificacions.get()
    assert notificacio.usuari == lector
    assert notificacio.text == EN_CAMI_AMB_JORDI


@pytest.mark.django_db
def test_la_resposta_porta_la_parada_completada(client_repartidor, recollida):
    dades = completa(client_repartidor, recollida).json()

    assert dades["id"] == recollida.pk
    assert dades["tipus"] == "recollida"
    assert dades["estat"] == "completada"


@pytest.mark.django_db
def test_el_recorregut_complet_de_la_recollida_al_lliurament(
    client_repartidor, recollida, lliurament, comanda, lector
):
    client_lector = APIClient()
    client_lector.force_authenticate(lector)

    assert completa(client_repartidor, recollida).status_code == 200
    assert client_lector.get("/api/prestecs/comandes/").json()[0]["estat"] == "en_cami"
    ruta = client_repartidor.get("/api/prestecs/repartidor/ruta-avui/").json()
    assert [parada["estat"] for parada in ruta] == ["en_cami", "en_cami"]

    assert completa(client_repartidor, lliurament).status_code == 200
    comanda.refresh_from_db()
    assert comanda.estat == Estat.LLIURADA
    assert list(comanda.canvis_estat.order_by("moment", "id").values_list("estat", flat=True)) == [
        Estat.EN_CAMI,
        Estat.LLIURADA,
    ]
    textos = [notificacio["text"] for notificacio in client_lector.get("/api/prestecs/notificacions/").json()]
    assert textos == [
        "La teva comanda s'ha lliurat correctament. Gaudeix del teu llibre!",
        EN_CAMI_AMB_JORDI,
    ]


@pytest.mark.django_db
def test_no_es_pot_completar_el_lliurament_abans_de_la_recollida(client_repartidor, recollida, lliurament, comanda):
    resposta = completa(client_repartidor, lliurament)

    assert resposta.status_code == 409
    lliurament.refresh_from_db()
    comanda.refresh_from_db()
    assert lliurament.estat == Parada.Estat.PENDENT
    assert comanda.estat == Estat.PREPARADA
    assert not comanda.notificacions.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("estat", [Estat.REBUDA, Estat.EN_CAMI, Estat.LLIURADA, Estat.CANCELLADA])
def test_no_es_pot_recollir_una_comanda_que_no_esta_preparada(client_repartidor, recollida, comanda, estat):
    Comanda.objects.filter(pk=comanda.pk).update(estat=estat)

    resposta = completa(client_repartidor, recollida)

    assert resposta.status_code == 409
    assert resposta.json() == {"detail": "La comanda no permet completar aquest lliurament."}
    recollida.refresh_from_db()
    comanda.refresh_from_db()
    assert recollida.estat == Parada.Estat.PENDENT
    assert comanda.estat == estat
    assert not comanda.notificacions.exists()


@pytest.mark.django_db
def test_completar_dues_vegades_la_recollida_no_repeteix_el_canvi_ni_l_avis(client_repartidor, recollida, comanda):
    completa(client_repartidor, recollida)

    resposta = completa(client_repartidor, recollida)

    assert resposta.status_code == 409
    assert comanda.canvis_estat.count() == 1
    assert comanda.notificacions.count() == 1


@pytest.mark.django_db
def test_si_falla_l_avis_la_recollida_no_queda_completada(client_repartidor, recollida, comanda):
    with mock.patch("prestecs.serveis.notifica", side_effect=RuntimeError("error de prova")):
        with pytest.raises(RuntimeError):
            completa(client_repartidor, recollida)

    recollida.refresh_from_db()
    comanda.refresh_from_db()
    assert recollida.estat == Parada.Estat.PENDENT
    assert recollida.completada_el is None
    assert comanda.estat == Estat.PREPARADA
    assert not comanda.canvis_estat.exists()
