"""Tests de les parades de les comandes cancel·lades (US13-T11).

Quan es consulta la ruta del dia, les parades pendents d'una comanda cancel·lada
es marquen com a cancel·lades i no es mostren.
"""

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from prestecs.models import Comanda, Parada, Ruta
from prestecs.rutes import calcula_i_desaa_ordre_ruta
from usuaris.models import Biblioteca, PerfilRepartidor, Usuari

Estat = Comanda.Estat
Tipus = Parada.Tipus
URL_RUTA_AVUI = "/api/prestecs/repartidor/ruta-avui/"


def crea_usuari(correu, rol=Usuari.Role.USUARI):
    return Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {"name": correu.split("@")[0], "address": "C/ Major 1", "library_card_number": correu, "role": rol},
    )


@pytest.fixture
def repartidor():
    usuari = crea_usuari("jordi@example.com", Usuari.Role.REPARTIDOR)
    PerfilRepartidor.objects.create(
        usuari=usuari,
        cognoms="Puig",
        dni="12345678Z",
        telefon="612345678",
        vehicle=PerfilRepartidor.Vehicle.BICI,
        num_seguretat_social="281234567840",
        estat=PerfilRepartidor.Estat.VALIDAT,
    )
    return usuari


@pytest.fixture
def biblioteca():
    usuari = crea_usuari("biblioteca@example.com", Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=usuari, nom="Biblioteca Montbau")
    usuari.is_active = True
    usuari.save(update_fields=["is_active"])
    return usuari


@pytest.fixture
def ruta(repartidor):
    return Ruta.objects.create(repartidor=repartidor, data=timezone.localdate())


@pytest.fixture
def nova_comanda(repartidor, biblioteca, ruta):
    """Crea una comanda a la ruta, amb la recollida i el lliurament."""
    lector = crea_usuari("lector@example.com")
    ordre = iter(range(1, 100))

    def crea(estat=Estat.PREPARADA):
        comanda = Comanda.objects.create(usuari=lector, biblioteca=biblioteca, repartidor=repartidor, estat=estat)
        for tipus in (Tipus.RECOLLIDA, Tipus.LLIVRAMENT):
            Parada.objects.create(ruta=ruta, comanda=comanda, tipus=tipus, ordre=next(ordre))
        return comanda

    return crea


def client_de(usuari):
    client = APIClient()
    client.force_authenticate(usuari)
    return client


@pytest.mark.django_db
def test_la_ruta_no_mostra_les_parades_d_una_comanda_cancellada(repartidor, nova_comanda):
    activa = nova_comanda()
    nova_comanda(Estat.CANCELLADA)

    parades = client_de(repartidor).get(URL_RUTA_AVUI).json()

    assert [(parada["ordre"], parada["tipus"], parada["comanda"]) for parada in parades] == [
        (1, "recollida", activa.pk),
        (2, "lliurament", activa.pk),
    ]


@pytest.mark.django_db
def test_les_parades_pendents_d_una_comanda_cancellada_queden_cancellades(repartidor, nova_comanda):
    cancellada = nova_comanda(Estat.CANCELLADA)

    client_de(repartidor).get(URL_RUTA_AVUI)

    assert set(cancellada.parades.values_list("estat", flat=True)) == {Parada.Estat.CANCELLADA}


@pytest.mark.django_db
def test_una_parada_ja_completada_no_es_toca(ruta, nova_comanda):
    comanda = nova_comanda(Estat.CANCELLADA)
    recollida = comanda.parades.get(tipus=Tipus.RECOLLIDA)
    Parada.objects.filter(pk=recollida.pk).update(estat=Parada.Estat.COMPLETADA)

    calcula_i_desaa_ordre_ruta(ruta)

    recollida.refresh_from_db()
    assert recollida.estat == Parada.Estat.COMPLETADA
    assert comanda.parades.get(tipus=Tipus.LLIVRAMENT).estat == Parada.Estat.CANCELLADA


@pytest.mark.django_db
def test_les_cancellades_no_fan_repetir_els_numeros_d_ordre(ruta, nova_comanda):
    nova_comanda(Estat.CANCELLADA)
    primera = nova_comanda()
    segona = nova_comanda()

    ordenades = calcula_i_desaa_ordre_ruta(ruta)

    assert [parada.ordre for parada in ordenades] == [1, 2, 3, 4]
    assert {parada.comanda_id for parada in ordenades} == {primera.pk, segona.pk}
    ordres = list(ruta.parades.values_list("ordre", flat=True))
    assert sorted(ordres) == list(range(1, 7))


@pytest.mark.django_db
def test_una_ruta_amb_nomes_comandes_cancellades_queda_buida(repartidor, nova_comanda):
    nova_comanda(Estat.CANCELLADA)

    assert client_de(repartidor).get(URL_RUTA_AVUI).json() == []


@pytest.mark.django_db
def test_consultar_la_ruta_dues_vegades_dona_el_mateix(repartidor, nova_comanda):
    nova_comanda(Estat.CANCELLADA)
    nova_comanda()
    client = client_de(repartidor)

    primera = client.get(URL_RUTA_AVUI).json()
    segona = client.get(URL_RUTA_AVUI).json()

    assert primera == segona


@pytest.mark.django_db
def test_no_es_pot_completar_una_parada_d_una_comanda_cancellada(repartidor, nova_comanda):
    comanda = nova_comanda(Estat.CANCELLADA)
    client = client_de(repartidor)
    client.get(URL_RUTA_AVUI)
    recollida = comanda.parades.get(tipus=Tipus.RECOLLIDA)

    resposta = client.post(f"/api/prestecs/repartidor/parades/{recollida.pk}/completar/")

    assert resposta.status_code == 409
    comanda.refresh_from_db()
    assert comanda.estat == Estat.CANCELLADA
