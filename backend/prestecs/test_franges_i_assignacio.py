"""Tests de les franges desades pel repartidor i de l'assignació estricta dins d'elles (US14-T4).

Completen els de les franges (`usuaris/test_api_franges.py`) i els de l'assignació
(`test_assignacio.py`) provant les dues parts juntes: el repartidor desa les franges
amb l'API i les comandes s'hi assignen sense sortir-ne mai.
"""

from datetime import date, datetime, time, timedelta

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from prestecs.assignacio import assigna_comanda, assigna_pendents, primer_forat
from prestecs.models import Comanda
from usuaris.models import Biblioteca, FranjaDisponibilitat, PerfilRepartidor, Usuari

Estat = Comanda.Estat
Dia = FranjaDisponibilitat.Dia
URL_FRANGES = "/api/usuaris/repartidor/franges/"
# El 23 de novembre de 2026 és dilluns.
DILLUNS = date(2026, 11, 23)


def crea_usuari(correu, rol=Usuari.Role.USUARI, nom=None):
    return Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {"name": nom or correu.split("@")[0], "address": "C/ Major 1", "library_card_number": correu, "role": rol},
    )


def crea_repartidor(nom, dni, estat=PerfilRepartidor.Estat.VALIDAT):
    usuari = crea_usuari(f"{nom.lower()}@example.com", Usuari.Role.REPARTIDOR, nom=nom)
    PerfilRepartidor.objects.create(
        usuari=usuari,
        cognoms="Puig",
        dni=dni,
        telefon="612345678",
        vehicle=PerfilRepartidor.Vehicle.BICI,
        num_seguretat_social="281234567840",
        estat=estat,
    )
    return usuari


def desa_franges(repartidor, franges):
    client = APIClient()
    client.force_authenticate(repartidor)
    return client.put(
        URL_FRANGES,
        {"franges": [{"dia": dia, "hora_inici": inici, "hora_fi": fi} for dia, inici, fi in franges]},
        format="json",
    )


@pytest.fixture
def biblioteca():
    usuari = crea_usuari("biblioteca@example.com", Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=usuari, nom="Biblioteca Montbau")
    usuari.is_active = True
    usuari.save(update_fields=["is_active"])
    return usuari


@pytest.fixture
def nova_comanda(biblioteca):
    lector = crea_usuari("lector@example.com")

    def crea(estat=Estat.PREPARADA, **camps):
        return Comanda.objects.create(usuari=lector, biblioteca=biblioteca, estat=estat, **camps)

    return crea


def lliurament(comanda):
    comanda.refresh_from_db()
    return comanda.data_lliurament, comanda.hora_inici_lliurament, comanda.hora_fi_lliurament


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_les_franges_desades_amb_l_api_es_fan_servir_per_assignar(nova_comanda):
    jordi = crea_repartidor("Jordi", "12345678Z")
    assert desa_franges(jordi, [(Dia.DIMECRES, "10:00", "12:00")]).status_code == 200
    comanda = nova_comanda()

    assert assigna_comanda(comanda, primer_dia=DILLUNS)

    comanda.refresh_from_db()
    assert comanda.repartidor == jordi
    assert lliurament(comanda) == (date(2026, 11, 25), time(10), time(10, 30))


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_si_el_repartidor_canvia_les_franges_s_assigna_segons_les_noves(nova_comanda):
    jordi = crea_repartidor("Jordi", "12345678Z")
    desa_franges(jordi, [(Dia.DILLUNS, "09:00", "13:00")])
    desa_franges(jordi, [(Dia.DIVENDRES, "16:00", "18:00")])
    comanda = nova_comanda()

    assigna_comanda(comanda, primer_dia=DILLUNS)

    assert lliurament(comanda) == (date(2026, 11, 27), time(16), time(16, 30))


@pytest.mark.django_db
def test_si_el_repartidor_es_treu_totes_les_franges_ja_no_rep_comandes(nova_comanda):
    jordi = crea_repartidor("Jordi", "12345678Z")
    desa_franges(jordi, [(Dia.DILLUNS, "09:00", "13:00")])
    desa_franges(jordi, [])

    assert not assigna_comanda(nova_comanda(), primer_dia=DILLUNS)


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_l_ordre_assigna_les_comandes_quan_el_repartidor_afegeix_franges(nova_comanda):
    jordi = crea_repartidor("Jordi", "12345678Z")
    comanda = nova_comanda()
    assert assigna_pendents(primer_dia=DILLUNS) == (0, 1)

    desa_franges(jordi, [(Dia.DIMARTS, "08:00", "09:00")])

    assert assigna_pendents(primer_dia=DILLUNS) == (1, 0)
    assert lliurament(comanda) == (date(2026, 11, 24), time(8), time(8, 30))


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_omple_el_forat_que_queda_abans_d_un_lliurament_ja_assignat(nova_comanda):
    jordi = crea_repartidor("Jordi", "12345678Z")
    desa_franges(jordi, [(Dia.DILLUNS, "09:00", "11:00")])
    nova_comanda(
        repartidor=jordi,
        data_lliurament=DILLUNS,
        hora_inici_lliurament=time(9, 30),
        hora_fi_lliurament=time(10),
    )
    comanda = nova_comanda()

    assigna_comanda(comanda, primer_dia=DILLUNS)

    assert lliurament(comanda) == (DILLUNS, time(9), time(9, 30))


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=30)
def test_si_el_forat_es_massa_petit_va_despres_del_lliurament(nova_comanda):
    jordi = crea_repartidor("Jordi", "12345678Z")
    desa_franges(jordi, [(Dia.DILLUNS, "09:00", "11:00")])
    nova_comanda(
        repartidor=jordi,
        data_lliurament=DILLUNS,
        hora_inici_lliurament=time(9, 20),
        hora_fi_lliurament=time(9, 50),
    )
    comanda = nova_comanda()

    assigna_comanda(comanda, primer_dia=DILLUNS)

    assert lliurament(comanda) == (DILLUNS, time(9, 50), time(10, 20))


