"""Vistes de l'API del mòdul prestecs."""

from rest_framework import generics, status
from rest_framework.response import Response

from prestecs.models import Comanda
from prestecs.permisos import EsUsuariActiu
from prestecs.serializers import SENSE_ESTOC, ComandaSerializer, ConfirmacioComandaSerializer
from prestecs.serveis import LlibresSenseEstoc, confirma_comanda, cost_enviament


class ComandesView(generics.GenericAPIView):
    """Confirma una comanda amb un o més llibres (US6-T2). Contracte a `docs/api-comandes.md`."""

    serializer_class = ConfirmacioComandaSerializer
    permission_classes = [EsUsuariActiu]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            dades = serializer.validated_data
            comanda = confirma_comanda(
                request.user,
                dades["biblioteca"],
                dades["llibres"],
                dades["tipus_lliurament"],
                dades["adreca_lliurament"],
            )
        except LlibresSenseEstoc as error:
            # `sense_estoc` porta els id dels llibres perquè el frontend ofereixi
            # la llista d'espera (US5).
            return Response(
                {"llibres": [SENSE_ESTOC], "sense_estoc": error.ids_llibres},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(ComandaSerializer(comanda).data, status=status.HTTP_201_CREATED)


class CostEnviamentView(generics.GenericAPIView):
    """Cost de cada tipus de lliurament, per mostrar-lo abans de confirmar (US7)."""

    permission_classes = [EsUsuariActiu]

    def get(self, request):
        return Response(
            {tipus: str(cost_enviament(tipus)) for tipus in Comanda.TipusLliurament.values}
        )
