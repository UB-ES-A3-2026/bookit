"""Operacions de les comandes que van més enllà d'un sol model."""

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from cataleg.models import ExemplarBiblioteca
from prestecs.models import CanviEstat, Comanda, LiniaComanda, Notificacio, Prestec
from usuaris.geocodificacio import geocodifica_text

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


def desa_coordenades_lliurament(comanda):
    """Geocodifica l'adreça de lliurament i en desa les coordenades (US12-T13).

    Es crida fora de la transacció de `confirma_comanda`, perquè la petició al
    geocodificador no bloquegi els exemplars. Si no es pot geocodificar, les
    coordenades queden buides i la comanda continua sent vàlida: la parada surt
    a la llista de la ruta, però no al mapa. Retorna si s'han trobat.
    """
    coordenades = None
    if (
        comanda.tipus_lliurament == Comanda.TipusLliurament.DOMICILI
        and comanda.adreca_lliurament.strip()
    ):
        coordenades = geocodifica_text(f"{comanda.adreca_lliurament}, Catalunya, Espanya")

    comanda.latitud_lliurament, comanda.longitud_lliurament = coordenades or (None, None)
    comanda.save(update_fields=["latitud_lliurament", "longitud_lliurament"])
    return coordenades is not None


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
    notificació en digui el nom. Quan passa a "lliurada", també es creen els
    préstecs dels seus llibres (US19).

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
        if nou_estat == Estat.LLIURADA:
            # Dins de la mateixa transacció: si no es poden crear els préstecs,
            # la comanda no queda lliurada.
            crea_prestecs(actual)
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

    Si la comanda ja estava assignada a un repartidor (US14), se li treuen el
    repartidor, el dia i l'hora del lliurament: ja no l'ha de portar ningú
    (US20-T8).
    """
    with transaction.atomic():
        canvia_estat(comanda, Comanda.Estat.CANCELLADA)
        sense_lliurament = {
            "repartidor": None,
            "data_lliurament": None,
            "hora_inici_lliurament": None,
            "hora_fi_lliurament": None,
        }
        Comanda.objects.filter(pk=comanda.pk).update(**sense_lliurament)
        for camp, valor in sense_lliurament.items():
            setattr(comanda, camp, valor)

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


class ParadaJaCompletada(Exception):
    """La parada ja ha estat completada."""

    def __init__(self):
        super().__init__("La parada ja està completada.")


class ParadaEnEstatTerminal(Exception):
    """La parada no es pot completar per estar fallida o cancel·lada."""

    def __init__(self):
        super().__init__("La parada no es pot completar.")


class ParadaAmbComandaInvalida(Exception):
    """La comanda no permet completar aquest lliurament."""

    def __init__(self):
        super().__init__("La comanda no permet completar aquest lliurament.")


class LliuramentSenseRecollida(ParadaAmbComandaInvalida):
    """S'ha intentat completar el lliurament d'una comanda que encara no s'ha recollit."""

    def __init__(self):
        Exception.__init__(
            self, "Primer has de completar la recollida d'aquesta comanda a la biblioteca."
        )


def completa_parada(parada):
    """Completa una parada i canvia l'estat de la comanda en la mateixa transacció.

    Completar la recollida a la biblioteca passa la comanda a "en camí" i
    completar el lliurament la passa a "lliurada" (US13-T10). En tots dos casos
    l'usuari rep la notificació amb el nom del repartidor de la ruta (US8). Si la
    comanda no pot fer aquest canvi, per exemple perquè s'ha cancel·lat o perquè
    encara no s'ha recollit, la parada no es completa.
    """

    from prestecs.models import Parada

    with transaction.atomic():
        parada = (
            Parada.objects.select_for_update()
            .select_related("ruta", "comanda")
            .get(pk=parada.pk)
        )

        if parada.estat == Parada.Estat.COMPLETADA:
            raise ParadaJaCompletada()

        if parada.estat in (
            Parada.Estat.FALLIDA,
            Parada.Estat.CANCELLADA,
        ):
            raise ParadaEnEstatTerminal()

        if parada.tipus == Parada.Tipus.RECOLLIDA:
            nou_estat = Comanda.Estat.EN_CAMI
        else:
            nou_estat = Comanda.Estat.LLIURADA
            if parada.comanda.estat == Comanda.Estat.PREPARADA:
                # Una comanda no pot passar de preparada a lliurada sense sortir de
                # la biblioteca: el repartidor ha de completar abans la recollida.
                raise LliuramentSenseRecollida()
        try:
            canvia_estat(
                parada.comanda,
                nou_estat,
                repartidor=parada.ruta.repartidor,
            )
        except TransicioNoPermesa as error:
            raise ParadaAmbComandaInvalida() from error

        parada.estat = Parada.Estat.COMPLETADA
        parada.completada_el = timezone.now()
        parada.save(update_fields=["estat", "completada_el"])

    return parada

class ParadaFallarJaFallida(Exception):
    def __init__(self, motiu):
        super().__init__("La parada ja està fallida.")
        self.motiu = motiu


class ParadaNoEsPotFallar(Exception):
    """La parada ja està completada o cancel·lada i no es pot marcar com a fallida."""

    def __init__(self):
        super().__init__("La parada no es pot marcar com a fallida.")


def fallar_parada(parada, motiu):
    from prestecs.models import Parada

    with transaction.atomic():
        parada = (
            Parada.objects.select_for_update()
            .select_related("ruta", "comanda")
            .get(pk=parada.pk)
        )

        if parada.estat == Parada.Estat.FALLIDA:
            if parada.motiu == motiu:
                return parada
            raise ParadaFallarJaFallida(parada.motiu)

        if parada.estat in (
            Parada.Estat.COMPLETADA,
            Parada.Estat.CANCELLADA,
        ):
            raise ParadaNoEsPotFallar()

        parada.estat = Parada.Estat.FALLIDA
        parada.motiu = motiu
        parada.save(update_fields=["estat", "motiu"])

        comanda = parada.comanda
        if comanda.estat == Comanda.Estat.EN_CAMI:
            # Ha fallat el lliurament: la comanda torna a la biblioteca (US13-T3).
            canvia_estat(comanda, Comanda.Estat.PREPARADA, des_de=[Comanda.Estat.EN_CAMI])
            torna_a_planificar(comanda, parada)
        elif comanda.estat == Comanda.Estat.PREPARADA:
            # Ha fallat abans de sortir de la biblioteca, per exemple la recollida:
            # la comanda continua preparada, però s'ha de tornar a planificar (US13-T12).
            torna_a_planificar(comanda, parada)

    return parada


def torna_a_planificar(comanda, parada_fallida):
    """Treu la comanda de la ruta on era i la torna a assignar a un repartidor.

    Les altres parades pendents de la comanda es cancel·len, perquè el repartidor
    ja no hi ha d'anar. La comanda es queda sense repartidor ni horari i
    `assigna_comanda` li busca un forat nou, amb les seves parades (US12-T12).
    """
    from prestecs.assignacio import assigna_comanda
    from prestecs.models import Parada

    Parada.objects.filter(comanda=comanda, estat=Parada.Estat.PENDENT).exclude(
        pk=parada_fallida.pk
    ).update(estat=Parada.Estat.CANCELLADA)

    comanda.repartidor = None
    comanda.data_lliurament = None
    comanda.hora_inici_lliurament = None
    comanda.hora_fi_lliurament = None
    comanda.save(
        update_fields=[
            "repartidor",
            "data_lliurament",
            "hora_inici_lliurament",
            "hora_fi_lliurament",
            "actualitzada",
        ]
    )
    assigna_comanda(comanda)
