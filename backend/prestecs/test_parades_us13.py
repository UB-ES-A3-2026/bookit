from datetime import date, time, timedelta

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from prestecs.models import CanviEstat, Comanda, Notificacio, Parada, Ruta
from usuaris.models import Biblioteca, PerfilRepartidor, Usuari


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


def url_fallar(parada):
    return f"/api/prestecs/repartidor/parades/{parada.id}/fallida/"


def test_completar_parada_fallida_retorna_409_i_no_canvia_estat():
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
        tipus=Parada.Tipus.LLIVRAMENT,
        ordre=1,
        estat=Parada.Estat.FALLIDA,
        motiu="Destinatari absent",
    )

    resposta = client_repartidor(repartidor).post(url_completar(parada))

    assert resposta.status_code == status.HTTP_409_CONFLICT
    parada.refresh_from_db()
    comanda.refresh_from_db()
    assert parada.estat == Parada.Estat.FALLIDA
    assert parada.completada_el is None
    assert comanda.estat == Comanda.Estat.PREPARADA


@pytest.mark.parametrize("autoritzacio", ["invalid", "caducat"])
def test_completar_token_invalid_o_caducat_retorna_401(autoritzacio):
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
        tipus=Parada.Tipus.LLIVRAMENT,
        ordre=1,
    )

    client = APIClient()
    if autoritzacio == "invalid":
        client.credentials(HTTP_AUTHORIZATION="Bearer token-invalid")
    else:
        token = AccessToken.for_user(repartidor)
        token.set_exp(lifetime=timedelta(seconds=-1))
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    resposta = client.post(url_completar(parada))

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED
    parada.refresh_from_db()
    assert parada.estat == Parada.Estat.PENDENT


def test_fallar_parada_amb_motiu_null_retorna_400():
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
        tipus=Parada.Tipus.LLIVRAMENT,
        ordre=1,
    )

    resposta = client_repartidor(repartidor).post(
        url_fallar(parada),
        {"motiu": None},
        format="json",
    )

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    parada.refresh_from_db()
    comanda.refresh_from_db()
    assert parada.estat == Parada.Estat.PENDENT
    assert comanda.estat == Comanda.Estat.EN_CAMI


def test_fallar_recollida_replanifica_la_comanda():
    repartidor = crea_repartidor()
    lector = crea_usuari()
    biblioteca = crea_biblioteca()
    comanda = Comanda.objects.create(
        usuari=lector,
        biblioteca=biblioteca,
        repartidor=repartidor,
        estat=Comanda.Estat.EN_CAMI,
        data_lliurament=date(2026, 11, 24),
        hora_inici_lliurament=time(9, 0),
        hora_fi_lliurament=time(11, 0),
    )
    ruta = Ruta.objects.create(repartidor=repartidor, data=date(2026, 11, 24))
    parada = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.RECOLLIDA,
        ordre=1,
    )

    resposta = client_repartidor(repartidor).post(
        url_fallar(parada),
        {"motiu": "Biblioteca tancada per incidència"},
        format="json",
    )

    assert resposta.status_code == status.HTTP_200_OK
    parada.refresh_from_db()
    comanda.refresh_from_db()
    assert parada.estat == Parada.Estat.FALLIDA
    assert comanda.estat == Comanda.Estat.PREPARADA
    assert comanda.repartidor is None
    assert comanda.data_lliurament is None
    assert CanviEstat.objects.filter(
        comanda=comanda, estat=Comanda.Estat.PREPARADA
    ).exists()


def test_completar_ignora_camps_extra_al_cos():
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
        tipus=Parada.Tipus.LLIVRAMENT,
        ordre=1,
    )

    resposta = client_repartidor(repartidor).post(
        url_completar(parada),
        {"estat": Parada.Estat.FALLIDA, "repartidor": 999999},
        format="json",
    )

    assert resposta.status_code == status.HTTP_200_OK
    parada.refresh_from_db()
    assert parada.estat == Parada.Estat.COMPLETADA
    assert parada.ruta.repartidor == repartidor
    assert Notificacio.objects.filter(comanda=comanda, usuari=lector).count() == 1


def test_usuari_biblioteca_no_pot_completar_ni_fallar_parada():
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
        tipus=Parada.Tipus.LLIVRAMENT,
        ordre=1,
    )

    client = APIClient()
    client.force_authenticate(biblioteca)

    resp_completar = client.post(url_completar(parada))
    resp_fallar = client.post(
        url_fallar(parada), {"motiu": "Intent no autoritzat"}, format="json"
    )

    assert resp_completar.status_code == status.HTTP_403_FORBIDDEN
    assert resp_fallar.status_code == status.HTTP_403_FORBIDDEN
    parada.refresh_from_db()
    assert parada.estat == Parada.Estat.PENDENT
