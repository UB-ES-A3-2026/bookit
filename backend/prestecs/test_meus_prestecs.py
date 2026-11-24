"""Tests de l'endpoint dels meus préstecs (US19-T2)."""

from datetime import date, datetime, timedelta
from datetime import timezone as tz

import pytest
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from cataleg.models import Llibre
from prestecs.models import Comanda, LiniaComanda, Prestec
from prestecs.serveis import crea_prestecs
from usuaris.models import Biblioteca, Usuari

URL = "/api/prestecs/prestecs/"


def crea_usuari(correu, rol=Usuari.Role.USUARI):
    return Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {"name": correu.split("@")[0], "address": "C/ Major 1", "library_card_number": correu, "role": rol},
    )


def crea_biblioteca(correu, nom):
    usuari = crea_usuari(correu, Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=usuari, nom=nom)
    return usuari


@pytest.fixture
def lector():
    return crea_usuari("lector@example.com")


@pytest.fixture
def client(lector):
    client = APIClient()
    client.force_authenticate(lector)
    return client


@pytest.fixture
def biblioteca():
    return crea_biblioteca("biblioteca@example.com", "Biblioteca Montbau")


def crea_prestec(usuari, biblioteca, data_limit, titol="Solitud", data_devolucio=None):
    llibre = Llibre.objects.create(titol=titol, autor="Autor de prova", isbn=f"978{Llibre.objects.count():010d}")
    comanda = Comanda.objects.create(usuari=usuari, biblioteca=biblioteca, estat=Comanda.Estat.LLIURADA)
    linia = LiniaComanda.objects.create(comanda=comanda, llibre=llibre)
    return Prestec.objects.create(
        linia=linia,
        usuari=usuari,
        llibre=llibre,
        biblioteca=biblioteca,
        data_inici=data_limit - timedelta(days=30),
        data_limit=data_limit,
        data_devolucio=data_devolucio,
    )


def avui():
    return timezone.localdate()


@pytest.mark.django_db
def test_mostra_el_llibre_la_biblioteca_i_la_data_limit(client, lector, biblioteca):
    prestec = crea_prestec(lector, biblioteca, date(2026, 12, 18), titol="La plaça del Diamant")

    resposta = client.get(URL)

    assert resposta.status_code == 200
    assert resposta.json() == [
        {
            "id": prestec.pk,
            "llibre": {
                "id": prestec.llibre_id,
                "titol": "La plaça del Diamant",
                "autor": "Autor de prova",
                "portada": "",
            },
            "biblioteca": {"id": biblioteca.pk, "nom": "Biblioteca Montbau"},
            "data_inici": "2026-11-18",
            "data_limit": "2026-12-18",
            "termini_superat": prestec.termini_superat(),
        }
    ]


@pytest.mark.django_db
def test_surten_per_data_limit_del_mes_proper_al_mes_llunya(client, lector, biblioteca):
    tard = crea_prestec(lector, biblioteca, avui() + timedelta(days=20))
    vencut = crea_prestec(lector, biblioteca, avui() - timedelta(days=3))
    aviat = crea_prestec(lector, biblioteca, avui() + timedelta(days=2))

    ids = [prestec["id"] for prestec in client.get(URL).json()]

    assert ids == [vencut.pk, aviat.pk, tard.pk]


@pytest.mark.django_db
def test_amb_la_mateixa_data_limit_surt_primer_el_mes_antic(client, lector, biblioteca):
    primer = crea_prestec(lector, biblioteca, avui() + timedelta(days=5))
    segon = crea_prestec(lector, biblioteca, avui() + timedelta(days=5))

    ids = [prestec["id"] for prestec in client.get(URL).json()]

    assert ids == [primer.pk, segon.pk]


@pytest.mark.django_db
def test_marca_els_que_tenen_el_termini_superat(client, lector, biblioteca):
    crea_prestec(lector, biblioteca, avui() - timedelta(days=1), titol="Vençut")
    crea_prestec(lector, biblioteca, avui(), titol="Venç avui")
    crea_prestec(lector, biblioteca, avui() + timedelta(days=1), titol="Venç demà")

    superats = {prestec["llibre"]["titol"]: prestec["termini_superat"] for prestec in client.get(URL).json()}

    assert superats == {"Vençut": True, "Venç avui": False, "Venç demà": False}


@pytest.mark.django_db
def test_no_surten_els_llibres_ja_tornats(client, lector, biblioteca):
    pendent = crea_prestec(lector, biblioteca, avui() + timedelta(days=10))
    crea_prestec(lector, biblioteca, avui() - timedelta(days=5), data_devolucio=avui() - timedelta(days=7))

    ids = [prestec["id"] for prestec in client.get(URL).json()]

    assert ids == [pendent.pk]


@pytest.mark.django_db
def test_no_surten_els_prestecs_d_altres_usuaris(client, lector, biblioteca):
    meu = crea_prestec(lector, biblioteca, avui() + timedelta(days=10))
    crea_prestec(crea_usuari("altre@example.com"), biblioteca, avui() + timedelta(days=10))

    ids = [prestec["id"] for prestec in client.get(URL).json()]

    assert ids == [meu.pk]


@pytest.mark.django_db
def test_sense_prestecs_retorna_una_llista_buida(client):
    resposta = client.get(URL)

    assert resposta.status_code == 200
    assert resposta.json() == []


