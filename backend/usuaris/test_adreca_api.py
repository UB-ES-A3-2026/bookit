import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from usuaris.models import Adreca, Usuari
from usuaris.validacions import ADRECA_FORA_ZONA_SERVEI

from decimal import Decimal
from datetime import timedelta

COLLECCIO = "/api/usuaris/adreces/"


def crear_usuari(email="anna@example.com", carnet="1234567890", **camps):
    dades = {
        "email": email,
        "password": "una-contrasenya-segura",
        "name": "Anna Puig",
        "address": "C/ Major 1, 08001 Barcelona",
        "library_card_number": carnet,
    }
    dades.update(camps)
    return Usuari.objects.create_user(**dades)


def client_de(usuari):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(usuari)}")
    return client


def dades_adreca(**canvis):
    dades = {
        "municipi": "Barcelona",
        "carrer": "C/ Major 1",
        "pis": "2n A",
        "codi_postal": "08001",
    }
    dades.update(canvis)
    return dades


@pytest.mark.django_db
@pytest.mark.parametrize("metode", ["get", "post"])
def test_sense_token_colleccio_rebutja_peticio(metode):
    client = APIClient()
    resposta = getattr(client, metode)(
        COLLECCIO,
        dades_adreca(),
        format="json",
    )
    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_sense_token_detall_rebutja_peticio():
    usuari = crear_usuari()
    adreca = Adreca.objects.create(usuari=usuari, **dades_adreca())

    client = APIClient()

    assert client.get(f"{COLLECCIO}{adreca.id}/").status_code == 401
    assert client.patch(
        f"{COLLECCIO}{adreca.id}/",
        {"carrer": "C/ Nova"},
        format="json",
    ).status_code == 401
    assert client.delete(f"{COLLECCIO}{adreca.id}/").status_code == 401


@pytest.mark.django_db
def test_llista_només_retorna_adreces_propies():
    usuari = crear_usuari()
    altre = crear_usuari(
        email="pere@example.com",
        carnet="0987654321",
        name="Pere Vila",
    )
    propria = Adreca.objects.create(usuari=usuari, **dades_adreca())
    Adreca.objects.create(
        usuari=altre,
        **dades_adreca(carrer="C/ Alien 1", codi_postal="17001"),
    )

    resposta = client_de(usuari).get(COLLECCIO)

    assert resposta.status_code == status.HTTP_200_OK
    assert [adreca["id"] for adreca in resposta.data] == [propria.id]


@pytest.mark.django_db
def test_crear_adreca_ignora_usuari_i_l_assigna_al_token():
    usuari = crear_usuari()
    altre = crear_usuari(
        email="pere@example.com",
        carnet="0987654321",
        name="Pere Vila",
    )

    resposta = client_de(usuari).post(
        COLLECCIO,
        dades_adreca() | {"usuari": altre.id},
        format="json",
    )

    assert resposta.status_code == status.HTTP_201_CREATED
    adreca = Adreca.objects.get(pk=resposta.data["id"])
    assert adreca.usuari == usuari


@pytest.mark.django_db
def test_crear_adreca_fora_zona_retorna_error_exacte():
    usuari = crear_usuari()

    resposta = client_de(usuari).post(
        COLLECCIO,
        dades_adreca(codi_postal="28001"),
        format="json",
    )

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data["codi_postal"] == [ADRECA_FORA_ZONA_SERVEI]


@pytest.mark.django_db
def test_editar_adreca_fora_zona_retorna_error_exacte():
    usuari = crear_usuari()
    adreca = Adreca.objects.create(usuari=usuari, **dades_adreca())

    resposta = client_de(usuari).patch(
        f"{COLLECCIO}{adreca.id}/",
        {"codi_postal": "28001"},
        format="json",
    )

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data["codi_postal"] == [ADRECA_FORA_ZONA_SERVEI]


@pytest.mark.django_db
def test_patch_valida_valor_final_sense_reenviar_codi_postal():
    usuari = crear_usuari()
    adreca = Adreca.objects.create(usuari=usuari, **dades_adreca())

    resposta = client_de(usuari).patch(
        f"{COLLECCIO}{adreca.id}/",
        {"carrer": "C/ Nova"},
        format="json",
    )

    assert resposta.status_code == status.HTTP_200_OK
    adreca.refresh_from_db()
    assert adreca.carrer == "C/ Nova"


