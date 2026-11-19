"""Vistes de l'API del mòdul prestecs."""

from rest_framework import generics, status
from rest_framework.response import Response

from cataleg.permisos import EsBibliotecaActiva
from prestecs.models import Comanda
from prestecs.permisos import EsUsuariActiu
from prestecs.serializers import SENSE_ESTOC, ComandaSerializer, ConfirmacioComandaSerializer
from prestecs.serveis import LlibresSenseEstoc, TransicioNoPermesa, canvia_estat, confirma_comanda


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


class ComandaLlestaView(generics.GenericAPIView):
    """La biblioteca marca una comanda seva com a llesta per a recollida (US15-T1).

    "Llesta per a recollida" és l'estat `preparada` (US8). A partir d'aquí la
    comanda es pot assignar a un repartidor (US14).
    """

    permission_classes = [EsBibliotecaActiva]

    def get_queryset(self):
        # Una comanda d'una altra biblioteca rep el mateix 404 que una que no existeix.
        return Comanda.objects.filter(biblioteca=self.request.user)

    def post(self, request, pk):
        comanda = self.get_object()
        try:
            canvia_estat(comanda, Comanda.Estat.PREPARADA, des_de=[Comanda.Estat.REBUDA])
        except TransicioNoPermesa as error:
            return Response({"detail": missatge_no_llesta(error.estat_actual)}, status=status.HTTP_409_CONFLICT)
        return Response(ComandaSerializer(comanda).data)


def missatge_no_llesta(estat_actual):
    if estat_actual == Comanda.Estat.PREPARADA:
        return "Aquesta comanda ja està llesta per a recollida."
    estat = Comanda.Estat(estat_actual).label.lower()
    return f"Aquesta comanda no es pot marcar com a llesta perquè està {estat}."
