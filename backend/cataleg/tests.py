from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from cataleg.models import ExemplarBiblioteca, Llibre, Valoracio
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


class ValoracioTests(TestCase):
    def setUp(self):
        self.usuari = Usuari.objects.create_user(
            email="usuari@example.com",
            name="Usuari de prova",
            address="Carrer Major, 1",
            library_card_number="USR-001",
        )
        self.altre_usuari = Usuari.objects.create_user(
            email="altre@example.com",
            name="Altre usuari",
            address="Carrer Nou, 2",
            library_card_number="USR-002",
        )
        self.llibre = Llibre.objects.create(
            titol="La plaça del Diamant",
            autor="Mercè Rodoreda",
            isbn="9788429740011",
        )

    def test_guarda_una_valoracio_i_calcula_la_mitjana_i_el_nombre(self):
        Valoracio.objects.create(llibre=self.llibre, usuari=self.usuari, puntuacio=4)
        Valoracio.objects.create(
            llibre=self.llibre,
            usuari=self.altre_usuari,
            puntuacio=2,
        )

        self.assertEqual(self.llibre.mitjana_valoracions, 3)
        self.assertEqual(self.llibre.nombre_valoracions, 2)

    def test_no_permet_mes_duna_valoracio_del_mateix_usuari(self):
        Valoracio.objects.create(llibre=self.llibre, usuari=self.usuari, puntuacio=4)

        with self.assertRaises(IntegrityError):
            Valoracio.objects.create(
                llibre=self.llibre,
                usuari=self.usuari,
                puntuacio=5,
            )

    def test_la_puntuacio_ha_estat_entre_u_i_cinc(self):
        valoracio = Valoracio(
            llibre=self.llibre,
            usuari=self.usuari,
            puntuacio=6,
        )

        with self.assertRaises(ValidationError):
            valoracio.full_clean()
