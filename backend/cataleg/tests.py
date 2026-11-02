from django.db import IntegrityError
from django.test import TestCase

from cataleg.models import ExemplarBiblioteca, Llibre
from usuaris.models import Usuari


class LlibreTests(TestCase):
    def test_crea_un_llibre_i_mostra_el_titol(self):
        llibre = Llibre.objects.create(
            titol="La plaça del Diamant",
            autor="Mercè Rodoreda",
            isbn="9788429740011",
        )

        self.assertEqual(str(llibre), "La plaça del Diamant")
        self.assertEqual(llibre.portada, "")


class ExemplarBibliotecaTests(TestCase):
    def setUp(self):
        self.biblioteca = Usuari.objects.create_user(
            email="biblioteca@example.com",
            password="ContrasenyaSegura123!",
            name="Biblioteca Central",
            address="Carrer Major, 1",
            library_card_number="BIB-001",
            role=Usuari.Role.BIBLIOTECA,
        )
        self.llibre = Llibre.objects.create(
            titol="La plaça del Diamant",
            autor="Mercè Rodoreda",
            isbn="9788429740011",
        )

    def test_guarda_la_quantitat_de_exemplars_per_biblioteca(self):
        exemplars = ExemplarBiblioteca.objects.create(
            llibre=self.llibre,
            biblioteca=self.biblioteca,
            quantitat=3,
        )

        self.assertEqual(exemplars.quantitat, 3)
        self.assertEqual(self.llibre.exemplars.get(), exemplars)
        self.assertEqual(self.biblioteca.exemplars_biblioteca.get(), exemplars)

    def test_no_permet_repetir_un_llibre_a_la_mateixa_biblioteca(self):
        ExemplarBiblioteca.objects.create(
            llibre=self.llibre,
            biblioteca=self.biblioteca,
            quantitat=3,
        )

        with self.assertRaises(IntegrityError):
            ExemplarBiblioteca.objects.create(
                llibre=self.llibre,
                biblioteca=self.biblioteca,
                quantitat=2,
            )
