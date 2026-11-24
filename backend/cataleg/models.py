from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg

from cataleg.validacions import PORTADA_MAX_LENGTH, valida_portada


class Llibre(models.Model):
    titol = models.CharField(max_length=255)
    autor = models.CharField(max_length=255)
    isbn = models.CharField(max_length=17, unique=True)
    portada = models.CharField(
        max_length=PORTADA_MAX_LENGTH,
        blank=True,
        default="",
        validators=[valida_portada],
    )

    def __str__(self):
        return self.titol

    @property
    def mitjana_valoracions(self):
        return self.valoracions.aggregate(mitjana=Avg("puntuacio"))["mitjana"]

    @property
    def nombre_valoracions(self):
        return self.valoracions.count()


class Valoracio(models.Model):
    llibre = models.ForeignKey(
        Llibre,
        on_delete=models.CASCADE,
        related_name="valoracions",
    )
    usuari = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="valoracions",
    )
    puntuacio = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["llibre", "usuari"],
                name="una_valoracio_per_usuari_i_llibre",
            ),
            models.CheckConstraint(
                condition=models.Q(puntuacio__gte=1, puntuacio__lte=5),
                name="puntuacio_valoracio_entre_1_i_5",
            ),
        ]

    def __str__(self):
        return f"{self.usuari} - {self.llibre}: {self.puntuacio}"


class ExemplarBiblioteca(models.Model):
    llibre = models.ForeignKey(
        Llibre,
        on_delete=models.CASCADE,
        related_name="exemplars",
    )
    biblioteca = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        limit_choices_to={"role": "biblioteca"},
        on_delete=models.CASCADE,
        related_name="exemplars_biblioteca",
    )
    quantitat = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["llibre", "biblioteca"],
                name="un_llibre_per_biblioteca",
            ),
        ]

    def __str__(self):
        return f"{self.llibre} - {self.biblioteca}"
