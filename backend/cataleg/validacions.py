"""Validació dels camps dels llibres del catàleg: l'ISBN (US17-T2) i la portada (US17-T5).

L'ISBN accepta ISBN-10 i ISBN-13, amb guions o espais o sense, i comprova el dígit de control.
La portada és un enllaç http o https a la imatge, que el frontend mostra tal com està desat.
"""

import re

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

ISBN_INVALID = "L'ISBN introduït no és vàlid"

RE_ISBN_10 = re.compile(r"\A[0-9]{9}[0-9X]\Z")
RE_ISBN_13 = re.compile(r"\A97[89][0-9]{10}\Z")


def normalitza_isbn(valor):
    """Elimina guions i espais, i passa la X final de l'ISBN-10 a majúscula."""
    if not isinstance(valor, str):
        return ""
    return re.sub(r"[\s\-]", "", valor).upper()


def es_isbn_10_valid(text):
    """Comprova un ISBN-10 normalitzat: la suma ponderada (10..1) ha de ser múltiple d'11.

    L'últim caràcter pot ser una X, que val 10.
    """
    if not RE_ISBN_10.match(text):
        return False

    suma = 0
    for posicio, caracter in enumerate(text):
        valor = 10 if caracter == "X" else int(caracter)
        suma += valor * (10 - posicio)
    return suma % 11 == 0


def es_isbn_13_valid(text):
    """Comprova un ISBN-13 normalitzat: la suma ponderada (1, 3, 1, 3...) ha de ser múltiple de 10."""
    if not RE_ISBN_13.match(text):
        return False

    suma = sum(int(xifra) * (1 if posicio % 2 == 0 else 3) for posicio, xifra in enumerate(text))
    return suma % 10 == 0


def es_isbn_valid(valor):
    """Comprova si un valor és un ISBN-10 o un ISBN-13 vàlid, acceptant guions i espais."""
    text = normalitza_isbn(valor)
    if len(text) == 10:
        return es_isbn_10_valid(text)
    if len(text) == 13:
        return es_isbn_13_valid(text)
    return False


def valida_isbn(valor):
    """Validador de Django per a l'ISBN."""
    if not es_isbn_valid(valor):
        raise ValidationError(ISBN_INVALID, code="invalid")


# Portada

PORTADA_MAX_LENGTH = 500
PORTADA_INVALIDA = URLValidator.message

# Només http i https: el navegador ha de poder carregar l'enllaç com a imatge, i esquemes com
# `javascript:` o `data:` no s'han d'acceptar.
_valida_enllac_portada = URLValidator(schemes=["http", "https"])


def valida_portada(valor):
    """Validador de Django per a l'enllaç de la portada.

    És una funció i no directament el `URLValidator` perquè Django REST Framework descarta els `URLValidator`
    del model en generar els serializers, i llavors no es comprovaria l'esquema.
    """
    _valida_enllac_portada(valor)
