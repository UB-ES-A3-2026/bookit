"""Tests de l'endpoint per marcar una comanda com a llesta per a recollida (US15-T1)."""

import threading

import pytest
from django.db import connection
from rest_framework.test import APIClient

from cataleg.models import Llibre
from prestecs.models import Comanda, LiniaComanda
from prestecs.serveis import TransicioNoPermesa, canvia_estat
from usuaris.models import Biblioteca, Usuari

Estat = Comanda.Estat


def url(comanda_id):
    return f"/api/prestecs/biblioteca/comandes/{comanda_id}/preparada/"


def crea_usuari(correu, rol=Usuari.Role.USUARI):
    return Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {"name": correu.split("@")[0], "address": "C/ Major 1", "library_card_number": correu, "role": rol},
    )


def crea_biblioteca(correu, nom):
    usuari = crea_usuari(correu, Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=usuari, nom=nom)
    usuari.is_active = True
    usuari.save(update_fields=["is_active"])
    return usuari


@pytest.fixture
def biblioteca():
    return crea_biblioteca("biblioteca@example.com", "Biblioteca Montbau")


@pytest.fixture
def client(biblioteca):
    client = APIClient()
    client.force_authenticate(biblioteca)
    return client


@pytest.fixture
def comanda(biblioteca):
    comanda = Comanda.objects.create(usuari=crea_usuari("lector@example.com"), biblioteca=biblioteca)
    llibre = Llibre.objects.create(titol="Solitud", autor="Víctor Català", isbn="9788475882574")
    LiniaComanda.objects.create(comanda=comanda, llibre=llibre)
    return comanda


@pytest.mark.django_db
def test_marca_una_comanda_rebuda_com_a_llesta(client, comanda):
    resposta = client.post(url(comanda.pk))

    assert resposta.status_code == 200
    assert resposta.json()["id"] == comanda.pk
    assert resposta.json()["estat"] == "preparada"
    comanda.refresh_from_db()
    assert comanda.estat == Estat.PREPARADA


@pytest.mark.django_db
def test_el_canvi_queda_a_l_historial_de_la_comanda(client, comanda):
    client.post(url(comanda.pk))

    assert list(comanda.canvis_estat.values_list("estat", flat=True)) == [Estat.PREPARADA]


@pytest.mark.django_db
def test_una_comanda_que_ja_esta_llesta_dona_409(client, comanda):
    comanda.estat = Estat.PREPARADA
    comanda.save()

    resposta = client.post(url(comanda.pk))

    assert resposta.status_code == 409
    assert resposta.json() == {"detail": "Aquesta comanda ja està llesta per a recollida."}
    assert not comanda.canvis_estat.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("estat", "text"),
    [(Estat.EN_CAMI, "en camí"), (Estat.LLIURADA, "lliurada"), (Estat.CANCELLADA, "cancel·lada")],
)
def test_una_comanda_que_ja_ha_sortit_o_s_ha_cancellat_no_es_pot_marcar(client, comanda, estat, text):
    comanda.estat = estat
    comanda.save()

    resposta = client.post(url(comanda.pk))

    assert resposta.status_code == 409
    assert resposta.json() == {"detail": f"Aquesta comanda no es pot marcar com a llesta perquè està {text}."}
    comanda.refresh_from_db()
    assert comanda.estat == estat


@pytest.mark.django_db
def test_una_comanda_d_una_altra_biblioteca_dona_404(comanda):
    client = APIClient()
    client.force_authenticate(crea_biblioteca("altra@example.com", "Biblioteca Sant Gervasi"))

    resposta = client.post(url(comanda.pk))

    assert resposta.status_code == 404
    comanda.refresh_from_db()
    assert comanda.estat == Estat.REBUDA


@pytest.mark.django_db
def test_una_comanda_que_no_existeix_dona_404(client):
    assert client.post(url(999999)).status_code == 404


@pytest.mark.django_db
def test_sense_sessio_rep_401(comanda):
    assert APIClient().post(url(comanda.pk)).status_code == 401


@pytest.mark.django_db
@pytest.mark.parametrize("rol", [Usuari.Role.USUARI, Usuari.Role.REPARTIDOR])
def test_un_lector_o_un_repartidor_reben_403(comanda, rol):
    client = APIClient()
    client.force_authenticate(crea_usuari("altre@example.com", rol))

    assert client.post(url(comanda.pk)).status_code == 403


