from datetime import date

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from prestecs.models import Comanda, Parada, Ruta
from usuaris.models import PerfilRepartidor, Usuari


pytestmark = pytest.mark.django_db


def crea_repartidor(correu="repartidor@example.com", dni="12345678Z"):
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
    from usuaris.models import Biblioteca
    Biblioteca.objects.create(usuari=usuari, nom="Biblioteca Central")
    usuari.is_active = True
    usuari.save(update_fields=["is_active"])
    return usuari


def client_repartidor(repartidor):
    client = APIClient()
    client.force_authenticate(repartidor)
    return client


def url_completar(parada):
    return f"/api/prestecs/repartidor/parades/{parada.id}/completar/"


def test_completar_lliurament_lliu_raa_la_comanda_i_crea_notificacio():
    repartidor = crea_repartidor()
    lector = crea_usuari()
    biblioteca = crea_biblioteca()
    comanda = Comanda.objects.create(
        usuari=lector,
        biblioteca=biblioteca,
        repartidor=repartidor,
        estat=Comanda.Estat.EN_CAMI,
    )
    ruta = Ruta.objects.create(repartidor=repartidor, data=date(2026, 11, 24))
    parada = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.LLIURAMENT,
        ordre=1,
    )

    resposta = client_repartidor(repartidor).post(url_completar(parada))

    assert resposta.status_code == status.HTTP_200_OK
    parada.refresh_from_db()
    comanda.refresh_from_db()
    assert parada.estat == Parada.Estat.COMPLETADA
    assert parada.completada_el is not None
    assert comanda.estat == Comanda.Estat.LLIURADA
    assert comanda.notificacions.count() == 1
    assert comanda.notificacions.get().usuari == lector
    assert comanda.notificacions.get().text == (
        "La teva comanda s'ha lliurat correctament. Gaudeix del teu llibre!"
    )


def test_completar_recollida_no_lliu_ra_la_comanda():
    repartidor = crea_repartidor()
    lector = crea_usuari()
    biblioteca = crea_biblioteca()
    comanda = Comanda.objects.create(
        usuari=lector,
        biblioteca=biblioteca,
        repartidor=repartidor,
        estat=Comanda.Estat.PREPARADA,
    )
    ruta = Ruta.objects.create(repartidor=repartidor, data=date(2026, 11, 24))
    parada = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.RECOLLIDA,
        ordre=1,
    )

    resposta = client_repartidor(repartidor).post(url_completar(parada))

    assert resposta.status_code == status.HTTP_200_OK
    parada.refresh_from_db()
    comanda.refresh_from_db()
    assert parada.estat == Parada.Estat.COMPLETADA
    assert parada.completada_el is not None
    assert comanda.estat == Comanda.Estat.PREPARADA
    assert not comanda.notificacions.exists()


def test_completar_una_parada_ja_completada_no_duplica_notificacions():
    repartidor = crea_repartidor()
    lector = crea_usuari()
    biblioteca = crea_biblioteca()
    comanda = Comanda.objects.create(
        usuari=lector,
        biblioteca=biblioteca,
        repartidor=repartidor,
        estat=Comanda.Estat.EN_CAMI,
    )
    ruta = Ruta.objects.create(repartidor=repartidor, data=date(2026, 11, 24))
    parada = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.LLIURAMENT,
        ordre=1,
    )
    client = client_repartidor(repartidor)

    primera = client.post(url_completar(parada))
    segona = client.post(url_completar(parada))

    assert primera.status_code == status.HTTP_200_OK
    assert segona.status_code == status.HTTP_409_CONFLICT
    assert segona.json() == {"detail": "La parada ja està completada."}
    assert comanda.notificacions.count() == 1


def test_sense_autenticacio_retorna_401():
    resposta = APIClient().post("/api/prestecs/repartidor/parades/999/completar/")
    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


def test_usuari_no_repartidor_retorna_403():
    usuari = crea_usuari()
    client = APIClient()
    client.force_authenticate(usuari)

    resposta = client.post("/api/prestecs/repartidor/parades/999/completar/")
    assert resposta.status_code == status.HTTP_403_FORBIDDEN


def test_parada_inexistent_retorna_404():
    repartidor = crea_repartidor()
    resposta = client_repartidor(repartidor).post(
        "/api/prestecs/repartidor/parades/999/completar/"
    )
    assert resposta.status_code == status.HTTP_404_NOT_FOUND


def test_no_pot_completar_la_parada_d_un_altre_repartidor():
    repartidor = crea_repartidor()
    altre = crea_repartidor("altre@example.com", "87654321X")
    lector = crea_usuari()
    biblioteca = crea_biblioteca()
    comanda = Comanda.objects.create(
        usuari=lector,
        biblioteca=biblioteca,
        repartidor=altre,
    )
    ruta = Ruta.objects.create(repartidor=altre, data=date(2026, 11, 24))
    parada = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.RECOLLIDA,
        ordre=1,
    )

    resposta = client_repartidor(repartidor).post(url_completar(parada))

    assert resposta.status_code == status.HTTP_404_NOT_FOUND
    parada.refresh_from_db()
    comanda.refresh_from_db()
    assert parada.estat == Parada.Estat.PENDENT
    assert comanda.estat != Comanda.Estat.LLIURADA
