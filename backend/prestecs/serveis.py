"""Operacions de les comandes que van més enllà d'un sol model."""

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from cataleg.models import ExemplarBiblioteca
from prestecs.models import CanviEstat, Comanda, LiniaComanda, Notificacio, Prestec

Estat = Comanda.Estat

# Text de la notificació segons l'estat al qual passa la comanda. Els de rebuda,
# preparada, en camí i lliurada són literals dels criteris de la US8. El de la
# cancel·lació no el diu cap criteri (US20).
NOTIFICACIONS = {
    Estat.REBUDA: "La teva comanda s'ha rebut correctament. La biblioteca ja l'està preparant",
    Estat.PREPARADA: "La teva comanda ja està preparada i aviat sortirà cap a casa teva",
    Estat.EN_CAMI: "En/Na {repartidor} ja porta la teva comanda. Està en camí!",
    Estat.LLIURADA: "La teva comanda s'ha lliurat correctament. Gaudeix del teu llibre!",
    Estat.CANCELLADA: "La teva comanda s'ha cancel·lat.",
}
# Mentre la comanda no tingui repartidor assignat (US12), no en podem dir el nom.
EN_CAMI_SENSE_REPARTIDOR = "El repartidor ja porta la teva comanda. Està en camí!"


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
        notifica(comanda)
    return comanda


def text_notificacio(estat, repartidor=None):
    """Text de la notificació d'una comanda que passa a `estat`."""
    if estat == Estat.EN_CAMI:
        if repartidor is None:
            return EN_CAMI_SENSE_REPARTIDOR
        return NOTIFICACIONS[estat].format(repartidor=repartidor.name)
    return NOTIFICACIONS[estat]


def notifica(comanda, repartidor=None):
    """Avisa l'usuari de l'estat actual de la seva comanda."""
    return Notificacio.objects.create(
        usuari_id=comanda.usuari_id,
        comanda=comanda,
        text=text_notificacio(comanda.estat, repartidor),
    )


def canvia_estat(comanda, nou_estat, repartidor=None):
    """Canvia l'estat de la comanda, en guarda el canvi a l'historial i n'avisa l'usuari (US8).

    `repartidor` és qui porta la comanda quan passa a "en camí", perquè la
    notificació en digui el nom.

    Si el canvi no està permès (vegeu `TRANSICIONS`), no es toca res i es llança
    `TransicioNoPermesa`. La comanda es bloqueja mentre es canvia, perquè dues
    accions alhora (per exemple, cancel·lar-la i recollir-la) no la deixin en un
    estat incoherent: la segona veu l'estat que ha deixat la primera.
    """
    with transaction.atomic():
        actual = Comanda.objects.select_for_update().get(pk=comanda.pk)
        if not actual.pot_passar_a(nou_estat):
            raise TransicioNoPermesa(actual.estat, nou_estat)

        actual.estat = nou_estat
        actual.save(update_fields=["estat", "actualitzada"])
        CanviEstat.objects.create(comanda=actual, estat=nou_estat)
        notifica(actual, repartidor)

    comanda.estat = actual.estat
    comanda.actualitzada = actual.actualitzada
    return comanda


def crea_prestecs(comanda, data_inici=None):
    """Crea un préstec per cada llibre d'una comanda que s'acaba de lliurar (US19).

    El préstec comença el dia del lliurament i dura `DURADA_PRESTEC_DIES`. Si la
    comanda ja tenia els préstecs creats, no en crea de nous i retorna els que hi ha.
    """
    data_inici = data_inici or timezone.localdate()
    data_limit = data_inici + timedelta(days=settings.DURADA_PRESTEC_DIES)

    with transaction.atomic():
        # En l'ordre de la comanda, perquè els préstecs surtin en el mateix ordre.
        for linia in comanda.linies.filter(prestec__isnull=True).order_by("pk"):
            Prestec.objects.create(
                linia=linia,
                usuari=comanda.usuari,
                llibre=linia.llibre,
                biblioteca=comanda.biblioteca,
                data_inici=data_inici,
                data_limit=data_limit,
            )
    return list(Prestec.objects.filter(linia__comanda=comanda))
