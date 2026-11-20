"""Tests dels estats de la comanda i de les notificacions de cada canvi (US8-T4).

Completen els dels canvis d'estat (`test_canvis_estat.py`), els de les notificacions
(`test_notificacions.py`) i els dels endpoints (`test_meves_comandes.py` i
`test_api_notificacions.py`): textos literals dels criteris, cap notificació en els
canvis prohibits, el recorregut complet a través de l'API i canvis simultanis.
"""

import threading

import pytest
from django.db import connection
from rest_framework.test import APIClient

from cataleg.models import ExemplarBiblioteca, Llibre
from prestecs.models import TRANSICIONS, Comanda, Notificacio
from prestecs.serveis import TransicioNoPermesa, canvia_estat, confirma_comanda, text_notificacio
from usuaris.models import Biblioteca, Usuari

Estat = Comanda.Estat
PROHIBITS = [(actual, nou) for actual in Estat.values for nou in Estat.values if nou not in TRANSICIONS[actual]]


def crea_usuari(correu, rol=Usuari.Role.USUARI, nom=None):
    return Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {"name": nom or correu.split("@")[0], "address": "C/ Major 1", "library_card_number": correu, "role": rol},
    )


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
def llibre(biblioteca):
    llibre = Llibre.objects.create(titol="Solitud", autor="Víctor Català", isbn="9788475882574")
    ExemplarBiblioteca.objects.create(llibre=llibre, biblioteca=biblioteca, quantitat=5)
    return llibre


@pytest.fixture
def comanda(lector, biblioteca, llibre):
    return confirma_comanda(lector, biblioteca, [llibre])


@pytest.mark.parametrize(
    ("estat", "text"),
    [
        (Estat.REBUDA, "La teva comanda s'ha rebut correctament. La biblioteca ja l'està preparant"),
        (Estat.PREPARADA, "La teva comanda ja està preparada i aviat sortirà cap a casa teva"),
        (Estat.LLIURADA, "La teva comanda s'ha lliurat correctament. Gaudeix del teu llibre!"),
    ],
)
def test_els_textos_son_els_dels_criteris_de_la_us8(estat, text):
    assert text_notificacio(estat) == text


def test_el_text_d_en_cami_porta_el_nom_del_repartidor_tal_com_es():
    repartidor = Usuari(name="Núria Sant-Joan")

    assert text_notificacio(Estat.EN_CAMI, repartidor) == (
        "En/Na Núria Sant-Joan ja porta la teva comanda. Està en camí!"
    )


@pytest.mark.django_db
@pytest.mark.parametrize(("actual", "nou"), PROHIBITS)
def test_cap_canvi_prohibit_crea_cap_notificacio(comanda, actual, nou):
    Comanda.objects.filter(pk=comanda.pk).update(estat=actual)
    abans = comanda.notificacions.count()

    with pytest.raises(TransicioNoPermesa):
        canvia_estat(comanda, nou)

    assert comanda.notificacions.count() == abans


@pytest.mark.django_db
def test_cada_notificacio_va_a_la_seva_comanda(lector, biblioteca, llibre):
    primera = confirma_comanda(lector, biblioteca, [llibre])
    segona = confirma_comanda(lector, biblioteca, [llibre])

    canvia_estat(segona, Estat.PREPARADA)

    assert primera.notificacions.count() == 1
    assert list(segona.notificacions.order_by("creada", "id").values_list("text", flat=True)) == [
        text_notificacio(Estat.REBUDA),
        text_notificacio(Estat.PREPARADA),
    ]


@pytest.mark.django_db
def test_el_recorregut_complet_a_traves_de_l_api(lector, biblioteca, llibre):
    repartidor = crea_usuari("jordi@example.com", Usuari.Role.REPARTIDOR, nom="Jordi")
    client = APIClient()
    client.force_authenticate(lector)

    confirmada = client.post(
        "/api/prestecs/comandes/", {"biblioteca": biblioteca.pk, "llibres": [llibre.pk]}, format="json"
    )
    comanda = Comanda.objects.get(pk=confirmada.json()["id"])
    notificacions = client.get("/api/prestecs/notificacions/").json()
    assert [(n["text"], n["llegida"], n["comanda"]) for n in notificacions] == [
        (text_notificacio(Estat.REBUDA), False, comanda.pk)
    ]

    canvia_estat(comanda, Estat.PREPARADA)
    canvia_estat(comanda, Estat.EN_CAMI, repartidor=repartidor)
    assert client.get("/api/prestecs/comandes/").json()[0]["estat"] == "en_cami"
    assert client.post("/api/prestecs/notificacions/llegides/").json() == {"marcades": 3}

    canvia_estat(comanda, Estat.LLIURADA)
    comandes = client.get("/api/prestecs/comandes/").json()
    notificacions = client.get("/api/prestecs/notificacions/").json()

    assert comandes[0]["estat"] == "lliurada"
    assert [(n["text"], n["llegida"]) for n in notificacions] == [
        (text_notificacio(Estat.LLIURADA), False),
        ("En/Na Jordi ja porta la teva comanda. Està en camí!", True),
        (text_notificacio(Estat.PREPARADA), True),
        (text_notificacio(Estat.REBUDA), True),
    ]


@pytest.mark.django_db
def test_el_text_desat_no_canvia_encara_que_canvii_el_repartidor(comanda):
    repartidor = crea_usuari("jordi@example.com", Usuari.Role.REPARTIDOR, nom="Jordi")
    canvia_estat(comanda, Estat.PREPARADA)
    canvia_estat(comanda, Estat.EN_CAMI, repartidor=repartidor)

    repartidor.name = "Jordi Vila"
    repartidor.save(update_fields=["name"])

    assert comanda.notificacions.order_by("-creada", "-id").first().text == (
        "En/Na Jordi ja porta la teva comanda. Està en camí!"
    )


@pytest.mark.django_db(transaction=True)
def test_dos_canvis_d_estat_alhora_nomes_en_deixen_passar_un():
    """El repartidor recull la comanda alhora que l'usuari la cancel·la.

    Passi el que passi primer, l'altre canvi ja no està permès: una comanda en camí
    no es pot cancel·lar i una de cancel·lada no pot sortir.
    """
    biblioteca = crea_usuari("biblioteca@example.com", Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=biblioteca, nom="Biblioteca Montbau")
    lector = crea_usuari("lector@example.com")
    comanda = Comanda.objects.create(usuari=lector, biblioteca=biblioteca, estat=Estat.PREPARADA)
    sortida = threading.Barrier(2)
    resultats = []

    def canvia(nou_estat):
        try:
            sortida.wait()
            canvia_estat(Comanda.objects.get(pk=comanda.pk), nou_estat)
            resultats.append(nou_estat)
        except TransicioNoPermesa:
            resultats.append("rebutjat")
        finally:
            connection.close()

    fils = [threading.Thread(target=canvia, args=(estat,)) for estat in (Estat.EN_CAMI, Estat.CANCELLADA)]
    for fil in fils:
        fil.start()
    for fil in fils:
        fil.join()

    comanda.refresh_from_db()
    guanyador = next(resultat for resultat in resultats if resultat != "rebutjat")
    assert "rebutjat" in resultats
    assert comanda.estat == guanyador
    assert comanda.canvis_estat.count() == 1
    assert Notificacio.objects.filter(comanda=comanda).count() == 1
