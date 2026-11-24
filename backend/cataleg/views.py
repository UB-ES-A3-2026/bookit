"""Vistes de l'API del mòdul cataleg."""

from django.db.models import Avg, Count, Exists, OuterRef, Q
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny

from cataleg.models import ExemplarBiblioteca, Llibre
from cataleg.permisos import EsBibliotecaActiva
from cataleg.serializers import (
    EdicioLlibreCatalegSerializer,
    ExemplarsCatalegSerializer,
    LlibreCatalegSerializer,
    LlibreCercaSerializer,
)


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