@pytest.mark.django_db
def test_editar_i_suprimir_adreca_propia():
    usuari = crear_usuari()
    adreca = Adreca.objects.create(usuari=usuari, **dades_adreca())
    client = client_de(usuari)

    resposta_edicio = client.patch(
        f"{COLLECCIO}{adreca.id}/",
        {"pis": "3r B"},
        format="json",
    )
    assert resposta_edicio.status_code == status.HTTP_200_OK

    resposta_esborra = client.delete(f"{COLLECCIO}{adreca.id}/")
    assert resposta_esborra.status_code == status.HTTP_204_NO_CONTENT
    assert not Adreca.objects.filter(pk=adreca.id).exists()


@pytest.mark.django_db
def test_no_pot_editar_ni_suprimir_adreca_aliena():
    usuari = crear_usuari()
    altre = crear_usuari(
        email="pere@example.com",
        carnet="0987654321",
        name="Pere Vila",
    )
    aliena = Adreca.objects.create(usuari=altre, **dades_adreca())

    client = client_de(usuari)

    assert client.patch(
        f"{COLLECCIO}{aliena.id}/",
        {"carrer": "C/ Inaccessible"},
        format="json",
    ).status_code == status.HTTP_404_NOT_FOUND
    assert client.delete(
        f"{COLLECCIO}{aliena.id}/"
    ).status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_predeterminada_no_es_pot_enviar():
    usuari = crear_usuari()
    adreca = Adreca.objects.create(usuari=usuari, **dades_adreca())

    resposta = client_de(usuari).patch(
        f"{COLLECCIO}{adreca.id}/",
        {"predeterminada": True},
        format="json",
    )

    assert resposta.status_code == status.HTTP_200_OK
    adreca.refresh_from_db()
    assert adreca.predeterminada is False


@pytest.mark.django_db
def test_sense_token_marcar_predeterminada_retorna_401():
    usuari = crear_usuari()
    adreca = Adreca.objects.create(usuari=usuari, **dades_adreca())

    resposta = APIClient().post(
        f"{COLLECCIO}{adreca.id}/predeterminada/",
        format="json",
    )

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_marcar_adreca_predeterminada():
    usuari = crear_usuari()
    adreca = Adreca.objects.create(usuari=usuari, **dades_adreca())

    resposta = client_de(usuari).post(
        f"{COLLECCIO}{adreca.id}/predeterminada/",
        format="json",
    )

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["predeterminada"] is True
    adreca.refresh_from_db()
    assert adreca.predeterminada is True


@pytest.mark.django_db
def test_marcar_segona_adreca_desmarca_la_primera():
    usuari = crear_usuari()
    primera = Adreca.objects.create(
        usuari=usuari,
        **dades_adreca(predeterminada=True),
    )
    segona = Adreca.objects.create(usuari=usuari, **dades_adreca())

    resposta = client_de(usuari).post(
        f"{COLLECCIO}{segona.id}/predeterminada/",
        format="json",
    )

    assert resposta.status_code == status.HTTP_200_OK
    primera.refresh_from_db()
    segona.refresh_from_db()
    assert primera.predeterminada is False
    assert segona.predeterminada is True
    assert Adreca.objects.filter(
        usuari=usuari,
        predeterminada=True,
    ).count() == 1


@pytest.mark.django_db
def test_marcar_predeterminada_no_afecta_altre_usuari():
    usuari = crear_usuari()
    altra = crear_usuari(
        email="pere@example.com",
        carnet="0987654321",
        name="Pere Vila",
    )
    adreca_usuari = Adreca.objects.create(usuari=usuari, **dades_adreca())
    adreca_altra = Adreca.objects.create(
        usuari=altra,
        **dades_adreca(predeterminada=True),
    )

    resposta = client_de(usuari).post(
        f"{COLLECCIO}{adreca_usuari.id}/predeterminada/",
        format="json",
    )

    assert resposta.status_code == status.HTTP_200_OK
    adreca_altra.refresh_from_db()
    assert adreca_altra.predeterminada is True


@pytest.mark.django_db
def test_adreca_aliena_no_es_pot_marcar_predeterminada():
    usuari = crear_usuari()
    altra = crear_usuari(
        email="pere@example.com",
        carnet="0987654321",
        name="Pere Vila",
    )
    aliena = Adreca.objects.create(usuari=altra, **dades_adreca())

    resposta = client_de(usuari).post(
        f"{COLLECCIO}{aliena.id}/predeterminada/",
        format="json",
    )

    assert resposta.status_code == status.HTTP_404_NOT_FOUND
    aliena.refresh_from_db()
    assert aliena.predeterminada is False


