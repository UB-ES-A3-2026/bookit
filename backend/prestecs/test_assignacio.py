"""Tests de l'assignació de les comandes als repartidors segons les franges (US14-T3)."""

import threading
from datetime import date, time
from io import StringIO

import pytest
from django.core.management import call_command
from django.db import connection
from django.test import override_settings
from rest_framework.test import APIClient

from prestecs.assignacio import assigna_comanda, assigna_pendents
from prestecs.models import Comanda
from usuaris.models import Biblioteca, FranjaDisponibilitat, PerfilRepartidor, Usuari

Estat = Comanda.Estat
Dia = FranjaDisponibilitat.Dia
# El 23 de novembre de 2026 és dilluns.
DILLUNS = date(2026, 11, 23)
DIMARTS = date(2026, 11, 24)


def crea_usuari(correu, rol=Usuari.Role.USUARI, nom=None):
    return Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {"name": nom or correu.split("@")[0], "address": "C/ Major 1", "library_card_number": correu, "role": rol},
    )


def crea_repartidor(nom, dni, franges=(), estat=PerfilRepartidor.Estat.VALIDAT):
    usuari = crea_usuari(f"{nom.lower()}@example.com", Usuari.Role.REPARTIDOR, nom=nom)
    perfil = PerfilRepartidor.objects.create(
        usuari=usuari,
        cognoms="Puig",
        dni=dni,
        telefon="612345678",
        vehicle=PerfilRepartidor.Vehicle.BICI,
        num_seguretat_social="281234567840",
        estat=estat,
    )
    for dia, inici, fi in franges:
        perfil.franges.create(dia=dia, hora_inici=inici, hora_fi=fi)
    return usuari


@pytest.fixture
def biblioteca():
    usuari = crea_usuari("biblioteca@example.com", Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=usuari, nom="Biblioteca Montbau")
    usuari.is_active = True
    usuari.save(update_fields=["is_active"])
    return usuari


@pytest.fixture
def lector():
    return crea_usuari("lector@example.com")


@pytest.fixture
def nova_comanda(lector, biblioteca):
    def crea(estat=Estat.PREPARADA):
        return Comanda.objects.create(usuari=lector, biblioteca=biblioteca, estat=estat)

    return crea


def horari(comanda):
    comanda.refresh_from_db()
    return (comanda.repartidor, comanda.data_lliurament, comanda.hora_inici_lliurament, comanda.hora_fi_lliurament)


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_assigna_la_comanda_al_principi_de_la_franja(nova_comanda):
    jordi = crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(13))])
    comanda = nova_comanda()

    assert assigna_comanda(comanda, primer_dia=DILLUNS)

    assert horari(comanda) == (jordi, DILLUNS, time(9), time(9, 30))


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_la_seguent_comanda_va_despres_de_l_anterior(nova_comanda):
    jordi = crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(13))])
    primera, segona = nova_comanda(), nova_comanda()

    assigna_comanda(primera, primer_dia=DILLUNS)
    assigna_comanda(segona, primer_dia=DILLUNS)

    assert horari(segona) == (jordi, DILLUNS, time(9, 30), time(10))


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_un_lliurament_que_no_cap_sencer_a_la_franja_no_s_hi_assigna(nova_comanda):
    crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(9, 20))])
    comanda = nova_comanda()

    assert not assigna_comanda(comanda, primer_dia=DILLUNS)

    assert horari(comanda) == (None, None, None, None)


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_un_lliurament_que_acaba_just_al_final_de_la_franja_s_hi_assigna(nova_comanda):
    crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(9, 30))])

    assert assigna_comanda(nova_comanda(), primer_dia=DILLUNS)


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_quan_una_franja_s_omple_passa_a_la_seguent_del_mateix_dia(nova_comanda):
    jordi = crea_repartidor(
        "Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(9, 30)), (Dia.DILLUNS, time(16), time(18))]
    )
    primera, segona = nova_comanda(), nova_comanda()

    assigna_comanda(primera, primer_dia=DILLUNS)
    assigna_comanda(segona, primer_dia=DILLUNS)

    assert horari(segona) == (jordi, DILLUNS, time(16), time(16, 30))


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_quan_el_dia_s_omple_passa_al_seguent_dia_amb_franja(nova_comanda):
    jordi = crea_repartidor(
        "Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(9, 30)), (Dia.DIJOUS, time(10), time(12))]
    )
    primera, segona = nova_comanda(), nova_comanda()

    assigna_comanda(primera, primer_dia=DILLUNS)
    assigna_comanda(segona, primer_dia=DILLUNS)

    assert horari(segona) == (jordi, date(2026, 11, 26), time(10), time(10, 30))


