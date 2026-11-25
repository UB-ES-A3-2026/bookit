import time

from django.core.management.base import BaseCommand

from prestecs.models import Comanda
from prestecs.serveis import desa_coordenades_lliurament

# Les comandes lliurades o cancel·lades ja no surten a cap ruta.
ESTATS_PENDENTS = (
    Comanda.Estat.REBUDA,
    Comanda.Estat.PREPARADA,
    Comanda.Estat.EN_CAMI,
)


class Command(BaseCommand):
    help = (
        "Geocodifica l'adreça de lliurament de les comandes a domicili pendents "
        "que encara no tenen coordenades (US12-T13)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--pausa",
            type=float,
            default=1.0,
            help="Segons d'espera entre peticions al geocodificador (per defecte, 1).",
        )

    def handle(self, *args, **options):
        comandes = (
            Comanda.objects.filter(
                tipus_lliurament=Comanda.TipusLliurament.DOMICILI,
                estat__in=ESTATS_PENDENTS,
                latitud_lliurament__isnull=True,
            )
            .exclude(adreca_lliurament="")
            .order_by("id")
        )

        processades = 0
        amb_coordenades = 0
        for comanda in comandes.iterator():
            if processades and options["pausa"]:
                time.sleep(options["pausa"])
            if desa_coordenades_lliurament(comanda):
                amb_coordenades += 1
            processades += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Comandes processades: {processades}. "
                f"Comandes geocodificades: {amb_coordenades}."
            )
        )
