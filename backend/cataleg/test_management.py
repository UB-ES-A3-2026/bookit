from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from cataleg.models import ExemplarBiblioteca, Llibre, Valoracio
from usuaris.models import Usuari


class CarregaDadesExempleTests(TestCase):
    def test_carrega_biblioteques_llibres_exemplars_i_valoracions(self):
        sortida = StringIO()

        call_command("carrega_dades_exemple", stdout=sortida)

        self.assertEqual(Usuari.objects.filter(role=Usuari.Role.BIBLIOTECA).count(), 2)
        self.assertEqual(
            Usuari.objects.filter(role=Usuari.Role.USUARI).count(),
            2,
        )
        self.assertEqual(Llibre.objects.count(), 4)
        self.assertEqual(ExemplarBiblioteca.objects.count(), 5)
        self.assertEqual(Valoracio.objects.count(), 4)
        self.assertIn("Dades d'exemple carregades", sortida.getvalue())

    def test_la_carrega_es_idempotent(self):
        call_command("carrega_dades_exemple")
        call_command("carrega_dades_exemple")

        self.assertEqual(Llibre.objects.count(), 4)
        self.assertEqual(ExemplarBiblioteca.objects.count(), 5)
        self.assertEqual(Valoracio.objects.count(), 4)
