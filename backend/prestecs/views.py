"""Vistes de l'API del mòdul prestecs."""

from rest_framework import generics, status
from rest_framework.response import Response

from prestecs.models import Comanda
from prestecs.permisos import EsUsuariActiu
from prestecs.serializers import (
    SENSE_ESTOC,
    ComandaSerializer,
    ConfirmacioComandaSerializer,
    NotificacioSerializer,
)
from prestecs.serveis import LlibresSenseEstoc, confirma_comanda, cost_enviament


class ComandesView(generics.GenericAPIView):
    """Comandes de l'usuari autenticat. Contracte a `docs/api-comandes.md`.

    GET les llista amb el seu estat (US8-T3) i POST en confirma una de nova (US6-T2).
    """

    serializer_class = ConfirmacioComandaSerializer
    permission_classes = [EsUsuariActiu]

    def get(self, request):
        comandes = (
            Comanda.objects.filter(usuari=request.user)
            .select_related("biblioteca__biblioteca")
            .prefetch_related("linies__llibre")
        )
        return Response(ComandaSerializer(comandes, many=True).data)

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


class NotificacionsView(generics.ListAPIView):
    """Notificacions de l'usuari autenticat, de la més nova a la més antiga (US8-T3)."""

    serializer_class = NotificacioSerializer
    permission_classes = [EsUsuariActiu]
    pagination_class = None

    def get_queryset(self):
        return self.request.user.notificacions.all()


class NotificacioLlegidaView(generics.GenericAPIView):
    """Marca una notificació de l'usuari com a llegida (US8-T3)."""

    serializer_class = NotificacioSerializer
    permission_classes = [EsUsuariActiu]

    def get_queryset(self):
        # Una notificació d'un altre usuari rep el mateix 404 que una que no existeix.
        return self.request.user.notificacions.all()

    def post(self, request, pk):
        notificacio = self.get_object()
        if not notificacio.llegida:
            notificacio.llegida = True
            notificacio.save(update_fields=["llegida"])
        return Response(self.get_serializer(notificacio).data)


class NotificacionsLlegidesView(generics.GenericAPIView):
    """Marca com a llegides totes les notificacions de l'usuari (US8-T3)."""

    permission_classes = [EsUsuariActiu]

    def post(self, request):
        marcades = request.user.notificacions.filter(llegida=False).update(llegida=True)
        return Response({"marcades": marcades})
