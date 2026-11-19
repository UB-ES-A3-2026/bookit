"""Tests de la cancel·lació d'una comanda (US20-T1)."""

import threading
from unittest import mock

import pytest
from django.db import connection
from rest_framework.test import APIClient

from cataleg.models import ExemplarBiblioteca, Llibre
from prestecs.models import Comanda
from prestecs.serveis import LlibresSenseEstoc, cancella_comanda, confirma_comanda
from usuaris.models import Biblioteca, Usuari

Estat = Comanda.Estat
JA_HA_SORTIT = "Aquesta comanda ja ha sortit i no es pot cancel·lar"


def url(comanda_id):
    return f"/api/prestecs/comandes/{comanda_id}/cancellar/"


def crea_usuari(correu, rol=Usuari.Role.USUARI):
    return Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {"name": correu.split("@")[0], "address": "C/ Major 1", "library_card_number": correu, "role": rol},
    )


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
    usuari = crea_usuari("biblioteca@example.com", Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=usuari, nom="Biblioteca Montbau")
    return usuari


@pytest.fixture
def llibres(biblioteca):
    llibres = [
        Llibre.objects.create(titol="La plaça del Diamant", autor="Mercè Rodoreda", isbn="9788429740011"),
        Llibre.objects.create(titol="Solitud", autor="Víctor Català", isbn="9788475882574"),
    ]
    for llibre in llibres:
        ExemplarBiblioteca.objects.create(llibre=llibre, biblioteca=biblioteca, quantitat=2)
    return llibres


@pytest.fixture
def comanda(lector, biblioteca, llibres):
    # Confirmar-la reserva un exemplar de cada llibre: en queda 1 de cadascun.
    return confirma_comanda(lector, biblioteca, llibres)


def exemplars(llibre, biblioteca):
    return ExemplarBiblioteca.objects.get(llibre=llibre, biblioteca=biblioteca).quantitat


def posa_estat(comanda, estat):
    Comanda.objects.filter(pk=comanda.pk).update(estat=estat)


@pytest.mark.django_db
def test_cancella_una_comanda_rebuda(client, comanda):
    resposta = client.post(url(comanda.pk))

    assert resposta.status_code == 200
    assert resposta.json()["id"] == comanda.pk
    assert resposta.json()["estat"] == "cancellada"
    comanda.refresh_from_db()
    assert comanda.estat == Estat.CANCELLADA


@pytest.mark.django_db
def test_es_pot_cancellar_una_comanda_preparada(client, comanda):
    posa_estat(comanda, Estat.PREPARADA)

    assert client.post(url(comanda.pk)).status_code == 200


@pytest.mark.django_db
def test_els_exemplars_tornen_a_la_biblioteca(client, comanda, biblioteca, llibres):
    client.post(url(comanda.pk))

    assert [exemplars(llibre, biblioteca) for llibre in llibres] == [2, 2]


@pytest.mark.django_db
def test_no_toca_els_exemplars_d_altres_biblioteques(client, comanda, llibres):
    altra = crea_usuari("altra@example.com", Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=altra, nom="Biblioteca Sant Gervasi")
    ExemplarBiblioteca.objects.create(llibre=llibres[0], biblioteca=altra, quantitat=5)

    client.post(url(comanda.pk))

    assert exemplars(llibres[0], altra) == 5


@pytest.mark.django_db
def test_un_llibre_tret_del_cataleg_no_es_torna(client, comanda, biblioteca, llibres):
    ExemplarBiblioteca.objects.filter(llibre=llibres[1], biblioteca=biblioteca).delete()

    resposta = client.post(url(comanda.pk))

    assert resposta.status_code == 200
    assert exemplars(llibres[0], biblioteca) == 2
    assert not ExemplarBiblioteca.objects.filter(llibre=llibres[1], biblioteca=biblioteca).exists()


@pytest.mark.django_db
def test_la_cancellacio_queda_a_l_historial(client, comanda):
    client.post(url(comanda.pk))

    assert list(comanda.canvis_estat.values_list("estat", flat=True)) == [Estat.REBUDA, Estat.CANCELLADA]


