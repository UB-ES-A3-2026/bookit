import pytest
from django.core import mail
from django.test import override_settings

from usuaris.models import Biblioteca, Usuari


URL = "/api/auth/register/biblioteca/"


def dades_valides(**canvis):
    dades = {
        "nom": "Biblioteca Central",
        "correu": "biblioteca@example.com",
    }
    dades.update(canvis)
    return dades


@pytest.mark.django_db
def test_registre_biblioteca_crea_un_compte_inactiu_i_retorna_201(client):
    resposta = client.post(URL, dades_valides(), content_type="application/json")

    assert resposta.status_code == 201
    assert resposta.json() == {
        "nom": "Biblioteca Central",
        "correu": "biblioteca@example.com",
    }
    usuari = Usuari.objects.get(email="biblioteca@example.com")
    assert usuari.role == Usuari.Role.BIBLIOTECA
    assert not usuari.is_active
    assert Biblioteca.objects.get(usuari=usuari).nom == "Biblioteca Central"


@pytest.mark.django_db
@pytest.mark.parametrize("camp", ["nom", "correu"])
def test_registre_biblioteca_sense_camp_retorna_400(client, camp):
    dades = dades_valides()
    del dades[camp]

    resposta = client.post(URL, dades, content_type="application/json")

    assert resposta.status_code == 400
    assert resposta.json()[camp]


@pytest.mark.django_db
def test_registre_biblioteca_amb_correu_duplicat_retorna_400(client):
    client.post(URL, dades_valides(), content_type="application/json")

    resposta = client.post(
        URL,
        dades_valides(correu="BIBLIOTECA@EXAMPLE.COM"),
        content_type="application/json",
    )

    assert resposta.status_code == 400
    assert resposta.json() == {
        "correu": [
            "Aquest correu correspon a un compte existent, torna a probar amb un altre correu"
        ]
    }


@pytest.mark.django_db
def test_registre_biblioteca_no_requereix_autenticacio(client):
    resposta = client.post(URL, dades_valides(), content_type="application/json")

    assert resposta.status_code not in (401, 403)


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_registre_biblioteca_envia_correu_de_verificacio(client):
    resposta = client.post(URL, dades_valides(), content_type="application/json")

    assert resposta.status_code == 201
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["biblioteca@example.com"]
    assert "verify/biblioteca/" in mail.outbox[0].body
    assert "Aquest enllaç caduca en 24 hores." in mail.outbox[0].body
