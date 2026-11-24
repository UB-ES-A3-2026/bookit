"""Operacions de les comandes que van més enllà d'un sol model."""

from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import F

from cataleg.models import ExemplarBiblioteca
from prestecs.models import CanviEstat, Comanda, LiniaComanda, Notificacio

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


def canvia_estat(comanda, nou_estat, repartidor=None, des_de=None):
    """Canvia l'estat de la comanda, en guarda el canvi a l'historial i n'avisa l'usuari (US8).

    `repartidor` és qui porta la comanda quan passa a "en camí", perquè la
    notificació en digui el nom.

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
        notifica(actual, repartidor)

    comanda.estat = actual.estat
    comanda.actualitzada = actual.actualitzada
    return comanda


def cancella_comanda(comanda):
    """Cancel·la la comanda i torna els seus exemplars a la biblioteca (US20).

    Només es pot cancel·lar una comanda que encara no ha sortit (rebuda o
    preparada); si no, es llança `TransicioNoPermesa` i no es toca res. El canvi
    d'estat i la devolució dels exemplars van junts: o es fan tots dos o cap.

    Si la biblioteca ha tret el llibre del seu catàleg mentrestant, no se li torna
    l'exemplar, perquè ja no l'ofereix.
    """
    with transaction.atomic():
        canvia_estat(comanda, Comanda.Estat.CANCELLADA)

        llibres = comanda.linies.values_list("llibre_id", flat=True)
        # Bloquejats en el mateix ordre que en confirmar una comanda (per llibre),
        # perquè una cancel·lació i una confirmació alhora no s'esperin mútuament.
        exemplars = list(
            ExemplarBiblioteca.objects.select_for_update()
            .filter(biblioteca_id=comanda.biblioteca_id, llibre_id__in=llibres)
            .order_by("llibre_id")
            .values_list("pk", flat=True)
        )
        ExemplarBiblioteca.objects.filter(pk__in=exemplars).update(quantitat=F("quantitat") + 1)
    return comanda