@pytest.mark.django_db
@pytest.mark.parametrize("estat", [Estat.EN_CAMI, Estat.LLIURADA])
def test_una_comanda_que_ja_ha_sortit_no_es_pot_cancellar(client, comanda, biblioteca, llibres, estat):
    posa_estat(comanda, estat)

    resposta = client.post(url(comanda.pk))

    assert resposta.status_code == 409
    assert resposta.json() == {"detail": JA_HA_SORTIT}
    comanda.refresh_from_db()
    assert comanda.estat == estat
    assert [exemplars(llibre, biblioteca) for llibre in llibres] == [1, 1]


@pytest.mark.django_db
def test_cancellar_dues_vegades_no_torna_els_exemplars_dos_cops(client, comanda, biblioteca, llibres):
    client.post(url(comanda.pk))

    resposta = client.post(url(comanda.pk))

    assert resposta.status_code == 409
    assert resposta.json() == {"detail": "Aquesta comanda ja està cancel·lada."}
    assert [exemplars(llibre, biblioteca) for llibre in llibres] == [2, 2]


@pytest.mark.django_db
def test_si_falla_la_devolucio_la_comanda_no_queda_cancellada(comanda, biblioteca, llibres):
    with mock.patch.object(
        ExemplarBiblioteca.objects, "select_for_update", side_effect=RuntimeError("error de prova")
    ):
        with pytest.raises(RuntimeError):
            cancella_comanda(comanda)

    assert Comanda.objects.get(pk=comanda.pk).estat == Estat.REBUDA
    assert [exemplars(llibre, biblioteca) for llibre in llibres] == [1, 1]


@pytest.mark.django_db
def test_una_comanda_d_un_altre_usuari_dona_404(comanda):
    client = APIClient()
    client.force_authenticate(crea_usuari("altre@example.com"))

    resposta = client.post(url(comanda.pk))

    assert resposta.status_code == 404
    assert Comanda.objects.get(pk=comanda.pk).estat == Estat.REBUDA


@pytest.mark.django_db
def test_una_comanda_que_no_existeix_dona_404(client):
    assert client.post(url(999999)).status_code == 404


@pytest.mark.django_db
def test_sense_sessio_rep_401(comanda):
    assert APIClient().post(url(comanda.pk)).status_code == 401


@pytest.mark.django_db
@pytest.mark.parametrize("rol", [Usuari.Role.BIBLIOTECA, Usuari.Role.REPARTIDOR])
def test_una_biblioteca_o_un_repartidor_reben_403(comanda, rol):
    client = APIClient()
    client.force_authenticate(crea_usuari("altre@example.com", rol))

    assert client.post(url(comanda.pk)).status_code == 403


@pytest.mark.django_db
def test_nomes_es_pot_fer_post(client, comanda):
    assert client.get(url(comanda.pk)).status_code == 405


@pytest.mark.django_db
def test_la_resposta_te_el_format_de_comanda_del_contracte(client, comanda):
    dades = client.post(url(comanda.pk)).json()

    assert set(dades) == {"id", "estat", "biblioteca", "llibres", "data_lliurament", "creada"}
    assert [llibre["titol"] for llibre in dades["llibres"]] == ["La plaça del Diamant", "Solitud"]


@pytest.mark.django_db
def test_cancellar_una_comanda_preparada_tambe_torna_els_exemplars(client, comanda, biblioteca, llibres):
    posa_estat(comanda, Estat.PREPARADA)

    client.post(url(comanda.pk))

    assert [exemplars(llibre, biblioteca) for llibre in llibres] == [2, 2]


@pytest.mark.django_db
def test_l_exemplar_alliberat_el_pot_demanar_un_altre_usuari(client, lector, biblioteca):
    llibre = Llibre.objects.create(titol="Mirall trencat", autor="Mercè Rodoreda", isbn="9788475881355")
    ExemplarBiblioteca.objects.create(llibre=llibre, biblioteca=biblioteca, quantitat=1)
    comanda = confirma_comanda(lector, biblioteca, [llibre])
    altre = crea_usuari("altre@example.com")
    with pytest.raises(LlibresSenseEstoc):
        confirma_comanda(altre, biblioteca, [llibre])

    client.post(url(comanda.pk))

    assert confirma_comanda(altre, biblioteca, [llibre]).usuari == altre
    assert exemplars(llibre, biblioteca) == 0


