"""Assignació de les comandes preparades als repartidors (US14-T3).

Una comanda preparada (llesta per a recollida, US15) s'assigna al primer forat
lliure d'un repartidor validat. Cada lliurament ocupa `DURADA_LLIURAMENT_MINUTS`
i ha de cabre sencer dins d'una franja de disponibilitat del repartidor, sense
trepitjar els altres lliuraments que ja té aquell dia.
"""

from datetime import datetime, timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from prestecs.models import Comanda
from usuaris.models import FranjaDisponibilitat, PerfilRepartidor

# Dies, a partir del primer, en què es busca un forat. Amb una setmana es passa
# per tots els dies de la setmana, i per tant per totes les franges.
DIES_A_BUSCAR = 7


def assigna_comanda(comanda, primer_dia=None):
    """Assigna la comanda a un repartidor i li posa el dia i l'hora del lliurament.

    Busca a partir de `primer_dia` (per defecte, demà) el primer dia que algun
    repartidor tingui un forat, i d'aquell dia tria el forat que comença abans.
    Si n'hi ha dos a la mateixa hora, tria el repartidor amb menys lliuraments
    aquell dia.

    Retorna `True` si l'ha assignada. Si la comanda no està preparada, ja té
    repartidor o no hi ha cap forat, no la toca i retorna `False`.
    """
    primer_dia = primer_dia or timezone.localdate() + timedelta(days=1)
    durada = timedelta(minutes=settings.DURADA_LLIURAMENT_MINUTS)

    with transaction.atomic():
        # Bloquejar els repartidors fa que dues assignacions alhora vagin una
        # darrere l'altra i no posin dues comandes al mateix forat.
        repartidors = list(
            PerfilRepartidor.objects.select_for_update(of=("self",))
            .filter(estat=PerfilRepartidor.Estat.VALIDAT, usuari__is_active=True)
            .order_by("pk")
        )
        actual = Comanda.objects.select_for_update().get(pk=comanda.pk)
        if actual.estat != Comanda.Estat.PREPARADA or actual.repartidor_id is not None:
            return False

        for dies in range(DIES_A_BUSCAR):
            dia = primer_dia + timedelta(days=dies)
            forat = millor_forat(repartidors, dia, durada)
            if forat is None:
                continue

            repartidor, inici = forat
            actual.repartidor_id = repartidor.usuari_id
            actual.data_lliurament = dia
            actual.hora_inici_lliurament = inici.time()
            actual.hora_fi_lliurament = (inici + durada).time()
            actual.save(
                update_fields=[
                    "repartidor",
                    "data_lliurament",
                    "hora_inici_lliurament",
                    "hora_fi_lliurament",
                    "actualitzada",
                ]
            )
            for camp in ("repartidor_id", "data_lliurament", "hora_inici_lliurament", "hora_fi_lliurament"):
                setattr(comanda, camp, getattr(actual, camp))
            return True
    return False


def assigna_pendents(primer_dia=None):
    """Prova d'assignar totes les comandes preparades que encara no tenen repartidor.

    Les més antigues van primer. Retorna quantes s'han assignat i quantes no.
    """
    assignades = sense_repartidor = 0
    pendents = Comanda.objects.filter(
        estat=Comanda.Estat.PREPARADA, repartidor__isnull=True
    ).order_by("creada", "id")
    for comanda in pendents:
        if assigna_comanda(comanda, primer_dia):
            assignades += 1
        else:
            sense_repartidor += 1
    return assignades, sense_repartidor


def millor_forat(repartidors, dia, durada):
    """Retorna el repartidor i l'hora d'inici del primer forat del dia, o `None`."""
    franges = {}
    for franja in FranjaDisponibilitat.objects.filter(repartidor__in=repartidors, dia=dia.weekday()):
        franges.setdefault(franja.repartidor_id, []).append(franja)

    ocupats = {}
    lliuraments = (
        Comanda.objects.filter(repartidor__perfil_repartidor__in=repartidors, data_lliurament=dia)
        .exclude(estat=Comanda.Estat.CANCELLADA)
        .exclude(hora_inici_lliurament__isnull=True)
    )
    for comanda in lliuraments:
        ocupats.setdefault(comanda.repartidor_id, []).append(
            (
                datetime.combine(dia, comanda.hora_inici_lliurament),
                datetime.combine(dia, comanda.hora_fi_lliurament),
            )
        )

    candidats = []
    for repartidor in repartidors:
        franges_seves = sorted(franges.get(repartidor.pk, []), key=lambda franja: franja.hora_inici)
        ocupats_seus = sorted(ocupats.get(repartidor.usuari_id, []))
        inici = primer_forat(dia, franges_seves, ocupats_seus, durada)
        if inici is not None:
            candidats.append((inici, len(ocupats_seus), repartidor.pk, repartidor))

    if not candidats:
        return None
    inici, _, _, repartidor = min(candidats, key=lambda candidat: candidat[:3])
    return repartidor, inici


def primer_forat(dia, franges, ocupats, durada):
    """Primera hora del dia en què cap un lliurament sencer dins d'alguna franja.

    `franges` van ordenades per hora d'inici i `ocupats` són els lliuraments que
    el repartidor ja té aquell dia, ordenats, com a parelles (inici, fi).
    """
    for franja in franges:
        inici = datetime.combine(dia, franja.hora_inici)
        for ocupat_inici, ocupat_fi in ocupats:
            if inici + durada <= ocupat_inici:
                break
            if inici < ocupat_fi:
                inici = ocupat_fi
        if franja.cobreix(inici, inici + durada):
            return inici
    return None
