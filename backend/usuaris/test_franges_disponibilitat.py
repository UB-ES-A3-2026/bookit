"""Tests del model de franges de disponibilitat del repartidor (US14-T1)."""

from datetime import datetime, time

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from usuaris.models import FranjaDisponibilitat, PerfilRepartidor, Usuari

DILLUNS = FranjaDisponibilitat.Dia.DILLUNS
DIMARTS = FranjaDisponibilitat.Dia.DIMARTS


def crea_repartidor(correu="repartidor@example.com", dni="12345678Z"):
    usuari = Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {
            "name": "Jordi",
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
        num_seguretat_social="281234567840",
    )


@pytest.fixture
def repartidor():
    return crea_repartidor()


def franja(repartidor, dia, inici, fi):
    return FranjaDisponibilitat(repartidor=repartidor, dia=dia, hora_inici=inici, hora_fi=fi)


@pytest.mark.django_db
def test_un_repartidor_pot_tenir_diverses_franges(repartidor):
    franja(repartidor, DILLUNS, time(9), time(13)).save()
    franja(repartidor, DILLUNS, time(16), time(20)).save()
    franja(repartidor, DIMARTS, time(9), time(13)).save()

    assert repartidor.franges.count() == 3


@pytest.mark.django_db
def test_les_franges_surten_per_dia_i_hora(repartidor):
    tarda = franja(repartidor, DILLUNS, time(16), time(20))
    dimarts = franja(repartidor, DIMARTS, time(9), time(13))
    mati = franja(repartidor, DILLUNS, time(9), time(13))
    for f in (tarda, dimarts, mati):
        f.save()

    assert list(repartidor.franges.all()) == [mati, tarda, dimarts]


@pytest.mark.django_db
def test_el_text_de_la_franja(repartidor):
    assert str(franja(repartidor, DILLUNS, time(9), time(13, 30))) == "Dilluns de 09:00 a 13:30"


@pytest.mark.django_db
@pytest.mark.parametrize("fi", [time(9), time(8)])
def test_una_franja_ha_d_acabar_despres_de_comencar(repartidor, fi):
    nova = franja(repartidor, DILLUNS, time(9), fi)

    with pytest.raises(ValidationError) as error:
        nova.full_clean()
    assert error.value.message_dict["hora_fi"] == ["La franja ha d'acabar després de començar."]

    with pytest.raises(IntegrityError), transaction.atomic():
        nova.save()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "inici, fi",
    [(time(12), time(14)), (time(8), time(10)), (time(10), time(11)), (time(8), time(14))],
)
def test_dues_franges_del_mateix_dia_no_es_poden_trepitjar(repartidor, inici, fi):
    franja(repartidor, DILLUNS, time(9), time(13)).save()

    with pytest.raises(ValidationError) as error:
        franja(repartidor, DILLUNS, inici, fi).full_clean()
    assert "es trepitja" in str(error.value)


@pytest.mark.django_db
def test_franges_seguides_o_d_altres_dies_o_repartidors_no_es_trepitgen(repartidor):
    franja(repartidor, DILLUNS, time(9), time(13)).save()
    altre = crea_repartidor("altre@example.com", "87654321X")

    franja(repartidor, DILLUNS, time(13), time(15)).full_clean()
    franja(repartidor, DIMARTS, time(9), time(13)).full_clean()
    franja(altre, DILLUNS, time(9), time(13)).full_clean()


@pytest.mark.django_db
def test_modificar_una_franja_no_la_compara_amb_ella_mateixa(repartidor):
    existent = franja(repartidor, DILLUNS, time(9), time(13))
    existent.save()

    existent.hora_fi = time(14)
    existent.full_clean()


@pytest.mark.django_db
def test_en_esborrar_el_repartidor_s_esborren_les_seves_franges(repartidor):
    franja(repartidor, DILLUNS, time(9), time(13)).save()

    repartidor.delete()

    assert not FranjaDisponibilitat.objects.exists()


# El 16 de novembre de 2026 és dilluns.
@pytest.mark.parametrize(
    "inici, fi, cobreix",
    [
        (datetime(2026, 11, 16, 10), datetime(2026, 11, 16, 11), True),
        (datetime(2026, 11, 16, 9), datetime(2026, 11, 16, 13), True),
        (datetime(2026, 11, 16, 8, 30), datetime(2026, 11, 16, 10), False),
        (datetime(2026, 11, 16, 12), datetime(2026, 11, 16, 13, 30), False),
        (datetime(2026, 11, 17, 10), datetime(2026, 11, 17, 11), False),
        (datetime(2026, 11, 16, 12), datetime(2026, 11, 17, 10), False),
    ],
)
def test_la_franja_nomes_cobreix_lliuraments_que_hi_caben_sencers(inici, fi, cobreix):
    dilluns_mati = FranjaDisponibilitat(dia=DILLUNS, hora_inici=time(9), hora_fi=time(13))

    assert dilluns_mati.cobreix(inici, fi) is cobreix