@pytest.mark.django_db
def test_marcar_un_id_inexistent_retorna_404():
    usuari = crear_usuari()

    resposta = client_de(usuari).post(
        f"{COLLECCIO}999999/predeterminada/",
        format="json",
    )

    assert resposta.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_marcar_ja_predeterminada_es_idempotent():
    usuari = crear_usuari()
    adreca = Adreca.objects.create(
        usuari=usuari,
        **dades_adreca(predeterminada=True),
    )

    resposta = client_de(usuari).post(
        f"{COLLECCIO}{adreca.id}/predeterminada/",
        format="json",
    )

    assert resposta.status_code == status.HTTP_200_OK
    adreca.refresh_from_db()
    assert adreca.predeterminada is True
    assert Adreca.objects.filter(
        usuari=usuari,
        predeterminada=True,
    ).count() == 1


@pytest.mark.django_db
def test_llista_retorna_tots_els_camps():
    usuari = crear_usuari()
    Adreca.objects.create(usuari=usuari, **dades_adreca())

    resposta = client_de(usuari).get(COLLECCIO)

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data[0].keys() == {
        "id",
        "municipi",
        "carrer",
        "pis",
        "codi_postal",
        "latitud",
        "longitud",
        "predeterminada",
    }


@pytest.mark.django_db
def test_llista_buida_retorna_llista_vacia():
    usuari = crear_usuari()

    resposta = client_de(usuari).get(COLLECCIO)

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data == []


@pytest.mark.django_db
@pytest.mark.parametrize(
    "camp",
    ["municipi", "carrer", "pis", "codi_postal"],
)
@pytest.mark.parametrize("valor", ["", None])
def test_afegir_camp_obligatori_buit_retorna_400(camp, valor):
    usuari = crear_usuari()
    dades = dades_adreca()
    dades[camp] = valor

    resposta = client_de(usuari).post(COLLECCIO, dades, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert camp in resposta.data


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("camp", "valor"),
    [
        ("municipi", "X" * 101),
        ("carrer", "X" * 256),
        ("pis", "X" * 21),
        ("codi_postal", "123456"),
    ],
)
def test_afegir_camp_massa_llarg_retorna_400(camp, valor):
    usuari = crear_usuari()

    resposta = client_de(usuari).post(
        COLLECCIO,
        dades_adreca(**{camp: valor}),
        format="json",
    )

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert camp in resposta.data


