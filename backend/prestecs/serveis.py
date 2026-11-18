"""Operacions de les comandes que van més enllà d'un sol model."""

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from cataleg.models import ExemplarBiblioteca
from prestecs.models import Comanda, LiniaComanda, Prestec


class LlibresSenseEstoc(Exception):
    """Algun llibre de la comanda no té exemplars disponibles a la biblioteca."""

    def __init__(self, ids_llibres):
        super().__init__(ids_llibres)
        self.ids_llibres = ids_llibres


def confirma_comanda(usuari, biblioteca, llibres):
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

        comanda = Comanda.objects.create(usuari=usuari, biblioteca=biblioteca)
        LiniaComanda.objects.bulk_create(
            LiniaComanda(comanda=comanda, llibre=llibre) for llibre in llibres
        )
    return comanda


def crea_prestecs(comanda, data_inici=None):
    """Crea un préstec per cada llibre d'una comanda que s'acaba de lliurar (US19).

    El préstec comença el dia del lliurament i dura `DURADA_PRESTEC_DIES`. Si la
    comanda ja tenia els préstecs creats, no en crea de nous i retorna els que hi ha.
    """
    data_inici = data_inici or timezone.localdate()
    data_limit = data_inici + timedelta(days=settings.DURADA_PRESTEC_DIES)

    with transaction.atomic():
        for linia in comanda.linies.filter(prestec__isnull=True):
            Prestec.objects.create(
                linia=linia,
                usuari=comanda.usuari,
                llibre=linia.llibre,
                biblioteca=comanda.biblioteca,
                data_inici=data_inici,
                data_limit=data_limit,
            )
    return list(Prestec.objects.filter(linia__comanda=comanda))
