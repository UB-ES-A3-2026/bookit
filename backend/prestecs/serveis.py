"""Operacions de les comandes que van més enllà d'un sol model."""

from django.db import transaction

from cataleg.models import ExemplarBiblioteca
from prestecs.models import Comanda, LiniaComanda


class LlibresSenseEstoc(Exception):
    """Algun llibre de la comanda no té exemplars disponibles a la biblioteca."""

    def __init__(self, ids_llibres):
        super().__init__(ids_llibres)
        self.ids_llibres = ids_llibres


def confirma_comanda(usuari, biblioteca, llibres):
    """Crea la comanda amb els llibres si la biblioteca en té tots en estoc.

    Si en falta algun, no es crea res i es llança `LlibresSenseEstoc` amb els
    llibres que no en tenen, perquè l'usuari s'hi pugui apuntar a la llista
    d'espera. La reserva dels exemplars s'afegeix a la US6-T3.
    """
    with transaction.atomic():
        amb_estoc = set(
            ExemplarBiblioteca.objects.filter(
                biblioteca=biblioteca,
                llibre__in=llibres,
                quantitat__gt=0,
            ).values_list("llibre_id", flat=True)
        )
        sense_estoc = [llibre.pk for llibre in llibres if llibre.pk not in amb_estoc]
        if sense_estoc:
            raise LlibresSenseEstoc(sense_estoc)

        comanda = Comanda.objects.create(usuari=usuari, biblioteca=biblioteca)
        LiniaComanda.objects.bulk_create(
            LiniaComanda(comanda=comanda, llibre=llibre) for llibre in llibres
        )
    return comanda
