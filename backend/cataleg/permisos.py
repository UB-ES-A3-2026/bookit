"""Permisos de l'API de gestió del catàleg (US17). Contracte a `docs/api-cataleg.md`."""

from rest_framework.permissions import BasePermission

from usuaris.models import Biblioteca, Usuari

SENSE_PERMISOS = "No té permisos per realitzar aquesta acció."


class EsBibliotecaActiva(BasePermission):
    """Només deixa passar una biblioteca amb el compte actiu i el perfil creat (US17-T1).

    Sense un token vàlid, la petició ja rep el 401 de l'autenticació JWT abans
    d'arribar aquí. Un usuari o un repartidor autenticats reben 403.

    Que cada biblioteca només vegi i modifiqui el seu catàleg no es comprova aquí
    amb `has_object_permission`: les vistes han de filtrar el queryset per
    `request.user.biblioteca`, perquè un llibre d'una altra biblioteca rebi el
    mateix 404 que un llibre inexistent i no se'n pugui saber res.
    """

    message = SENSE_PERMISOS

    def has_permission(self, request, view):
        usuari = request.user
        if not (
            usuari
            and usuari.is_authenticated
            and usuari.is_active
            and usuari.role == Usuari.Role.BIBLIOTECA
        ):
            return False
        # Un compte amb el rol però sense perfil no té catàleg on treballar.
        try:
            usuari.biblioteca
        except Biblioteca.DoesNotExist:
            return False
        return True