@pytest.mark.django_db
@pytest.mark.parametrize("camp", ["municipi", "carrer", "pis", "codi_postal"])
def test_afegir_camp_absent_retorna_400(camp):
    usuari = crear_usuari()
    dades = dades_adreca()
    del dades[camp]

    resposta = client_de(usuari).post(COLLECCIO, dades, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert camp in resposta.data


@pytest.mark.django_db
def test_afegir_adreca_dins_zona_retorna_201():
    usuari = crear_usuari()

    resposta = client_de(usuari).post(
        COLLECCIO,
        dades_adreca(codi_postal="08000"),
        format="json",
    )

    assert resposta.status_code == status.HTTP_201_CREATED
    assert Adreca.objects.filter(
        usuari=usuari,
        codi_postal="08000",
    ).exists()


@pytest.mark.django_db
def test_put_canvia_adreca_i_manté_predeterminada():
    usuari = crear_usuari()
    adreca = Adreca.objects.create(
        usuari=usuari,
        **dades_adreca(predeterminada=True),
    )

    resposta = client_de(usuari).put(
        f"{COLLECCIO}{adreca.id}/",
        {
            "municipi": "Girona",
            "carrer": "C/ Nou 5",
            "pis": "4t",
            "codi_postal": "17001",
        },
        format="json",
    )

    assert resposta.status_code == status.HTTP_200_OK
    adreca.refresh_from_db()
    assert adreca.municipi == "Girona"
    assert adreca.carrer == "C/ Nou 5"
    assert adreca.pis == "4t"
    assert adreca.codi_postal == "17001"
    assert adreca.predeterminada is True


@pytest.mark.django_db
def test_patch_no_esborra_els_altres_camps():
    usuari = crear_usuari()
    adreca = Adreca.objects.create(usuari=usuari, **dades_adreca())

    resposta = client_de(usuari).patch(
        f"{COLLECCIO}{adreca.id}/",
        {"municipi": "Sabadell"},
        format="json",
    )

    assert resposta.status_code == status.HTTP_200_OK
    adreca.refresh_from_db()
    assert adreca.municipi == "Sabadell"
    assert adreca.carrer == "C/ Major 1"
    assert adreca.pis == "2n A"
    assert adreca.codi_postal == "08001"


@pytest.mark.django_db
def test_get_adreca_inexistent_retorna_404():
    usuari = crear_usuari()

    resposta = client_de(usuari).get(f"{COLLECCIO}999999/")

    assert resposta.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_put_adreca_inexistent_retorna_404():
    usuari = crear_usuari()

    resposta = client_de(usuari).put(
        f"{COLLECCIO}999999/",
        dades_adreca(),
        format="json",
    )

    assert resposta.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_patch_adreca_inexistent_retorna_404():
    usuari = crear_usuari()

    resposta = client_de(usuari).patch(
        f"{COLLECCIO}999999/",
        {"carrer": "C/ Nova"},
        format="json",
    )

    assert resposta.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_delete_adreca_inexistent_retorna_404():
    usuari = crear_usuari()

    resposta = client_de(usuari).delete(f"{COLLECCIO}999999/")

    assert resposta.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_get_adreca_aliena_retorna_404():
    usuari = crear_usuari()
    altra = crear_usuari(
        email="pere@example.com",
        carnet="0987654321",
        name="Pere Vila",
    )
    aliena = Adreca.objects.create(usuari=altra, **dades_adreca())

    resposta = client_de(usuari).get(f"{COLLECCIO}{aliena.id}/")

    assert resposta.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_token_invalid_retorna_401_a_la_llista():
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer no-es-un-token")

    resposta = client.get(COLLECCIO)

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED
    assert resposta.data["code"] == "token_not_valid"


@pytest.mark.django_db
def test_token_caducat_retorna_401_a_la_llista():
    usuari = crear_usuari()
    token = AccessToken.for_user(usuari)
    token.set_exp(lifetime=-timedelta(seconds=1))
    client = client_de(usuari)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    resposta = client.get(COLLECCIO)

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_post_predeterminada_es_ignora():
    usuari = crear_usuari()

    resposta = client_de(usuari).post(
        COLLECCIO,
        dades_adreca() | {"predeterminada": True},
        format="json",
    )

    assert resposta.status_code == status.HTTP_201_CREATED
    adreca = Adreca.objects.get(pk=resposta.data["id"])
    assert adreca.predeterminada is False


@pytest.mark.django_db
def test_put_predeterminada_es_ignora():
    usuari = crear_usuari()
    adreca = Adreca.objects.create(usuari=usuari, **dades_adreca())

    resposta = client_de(usuari).put(
        f"{COLLECCIO}{adreca.id}/",
        dades_adreca() | {"predeterminada": True},
        format="json",
    )

    assert resposta.status_code == status.HTTP_200_OK
    adreca.refresh_from_db()
    assert adreca.predeterminada is False


@pytest.mark.django_db
def test_adreces_iguals_de_usuaris_diferents_no_es_barregen():
    usuari = crear_usuari()
    altre = crear_usuari(
        email="pere@example.com",
        carnet="0987654321",
        name="Pere Vila",
    )
    Adreca.objects.create(usuari=usuari, **dades_adreca())
    Adreca.objects.create(usuari=altre, **dades_adreca())

    resposta = client_de(usuari).get(COLLECCIO)

    assert resposta.status_code == status.HTTP_200_OK
    assert len(resposta.data) == 1
    assert resposta.data[0]["municipi"] == "Barcelona"
    assert Adreca.objects.filter(
        usuari=altre,
    ).count() == 1


@pytest.mark.django_db
def test_crear_adreca_desa_coordenades(monkeypatch):
    usuari = crear_usuari()
    coordenades = (
        Decimal("41.979400"),
        Decimal("2.821400"),
    )
    monkeypatch.setattr(
        "usuaris.serializers.geocodifica_adreca",
        lambda adreca: coordenades,
    )

    resposta = client_de(usuari).post(
        COLLECCIO,
        dades_adreca(),
        format="json",
    )

    assert resposta.status_code == status.HTTP_201_CREATED

    adreca = Adreca.objects.get(pk=resposta.data["id"])
    assert adreca.latitud == coordenades[0]
    assert adreca.longitud == coordenades[1]


@pytest.mark.django_db
def test_fallo_geocodificacio_desa_sense_coordenades(monkeypatch):
    usuari = crear_usuari()
    monkeypatch.setattr(
        "usuaris.serializers.geocodifica_adreca",
        lambda adreca: None,
    )

    resposta = client_de(usuari).post(
        COLLECCIO,
        dades_adreca(),
        format="json",
    )

    assert resposta.status_code == status.HTTP_201_CREATED

    adreca = Adreca.objects.get(pk=resposta.data["id"])
    assert adreca.latitud is None
    assert adreca.longitud is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("camp", "valor"),
    [
        ("carrer", "C/ Nova 8"),
        ("codi_postal", "17001"),
    ],
)
def test_editar_ubicacio_recalcula(monkeypatch, camp, valor):
    usuari = crear_usuari()
    adreca = Adreca.objects.create(
        usuari=usuari,
        latitud=Decimal("41.979400"),
        longitud=Decimal("2.821400"),
        **dades_adreca(),
    )
    coordenades_noves = (
        Decimal("41.388800"),
        Decimal("2.159000"),
    )
    monkeypatch.setattr(
        "usuaris.serializers.geocodifica_adreca",
        lambda adreca: coordenades_noves,
    )

    resposta = client_de(usuari).patch(
        f"{COLLECCIO}{adreca.id}/",
        {camp: valor},
        format="json",
    )

    assert resposta.status_code == status.HTTP_200_OK

    adreca.refresh_from_db()
    assert adreca.latitud == coordenades_noves[0]
    assert adreca.longitud == coordenades_noves[1]


