"""Tests dels permisos de l'API de gestió del catàleg (US17-T1)."""

import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from cataleg.permisos import SENSE_PERMISOS, EsBibliotecaActiva
from usuaris.models import Biblioteca, Usuari

URL = "/api/cataleg/biblioteca/llibres/"

pytestmark = pytest.mark.django_db


class VistaCataleg(APIView):
    """Vista de prova amb el permís dels endpoints del catàleg."""

    permission_classes = [EsBibliotecaActiva]

    def get(self, request):
        return Response({"biblioteca": request.user.biblioteca.nom})


def crear_usuari(email, role=Usuari.Role.USUARI, **camps):
    return Usuari.objects.create_user(
        email=email,
        password="una-contrasenya-segura",
        name="Anna Puig",
        address="C/ Major 1, 08001 Barcelona",
        library_card_number=f"carnet-{email}",
        role=role,
        **camps,
    )


def crear_biblioteca(email="biblioteca@example.com", activa=True):
    """Crea una biblioteca. En crear-la queda inactiva, com abans de verificar el correu."""
    usuari = crear_usuari(email, role=Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=usuari, nom="Biblioteca Central")
    if activa:
        usuari.is_active = True
        usuari.save(update_fields=["is_active"])
    return usuari


def peticio_amb_token(usuari):
    return APIRequestFactory().get(
        URL, HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(usuari)}"
    )


def crida(peticio):
    return VistaCataleg.as_view()(peticio)


def test_una_biblioteca_activa_hi_te_acces():
    resposta = crida(peticio_amb_token(crear_biblioteca()))

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data == {"biblioteca": "Biblioteca Central"}


def test_sense_token_respon_401():
    resposta = crida(APIRequestFactory().get(URL))

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


def test_amb_un_token_invalid_respon_401():
    peticio = APIRequestFactory().get(URL, HTTP_AUTHORIZATION="Bearer no-es-un-token")

    resposta = crida(peticio)

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("rol", [Usuari.Role.USUARI, Usuari.Role.REPARTIDOR])
def test_els_altres_rols_reben_403_amb_el_missatge_del_contracte(rol):
    usuari = crear_usuari(f"{rol}@example.com", role=rol)

    resposta = crida(peticio_amb_token(usuari))

    assert resposta.status_code == status.HTTP_403_FORBIDDEN
    assert resposta.data == {"detail": SENSE_PERMISOS}


def test_el_missatge_de_403_es_el_literal_del_contracte():
    assert SENSE_PERMISOS == "No té permisos per realitzar aquesta acció."


def test_una_biblioteca_sense_verificar_amb_token_respon_401():
    """La JWT ja rebutja els comptes inactius abans de comprovar els permisos."""
    biblioteca = crear_biblioteca(activa=False)

    resposta = crida(peticio_amb_token(biblioteca))

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


def test_una_biblioteca_inactiva_autenticada_rep_403():
    peticio = APIRequestFactory().get(URL)
    force_authenticate(peticio, user=crear_biblioteca(activa=False))

    resposta = crida(peticio)

    assert resposta.status_code == status.HTTP_403_FORBIDDEN
    assert resposta.data == {"detail": SENSE_PERMISOS}


def test_un_compte_amb_rol_biblioteca_sense_perfil_rep_403():
    usuari = crear_usuari("sense-perfil@example.com", role=Usuari.Role.BIBLIOTECA)

    resposta = crida(peticio_amb_token(usuari))

    assert resposta.status_code == status.HTTP_403_FORBIDDEN
    assert resposta.data == {"detail": SENSE_PERMISOS}


def test_el_permis_rebutja_un_usuari_anonim():
    peticio = APIRequestFactory().get(URL)
    peticio.user = AnonymousUser()

    assert EsBibliotecaActiva().has_permission(peticio, None) is False
