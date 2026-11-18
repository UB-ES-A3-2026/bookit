"""Operacions de les comandes que van més enllà d'un sol model."""

from decimal import Decimal

from django.conf import settings
from django.db import transaction

from cataleg.models import ExemplarBiblioteca
from prestecs.models import Comanda, LiniaComanda


class LlibresSenseEstoc(Exception):
    """Algun llibre de la comanda no té exemplars disponibles a la biblioteca."""

    def __init__(self, ids_llibres):
        super().__init__(ids_llibres)
        self.ids_llibres = ids_llibres


def cost_enviament(tipus_lliurament):
    """Cost en euros del lliurament (US7). La recollida a la biblioteca és gratuïta."""
    if tipus_lliurament == Comanda.TipusLliurament.RECOLLIDA:
        return Decimal("0.00")
    return settings.COST_ENVIAMENT_DOMICILI


def confirma_comanda(
    usuari,
    biblioteca,
    llibres,
    tipus_lliurament=Comanda.TipusLliurament.DOMICILI,
    adreca_lliurament="",
):
    """Crea la comanda i reserva un exemplar de cada llibre a la biblioteca.

    Si algun llibre no té exemplars disponibles, no es crea res i es llança
    `LlibresSenseEstoc` amb els llibres que no en tenen, perquè l'usuari s'hi
    pugui apuntar a la llista d'espera.

    Les files d'exemplars es bloquegen (`select_for_update`) fins que acaba la
    transacció. Així, si dues comandes demanen alhora l'últim exemplar d'un
    llibre, la segona espera que acabi la primera i ja el troba esgotat.
    """
    with transaction.atomic():
        # Sempre en el mateix ordre, perquè dues comandes amb els mateixos llibres
        # no es bloquegin l'una a l'altra esperant-se mútuament.
        exemplars = {
            exemplar.llibre_id: exemplar
            for exemplar in ExemplarBiblioteca.objects.select_for_update()
            .filter(biblioteca=biblioteca, llibre__in=llibres)
            .order_by("llibre_id")
        }
        sense_estoc = [
            llibre.pk
            for llibre in llibres
            if llibre.pk not in exemplars or exemplars[llibre.pk].quantitat == 0
        ]
        if sense_estoc:
            raise LlibresSenseEstoc(sense_estoc)

        for exemplar in exemplars.values():
            exemplar.quantitat -= 1
        ExemplarBiblioteca.objects.bulk_update(exemplars.values(), ["quantitat"])

        comanda = Comanda.objects.create(
            usuari=usuari,
            biblioteca=biblioteca,
            tipus_lliurament=tipus_lliurament,
            adreca_lliurament=adreca_lliurament,
            cost_enviament=cost_enviament(tipus_lliurament),
        )
        LiniaComanda.objects.bulk_create(
            LiniaComanda(comanda=comanda, llibre=llibre) for llibre in llibres
        )
    return comanda
