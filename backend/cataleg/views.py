"""Vistes de l'API del mòdul cataleg."""

from django.db.models import Avg, Count, Exists, OuterRef, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
)
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from cataleg.authentication import AutenticacioJWTOpcional
from cataleg.models import ExemplarBiblioteca, LlistaEspera, Llibre
from cataleg.permisos import EsBibliotecaActiva
from cataleg.serializers import (
    BibliotecaAmbEstocSerializer,
    EdicioLlibreCatalegSerializer,
    EntradaLlistaEsperaSerializer,
    ExemplarsCatalegSerializer,
    LlibreCatalegSerializer,
    LlibreCercaSerializer,
)
from cataleg.serveis import distancia_haversine_km
from usuaris.models import Adreca, Usuari


class CercaLlibresPagination(PageNumberPagination):
    page_size = 10


class CercaLlibresView(generics.ListAPIView):
    """Cerca llibres públicament per títol, autor o ISBN."""

    serializer_class = LlibreCercaSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    pagination_class = CercaLlibresPagination

    def get_queryset(self):
        cerca = self.request.query_params.get("q", "").strip()
        if not cerca:
            return Llibre.objects.none()

        exemplar_disponible = ExemplarBiblioteca.objects.filter(
            llibre_id=OuterRef("pk"),
            quantitat__gt=0,
        )
        return (
            Llibre.objects.filter(
                Q(titol__icontains=cerca)
                | Q(autor__icontains=cerca)
                | Q(isbn__icontains=cerca)
            )
            .annotate(
                disponible=Exists(exemplar_disponible),
                mitjana_valoracions_cerca=Avg("valoracions__puntuacio"),
                nombre_valoracions_cerca=Count(
                    "valoracions",
                    distinct=True,
                ),
            )
            .order_by("titol", "id")
        )


class CatalegBibliotecaView(generics.ListCreateAPIView):
    """Llista i afegeix els llibres del catàleg de la biblioteca autenticada (US17-T3)."""

    serializer_class = LlibreCatalegSerializer
    permission_classes = [EsBibliotecaActiva]
    pagination_class = None

    def get_queryset(self):
        # Només el catàleg de la biblioteca autenticada (vegeu `EsBibliotecaActiva`).
        return (
            ExemplarBiblioteca.objects.filter(biblioteca=self.request.user)
            .select_related("llibre")
            .order_by("llibre__titol", "llibre_id")
        )


class LlibreCatalegBibliotecaMixin:
    """Troba l'entrada del catàleg de la biblioteca autenticada per l'`id` del llibre (US17-T4).

    Un llibre que no és al catàleg de la biblioteca, encara que el tingui una altra,
    rep el mateix 404 que un llibre inexistent.
    """

    permission_classes = [EsBibliotecaActiva]
    lookup_field = "llibre_id"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        return ExemplarBiblioteca.objects.filter(
            biblioteca=self.request.user
        ).select_related("llibre")


class LlibreCatalegBibliotecaView(
    LlibreCatalegBibliotecaMixin, generics.UpdateAPIView, generics.DestroyAPIView
):
    """Edita les dades d'un llibre del catàleg o el retira (US17-T4).

    Retirar-lo esborra la fila d'exemplars de la biblioteca i manté el `Llibre`,
    que poden tenir altres biblioteques (P4 del contracte).
    """

    serializer_class = EdicioLlibreCatalegSerializer
    http_method_names = ["patch", "delete", "options"]


class ExemplarsCatalegBibliotecaView(LlibreCatalegBibliotecaMixin, generics.UpdateAPIView):
    """Canvia el nombre d'exemplars d'un llibre del catàleg (US17-T4)."""

    serializer_class = ExemplarsCatalegSerializer
    http_method_names = ["patch", "options"]

    def patch(self, request, *args, **kwargs):
        # No és parcial: `exemplars` és l'únic camp i és obligatori.
        return self.update(request, *args, **kwargs)


MISSATGE_SENSE_ESTOC = "Cap biblioteca te aquest llibre en estoc"
MISSATGE_SENSE_ADRECA = "Afegeix una adreça per continuar"
MISSATGE_ANONIM = "Registrat per ordenar les biblioteques per distància"


class BibliotequesAmbEstocLlibreView(APIView):
    authentication_classes = [AutenticacioJWTOpcional]
    permission_classes = [AllowAny]

    def get(self, request, id):
        llibre = get_object_or_404(Llibre, pk=id)
        exemplars = list(
            ExemplarBiblioteca.objects.filter(
                llibre=llibre,
                quantitat__gt=0,
                biblioteca__is_active=True,
                biblioteca__role=Usuari.Role.BIBLIOTECA,
                biblioteca__biblioteca__isnull=False,
            )
            .select_related(
                "llibre",
                "biblioteca",
                "biblioteca__biblioteca",
            )
            .order_by(
                "biblioteca__biblioteca__nom",
                "biblioteca_id",
            )
        )

        usuari_autenticat = (
            request.user
            and request.user.is_authenticated
        )
        adreca_predeterminada = None
        ordenada_per_distancia = False

        if usuari_autenticat:
            adreca_predeterminada = (
                Adreca.objects
                .filter(
                    usuari=request.user,
                    predeterminada=True,
                )
                .only("latitud", "longitud")
                .first()
            )

        adreca_amb_coordenades = (
            adreca_predeterminada is not None
            and adreca_predeterminada.latitud is not None
            and adreca_predeterminada.longitud is not None
        )

        if adreca_amb_coordenades:
            for exemplar in exemplars:
                biblioteca = exemplar.biblioteca.biblioteca
                if (
                    biblioteca.latitud is not None
                    and biblioteca.longitud is not None
                ):
                    exemplar.distancia_km = round(
                        distancia_haversine_km(
                            adreca_predeterminada.latitud,
                            adreca_predeterminada.longitud,
                            biblioteca.latitud,
                            biblioteca.longitud,
                        ),
                        1,
                    )

            exemplars.sort(
                key=lambda exemplar: (
                    not hasattr(exemplar, "distancia_km"),
                    getattr(exemplar, "distancia_km", float("inf")),
                    exemplar.biblioteca.biblioteca.nom.casefold(),
                    exemplar.biblioteca_id,
                )
            )
            ordenada_per_distancia = True

        if not exemplars:
            missatge = MISSATGE_SENSE_ESTOC
        elif not usuari_autenticat:
            missatge = MISSATGE_ANONIM
        elif not adreca_amb_coordenades:
            missatge = MISSATGE_SENSE_ADRECA
        else:
            missatge = None

        dades = BibliotecaAmbEstocSerializer(
            exemplars,
            many=True,
        ).data

        return Response({
            "biblioteques": dades,
            "ordenada_per_distancia": ordenada_per_distancia,
            "missatge": missatge,
        })

class LlistaEsperaLlibreView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        llibre = get_object_or_404(Llibre, pk=id)

        entrada, creada = LlistaEspera.objects.get_or_create(
            usuari=request.user,
            llibre=llibre,
        )

        dades = EntradaLlistaEsperaSerializer(entrada).data
        estat = HTTP_201_CREATED if creada else HTTP_200_OK
        return Response(dades, status=estat)

    def delete(self, request, id):
        llibre = get_object_or_404(Llibre, pk=id)

        LlistaEspera.objects.filter(
            usuari=request.user,
            llibre=llibre,
        ).delete()

        return Response(status=HTTP_204_NO_CONTENT)
