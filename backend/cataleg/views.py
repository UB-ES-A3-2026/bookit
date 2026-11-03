"""Vistes de l'API del mòdul cataleg."""

from django.db.models import Avg, Count, Exists, OuterRef, Q
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny

from cataleg.models import ExemplarBiblioteca, Llibre
from cataleg.permisos import EsBibliotecaActiva
from cataleg.serializers import LlibreCatalegSerializer, LlibreCercaSerializer


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
