"""Vistes de l'API del mòdul prestecs."""

from rest_framework import generics, status
from rest_framework.response import Response

from prestecs.models import Comanda
from prestecs.permisos import EsUsuariActiu
from prestecs.serializers import SENSE_ESTOC, ComandaSerializer, ConfirmacioComandaSerializer
from prestecs.serveis import (
    LlibresSenseEstoc,
    TransicioNoPermesa,
    cancella_comanda,
    confirma_comanda,
)

# Literal dels criteris d'acceptació de la US20.
JA_HA_SORTIT = "Aquesta comanda ja ha sortit i no es pot cancel·lar"
JA_CANCELLADA = "Aquesta comanda ja està cancel·lada."


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


class CancellarComandaView(generics.GenericAPIView):
    """L'usuari cancel·la una comanda seva que encara no ha sortit (US20-T1).

    La comanda passa a "cancel·lada" i els exemplars tornen a la biblioteca.
    Contracte a `docs/api-comandes.md`.
    """

    permission_classes = [EsUsuariActiu]

    def get_queryset(self):
        # Una comanda d'un altre usuari rep el mateix 404 que una que no existeix.
        return Comanda.objects.filter(usuari=self.request.user)

    def post(self, request, pk):
        comanda = self.get_object()
        try:
            cancella_comanda(comanda)
        except TransicioNoPermesa as error:
            missatge = JA_CANCELLADA if error.estat_actual == Comanda.Estat.CANCELLADA else JA_HA_SORTIT
            return Response({"detail": missatge}, status=status.HTTP_409_CONFLICT)
        return Response(ComandaSerializer(comanda).data)
