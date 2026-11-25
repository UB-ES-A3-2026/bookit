"""Coordenades de les parades per al mapa de la ruta (US12-T13).

Cap test fa peticions reals al geocodificador: la fixture `geocodificador_sense_xarxa`
de `conftest.py` fa que per defecte no trobi res, i els tests que necessiten
coordenades substitueixen `geocodifica_text` allà on s'usa.
"""

import io
import json
from datetime import date
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from cataleg.models import ExemplarBiblioteca, Llibre
from prestecs.models import Comanda, Parada, Ruta
from prestecs.serveis import desa_coordenades_lliurament
from prestecs.test_ruta_avui import (
    URL_RUTA_AVUI,
    client_repartidor,
    crea_biblioteca,
    crea_repartidor,
    crea_usuari,
)
from usuaris import geocodificacio
from usuaris.models import Biblioteca, Usuari

pytestmark = pytest.mark.django_db

URL_COMANDES = "/api/prestecs/comandes/"
UBICACIO = (Decimal("41.403629"), Decimal("2.174355"))


class GeocodificadorFals:
    """Substitueix `geocodifica_text` i recorda amb quin text s'ha cridat."""

    def __init__(self, resultat=UBICACIO):
        self.resultat = resultat
        self.consultes = []

    def __call__(self, consulta):
        self.consultes.append(consulta)
        return self.resultat


@pytest.fixture
def geocodificador(monkeypatch):
    fals = GeocodificadorFals()
    monkeypatch.setattr("prestecs.serveis.geocodifica_text", fals)
    return fals


@pytest.fixture
def lector():
    return crea_usuari()


@pytest.fixture
def biblioteca():
    return crea_biblioteca()


@pytest.fixture
def llibre(biblioteca):
    llibre = Llibre.objects.create(titol="Solitud", autor="Víctor Català", isbn="9788475882574")
    ExemplarBiblioteca.objects.create(llibre=llibre, biblioteca=biblioteca, quantitat=3)
    return llibre


def confirma(lector, biblioteca, llibre, **dades):
    client = APIClient()
    client.force_authenticate(lector)
    return client.post(
        URL_COMANDES,
        {"biblioteca": biblioteca.pk, "llibres": [llibre.pk], **dades},
        format="json",
    )


def comanda_de(lector, biblioteca, **camps):
    return Comanda.objects.create(usuari=lector, biblioteca=biblioteca, **camps)


# --- Geocodificació de text lliure --------------------------------------------


