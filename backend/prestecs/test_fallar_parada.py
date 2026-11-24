from datetime import date
from datetime import timedelta

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

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
    usuari.is_active = True
    usuari.save(update_fields=["is_active"])
    from usuaris.models import Biblioteca
    Biblioteca.objects.create(usuari=usuari, nom="Biblioteca Central")
    return usuari


def client_repartidor(repartidor):
    client = APIClient()
    client.force_authenticate(repartidor)
    return client


def url_fallar(parada):
    return f"/api/prestecs/repartidor/parades/{parada.pk}/fallida/"


@pytest.fixture
def dades_parada():
    repartidor = crea_repartidor()
    lector = crea_usuari()
    biblioteca = crea_biblioteca()
    comanda = Comanda.objects.create(
        usuari=lector,
        biblioteca=biblioteca,
        repartidor=repartidor,
    )
    ruta = Ruta.objects.create(
        repartidor=repartidor,
        data=date(2026, 11, 24),
    )
    parada = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.LLIVRAMENT,
        ordre=1,
    )
    return repartidor, comanda, parada


def test_sense_autenticacio_retorna_401(dades_parada):
    _, _, parada = dades_parada
    resposta = APIClient().post(
        url_fallar(parada),
        {"motiu": "Destinatari absent"},
        format="json",
    )
    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("autoritzacio", ["invalid", "caducat"])
def test_token_invalid_o_caducat_retorna_401(dades_parada, autoritzacio):
    repartidor, _, parada = dades_parada
    client = APIClient()

    if autoritzacio == "invalid":
        client.credentials(HTTP_AUTHORIZATION="Bearer token-invalid")
    else:
        token = AccessToken.for_user(repartidor)
        token.set_exp(lifetime=timedelta(seconds=-1))
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    resposta = client.post(
        url_fallar(parada),
        {"motiu": "Destinatari absent"},
        format="json",
    )
    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


def test_usuari_no_repartidor_retorna_403(dades_parada):
    _, _, parada = dades_parada
    usuari = crea_usuari("lector-altre@example.com")
    client = APIClient()
    client.force_authenticate(usuari)

    resposta = client.post(
        url_fallar(parada),
        {"motiu": "Destinatari absent"},
        format="json",
    )
    assert resposta.status_code == status.HTTP_403_FORBIDDEN


def test_repartidor_propietari_des_afar_l_a_parada(dades_parada):
    repartidor, _, parada = dades_parada
    resposta = client_repartidor(repartidor).post(
        url_fallar(parada),
        {"motiu": "  Destinatari absent  "},
        format="json",
    )

    assert resposta.status_code == status.HTTP_200_OK
    parada.refresh_from_db()
    assert parada.estat == Parada.Estat.FALLIDA
    assert parada.motiu == "Destinatari absent"


def test_repartidor_no_pot_fallar_la_ruta_aliena(dades_parada):
    repartidor, _, _ = dades_parada
    altre = crea_repartidor("altre@example.com", "87654321X")
    lector = crea_usuari("lector-alien@example.com")
    biblioteca = crea_biblioteca("biblioteca-alien@example.com")
    comanda = Comanda.objects.create(
        usuari=lector,
        biblioteca=biblioteca,
        repartidor=altre,
    )
    ruta = Ruta.objects.create(repartidor=altre, data=date(2026, 11, 24))
    parada = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.LLIVRAMENT,
        ordre=1,
    )

    resposta = client_repartidor(repartidor).post(
        url_fallar(parada),
        {"motiu": "Destinatari absent"},
        format="json",
    )

    assert resposta.status_code == status.HTTP_404_NOT_FOUND
    parada.refresh_from_db()
    assert parada.estat == Parada.Estat.PENDENT
    assert parada.motiu == ""


@pytest.mark.parametrize(
    "dades",
    [
        {},
        {"motiu": ""},
        {"motiu": "   "},
    ],
)
def test_motiu_absent_buit_o_espais_retorna_400(dades_parada, dades):
    repartidor, _, parada = dades_parada
    resposta = client_repartidor(repartidor).post(
        url_fallar(parada),
        dades,
        format="json",
    )
    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    parada.refresh_from_db()
    assert parada.estat == Parada.Estat.PENDENT


def test_camps_extra_no_modifiquen_repartidor_o_estat(dades_parada):
    repartidor, _, parada = dades_parada
    resposta = client_repartidor(repartidor).post(
        url_fallar(parada),
        {
            "motiu": "Destinatari absent",
            "estat": Parada.Estat.COMPLETADA,
            "repartidor": 999999,
        },
        format="json",
    )
    assert resposta.status_code == status.HTTP_200_OK
    parada.refresh_from_db()
    assert parada.estat == Parada.Estat.FALLIDA


def test_repetir_amb_el_mateix_motiu_es_idempotent(dades_parada):
    repartidor, _, parada = dades_parada
    client = client_repartidor(repartidor)

    primera = client.post(
        url_fallar(parada),
        {"motiu": "Destinatari absent"},
        format="json",
    )
    segona = client.post(
        url_fallar(parada),
        {"motiu": "Destinatari absent"},
        format="json",
    )

    assert primera.status_code == status.HTTP_200_OK
    assert segona.status_code == status.HTTP_200_OK
    parada.refresh_from_db()
    assert parada.motiu == "Destinatari absent"