@pytest.mark.django_db
def test_una_biblioteca_inactiva_rep_403(client, biblioteca, comanda):
    biblioteca.is_active = False
    biblioteca.save(update_fields=["is_active"])

    assert client.post(url(comanda.pk)).status_code == 403


@pytest.mark.django_db
def test_nomes_es_pot_fer_post(client, comanda):
    assert client.get(url(comanda.pk)).status_code == 405


@pytest.mark.django_db
def test_la_resposta_te_el_format_de_comanda_del_contracte(client, comanda):
    dades = client.post(url(comanda.pk)).json()

    assert set(dades) == {"id", "estat", "biblioteca", "llibres", "data_lliurament", "creada"}
    assert dades["biblioteca"] == {"id": comanda.biblioteca_id, "nom": "Biblioteca Montbau"}
    assert [llibre["titol"] for llibre in dades["llibres"]] == ["Solitud"]


@pytest.mark.django_db
def test_marcar_una_comanda_no_toca_les_altres(client, biblioteca, comanda):
    altra = Comanda.objects.create(usuari=comanda.usuari, biblioteca=biblioteca)

    client.post(url(comanda.pk))

    altra.refresh_from_db()
    assert altra.estat == Estat.REBUDA


@pytest.mark.django_db
def test_marcar_la_comanda_n_actualitza_la_data_de_modificacio(client, comanda):
    abans = comanda.actualitzada

    client.post(url(comanda.pk))

    comanda.refresh_from_db()
    assert comanda.actualitzada > abans


@pytest.mark.django_db
@pytest.mark.parametrize("estat", [Estat.PREPARADA, Estat.EN_CAMI, Estat.LLIURADA, Estat.CANCELLADA])
def test_si_no_es_pot_marcar_no_queda_res_a_l_historial(client, comanda, estat):
    comanda.estat = estat
    comanda.save()

    client.post(url(comanda.pk))

    assert not comanda.canvis_estat.exists()


@pytest.mark.django_db
def test_un_compte_de_biblioteca_sense_perfil_rep_403(comanda):
    client = APIClient()
    client.force_authenticate(crea_usuari("sense-perfil@example.com", Usuari.Role.BIBLIOTECA))

    resposta = client.post(url(comanda.pk))

    assert resposta.status_code == 403
    assert resposta.json() == {"detail": "No té permisos per realitzar aquesta acció."}


@pytest.mark.django_db
def test_el_servei_no_deixa_passar_d_en_cami_a_preparada_si_nomes_es_permet_des_de_rebuda(comanda):
    comanda.estat = Estat.EN_CAMI
    comanda.save()

    with pytest.raises(TransicioNoPermesa):
        canvia_estat(comanda, Estat.PREPARADA, des_de=[Estat.REBUDA])

    comanda.refresh_from_db()
    assert comanda.estat == Estat.EN_CAMI


@pytest.mark.django_db
def test_sense_limitar_l_estat_una_parada_fallida_encara_torna_a_preparada(comanda):
    """La limitació de la biblioteca no ha de trencar el cas de la parada fallida (US13)."""
    comanda.estat = Estat.EN_CAMI
    comanda.save()

    canvia_estat(comanda, Estat.PREPARADA)

    comanda.refresh_from_db()
    assert comanda.estat == Estat.PREPARADA


@pytest.mark.django_db
def test_des_de_no_permet_canvis_que_les_transicions_no_permeten(comanda):
    with pytest.raises(TransicioNoPermesa):
        canvia_estat(comanda, Estat.LLIURADA, des_de=[Estat.REBUDA])


@pytest.mark.django_db(transaction=True)
def test_dues_peticions_alhora_nomes_marquen_la_comanda_una_vegada():
    """Dos fils, cadascun amb la seva connexió, marquen alhora la mateixa comanda."""
    biblioteca = crea_biblioteca("biblioteca@example.com", "Biblioteca Montbau")
    comanda = Comanda.objects.create(usuari=crea_usuari("lector@example.com"), biblioteca=biblioteca)
    sortida = threading.Barrier(2)
    estats = []

    def marca():
        try:
            client = APIClient()
            client.force_authenticate(biblioteca)
            sortida.wait()
            estats.append(client.post(url(comanda.pk)).status_code)
        finally:
            connection.close()

    fils = [threading.Thread(target=marca) for _ in range(2)]
    for fil in fils:
        fil.start()
    for fil in fils:
        fil.join()

    assert sorted(estats) == [200, 409]
    assert comanda.canvis_estat.count() == 1
