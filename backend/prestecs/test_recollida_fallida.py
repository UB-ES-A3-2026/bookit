"""Tests de la replanificació quan falla la recollida a la biblioteca (US13-T12).

Si falla una parada d'una comanda que encara no ha sortit, la comanda es treu de
la ruta i es torna a assignar. També hi ha els missatges d'error de completar i
de fallar una parada, que abans es confonien.
"""

from datetime import timedelta, time

import pytest
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from prestecs.assignacio import assigna_comanda
from prestecs.models import Comanda, Parada, Ruta
from usuaris.models import Biblioteca, FranjaDisponibilitat, PerfilRepartidor, Usuari

Estat = Comanda.Estat
Tipus = Parada.Tipus
Dia = FranjaDisponibilitat.Dia
TOT_EL_DIA = [(dia, time(8), time(20)) for dia in Dia.values]


def crea_usuari(correu, rol=Usuari.Role.USUARI, nom=None):
    return Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {"name": nom or correu.split("@")[0], "address": "C/ Major 1", "library_card_number": correu, "role": rol},
    )


def crea_repartidor(nom, dni, franges=TOT_EL_DIA):
    usuari = crea_usuari(f"{nom.lower()}@example.com", Usuari.Role.REPARTIDOR, nom=nom)
    perfil = PerfilRepartidor.objects.create(
        usuari=usuari,
        cognoms="Puig",
        dni=dni,
        telefon="612345678",
        vehicle=PerfilRepartidor.Vehicle.BICI,
        num_seguretat_social="281234567840",
        estat=PerfilRepartidor.Estat.VALIDAT,
    )
    for dia, inici, fi in franges:
        perfil.franges.create(dia=dia, hora_inici=inici, hora_fi=fi)
    return usuari


@pytest.fixture
def jordi():
    return crea_repartidor("Jordi", "12345678Z")


@pytest.fixture
def comanda(jordi):
    biblioteca = crea_usuari("biblioteca@example.com", Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=biblioteca, nom="Biblioteca Montbau")
    biblioteca.is_active = True
    biblioteca.save(update_fields=["is_active"])
    comanda = Comanda.objects.create(
        usuari=crea_usuari("lector@example.com"), biblioteca=biblioteca, estat=Estat.PREPARADA
    )
    # Assignada a la ruta d'avui, amb la recollida i el lliurament.
    assert assigna_comanda(comanda, primer_dia=timezone.localdate())
    comanda.refresh_from_db()
    return comanda


def client_de(usuari):
    client = APIClient()
    client.force_authenticate(usuari)
    return client


def falla(usuari, parada, motiu="La biblioteca era tancada"):
    return client_de(usuari).post(
        f"/api/prestecs/repartidor/parades/{parada.pk}/fallida/", {"motiu": motiu}, format="json"
    )


def parada(comanda, tipus, data=None):
    return Parada.objects.get(comanda=comanda, tipus=tipus, ruta__data=data or timezone.localdate())


@pytest.mark.django_db
def test_si_falla_la_recollida_el_lliurament_es_cancella(comanda, jordi):
    resposta = falla(jordi, parada(comanda, Tipus.RECOLLIDA))

    assert resposta.status_code == 200
    assert parada(comanda, Tipus.RECOLLIDA).estat == Parada.Estat.FALLIDA
    assert parada(comanda, Tipus.RECOLLIDA).motiu == "La biblioteca era tancada"
    assert parada(comanda, Tipus.LLIVRAMENT).estat == Parada.Estat.CANCELLADA


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_si_falla_la_recollida_la_comanda_es_torna_a_assignar_un_altre_dia(comanda, jordi):
    dema = timezone.localdate() + timedelta(days=1)

    falla(jordi, parada(comanda, Tipus.RECOLLIDA))

    comanda.refresh_from_db()
    assert comanda.estat == Estat.PREPARADA
    assert comanda.repartidor == jordi
    assert comanda.data_lliurament == dema
    noves = Parada.objects.filter(comanda=comanda, ruta__data=dema)
    assert {(nova.tipus, nova.estat) for nova in noves} == {
        (Tipus.RECOLLIDA, Parada.Estat.PENDENT),
        (Tipus.LLIVRAMENT, Parada.Estat.PENDENT),
    }


