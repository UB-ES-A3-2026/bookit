"""Tests del lliurament que es marca abans de la recollida.

Una comanda no pot passar de preparada a lliurada sense sortir de la biblioteca:
el backend ho rebutja amb un missatge que diu què cal fer.
"""

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from prestecs.models import Comanda, Parada, Ruta
from usuaris.models import Biblioteca, PerfilRepartidor, Usuari

Estat = Comanda.Estat
Tipus = Parada.Tipus
SENSE_RECOLLIDA = "Primer has de completar la recollida d'aquesta comanda a la biblioteca."


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
def parades(repartidor):
    biblioteca = crea_usuari("biblioteca@example.com", Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=biblioteca, nom="Biblioteca Montbau")
    comanda = Comanda.objects.create(
        usuari=crea_usuari("lector@example.com"), biblioteca=biblioteca, repartidor=repartidor, estat=Estat.PREPARADA
    )
    ruta = Ruta.objects.create(repartidor=repartidor, data=timezone.localdate())
    recollida = Parada.objects.create(ruta=ruta, comanda=comanda, tipus=Tipus.RECOLLIDA, ordre=1)
    lliurament = Parada.objects.create(ruta=ruta, comanda=comanda, tipus=Tipus.LLIVRAMENT, ordre=2)
    return comanda, recollida, lliurament


def completa(repartidor, parada):
    client = APIClient()
    client.force_authenticate(repartidor)
    return client.post(f"/api/prestecs/repartidor/parades/{parada.pk}/completar/")


@pytest.mark.django_db
def test_marcar_el_lliurament_abans_de_la_recollida_diu_que_primer_cal_recollir(repartidor, parades):
    comanda, _, lliurament = parades

    resposta = completa(repartidor, lliurament)

    assert resposta.status_code == 409
    assert resposta.json() == {"detail": SENSE_RECOLLIDA}
    lliurament.refresh_from_db()
    comanda.refresh_from_db()
    assert lliurament.estat == Parada.Estat.PENDENT
    assert comanda.estat == Estat.PREPARADA
    assert not comanda.notificacions.exists()


@pytest.mark.django_db
def test_en_l_ordre_correcte_la_comanda_queda_lliurada(repartidor, parades):
    comanda, recollida, lliurament = parades

    assert completa(repartidor, recollida).status_code == 200
    assert completa(repartidor, lliurament).status_code == 200

    comanda.refresh_from_db()
    assert comanda.estat == Estat.LLIURADA


@pytest.mark.django_db
def test_un_lliurament_d_una_comanda_cancellada_continua_amb_el_missatge_general(repartidor, parades):
    comanda, _, lliurament = parades
    Comanda.objects.filter(pk=comanda.pk).update(estat=Estat.CANCELLADA)

    resposta = completa(repartidor, lliurament)

    assert resposta.status_code == 409
    assert resposta.json()["detail"] != SENSE_RECOLLIDA