@pytest.mark.django_db
def test_nomes_es_fa_servir_el_dia_de_la_setmana_de_la_franja(nova_comanda):
    crea_repartidor("Jordi", "12345678Z", [(Dia.DIMARTS, time(9), time(13))])
    comanda = nova_comanda()

    assigna_comanda(comanda, primer_dia=DILLUNS)

    comanda.refresh_from_db()
    assert comanda.data_lliurament == DIMARTS


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_si_una_setmana_no_hi_ha_cap_forat_la_comanda_no_s_assigna(nova_comanda):
    crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(9, 30))])
    primera, segona = nova_comanda(), nova_comanda()

    assert assigna_comanda(primera, primer_dia=DILLUNS)
    assert not assigna_comanda(segona, primer_dia=DILLUNS)


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_tria_el_repartidor_que_pot_comencar_abans(nova_comanda):
    crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(11), time(13))])
    marta = crea_repartidor("Marta", "87654321X", [(Dia.DILLUNS, time(9), time(13))])
    comanda = nova_comanda()

    assigna_comanda(comanda, primer_dia=DILLUNS)

    assert horari(comanda)[0] == marta


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_reparteix_les_comandes_entre_repartidors_amb_la_mateixa_franja(nova_comanda):
    jordi = crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(13))])
    marta = crea_repartidor("Marta", "87654321X", [(Dia.DILLUNS, time(9), time(13))])
    primera, segona = nova_comanda(), nova_comanda()

    assigna_comanda(primera, primer_dia=DILLUNS)
    assigna_comanda(segona, primer_dia=DILLUNS)

    assert {horari(primera)[0], horari(segona)[0]} == {jordi, marta}
    assert horari(segona)[2] == time(9)


@pytest.mark.django_db
@pytest.mark.parametrize("estat", [PerfilRepartidor.Estat.PENDENT, PerfilRepartidor.Estat.REBUTJAT])
def test_no_s_assigna_a_repartidors_sense_validar(nova_comanda, estat):
    crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(13))], estat=estat)

    assert not assigna_comanda(nova_comanda(), primer_dia=DILLUNS)


@pytest.mark.django_db
def test_no_s_assigna_a_repartidors_desactivats(nova_comanda):
    jordi = crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(13))])
    jordi.is_active = False
    jordi.save(update_fields=["is_active"])

    assert not assigna_comanda(nova_comanda(), primer_dia=DILLUNS)


@pytest.mark.django_db
def test_sense_repartidors_amb_franges_no_s_assigna(nova_comanda):
    crea_repartidor("Jordi", "12345678Z")

    assert not assigna_comanda(nova_comanda(), primer_dia=DILLUNS)


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_una_comanda_cancellada_allibera_el_seu_forat(nova_comanda):
    jordi = crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(9, 30))])
    cancellada = nova_comanda()
    assigna_comanda(cancellada, primer_dia=DILLUNS)
    Comanda.objects.filter(pk=cancellada.pk).update(estat=Estat.CANCELLADA)
    comanda = nova_comanda()

    assert assigna_comanda(comanda, primer_dia=DILLUNS)
    assert horari(comanda) == (jordi, DILLUNS, time(9), time(9, 30))


@pytest.mark.django_db
@pytest.mark.parametrize("estat", [Estat.REBUDA, Estat.EN_CAMI, Estat.LLIURADA, Estat.CANCELLADA])
def test_nomes_s_assignen_comandes_preparades(nova_comanda, estat):
    crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(13))])
    comanda = nova_comanda(estat=estat)

    assert not assigna_comanda(comanda, primer_dia=DILLUNS)
    assert horari(comanda)[0] is None


