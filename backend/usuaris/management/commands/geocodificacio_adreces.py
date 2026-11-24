import time

from django.core.management.base import BaseCommand

from usuaris.geocodificacio import geocodifica_adreca
from usuaris.models import Adreca


class Command(BaseCommand):
    help = "Geocodifica les adreces de lliurament."

    def add_arguments(self, parser):
        parser.add_argument(
            "--totes",
            action="store_true",
            help="Recalcula totes les adreces, incloses les que ja tenen coordenades.",
        )

    def handle(self, *args, **options):
        adreces = Adreca.objects.all()

        if not options["totes"]:
            adreces = adreces.filter(
                latitud__isnull=True,
                longitud__isnull=True,
            )

        adreces = adreces.order_by("id")

        processades = 0
        amb_coordenades = 0

        for adreca in adreces.iterator():
            coordenades = geocodifica_adreca(adreca)

            adreca.latitud = None
            adreca.longitud = None

            if coordenades is not None:
                adreca.latitud, adreca.longitud = coordenades
                amb_coordenades += 1

            adreca.save(update_fields=["latitud", "longitud"])
            processades += 1
            time.sleep(1)

        self.stdout.write(
            self.style.SUCCESS(
                f"Adreces processades: {processades}. "
                f"Adreces geocodificades: {amb_coordenades}."
            )
        )
