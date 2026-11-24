"""Ordre per assignar a repartidors les comandes preparades que encara no en tenen (US14)."""

from django.core.management.base import BaseCommand

from prestecs.assignacio import assigna_pendents


class Command(BaseCommand):
    help = "Assigna a un repartidor les comandes preparades que encara no en tenen."

    def handle(self, *args, **options):
        assignades, sense_repartidor = assigna_pendents()
        self.stdout.write(f"Comandes assignades: {assignades}. Sense repartidor disponible: {sense_repartidor}.")
