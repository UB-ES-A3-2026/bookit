"""Tests de la validació de repartidors des de l'admin (US1.1-T5)."""

import pytest
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from django.urls import reverse

from usuaris.models import PerfilRepartidor, Usuari
from usuaris.test_registre_repartidor import URL as URL_REGISTRE
from usuaris.test_registre_repartidor import dades_valides

pytestmark = pytest.mark.django_db

URL_LLISTA = reverse("admin:usuaris_perfilrepartidor_changelist")
URL_TOTS = f"{URL_LLISTA}?estat=tots"

Estat = PerfilRepartidor.Estat


def crea_perfil(cognoms="Puig", dni="12345678Z", estat=Estat.PENDENT):
    usuari = Usuari.objects.create_user(
        email=f"{dni}@example.com",
        password="contrasenya-segura",
        name="Anna",
        address="C/ Major 1, 08001 Barcelona",
        library_card_number=dni,
        role=Usuari.Role.REPARTIDOR,
    )
    return PerfilRepartidor.objects.create(
        usuari=usuari,
        cognoms=cognoms,
        dni=dni,
        telefon="612345678",
        vehicle=PerfilRepartidor.Vehicle.BICI,
        num_seguretat_social="281234567890",
        estat=estat,
    )


def crea_staff(*permisos, **camps):
    staff = Usuari.objects.create_user(
        email="staff@example.com",
        password="contrasenya-segura",
        name="Staff",
        address="C/ Major 2, 08001 Barcelona",
        library_card_number="staff",
        is_staff=True,
        **camps,
    )
    staff.user_permissions.set(Permission.objects.filter(codename__in=permisos))
    return staff


@pytest.fixture
def client_admin(client):
    client.force_login(crea_staff(is_superuser=True))
    return client


def executa_accio(client, accio, *perfils, url=URL_LLISTA):
    return client.post(
        url,
        {"action": accio, "_selected_action": [perfil.pk for perfil in perfils]},
    )


def estat_de(perfil):
    perfil.refresh_from_db()
    return perfil.estat


def missatges(resposta):
    return [str(missatge) for missatge in get_messages(resposta.wsgi_request)]


def resultats(resposta):
    return set(resposta.context["cl"].queryset)


def test_la_llista_mostra_nomes_els_pendents_per_defecte(client_admin):
    pendent = crea_perfil()
    crea_perfil("Soler", "X1234567L", Estat.VALIDAT)
    crea_perfil("Vila", "Y1234567X", Estat.REBUTJAT)

    assert resultats(client_admin.get(URL_LLISTA)) == {pendent}


def test_el_filtre_mostra_cada_estat_i_tots(client_admin):
    pendent = crea_perfil()
    validat = crea_perfil("Soler", "X1234567L", Estat.VALIDAT)
    rebutjat = crea_perfil("Vila", "Y1234567X", Estat.REBUTJAT)

    assert resultats(client_admin.get(URL_LLISTA, {"estat": "validat"})) == {validat}
    assert resultats(client_admin.get(URL_LLISTA, {"estat": "rebutjat"})) == {rebutjat}
    assert resultats(client_admin.get(URL_LLISTA, {"estat": "tots"})) == {
        pendent,
        validat,
        rebutjat,
    }


def test_el_filtre_no_ofereix_l_opcio_tot_de_django(client_admin):
    crea_perfil()

    llista = client_admin.get(URL_LLISTA).context["cl"]

    etiquetes = [opcio["display"] for opcio in llista.filter_specs[0].choices(llista)]
    assert etiquetes == ["Pendent de validació", "Validat", "Rebutjat", "Tots"]


def test_validar_canvia_l_estat_dels_seleccionats(client_admin):
    primer = crea_perfil()
    segon = crea_perfil("Soler", "X1234567L")
    no_seleccionat = crea_perfil("Vila", "Y1234567X")

    resposta = executa_accio(client_admin, "validar", primer, segon)

    assert estat_de(primer) == Estat.VALIDAT
    assert estat_de(segon) == Estat.VALIDAT
    assert estat_de(no_seleccionat) == Estat.PENDENT
    assert missatges(resposta) == ["Repartidors canviats a «Validat»: 2."]