@pytest.mark.django_db
def test_cancellar_una_comanda_no_toca_les_altres(client, lector, biblioteca, llibres, comanda):
    altra = confirma_comanda(lector, biblioteca, llibres[:1])

    client.post(url(comanda.pk))

    altra.refresh_from_db()
    assert altra.estat == Estat.REBUDA
    assert exemplars(llibres[0], biblioteca) == 1


@pytest.mark.django_db
@pytest.mark.parametrize("estat", [Estat.EN_CAMI, Estat.LLIURADA, Estat.CANCELLADA])
def test_si_no_es_pot_cancellar_no_queda_res_a_l_historial(client, comanda, estat):
    posa_estat(comanda, estat)

    client.post(url(comanda.pk))

    assert list(comanda.canvis_estat.values_list("estat", flat=True)) == [Estat.REBUDA]


@pytest.mark.django_db
def test_un_usuari_desactivat_rep_403(client, lector, comanda):
    lector.is_active = False
    lector.save(update_fields=["is_active"])

    resposta = client.post(url(comanda.pk))

    assert resposta.status_code == 403
    assert resposta.json() == {"detail": "No té permisos per realitzar aquesta acció."}


def en_paral_lel(*feines):
    """Executa les feines alhora, cadascuna en un fil amb la seva connexió."""
    sortida = threading.Barrier(len(feines))

    def executa(feina):
        try:
            sortida.wait()
            feina()
        finally:
            connection.close()

    fils = [threading.Thread(target=executa, args=(feina,)) for feina in feines]
    for fil in fils:
        fil.start()
    for fil in fils:
        fil.join()


@pytest.mark.django_db(transaction=True)
def test_dues_cancellacions_alhora_nomes_tornen_els_exemplars_una_vegada():
    biblioteca = crea_usuari("biblioteca@example.com", Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=biblioteca, nom="Biblioteca Montbau")
    lector = crea_usuari("lector@example.com")
    llibre = Llibre.objects.create(titol="Solitud", autor="Víctor Català", isbn="9788475882574")
    ExemplarBiblioteca.objects.create(llibre=llibre, biblioteca=biblioteca, quantitat=1)
    comanda = confirma_comanda(lector, biblioteca, [llibre])
    estats = []

    def cancella():
        client = APIClient()
        client.force_authenticate(lector)
        estats.append(client.post(url(comanda.pk)).status_code)

    en_paral_lel(cancella, cancella)

    assert sorted(estats) == [200, 409]
    assert exemplars(llibre, biblioteca) == 1


@pytest.mark.django_db(transaction=True)
def test_una_cancellacio_i_una_comanda_alhora_no_es_bloquegen():
    """Una cancel·la una comanda amb A i B mentre una altra demana B i A."""
    biblioteca = crea_usuari("biblioteca@example.com", Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=biblioteca, nom="Biblioteca Montbau")
    placa = Llibre.objects.create(titol="La plaça del Diamant", autor="Mercè Rodoreda", isbn="9788429740011")
    solitud = Llibre.objects.create(titol="Solitud", autor="Víctor Català", isbn="9788475882574")
    for llibre in (placa, solitud):
        ExemplarBiblioteca.objects.create(llibre=llibre, biblioteca=biblioteca, quantitat=2)
    comanda = confirma_comanda(crea_usuari("primer@example.com"), biblioteca, [placa, solitud])
    altre = crea_usuari("segon@example.com")
    errors = []

    def cancella():
        try:
            cancella_comanda(comanda)
        except Exception as error:
            errors.append(error)

    def demana():
        try:
            confirma_comanda(altre, biblioteca, [solitud, placa])
        except Exception as error:
            errors.append(error)

    en_paral_lel(cancella, demana)

    assert errors == []
    assert [exemplars(llibre, biblioteca) for llibre in (placa, solitud)] == [1, 1]