@pytest.mark.django_db
def test_editar_sense_ubicacio_no_recalcula(monkeypatch):
    usuari = crear_usuari()
    adreca = Adreca.objects.create(
        usuari=usuari,
        latitud=Decimal("41.979400"),
        longitud=Decimal("2.821400"),
        **dades_adreca(),
    )
    monkeypatch.setattr(
        "usuaris.serializers.geocodifica_adreca",
        lambda adreca: pytest.fail("No s'hauria de recalcular"),
    )

    resposta = client_de(usuari).patch(
        f"{COLLECCIO}{adreca.id}/",
        {"pis": "3r B"},
        format="json",
    )

    assert resposta.status_code == status.HTTP_200_OK
    adreca.refresh_from_db()
    assert adreca.latitud == Decimal("41.979400")
    assert adreca.longitud == Decimal("2.821400")


@pytest.mark.django_db
def test_fallo_recalcular_buia_coordenades(monkeypatch):
    usuari = crear_usuari()
    adreca = Adreca.objects.create(
        usuari=usuari,
        latitud=Decimal("41.979400"),
        longitud=Decimal("2.821400"),
        **dades_adreca(),
    )
    monkeypatch.setattr(
        "usuaris.serializers.geocodifica_adreca",
        lambda adreca: None,
    )

    resposta = client_de(usuari).patch(
        f"{COLLECCIO}{adreca.id}/",
        {"carrer": "Carrer inexistent"},
        format="json",
    )

    assert resposta.status_code == status.HTTP_200_OK

    adreca.refresh_from_db()
    assert adreca.latitud is None
    assert adreca.longitud is None


@pytest.mark.django_db
def test_marcar_predeterminada_no_recalcula(monkeypatch):
    usuari = crear_usuari()
    adreca = Adreca.objects.create(
        usuari=usuari,
        latitud=Decimal("41.979400"),
        longitud=Decimal("2.821400"),
        **dades_adreca(),
    )
    monkeypatch.setattr(
        "usuaris.serializers.geocodifica_adreca",
        lambda adreca: pytest.fail("No s'hauria de recalcular"),
    )

    resposta = client_de(usuari).post(
        f"{COLLECCIO}{adreca.id}/predeterminada/",
        format="json",
    )

    assert resposta.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_client_no_pot_escriure_coordenades():
    usuari = crear_usuari()
    monkeypatch = None

    resposta = client_de(usuari).post(
        COLLECCIO,
        dades_adreca()
        | {
            "latitud": "41.979400",
            "longitud": "2.821400",
        },
        format="json",
    )

    assert resposta.status_code == status.HTTP_201_CREATED

    adreca = Adreca.objects.get(pk=resposta.data["id"])
    assert adreca.latitud is None
    assert adreca.longitud is None
