"""Operacions de les comandes que van més enllà d'un sol model."""

from django.db import transaction

from cataleg.models import ExemplarBiblioteca
from prestecs.models import CanviEstat, Comanda, LiniaComanda


class TransicioNoPermesa(Exception):
    """La comanda no pot passar de l'estat actual al que es demana."""

    def __init__(self, estat_actual, nou_estat):
        super().__init__(f"Una comanda {estat_actual} no pot passar a {nou_estat}.")
        self.estat_actual = estat_actual
        self.nou_estat = nou_estat


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
        CanviEstat.objects.create(comanda=comanda, estat=comanda.estat)
    return comanda


def canvia_estat(comanda, nou_estat, des_de=None):
    """Canvia l'estat de la comanda i en guarda el canvi a l'historial (US8).

    `des_de` limita encara més els estats des dels quals es pot fer el canvi. Per
    exemple, la biblioteca només pot marcar com a preparada una comanda rebuda,
    encara que una comanda en camí també hi pugui tornar si falla la parada.

    Si el canvi no està permès (vegeu `TRANSICIONS`), no es toca res i es llança
    `TransicioNoPermesa`. La comanda es bloqueja mentre es canvia, perquè dues
    accions alhora (per exemple, cancel·lar-la i recollir-la) no la deixin en un
    estat incoherent: la segona veu l'estat que ha deixat la primera.
    """
    with transaction.atomic():
        actual = Comanda.objects.select_for_update().get(pk=comanda.pk)
        permes_aqui = des_de is None or actual.estat in des_de
        if not (permes_aqui and actual.pot_passar_a(nou_estat)):
            raise TransicioNoPermesa(actual.estat, nou_estat)

        actual.estat = nou_estat
        actual.save(update_fields=["estat", "actualitzada"])
        CanviEstat.objects.create(comanda=actual, estat=nou_estat)

    comanda.estat = actual.estat
    comanda.actualitzada = actual.actualitzada
    return comanda