def test_rebutjar_canvia_l_estat_dels_seleccionats(client_admin):
    perfil = crea_perfil()

    resposta = executa_accio(client_admin, "rebutjar", perfil)

    assert estat_de(perfil) == Estat.REBUTJAT
    assert missatges(resposta) == ["Repartidors canviats a «Rebutjat»: 1."]


@pytest.mark.parametrize(
    "accio, estat_inicial, etiqueta",
    [
        ("validar", Estat.REBUTJAT, "Validat"),
        ("rebutjar", Estat.VALIDAT, "Rebutjat"),
    ],
)
def test_les_accions_no_canvien_un_repartidor_ja_resolt(
    client_admin, accio, estat_inicial, etiqueta
):
    resolt = crea_perfil(estat=estat_inicial)

    resposta = executa_accio(client_admin, accio, resolt, url=URL_TOTS)

    assert estat_de(resolt) == estat_inicial
    assert missatges(resposta) == [
        f"Repartidors canviats a «{etiqueta}»: 0.",
        "Repartidors omesos perquè no estaven pendents: 1.",
    ]


def test_seleccio_mixta_nomes_canvia_els_pendents(client_admin):
    pendent = crea_perfil()
    rebutjat = crea_perfil("Vila", "Y1234567X", Estat.REBUTJAT)

    resposta = executa_accio(client_admin, "validar", pendent, rebutjat, url=URL_TOTS)

    assert estat_de(pendent) == Estat.VALIDAT
    assert estat_de(rebutjat) == Estat.REBUTJAT
    assert missatges(resposta) == [
        "Repartidors canviats a «Validat»: 1.",
        "Repartidors omesos perquè no estaven pendents: 1.",
    ]


def test_un_repartidor_resolt_des_d_una_llista_desfasada_no_canvia(client_admin):
    resolt = crea_perfil(estat=Estat.REBUTJAT)

    executa_accio(client_admin, "validar", resolt)

    assert estat_de(resolt) == Estat.REBUTJAT


def test_staff_amb_permis_de_canvi_pot_validar(client):
    client.force_login(crea_staff("view_perfilrepartidor", "change_perfilrepartidor"))
    perfil = crea_perfil()

    executa_accio(client, "validar", perfil)

    assert estat_de(perfil) == Estat.VALIDAT


def test_staff_nomes_de_lectura_no_pot_validar(client):
    client.force_login(crea_staff("view_perfilrepartidor"))
    perfil = crea_perfil()

    executa_accio(client, "validar", perfil)

    assert estat_de(perfil) == Estat.PENDENT


def test_usuari_sense_staff_no_entra_a_la_llista(client):
    client.force_login(crea_perfil().usuari)

    resposta = client.get(URL_LLISTA)

    assert resposta.status_code == 302
    assert reverse("admin:login") in resposta.url


def test_usuari_sense_staff_no_pot_validar(client):
    perfil = crea_perfil()
    client.force_login(perfil.usuari)

    executa_accio(client, "validar", perfil)

    assert estat_de(perfil) == Estat.PENDENT


def test_un_repartidor_registrat_per_l_api_surt_a_la_llista_de_pendents(client_admin):
    client_admin.post(URL_REGISTRE, dades_valides(), content_type="application/json")

    assert resultats(client_admin.get(URL_LLISTA)) == {PerfilRepartidor.objects.get()}


@pytest.mark.parametrize(
    "accio, estat",
    [("validar", Estat.VALIDAT), ("rebutjar", Estat.REBUTJAT)],
)
def test_es_pot_resoldre_un_repartidor_registrat_per_l_api(client_admin, accio, estat):
    client_admin.post(URL_REGISTRE, dades_valides(), content_type="application/json")
    perfil = PerfilRepartidor.objects.get()

    executa_accio(client_admin, accio, perfil)

    assert estat_de(perfil) == estat
    assert not resultats(client_admin.get(URL_LLISTA))
