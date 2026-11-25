"""Permisos de l'API de comandes. Contracte a `docs/api-comandes.md`."""

from rest_framework.permissions import BasePermission

from usuaris.models import Usuari

SENSE_PERMISOS = "No té permisos per realitzar aquesta acció."


class EsUsuariActiu(BasePermission):
    """Només deixa passar un usuari lector (rol `usuari`) amb el compte actiu.

    Sense un token vàlid, la petició ja rep el 401 de l'autenticació JWT abans
    d'arribar aquí. Una biblioteca o un repartidor autenticats reben 403.
    """

    message = SENSE_PERMISOS

    def has_permission(self, request, view):
        usuari = request.user
        return bool(
            usuari
            and usuari.is_authenticated
            and usuari.is_active
            and usuari.role == Usuari.Role.USUARI
        )
