from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APIClient

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


class CercaLlibresTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usuari = Usuari.objects.create_user(
            email="usuari-cerca@example.com",
            password="Contrasenya segura 123!",
            name="Usuari de cerca",
            address="Carrer Major, 1",
            library_card_number="USR-CERCA-001",
        )
        self.biblioteca = Usuari.objects.create_user(
            email="biblioteca-cerca@example.com",
            password="Contrasenya segura 123!",
            name="Biblioteca de cerca",
            address="Carrer Nou, 2",
            library_card_number="BIB-CERCA-001",
            role=Usuari.Role.BIBLIOTECA,
        )
        self.llibre = Llibre.objects.create(
            titol="La plaça del Diamant",
            autor="Mercè Rodoreda",
            isbn="9788429740011",
            portada="https://example.com/portada.jpg",
        )
        Valoracio.objects.create(
            llibre=self.llibre,
            usuari=self.usuari,
            puntuacio=4,
        )

    def test_cerca_per_titol_autor_i_isbn_sense_distingir_majuscules(self):
        for cerca in ("plaça", "RODOREDA", "9788429740011"):
            resposta = self.client.get("/api/cataleg/llibres/", {"q": cerca})

            self.assertEqual(resposta.status_code, 200)
            self.assertEqual(resposta.data["count"], 1)
            self.assertEqual(resposta.data["results"][0]["id"], self.llibre.id)

    def test_cerca_es_publica_i_no_exigeix_autenticacio(self):
        resposta = self.client.get(
            "/api/cataleg/llibres/",
            {"q": "La plaça"},
        )

        self.assertEqual(resposta.status_code, 200)

    def test_resultat_inclou_disponibilitat_i_valoracions(self):
        ExemplarBiblioteca.objects.create(
            llibre=self.llibre,
            biblioteca=self.biblioteca,
            quantitat=2,
        )

        resposta = self.client.get(
            "/api/cataleg/llibres/",
            {"q": "La plaça"},
        )

        resultat = resposta.data["results"][0]
        self.assertTrue(resultat["disponible"])
        self.assertEqual(resultat["mitjana_valoracions"], 4.0)
        self.assertEqual(resultat["nombre_valoracions"], 1)
        self.assertEqual(resultat["portada"], "https://example.com/portada.jpg")

    def test_resultat_sense_valoracions_te_mitjana_nulla_i_nombre_zero(self):
        llibre = Llibre.objects.create(
            titol="Llibre sense valoracions",
            autor="Autor de prova",
            isbn="9780000000002",
        )

        resposta = self.client.get(
            "/api/cataleg/llibres/",
            {"q": "sense valoracions"},
        )

        resultat = resposta.data["results"][0]
        self.assertEqual(resultat["id"], llibre.id)
        self.assertIsNone(resultat["mitjana_valoracions"])
        self.assertEqual(resultat["nombre_valoracions"], 0)

    def test_resultat_no_disponible_si_no_hi_ha_exemplars(self):
        resposta = self.client.get(
            "/api/cataleg/llibres/",
            {"q": "La plaça"},
        )

        self.assertFalse(resposta.data["results"][0]["disponible"])

    def test_cerca_sense_resultats_retorna_resultats_buits(self):
        resposta = self.client.get(
            "/api/cataleg/llibres/",
            {"q": "Llibre inexistent"},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data["count"], 0)
        self.assertEqual(resposta.data["results"], [])

    def test_cerca_sense_q_no_retorna_tot_el_cataleg(self):
        resposta = self.client.get("/api/cataleg/llibres/")

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data["count"], 0)
        self.assertEqual(resposta.data["results"], [])

    def test_cerca_amb_espais_no_retorna_resultats(self):
        resposta = self.client.get(
            "/api/cataleg/llibres/",
            {"q": "   "},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data["count"], 0)
        self.assertEqual(resposta.data["results"], [])

    def test_cerca_retorna_multiples_resultats_ordenats_per_titol(self):
        Llibre.objects.create(
            titol="Aventures a la plaça",
            autor="Autor de prova",
            isbn="9780000000003",
        )
        Llibre.objects.create(
            titol="Zig-zag a la plaça",
            autor="Autor de prova",
            isbn="9780000000004",
        )

        resposta = self.client.get(
            "/api/cataleg/llibres/",
            {"q": "plaça"},
        )

        self.assertEqual(resposta.data["count"], 3)
        self.assertEqual(
            [resultat["titol"] for resultat in resposta.data["results"]],
            [
                "Aventures a la plaça",
                "La plaça del Diamant",
                "Zig-zag a la plaça",
            ],
        )

    def test_resultats_paginats_i_segona_pagina(self):
        for index in range(20):
            Llibre.objects.create(
                titol=f"Llibre de prova {index:02d}",
                autor="Autor de prova",
                isbn=f"97800000{index:05d}",
            )

        primera_pagina = self.client.get(
            "/api/cataleg/llibres/",
            {"q": "Llibre"},
        )
        segona_pagina = self.client.get(
            "/api/cataleg/llibres/",
            {"q": "Llibre", "page": 2},
        )

        self.assertEqual(primera_pagina.status_code, 200)
        self.assertEqual(primera_pagina.data["count"], 20)
        self.assertEqual(len(primera_pagina.data["results"]), 10)
        self.assertIsNotNone(primera_pagina.data["next"])
        self.assertEqual(segona_pagina.status_code, 200)
        self.assertEqual(len(segona_pagina.data["results"]), 10)
        self.assertIsNone(segona_pagina.data["next"])
        self.assertNotEqual(
            primera_pagina.data["results"][0]["id"],
            segona_pagina.data["results"][0]["id"],
        )