@pytest.mark.django_db
@override_settings(DURADA_LLIURAMENT_MINUTS=25)
def test_cap_lliurament_surt_de_les_franges_ni_se_n_trepitja_cap(nova_comanda):
    jordi = crea_repartidor("Jordi", "12345678Z")
    marta = crea_repartidor("Marta", "87654321X")
    desa_franges(jordi, [(Dia.DILLUNS, "09:00", "10:10"), (Dia.DIMECRES, "17:00", "18:00")])
    desa_franges(marta, [(Dia.DILLUNS, "09:30", "10:00"), (Dia.DIJOUS, "08:15", "09:05")])
    comandes = [nova_comanda() for _ in range(12)]

    assignades, sense_repartidor = assigna_pendents(primer_dia=DILLUNS)

    # Jordi: 2 el dilluns i 2 el dimecres. Marta: 1 el dilluns i 2 el dijous.
    assert (assignades, sense_repartidor) == (7, 5)
    franges = {
        repartidor.pk: list(repartidor.perfil_repartidor.franges.all()) for repartidor in (jordi, marta)
    }
    per_repartidor = {}
    for comanda in comandes:
        comanda.refresh_from_db()
        if comanda.repartidor_id is None:
            continue
        inici = datetime.combine(comanda.data_lliurament, comanda.hora_inici_lliurament)
        fi = datetime.combine(comanda.data_lliurament, comanda.hora_fi_lliurament)
        assert fi - inici == timedelta(minutes=25)
        assert any(franja.cobreix(inici, fi) for franja in franges[comanda.repartidor_id])
        per_repartidor.setdefault(comanda.repartidor_id, []).append((inici, fi))

    for lliuraments in per_repartidor.values():
        lliuraments.sort()
        for (_, fi_anterior), (inici_seguent, _) in zip(lliuraments, lliuraments[1:]):
            assert fi_anterior <= inici_seguent


@pytest.mark.django_db
def test_un_repartidor_rebutjat_no_rep_comandes_encara_que_tingui_franges(nova_comanda):
    jordi = crea_repartidor("Jordi", "12345678Z")
    desa_franges(jordi, [(Dia.DILLUNS, "09:00", "13:00")])
    PerfilRepartidor.objects.filter(usuari=jordi).update(estat=PerfilRepartidor.Estat.REBUTJAT)

    assert not assigna_comanda(nova_comanda(), primer_dia=DILLUNS)


def franja(dia, inici, fi):
    return FranjaDisponibilitat(dia=dia, hora_inici=inici, hora_fi=fi)


def a_les(hora, minuts=0):
    return datetime.combine(DILLUNS, time(hora, minuts))


def test_primer_forat_sense_lliuraments_comenca_amb_la_franja():
    franges = [franja(Dia.DILLUNS, time(9), time(10))]

    assert primer_forat(DILLUNS, franges, [], timedelta(minutes=30)) == a_les(9)


def test_primer_forat_salta_els_lliuraments_que_ja_hi_ha():
    franges = [franja(Dia.DILLUNS, time(9), time(11))]
    ocupats = [(a_les(9), a_les(9, 30)), (a_les(9, 30), a_les(10))]

    assert primer_forat(DILLUNS, franges, ocupats, timedelta(minutes=30)) == a_les(10)


def test_primer_forat_ignora_els_lliuraments_d_abans_de_la_franja():
    franges = [franja(Dia.DILLUNS, time(16), time(17))]
    ocupats = [(a_les(9), a_les(9, 30))]

    assert primer_forat(DILLUNS, franges, ocupats, timedelta(minutes=30)) == a_les(16)


def test_primer_forat_retorna_none_si_no_cap_a_cap_franja():
    franges = [franja(Dia.DILLUNS, time(9), time(9, 45))]
    ocupats = [(a_les(9, 15), a_les(9, 30))]

    assert primer_forat(DILLUNS, franges, ocupats, timedelta(minutes=20)) is None


def test_primer_forat_no_fa_servir_franges_d_un_altre_dia():
    franges = [franja(Dia.DIMARTS, time(9), time(13))]

    assert primer_forat(DILLUNS, franges, [], timedelta(minutes=30)) is None
