"""Vistes de l'API del mòdul prestecs."""

from rest_framework import generics, status
from rest_framework.response import Response

from prestecs.models import Prestec
from prestecs.permisos import EsUsuariActiu
from prestecs.serializers import (
    SENSE_ESTOC,
    ComandaSerializer,
    ConfirmacioComandaSerializer,
    PrestecSerializer,
)
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


class PrestecsView(generics.ListAPIView):
    """Llibres que l'usuari autenticat té en préstec (US19-T2).

    Només surten els que encara no ha tornat, ordenats per data límit, del més
    proper al més llunyà. Contracte a `docs/api-prestecs.md`.
    """

    serializer_class = PrestecSerializer
    permission_classes = [EsUsuariActiu]
    pagination_class = None

    def get_queryset(self):
        return (
            Prestec.objects.filter(usuari=self.request.user, data_devolucio__isnull=True)
            .select_related("llibre", "biblioteca__biblioteca")
            .order_by("data_limit", "id")
        )
