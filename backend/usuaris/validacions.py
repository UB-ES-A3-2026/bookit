"""Funcions de validació reutilitzables per a les dades d'usuaris i perfils (US1.1-T2).

Comprovacions de DNI/NIE amb lletra de control, telèfon espanyol (+34 opcional),
matrícula espanyola i número de la Seguretat Social de 12 dígits.
"""

import re

from django.core.exceptions import ValidationError

DNI_NIE_INVALID = "El DNI/NIE no és vàlid"
TELEFON_INVALID = "El telèfon ha de tenir 9 xifres"
MATRICULA_INVALIDA = "La matrícula ha de tenir 4 xifres i 3 lletres"
SEGURETAT_SOCIAL_INVALIDA = "El número de la Seguretat Social ha de tenir 12 xifres"

LLETRES_DNI = "TRWAGMYFPDXBNJZSQVHLCKE"
RE_DNI_NIE = re.compile(r"\A[XYZ0-9][0-9]{7}[A-Z]\Z")
RE_TELEFON = re.compile(r"\A(?:\+34)?[6-9][0-9]{8}\Z")
RE_MATRICULA = re.compile(r"\A[0-9]{4}[BCDFGHJKLMNPRSTVWXYZ]{3}\Z")
RE_SEGURETAT_SOCIAL = re.compile(r"\A[0-9]{12}\Z")


def normalitza(text):
    """Elimina espais, guions i barres, i passa el text a majúscules."""
    if not isinstance(text, str):
        return ""
    return re.sub(r"[\s\-/]", "", text).upper()


def es_dni_nie_valid(valor):
    """Comprova si un DNI o NIE té un format correcte i la lletra de control adequada.

    - DNI: 8 xifres i lletra de control.
    - NIE: lletra inicial (X, Y o Z), 7 xifres i lletra de control.
      En el NIE, X compta com a 0, Y com a 1 i Z com a 2.
    """
    if not isinstance(valor, str):
        return False

    text = normalitza(valor)
    if not RE_DNI_NIE.match(text):
        return False

    primer = text[0]
    if primer == "X":
        prefix = "0"
    elif primer == "Y":
        prefix = "1"
    elif primer == "Z":
        prefix = "2"
    else:
        prefix = primer

    numero = int(prefix + text[1:8])
    lletra_esperada = LLETRES_DNI[numero % 23]
    return text[8] == lletra_esperada


def valida_dni_nie(valor):
    """Validador de Django per a DNI o NIE."""
    if not es_dni_nie_valid(valor):
        raise ValidationError(DNI_NIE_INVALID, code="invalid")


def es_telefon_valid(valor):
    """Comprova si un telèfon espanyol té 9 xifres i comença per 6, 7, 8 o 9 (+34 opcional)."""
    if not isinstance(valor, str):
        return False

    text = normalitza(valor)
    return bool(RE_TELEFON.match(text))


def valida_telefon(valor):
    """Validador de Django per a telèfons espanyols."""
    if not es_telefon_valid(valor):
        raise ValidationError(TELEFON_INVALID, code="invalid")


def es_matricula_valida(valor):
    """Comprova si una matrícula té el format espanyol actual (4 xifres i 3 consonants, sense vocals, Ñ ni Q)."""
    if not isinstance(valor, str):
        return False

    text = normalitza(valor)
    return bool(RE_MATRICULA.match(text))


def valida_matricula(valor):
    """Validador de Django per a matrícules espanyoles."""
    if not es_matricula_valida(valor):
        raise ValidationError(MATRICULA_INVALIDA, code="invalid")


def es_num_seguretat_social_valid(valor):
    """Comprova si el número de la Seguretat Social té 12 xifres."""
    if not isinstance(valor, str):
        return False

    text = normalitza(valor)
    return bool(RE_SEGURETAT_SOCIAL.match(text))


def valida_num_seguretat_social(valor):
    """Validador de Django per al número de la Seguretat Social."""
    if not es_num_seguretat_social_valid(valor):
        raise ValidationError(SEGURETAT_SOCIAL_INVALIDA, code="invalid")