@pytest.mark.django_db
def test_el_nombre_de_consultes_no_creix_amb_els_prestecs(client, lector, biblioteca):
    crea_prestec(lector, biblioteca, avui() + timedelta(days=10))
    with CaptureQueriesContext(connection) as amb_un:
        client.get(URL)

    altra = crea_biblioteca("altra@example.com", "Biblioteca Sant Gervasi")
    for dies in range(4):
        crea_prestec(lector, altra, avui() + timedelta(days=dies))
    with CaptureQueriesContext(connection) as amb_cinc:
        client.get(URL)

    assert len(amb_cinc) == len(amb_un)


@pytest.mark.django_db
def test_sense_sessio_rep_401():
    assert APIClient().get(URL).status_code == 401


@pytest.mark.django_db
@pytest.mark.parametrize("rol", [Usuari.Role.BIBLIOTECA, Usuari.Role.REPARTIDOR])
def test_una_biblioteca_o_un_repartidor_reben_403(rol):
    client = APIClient()
    client.force_authenticate(crea_usuari("altre@example.com", rol))

    assert client.get(URL).status_code == 403


@pytest.mark.django_db
def test_un_usuari_desactivat_rep_403(client, lector):
    lector.is_active = False
    lector.save(update_fields=["is_active"])

    assert client.get(URL).status_code == 403


@pytest.mark.django_db
def test_nomes_es_pot_consultar(client):
    assert client.post(URL, {}, format="json").status_code == 405


@pytest.mark.django_db
def test_el_termini_es_compta_amb_el_dia_de_barcelona_i_no_amb_el_d_utc(client, lector, biblioteca, monkeypatch):
    # Les 23:30 UTC del 18 de novembre ja són les 0:30 del 19 a Barcelona.
    monkeypatch.setattr("django.utils.timezone.now", lambda: datetime(2026, 11, 18, 23, 30, tzinfo=tz.utc))
    crea_prestec(lector, biblioteca, date(2026, 11, 18))

    assert client.get(URL).json()[0]["termini_superat"] is True


@pytest.mark.django_db
def test_l_ultim_dia_encara_no_esta_superat_fins_a_mitjanit_a_barcelona(client, lector, biblioteca, monkeypatch):
    # Les 22:30 UTC del 18 de novembre són les 23:30 del 18 a Barcelona.
    monkeypatch.setattr("django.utils.timezone.now", lambda: datetime(2026, 11, 18, 22, 30, tzinfo=tz.utc))
    crea_prestec(lector, biblioteca, date(2026, 11, 18))

    assert client.get(URL).json()[0]["termini_superat"] is False


@pytest.mark.django_db
@override_settings(DURADA_PRESTEC_DIES=21)
def test_els_prestecs_d_una_comanda_lliurada_surten_a_la_llista(client, lector, biblioteca):
    mirall = Llibre.objects.create(titol="Mirall trencat", autor="Mercè Rodoreda", isbn="9788475881355")
    solitud = Llibre.objects.create(titol="Solitud", autor="Víctor Català", isbn="9788475882574")
    comanda = Comanda.objects.create(usuari=lector, biblioteca=biblioteca, estat=Comanda.Estat.LLIURADA)
    for llibre in (mirall, solitud):
        LiniaComanda.objects.create(comanda=comanda, llibre=llibre)

    crea_prestecs(comanda, data_inici=avui())
    prestecs = client.get(URL).json()

    assert [prestec["llibre"]["titol"] for prestec in prestecs] == ["Mirall trencat", "Solitud"]
    for prestec in prestecs:
        assert prestec["data_inici"] == avui().isoformat()
        assert prestec["data_limit"] == (avui() + timedelta(days=21)).isoformat()
        assert prestec["termini_superat"] is False


@pytest.mark.django_db
def test_cada_prestec_diu_la_biblioteca_a_la_qual_pertany(client, lector, biblioteca):
    altra = crea_biblioteca("altra@example.com", "Biblioteca Sant Gervasi")
    crea_prestec(lector, biblioteca, avui() + timedelta(days=1))
    crea_prestec(lector, altra, avui() + timedelta(days=2))

    biblioteques = [prestec["biblioteca"]["nom"] for prestec in client.get(URL).json()]

    assert biblioteques == ["Biblioteca Montbau", "Biblioteca Sant Gervasi"]


@pytest.mark.django_db
def test_si_ho_ha_tornat_tot_la_llista_es_buida(client, lector, biblioteca):
    crea_prestec(lector, biblioteca, avui() - timedelta(days=2), data_devolucio=avui() - timedelta(days=3))
    crea_prestec(lector, biblioteca, avui() + timedelta(days=5), data_devolucio=avui())

    assert client.get(URL).json() == []


@pytest.mark.django_db
def test_un_llibre_tornat_tard_no_surt_com_a_superat(client, lector, biblioteca):
    """Un llibre tornat després de la data límit ja no és a la llista: no se'l marca com a pendent."""
    crea_prestec(lector, biblioteca, avui() - timedelta(days=10), data_devolucio=avui() - timedelta(days=1))
    pendent = crea_prestec(lector, biblioteca, avui() + timedelta(days=3))

    prestecs = client.get(URL).json()

    assert [(prestec["id"], prestec["termini_superat"]) for prestec in prestecs] == [(pendent.pk, False)]


@pytest.mark.django_db
def test_una_biblioteca_rep_el_missatge_de_sense_permisos():
    client = APIClient()
    client.force_authenticate(crea_usuari("biblio@example.com", Usuari.Role.BIBLIOTECA))

    assert client.get(URL).json() == {"detail": "No té permisos per realitzar aquesta acció."}