@pytest.mark.django_db
def test_una_comanda_ja_assignada_no_es_torna_a_assignar(nova_comanda):
    jordi = crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(13))])
    crea_repartidor("Marta", "87654321X", [(Dia.DILLUNS, time(8), time(13))])
    comanda = nova_comanda()
    Comanda.objects.filter(pk=comanda.pk).update(repartidor=jordi)

    assert not assigna_comanda(comanda, primer_dia=DILLUNS)
    assert horari(comanda)[0] == jordi


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=45)
def test_la_durada_del_lliurament_es_configurable(nova_comanda):
    crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(13))])
    comanda = nova_comanda()

    assigna_comanda(comanda, primer_dia=DILLUNS)

    assert horari(comanda)[3] == time(9, 45)


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_assigna_les_pendents_de_la_mes_antiga_a_la_mes_nova(nova_comanda):
    crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(10))])
    primera, segona, tercera = nova_comanda(), nova_comanda(), nova_comanda()
    nova_comanda(estat=Estat.REBUDA)

    assert assigna_pendents(primer_dia=DILLUNS) == (2, 1)
    assert horari(primera)[2] == time(9)
    assert horari(segona)[2] == time(9, 30)
    assert horari(tercera)[0] is None


@pytest.mark.django_db
def test_l_ordre_assigna_les_comandes_pendents(nova_comanda, monkeypatch):
    monkeypatch.setattr("prestecs.assignacio.timezone.localdate", lambda: date(2026, 11, 22))
    crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(13))])
    comanda = nova_comanda()
    sortida = StringIO()

    call_command("assigna_comandes", stdout=sortida)

    assert horari(comanda)[1] == DILLUNS
    assert sortida.getvalue().strip() == "Comandes assignades: 1. Sense repartidor disponible: 0."


@pytest.mark.django_db
def test_en_marcar_la_comanda_com_a_llesta_s_assigna_a_un_repartidor(biblioteca, nova_comanda, monkeypatch):
    monkeypatch.setattr("prestecs.assignacio.timezone.localdate", lambda: date(2026, 11, 22))
    jordi = crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(13))])
    comanda = nova_comanda(estat=Estat.REBUDA)
    client = APIClient()
    client.force_authenticate(biblioteca)

    resposta = client.post(f"/api/prestecs/biblioteca/comandes/{comanda.pk}/preparada/")

    assert resposta.status_code == 200
    assert resposta.json()["data_lliurament"] == "2026-11-23"
    assert horari(comanda)[0] == jordi


@pytest.mark.django_db
def test_sense_repartidors_la_comanda_es_queda_preparada_sense_assignar(biblioteca, nova_comanda):
    comanda = nova_comanda(estat=Estat.REBUDA)
    client = APIClient()
    client.force_authenticate(biblioteca)

    resposta = client.post(f"/api/prestecs/biblioteca/comandes/{comanda.pk}/preparada/")

    assert resposta.status_code == 200
    comanda.refresh_from_db()
    assert comanda.estat == Estat.PREPARADA
    assert comanda.repartidor is None


@pytest.mark.django_db(transaction=True)
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_dues_assignacions_alhora_no_ocupen_el_mateix_forat():
    """Dos fils, cadascun amb la seva connexió, assignen alhora l'únic forat que hi ha."""
    biblioteca = crea_usuari("biblioteca@example.com", Usuari.Role.BIBLIOTECA)
    lector = crea_usuari("lector@example.com")
    crea_repartidor("Jordi", "12345678Z", [(Dia.DILLUNS, time(9), time(9, 30))])
    comandes = [
        Comanda.objects.create(usuari=lector, biblioteca=biblioteca, estat=Estat.PREPARADA) for _ in range(2)
    ]
    sortida = threading.Barrier(2)
    resultats = []

    def assigna(comanda):
        try:
            sortida.wait()
            resultats.append(assigna_comanda(comanda, primer_dia=DILLUNS))
        finally:
            connection.close()

    fils = [threading.Thread(target=assigna, args=(comanda,)) for comanda in comandes]
    for fil in fils:
        fil.start()
    for fil in fils:
        fil.join()

    assert sorted(resultats) == [False, True]
    assert Comanda.objects.filter(repartidor__isnull=False).count() == 1
