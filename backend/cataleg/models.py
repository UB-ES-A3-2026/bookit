from django.conf import settings
from django.db import models


class Llibre(models.Model):
    titol = models.CharField(max_length=255)
    autor = models.CharField(max_length=255)
    isbn = models.CharField(max_length=17, unique=True)
    portada = models.URLField(blank=True, default="")

    def __str__(self):
        return self.titol


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