class RespostaFalsa(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


@pytest.mark.parametrize("text", ["", "   ", None])
def test_geocodifica_text_buit_no_fa_cap_peticio(monkeypatch, text):
    def no_s_ha_de_cridar(*args, **kwargs):
        raise AssertionError("No s'ha de fer cap petició.")

    monkeypatch.setattr("usuaris.geocodificacio.urlopen", no_s_ha_de_cridar)

    assert geocodificacio.geocodifica_text(text) is None


def test_geocodifica_text_retorna_les_coordenades(monkeypatch):
    peticions = []

    def urlopen_fals(peticio, timeout):
        peticions.append(peticio.full_url)
        return RespostaFalsa(json.dumps([{"lat": "41.4036293", "lon": "2.1743553"}]).encode())

    monkeypatch.setattr("usuaris.geocodificacio.urlopen", urlopen_fals)

    assert geocodificacio.geocodifica_text("C/ Mallorca 401, Barcelona") == UBICACIO
    assert "Mallorca" in peticions[0]


def test_geocodifica_text_sense_xarxa_retorna_none():
    assert geocodificacio.geocodifica_text("C/ Mallorca 401, Barcelona") is None


def test_geocodifica_adreca_continua_fent_la_mateixa_consulta(monkeypatch):
    consultes = []
    monkeypatch.setattr(
        "usuaris.geocodificacio.geocodifica_text",
        lambda consulta: consultes.append(consulta) or UBICACIO,
    )

    class AdrecaFalsa:
        carrer = "C/ Mallorca 401"
        pis = "2n 1a"
        codi_postal = "08013"
        municipi = "Barcelona"

    assert geocodificacio.geocodifica_adreca(AdrecaFalsa()) == UBICACIO
    assert consultes == ["C/ Mallorca 401, 2n 1a, 08013 Barcelona, Catalunya, Espanya"]


# --- Coordenades del lliurament en confirmar la comanda ------------------------


def test_confirmar_una_comanda_a_domicili_en_desa_les_coordenades(
    lector, biblioteca, llibre, geocodificador
):
    resposta = confirma(lector, biblioteca, llibre, adreca_lliurament="C/ Mallorca 401, Barcelona")

    assert resposta.status_code == status.HTTP_201_CREATED
    comanda = Comanda.objects.get(pk=resposta.data["id"])
    assert (comanda.latitud_lliurament, comanda.longitud_lliurament) == UBICACIO
    assert geocodificador.consultes == ["C/ Mallorca 401, Barcelona, Catalunya, Espanya"]


def test_sense_adreca_geocodifica_la_del_perfil(lector, biblioteca, llibre, geocodificador):
    resposta = confirma(lector, biblioteca, llibre)

    assert resposta.status_code == status.HTTP_201_CREATED
    assert geocodificador.consultes == ["C/ Major 1, Catalunya, Espanya"]


def test_si_el_geocodificador_falla_la_comanda_es_crea_sense_coordenades(
    lector, biblioteca, llibre, geocodificador
):
    geocodificador.resultat = None

    resposta = confirma(lector, biblioteca, llibre, adreca_lliurament="Adreça inventada 999")

    assert resposta.status_code == status.HTTP_201_CREATED
    comanda = Comanda.objects.get(pk=resposta.data["id"])
    assert comanda.latitud_lliurament is None
    assert comanda.longitud_lliurament is None


def test_sense_xarxa_la_comanda_es_crea_sense_coordenades(lector, biblioteca, llibre):
    resposta = confirma(lector, biblioteca, llibre, adreca_lliurament="C/ Mallorca 401, Barcelona")

    assert resposta.status_code == status.HTTP_201_CREATED
    assert Comanda.objects.get(pk=resposta.data["id"]).latitud_lliurament is None


def test_la_recollida_a_la_biblioteca_no_es_geocodifica(lector, biblioteca, llibre, geocodificador):
    resposta = confirma(lector, biblioteca, llibre, tipus_lliurament="recollida")

    assert resposta.status_code == status.HTTP_201_CREATED
    assert geocodificador.consultes == []
    assert Comanda.objects.get(pk=resposta.data["id"]).latitud_lliurament is None


def test_una_comanda_sense_estoc_no_es_geocodifica(lector, biblioteca, llibre, geocodificador):
    ExemplarBiblioteca.objects.filter(llibre=llibre).update(quantitat=0)

    resposta = confirma(lector, biblioteca, llibre, adreca_lliurament="C/ Mallorca 401, Barcelona")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert geocodificador.consultes == []


def test_tornar_a_geocodificar_sense_resultat_esborra_les_coordenades_antigues(
    lector, biblioteca, geocodificador
):
    comanda = comanda_de(
        lector,
        biblioteca,
        adreca_lliurament="C/ Nova 2",
        latitud_lliurament=Decimal("41.1"),
        longitud_lliurament=Decimal("2.1"),
    )
    geocodificador.resultat = None

    assert desa_coordenades_lliurament(comanda) is False

    comanda.refresh_from_db()
    assert comanda.latitud_lliurament is None
    assert comanda.longitud_lliurament is None


# --- Ordre de gestió per a les comandes que ja existeixen ----------------------


def test_l_ordre_geocodifica_nomes_les_comandes_a_domicili_pendents(
    lector, biblioteca, geocodificador
):
    pendent = comanda_de(lector, biblioteca, adreca_lliurament="C/ Pendent 1")
    en_cami = comanda_de(
        lector, biblioteca, adreca_lliurament="C/ En camí 2", estat=Comanda.Estat.EN_CAMI
    )
    lliurada = comanda_de(
        lector, biblioteca, adreca_lliurament="C/ Lliurada 3", estat=Comanda.Estat.LLIURADA
    )
    recollida = comanda_de(
        lector, biblioteca, tipus_lliurament=Comanda.TipusLliurament.RECOLLIDA
    )
    sense_adreca = comanda_de(lector, biblioteca, adreca_lliurament="")
    ja_feta = comanda_de(
        lector,
        biblioteca,
        adreca_lliurament="C/ Feta 4",
        latitud_lliurament=Decimal("41.5"),
        longitud_lliurament=Decimal("2.5"),
    )
    sortida = io.StringIO()

    call_command("geocodifica_comandes", "--pausa", "0", stdout=sortida)

    assert geocodificador.consultes == [
        "C/ Pendent 1, Catalunya, Espanya",
        "C/ En camí 2, Catalunya, Espanya",
    ]
    for comanda in (pendent, en_cami):
        comanda.refresh_from_db()
        assert comanda.latitud_lliurament == UBICACIO[0]
    for comanda in (lliurada, recollida, sense_adreca):
        comanda.refresh_from_db()
        assert comanda.latitud_lliurament is None
    ja_feta.refresh_from_db()
    assert ja_feta.latitud_lliurament == Decimal("41.5")
    assert "Comandes processades: 2. Comandes geocodificades: 2." in sortida.getvalue()


def test_l_ordre_compta_les_que_no_es_poden_geocodificar(lector, biblioteca, geocodificador):
    comanda_de(lector, biblioteca, adreca_lliurament="Adreça inventada 999")
    geocodificador.resultat = None
    sortida = io.StringIO()

    call_command("geocodifica_comandes", "--pausa", "0", stdout=sortida)

    assert "Comandes processades: 1. Comandes geocodificades: 0." in sortida.getvalue()


# --- Coordenades a la ruta del dia ---------------------------------------------


@pytest.fixture
def avui(monkeypatch):
    dia = date(2026, 11, 24)
    monkeypatch.setattr("prestecs.views.timezone.localdate", lambda: dia)
    return dia


def crea_ruta(avui, comanda):
    repartidor = crea_repartidor()
    comanda.repartidor = repartidor
    comanda.estat = Comanda.Estat.PREPARADA
    comanda.data_lliurament = avui
    comanda.save()
    ruta = Ruta.objects.create(repartidor=repartidor, data=avui)
    Parada.objects.create(ruta=ruta, comanda=comanda, tipus=Parada.Tipus.RECOLLIDA, ordre=1)
    Parada.objects.create(ruta=ruta, comanda=comanda, tipus=Parada.Tipus.LLIVRAMENT, ordre=2)
    return repartidor


def adreces(repartidor):
    resposta = client_repartidor(repartidor).get(URL_RUTA_AVUI)
    assert resposta.status_code == status.HTTP_200_OK
    return [parada["adreca"] for parada in resposta.data]


def test_la_ruta_porta_les_coordenades_de_la_biblioteca_i_del_lliurament(
    avui, lector, biblioteca
):
    Biblioteca.objects.filter(usuari=biblioteca).update(
        latitud=Decimal("41.385064"), longitud=Decimal("2.173404")
    )
    comanda = comanda_de(
        lector,
        biblioteca,
        adreca_lliurament="C/ Mallorca 401, Barcelona",
        latitud_lliurament=UBICACIO[0],
        longitud_lliurament=UBICACIO[1],
    )

    recollida, lliurament = adreces(crea_ruta(avui, comanda))

    assert (recollida["latitud"], recollida["longitud"]) == (41.385064, 2.173404)
    assert (lliurament["latitud"], lliurament["longitud"]) == (41.403629, 2.174355)
    # Són números JSON, no text.
    assert all(
        isinstance(adreca[camp], float)
        for adreca in (recollida, lliurament)
        for camp in ("latitud", "longitud")
    )
    assert lliurament["text"] == "C/ Mallorca 401, Barcelona"


def test_sense_coordenades_la_ruta_retorna_null(avui, lector, biblioteca):
    comanda = comanda_de(lector, biblioteca, adreca_lliurament="Adreça inventada 999")

    recollida, lliurament = adreces(crea_ruta(avui, comanda))

    assert recollida["latitud"] is None and recollida["longitud"] is None
    assert lliurament["latitud"] is None and lliurament["longitud"] is None


def test_una_comanda_antiga_sense_adreca_de_lliurament_mostra_la_del_perfil(
    avui, lector, biblioteca
):
    comanda = comanda_de(lector, biblioteca, adreca_lliurament="")

    _, lliurament = adreces(crea_ruta(avui, comanda))

    assert lliurament["text"] == "C/ Major 1"


# --- Admin de les biblioteques ------------------------------------------------


@pytest.fixture
def client_admin(client):
    admin = Usuari.objects.create_superuser(
        "admin@example.com", "contrasenya-segura", {"name": "Admin", "address": "", "library_card_number": "admin"}
    )
    client.force_login(admin)
    return client


def test_l_admin_llista_les_biblioteques_i_si_tenen_ubicacio(client_admin, biblioteca):
    resposta = client_admin.get(reverse("admin:usuaris_biblioteca_changelist"))

    assert resposta.status_code == 200
    assert "Biblioteca Central" in resposta.content.decode()


def test_l_admin_desa_l_adreca_i_les_coordenades(client_admin, biblioteca):
    fitxa = biblioteca.biblioteca

    resposta = client_admin.post(
        reverse("admin:usuaris_biblioteca_change", args=[fitxa.pk]),
        {
            "nom": "Biblioteca Central",
            "carrer": "C/ Hospital 56",
            "numero_porta": "",
            "latitud": "41.380200",
            "longitud": "2.169900",
        },
    )

    assert resposta.status_code == 302
    fitxa.refresh_from_db()
    assert fitxa.carrer == "C/ Hospital 56"
    assert (fitxa.latitud, fitxa.longitud) == (Decimal("41.380200"), Decimal("2.169900"))


def test_l_admin_rebutja_coordenades_fora_de_rang(client_admin, biblioteca):
    fitxa = biblioteca.biblioteca

    resposta = client_admin.post(
        reverse("admin:usuaris_biblioteca_change", args=[fitxa.pk]),
        {"nom": "Biblioteca Central", "carrer": "", "numero_porta": "", "latitud": "100", "longitud": "2"},
    )

    assert resposta.status_code == 200
    fitxa.refresh_from_db()
    assert fitxa.latitud is None


def test_l_admin_no_permet_crear_ni_esborrar_biblioteques(client_admin, biblioteca):
    assert client_admin.get(reverse("admin:usuaris_biblioteca_add")).status_code == 403
    assert (
        client_admin.get(
            reverse("admin:usuaris_biblioteca_delete", args=[biblioteca.biblioteca.pk])
        ).status_code
        == 403
    )