def test_repetir_amb_un_altre_motiu_retorna_409(dades_parada):
    repartidor, _, parada = dades_parada
    client = client_repartidor(repartidor)

    client.post(
        url_fallar(parada),
        {"motiu": "Destinatari absent"},
        format="json",
    )
    resposta = client.post(
        url_fallar(parada),
        {"motiu": "Adreça inaccesible"},
        format="json",
    )

    assert resposta.status_code == status.HTTP_409_CONFLICT
    parada.refresh_from_db()
    assert parada.motiu == "Destinatari absent"


def test_parada_completada_retorna_409(dades_parada):
    repartidor, _, parada = dades_parada
    parada.estat = Parada.Estat.COMPLETADA
    parada.save(update_fields=["estat"])

    resposta = client_repartidor(repartidor).post(
        url_fallar(parada),
        {"motiu": "Destinatari absent"},
        format="json",
    )

    assert resposta.status_code == status.HTTP_409_CONFLICT
    parada.refresh_from_db()
    assert parada.estat == Parada.Estat.COMPLETADA


def test_id_inexistent_retorna_404(dades_parada):
    repartidor, _, _ = dades_parada
    resposta = client_repartidor(repartidor).post(
        "/api/prestecs/repartidor/parades/999999/fallida/",
        {"motiu": "Destinatari absent"},
        format="json",
    )
    assert resposta.status_code == status.HTTP_404_NOT_FOUND


# En backend/prestecs/test_fallar_parada.py (actualiza el import de models y añade al final)
from datetime import time
from prestecs.models import CanviEstat, Comanda, Notificacio, Parada, Ruta


def test_fallar_parada_en_cami_replanifica_la_comanda():
    repartidor = crea_repartidor()
    lector = crea_usuari()
    biblioteca = crea_biblioteca()
    comanda = Comanda.objects.create(
        usuari=lector,
        biblioteca=biblioteca,
        repartidor=repartidor,
        estat=Comanda.Estat.EN_CAMI,
        data_lliurament=date(2026, 11, 24),
        hora_inici_lliurament=time(10, 0),
        hora_fi_lliurament=time(12, 0),
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
        {"motiu": "Destinatari absent"},
        format="json",
    )

    assert resposta.status_code == status.HTTP_200_OK
    parada.refresh_from_db()
    comanda.refresh_from_db()
    assert parada.estat == Parada.Estat.FALLIDA
    assert comanda.estat == Comanda.Estat.PREPARADA
    assert comanda.repartidor is None
    assert comanda.data_lliurament is None
    assert comanda.hora_inici_lliurament is None
    assert comanda.hora_fi_lliurament is None
    assert CanviEstat.objects.filter(
        comanda=comanda, estat=Comanda.Estat.PREPARADA
    ).count() == 1
    assert Notificacio.objects.filter(comanda=comanda, usuari=lector).count() == 1


def test_repetir_fallida_idempotent_no_duplica_replanificacio():
    repartidor = crea_repartidor()
    lector = crea_usuari()
    biblioteca = crea_biblioteca()
    comanda = Comanda.objects.create(
        usuari=lector,
        biblioteca=biblioteca,
        repartidor=repartidor,
        estat=Comanda.Estat.EN_CAMI,
        data_lliurament=date(2026, 11, 24),
    )
    ruta = Ruta.objects.create(repartidor=repartidor, data=date(2026, 11, 24))
    parada = Parada.objects.create(
        ruta=ruta,
        comanda=comanda,
        tipus=Parada.Tipus.LLIVRAMENT,
        ordre=1,
    )
    client = client_repartidor(repartidor)

    primera = client.post(
        url_fallar(parada),
        {"motiu": "Destinatari absent"},
        format="json",
    )
    segona = client.post(
        url_fallar(parada),
        {"motiu": "Destinatari absent"},
        format="json",
    )

    assert primera.status_code == status.HTTP_200_OK
    assert segona.status_code == status.HTTP_200_OK
    assert CanviEstat.objects.filter(
        comanda=comanda, estat=Comanda.Estat.PREPARADA
    ).count() == 1
    assert Notificacio.objects.filter(comanda=comanda).count() == 1


def test_fallida_sense_motiu_no_replanifica_la_comanda():
    repartidor = crea_repartidor()
    lector = crea_usuari()
    biblioteca = crea_biblioteca()
    comanda = Comanda.objects.create(
        usuari=lector,
        biblioteca=biblioteca,
        repartidor=repartidor,
        estat=Comanda.Estat.EN_CAMI,
        data_lliurament=date(2026, 11, 24),
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
        {},
        format="json",
    )

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    comanda.refresh_from_db()
    assert comanda.estat == Comanda.Estat.EN_CAMI
    assert comanda.repartidor == repartidor
    assert comanda.data_lliurament == date(2026, 11, 24)
