from datetime import time
from heapq import heappop, heappush
from itertools import count

from django.db import transaction

from prestecs.models import Parada, Ruta


class DadesRutaInconsistents(ValueError):
    """Indica que les parades no poden formar una ordre vàlida i determinista."""


def _clau_ordenacio(parada):
    """Desempat secundari determinista per a parades sense restricció entre elles."""

    hora = parada.comanda.hora_inici_lliurament
    if hora is None:
        hora = time.max
    return (
        hora,
        parada.comanda_id,
        parada.id or 0,
    )


def ordena_parades(parades):
    """Calcula un ordre parcial respecte a les dependències recollida-lliurament.

    Les parades sense parella es tracten com a parades independents. Els tipus
    desconeguts i les dades amb dues parades del mateix tipus per comanda
    generen un error explícit.
    """

    parades = list(parades)
    if not parades:
        return []

    parades_per_id = {parada.id: parada for parada in parades if parada.id is not None}
    parades_per_comanda_tipus = {}

    for parada in parades:
        if parada.tipus not in (
            Parada.Tipus.RECOLLIDA,
            Parada.Tipus.LLIVRAMENT,
        ):
            raise DadesRutaInconsistents(
                f"Tipus de parada desconegut: {parada.tipus}"
            )

        clau = (parada.comanda_id, parada.tipus)
        if clau in parades_per_comanda_tipus:
            raise DadesRutaInconsistents(
                "Hi ha dues parades del mateix tipus per a la mateixa comanda"
            )
        parades_per_comanda_tipus[clau] = parada

    seguents = {parada.id or id(parada): [] for parada in parades}
    graus = {parada.id or id(parada): 0 for parada in parades}

    identificadors = {
        parada.id if parada.id is not None else id(parada): parada
        for parada in parades
    }

    for parada in parades:
        if parada.tipus == Parada.Tipus.LLIVRAMENT:
            recollida = parades_per_comanda_tipus.get(
                (parada.comanda_id, Parada.Tipus.RECOLLIDA)
            )
            if recollida is not None:
                origen = recollida.id or id(recollida)
                desti = parada.id or id(parada)
                seguents[origen].append(desti)
                graus[desti] += 1

    contador = count()
    disponibles = []
    for identificador, parada in identificadors.items():
        if graus[identificador] == 0:
            heappush(
                disponibles,
                (*_clau_ordenacio(parada), next(contador), identificador),
            )

    resultat = []
    while disponibles:
        *_, identificador = heappop(disponibles)
        parada = identificadors[identificador]
        resultat.append(parada)

        for seguident in seguents[identificador]:
            graus[seguident] -= 1
            if graus[seguident] == 0:
                parada_seguent = identificadors[seguident]
                heappush(
                    disponibles,
                    (
                        *_clau_ordenacio(parada_seguent),
                        next(contador),
                        seguident,
                    ),
                )

    if len(resultat) != len(parades):
        raise DadesRutaInconsistents(
            "Les dependències de recollida i lliurament formen un cicle"
        )

    return resultat


def calcula_i_desaa_ordre_ruta(ruta):
    """Calcula i desa l'ordre definitiu d'una ruta de manera atòmica.

    Retorna la llista de parades ja ordenades.
    """

    with transaction.atomic():
        ruta_bloquejada = Ruta.objects.select_for_update().get(pk=ruta.pk)
        parades = list(
            Parada.objects.select_for_update()
            .select_related("comanda")
            .filter(ruta=ruta_bloquejada)
            .order_by("id")
        )

        ordenades = ordena_parades(parades)

        if not ordenades:
            return []

        offset_temporal = len(parades) + 1
        for index, parada in enumerate(ordenades, start=1):
            parada.ordre = offset_temporal + index
        Parada.objects.bulk_update(ordenades, ["ordre"])

        for index, parada in enumerate(ordenades, start=1):
            parada.ordre = index
        Parada.objects.bulk_update(ordenades, ["ordre"])

    return ordenades
