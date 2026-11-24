"""Permisos de l'API del mòdul usuaris."""

from rest_framework.permissions import BasePermission

from usuaris.models import PerfilRepartidor, Usuari

SENSE_PERMISOS = "No té permisos per realitzar aquesta acció."


class EsRepartidorValidat(BasePermission):
    """Només deixa passar un repartidor actiu amb el perfil validat (US14).

    Un repartidor pendent o rebutjat ja no pot iniciar sessió, però si encara té
    un token d'abans de ser rebutjat, aquí rep 403. Sense token, la petició ja rep
    el 401 de l'autenticació JWT.
    """

    message = SENSE_PERMISOS

    def has_permission(self, request, view):
        usuari = request.user
        if not (
            usuari
            and usuari.is_authenticated
            and usuari.is_active
            and usuari.role == Usuari.Role.REPARTIDOR
        ):
            return False
        return PerfilRepartidor.objects.filter(
            usuari=usuari, estat=PerfilRepartidor.Estat.VALIDAT
        ).exists()
