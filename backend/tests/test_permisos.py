"""Tests de la configuració per defecte dels permisos de l'API."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.views import APIView


class VistaProtegida(APIView):
    def get(self, request):
        return Response({"status": "ok"})


def test_is_authenticated_es_el_permis_per_defecte():
    assert api_settings.DEFAULT_PERMISSION_CLASSES == [IsAuthenticated]


def test_una_vista_sense_permis_explicits_denega_una_peticio_anima():
    peticio = APIRequestFactory().get("/api/protegida/")

    resposta = VistaProtegida.as_view()(peticio)

    assert resposta.status_code == status.HTTP_403_FORBIDDEN


def test_registre_es_public():
    resposta = APIClient().post("/api/auth/register/", {}, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
