"""Vistes de l'API del mòdul prestecs."""

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.utils import timezone
from django.shortcuts import get_object_or_404

from cataleg.permisos import EsBibliotecaActiva
from prestecs.assignacio import assigna_comanda
from prestecs.models import Comanda, Parada, Ruta
from prestecs.permisos import EsUsuariActiu
from prestecs.serializers import (
    SENSE_ESTOC,
    ComandaSerializer,
    ConfirmacioComandaSerializer,
    NotificacioSerializer,
    ParadaRutaSerializer,
)
from prestecs.rutes import (
    DadesRutaInconsistents,
    calcula_i_desaa_ordre_ruta,
)
from prestecs.serveis import (
    LlibresSenseEstoc,
    TransicioNoPermesa,
    canvia_estat,
    confirma_comanda,
)

from prestecs.serializers import (
    ParadaCompletadaSerializer,
)
from prestecs.serveis import (
    ParadaJaCompletada,
    ParadaEnEstatTerminal,
    ParadaAmbComandaInvalida,
    completa_parada,
)

from usuaris.permisos import EsRepartidorValidat


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
    """La biblioteca marca una comanda seva com a llesta per a recollida (US15-T1)."""

    permission_classes = [EsBibliotecaActiva]

    def get_queryset(self):
        return Comanda.objects.filter(biblioteca=self.request.user)

    def post(self, request, pk):
        comanda = self.get_object()
        try:
            canvia_estat(
                comanda,
                Comanda.Estat.PREPARADA,
                des_de=[Comanda.Estat.REBUDA],
            )
        except TransicioNoPermesa as error:
            return Response(
                {"detail": missatge_no_llesta(error.estat_actual)},
                status=status.HTTP_409_CONFLICT,
            )
        assigna_comanda(comanda)
        return Response(ComandaSerializer(comanda).data)


def missatge_no_llesta(estat_actual):
    if estat_actual == Comanda.Estat.PREPARADA:
        return "Aquesta comanda ja està llesta per a recollida."
    estat = Comanda.Estat(estat_actual).label.lower()
    return f"Aquesta comanda no es pot marcar com a llesta perquè està {estat}."


class RutaAvuiView(APIView):
    permission_classes = [EsRepartidorValidat]

    def get(self, request):
        ruta = (
            Ruta.objects
            .filter(
                repartidor=request.user,
                data=timezone.localdate(),
            )
            .first()
        )

        if ruta is None:
            return Response([], status=status.HTTP_200_OK)

        try:
            parades = calcula_i_desaa_ordre_ruta(ruta)
        except DadesRutaInconsistents:
            return Response(
                {"detail": "La ruta conté dades inconsistents."},
                status=status.HTTP_409_CONFLICT,
            )

        dades = ParadaRutaSerializer(parades, many=True).data
        return Response(dades, status=status.HTTP_200_OK)


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

class CompletarParadaView(APIView):
    permission_classes = [EsRepartidorValidat]

    def post(self, request, pk):
        parada = get_object_or_404(
            Parada.objects.select_related("ruta", "comanda"),
            pk=pk,
            ruta__repartidor=request.user,
        )

        try:
            parada = completa_parada(parada)
        except ParadaJaCompletada as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_409_CONFLICT,
            )
        except (ParadaEnEstatTerminal, ParadaAmbComandaInvalida) as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_409_CONFLICT,
            )

        dades = ParadaCompletadaSerializer(parada).data
        return Response(dades, status=status.HTTP_200_OK)
