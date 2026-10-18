"""Vistes del projecte que no pertanyen a cap mòdul."""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def salut(request):
    """Indica que l'API està en marxa."""
    return Response({"status": "ok"})
