from django.core.management.base import BaseCommand
from django.db import transaction

from cataleg.models import ExemplarBiblioteca, Llibre, Valoracio
from usuaris.models import Usuari


class Command(BaseCommand):
    help = "Carrega dades d'exemple del catàleg per a l'entorn local i la demo."

    biblioteques = [
        {
            "email": "biblioteca-central@exemple.cat",
            "name": "Biblioteca Central",
            "address": "Plaça de la Vila, 1, Girona",
            "library_card_number": "BIB-EXEMPLE-001",
        },
        {
            "email": "biblioteca-nord@exemple.cat",
            "name": "Biblioteca del Nord",
            "address": "Carrer de la Marina, 12, Girona",
            "library_card_number": "BIB-EXEMPLE-002",
        },
    ]

    usuaris = [
        {
            "email": "anna.exemple@exemple.cat",
            "name": "Anna Exemple",
            "address": "Carrer Nou, 5, Girona",
            "library_card_number": "USR-EXEMPLE-001",
        },
        {
            "email": "pere.exemple@exemple.cat",
            "name": "Pere Exemple",
            "address": "Carrer Major, 8, Girona",
            "library_card_number": "USR-EXEMPLE-002",
        },
    ]

    llibres = [
        {
            "isbn": "9788429740011",
            "titol": "La plaça del Diamant",
            "autor": "Mercè Rodoreda",
            "portada": "https://covers.openlibrary.org/b/isbn/9788429740011-L.jpg",
        },
        {
            "isbn": "9788499302515",
            "titol": "La pell freda",
            "autor": "Albert Sánchez Piñol",
            "portada": "https://covers.openlibrary.org/b/isbn/9788499302515-L.jpg",
        },
        {
            "isbn": "9788417423139",
            "titol": "Canto jo i la muntanya balla",
            "autor": "Irene Solà",
            "portada": "https://covers.openlibrary.org/b/isbn/9788417423139-L.jpg",
        },
        {
            "isbn": "9788496863153",
            "titol": "Mecanoscrit del segon origen",
            "autor": "Manuel de Pedrolo",
            "portada": "https://covers.openlibrary.org/b/isbn/9788496863153-L.jpg",
        },
    ]

    valoracions = [
        ("9788429740011", "anna.exemple@exemple.cat", 5),
        ("9788429740011", "pere.exemple@exemple.cat", 4),
        ("9788499302515", "anna.exemple@exemple.cat", 4),
        ("9788417423139", "pere.exemple@exemple.cat", 5),
    ]

    exemplars = [
        ("9788429740011", "BIB-EXEMPLE-001", 3),
        ("9788429740011", "BIB-EXEMPLE-002", 1),
        ("9788499302515", "BIB-EXEMPLE-001", 2),
        ("9788417423139", "BIB-EXEMPLE-002", 0),
        ("9788496863153", "BIB-EXEMPLE-001", 1),
    ]

    @transaction.atomic
    def handle(self, *args, **options):
        biblioteques = {
            dades["library_card_number"]: self._crea_usuari(
                dades,
                Usuari.Role.BIBLIOTECA,
            )
            for dades in self.biblioteques
        }
        usuaris = {
            dades["email"]: self._crea_usuari(dades, Usuari.Role.USUARI)
            for dades in self.usuaris
        }
        llibres = {
            dades["isbn"]: Llibre.objects.update_or_create(
                isbn=dades["isbn"],
                defaults=dades,
            )[0]
            for dades in self.llibres
        }

        for isbn, carnet, quantitat in self.exemplars:
            ExemplarBiblioteca.objects.update_or_create(
                llibre=llibres[isbn],
                biblioteca=biblioteques[carnet],
                defaults={"quantitat": quantitat},
            )

        for isbn, email, puntuacio in self.valoracions:
            Valoracio.objects.update_or_create(
                llibre=llibres[isbn],
                usuari=usuaris[email],
                defaults={"puntuacio": puntuacio},
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Dades d'exemple carregades: "
                f"{len(llibres)} llibres, "
                f"{len(self.exemplars)} exemplars i "
                f"{len(self.valoracions)} valoracions."
            )
        )

    @staticmethod
    def _crea_usuari(dades, role):
        usuari, creat = Usuari.objects.get_or_create(
            email=dades["email"],
            defaults={
                **dades,
                "role": role,
            },
        )
        if creat:
            usuari.set_password("DadesExemple123!")
            usuari.save(update_fields=["password"])
        elif usuari.role != role:
            usuari.role = role
            usuari.save(update_fields=["role"])
        return usuari
