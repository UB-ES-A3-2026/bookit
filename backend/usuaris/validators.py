"""Reexportació dels validadors d'usuaris (US1.1-T2)."""

from usuaris.validacions import (
    DNI_NIE_INVALID,
    MATRICULA_INVALIDA,
    SEGURETAT_SOCIAL_INVALIDA,
    TELEFON_INVALID,
    es_dni_nie_valid,
    es_matricula_valida,
    es_num_seguretat_social_valid,
    es_telefon_valid,
    normalitza,
    valida_dni_nie,
    valida_matricula,
    valida_num_seguretat_social,
    valida_telefon,
)

__all__ = [
    "DNI_NIE_INVALID",
    "MATRICULA_INVALIDA",
    "SEGURETAT_SOCIAL_INVALIDA",
    "TELEFON_INVALID",
    "es_dni_nie_valid",
    "es_matricula_valida",
    "es_num_seguretat_social_valid",
    "es_telefon_valid",
    "normalitza",
    "valida_dni_nie",
    "valida_matricula",
    "valida_num_seguretat_social",
    "valida_telefon",
]