@pytest.mark.django_db
def test_si_no_hi_ha_cap_forat_es_queda_preparada_sense_repartidor(comanda, jordi):
    FranjaDisponibilitat.objects.all().delete()

    falla(jordi, parada(comanda, Tipus.RECOLLIDA))

    comanda.refresh_from_db()
    assert comanda.estat == Estat.PREPARADA
    assert (comanda.repartidor, comanda.data_lliurament, comanda.hora_inici_lliurament) == (None, None, None)


@pytest.mark.django_db
def test_la_ruta_d_avui_nomes_mostra_la_recollida_fallida(comanda, jordi):
    falla(jordi, parada(comanda, Tipus.RECOLLIDA))

    ruta = client_de(jordi).get("/api/prestecs/repartidor/ruta-avui/").json()

    assert [(item["tipus"], item["comanda"]) for item in ruta] == [("recollida", comanda.pk)]
    assert parada(comanda, Tipus.LLIVRAMENT).estat == Parada.Estat.CANCELLADA


@pytest.mark.django_db
def test_no_s_envia_cap_avis_a_l_usuari_perque_la_comanda_no_canvia_d_estat(comanda, jordi):
    abans = comanda.notificacions.count()

    falla(jordi, parada(comanda, Tipus.RECOLLIDA))

    assert comanda.notificacions.count() == abans


@pytest.mark.django_db
def test_si_falla_el_lliurament_continua_tornant_a_preparada(comanda, jordi):
    client = client_de(jordi)
    client.post(f"/api/prestecs/repartidor/parades/{parada(comanda, Tipus.RECOLLIDA).pk}/completar/")

    resposta = falla(jordi, parada(comanda, Tipus.LLIVRAMENT), "Destinatari absent")

    assert resposta.status_code == 200
    comanda.refresh_from_db()
    assert comanda.estat == Estat.PREPARADA
    assert parada(comanda, Tipus.RECOLLIDA).estat == Parada.Estat.COMPLETADA
    assert parada(comanda, Tipus.LLIVRAMENT).estat == Parada.Estat.FALLIDA


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_si_torna_a_la_mateixa_ruta_les_parades_tornen_a_estar_pendents(jordi):
    """Si la comanda era a la ruta de demà i hi torna, es reaprofiten les parades."""
    biblioteca = crea_usuari("biblioteca@example.com", Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=biblioteca, nom="Biblioteca Montbau")
    comanda = Comanda.objects.create(
        usuari=crea_usuari("lector@example.com"), biblioteca=biblioteca, estat=Estat.PREPARADA
    )
    dema = timezone.localdate() + timedelta(days=1)
    assert assigna_comanda(comanda)
    assert Ruta.objects.get().data == dema

    falla(jordi, parada(comanda, Tipus.RECOLLIDA, dema))

    assert Ruta.objects.count() == 1
    assert {(item.tipus, item.estat, item.motiu) for item in Parada.objects.filter(comanda=comanda)} == {
        (Tipus.RECOLLIDA, Parada.Estat.PENDENT, ""),
        (Tipus.LLIVRAMENT, Parada.Estat.PENDENT, ""),
    }


@pytest.mark.django_db
def test_completar_una_parada_cancellada_diu_que_no_es_pot_completar(comanda, jordi):
    falla(jordi, parada(comanda, Tipus.RECOLLIDA))
    lliurament = parada(comanda, Tipus.LLIVRAMENT)

    resposta = client_de(jordi).post(f"/api/prestecs/repartidor/parades/{lliurament.pk}/completar/")

    assert resposta.status_code == 409
    assert resposta.json() == {"detail": "La parada no es pot completar."}


@pytest.mark.django_db
def test_fallar_una_parada_completada_diu_que_no_es_pot_marcar_com_a_fallida(comanda, jordi):
    recollida = parada(comanda, Tipus.RECOLLIDA)
    client_de(jordi).post(f"/api/prestecs/repartidor/parades/{recollida.pk}/completar/")

    resposta = falla(jordi, recollida)

    assert resposta.status_code == 409
    assert resposta.json() == {"detail": "La parada no es pot marcar com a fallida."}
