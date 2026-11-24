"""Vistes de l'API del mòdul prestecs."""

from django.db.models import F
from rest_framework import generics, status
from rest_framework.response import Response

from cataleg.permisos import EsBibliotecaActiva
from prestecs.assignacio import assigna_comanda
from prestecs.models import Comanda, Prestec
from prestecs.permisos import EsUsuariActiu
from prestecs.serializers import (
    SENSE_ESTOC,
    ComandaBibliotecaSerializer,
    ComandaSerializer,
    ConfirmacioComandaSerializer,
    NotificacioSerializer,
    PrestecSerializer,
)
from prestecs.serveis import (
    LlibresSenseEstoc,
    TransicioNoPermesa,
    cancella_comanda,
    canvia_estat,
    confirma_comanda,
    cost_enviament,
)

# Literal dels criteris d'acceptació de la US20.
JA_HA_SORTIT = "Aquesta comanda ja ha sortit i no es pot cancel·lar"
JA_CANCELLADA = "Aquesta comanda ja està cancel·lada."


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


class ComandesBibliotecaView(generics.ListAPIView):
    """Comandes pendents de la biblioteca autenticada (US10-T1).

    Són les que encara ha de preparar o ja té preparades, i també les cancel·lades,
    perquè la biblioteca vegi que no les ha de preparar (US20). Surten ordenades per
    data de lliurament; les que encara no en tenen, al final.
    """

    serializer_class = ComandaBibliotecaSerializer
    permission_classes = [EsBibliotecaActiva]
    pagination_class = None

    ESTATS_PENDENTS = [Comanda.Estat.REBUDA, Comanda.Estat.PREPARADA, Comanda.Estat.CANCELLADA]

    def get_queryset(self):
        return (
            Comanda.objects.filter(biblioteca=self.request.user, estat__in=self.ESTATS_PENDENTS)
            .select_related("usuari", "biblioteca__biblioteca")
            .prefetch_related("linies__llibre")
            .order_by(F("data_lliurament").asc(nulls_last=True), "creada", "id")
        )


class ComandaLlestaView(generics.GenericAPIView):
    """La biblioteca marca una comanda seva com a llesta per a recollida (US15-T1).

    "Llesta per a recollida" és l'estat `preparada` (US8). En aquest moment
    s'assigna a un repartidor si n'hi ha cap amb un forat a les seves franges
    (US14). Si no, es queda preparada fins que l'ordre `assigna_comandes` la pugui
    assignar.
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
        assigna_comanda(comanda)
        return Response(ComandaSerializer(comanda).data)


class ComandaRecollidaView(generics.GenericAPIView):
    """La biblioteca lliura una comanda de recollida a l'usuari que la ve a buscar (US7-T8).

    Només les comandes de recollida que ja estan preparades (US15). La comanda passa
    a "lliurada": l'usuari en rep l'avís (US8) i es creen els préstecs (US19).
    """

    permission_classes = [EsBibliotecaActiva]

    def get_queryset(self):
        # Una comanda d'una altra biblioteca rep el mateix 404 que una que no existeix.
        return Comanda.objects.filter(biblioteca=self.request.user)

    def post(self, request, pk):
        comanda = self.get_object()
        if comanda.tipus_lliurament != Comanda.TipusLliurament.RECOLLIDA:
            return Response({"detail": ES_A_DOMICILI}, status=status.HTTP_409_CONFLICT)
        try:
            canvia_estat(comanda, Comanda.Estat.LLIURADA, des_de=[Comanda.Estat.PREPARADA])
        except TransicioNoPermesa as error:
            return Response({"detail": missatge_no_recollida(error.estat_actual)}, status=status.HTTP_409_CONFLICT)
        return Response(ComandaSerializer(comanda).data)


ES_A_DOMICILI = "Aquesta comanda és a domicili: la lliura el repartidor."


def missatge_no_recollida(estat_actual):
    if estat_actual == Comanda.Estat.REBUDA:
        return "Aquesta comanda encara no està llesta per a recollida."
    if estat_actual == Comanda.Estat.LLIURADA:
        return "Aquesta comanda ja està lliurada."
    estat = Comanda.Estat(estat_actual).label.lower()
    return f"Aquesta comanda no es pot lliurar perquè està {estat}."


def missatge_no_llesta(estat_actual):
    if estat_actual == Comanda.Estat.PREPARADA:
        return "Aquesta comanda ja està llesta per a recollida."
    estat = Comanda.Estat(estat_actual).label.lower()
    return f"Aquesta comanda no es pot marcar com a llesta perquè està {estat}."


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
