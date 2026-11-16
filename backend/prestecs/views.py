"""Vistes de l'API del mòdul prestecs."""

from rest_framework import generics, status
from rest_framework.response import Response

from prestecs.permisos import EsUsuariActiu
from prestecs.serializers import SENSE_ESTOC, ComandaSerializer, ConfirmacioComandaSerializer
from prestecs.serveis import LlibresSenseEstoc, confirma_comanda


class ComandesView(generics.GenericAPIView):
    """Confirma una comanda amb un o més llibres (US6-T2). Contracte a `docs/api-comandes.md`."""

    serializer_class = ConfirmacioComandaSerializer
    permission_classes = [EsUsuariActiu]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            comanda = confirma_comanda(
                request.user,
                serializer.validated_data["biblioteca"],
                serializer.validated_data["llibres"],
            )
        except LlibresSenseEstoc as error:
            # `sense_estoc` porta els id dels llibres perquè el frontend ofereixi
            # la llista d'espera (US5).
            return Response(
                {"llibres": [SENSE_ESTOC], "sense_estoc": error.ids_llibres},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(ComandaSerializer(comanda).data, status=status.HTTP_201_CREATED)
