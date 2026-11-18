from django.conf import settings
from django.db import models
from django.utils import timezone

from cataleg.models import Llibre


class Comanda(models.Model):
    """Comanda d'un usuari: un o més llibres d'una biblioteca (US6).

    Cada comanda és d'una sola biblioteca, que és la que la prepara i la veu a la
    seva llista de comandes pendents (US10).
    """

    class Estat(models.TextChoices):
        # Els quatre estats que veu l'usuari (US8) i el de cancel·lació (US20).
        # "Preparada" és l'estat que la biblioteca marca com a "Llesta per a
        # recollida" (US15).
        REBUDA = "rebuda", "Rebuda"
        PREPARADA = "preparada", "Preparada"
        EN_CAMI = "en_cami", "En camí"
        LLIURADA = "lliurada", "Lliurada"
        CANCELLADA = "cancellada", "Cancel·lada"

    usuari = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comandes",
    )
    biblioteca = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        limit_choices_to={"role": "biblioteca"},
        on_delete=models.PROTECT,
        related_name="comandes_biblioteca",
    )
    estat = models.CharField(
        max_length=10,
        choices=Estat.choices,
        default=Estat.REBUDA,
    )
    # La biblioteca ordena les comandes pendents per aquesta data (US10).
    data_lliurament = models.DateField(null=True, blank=True)
    creada = models.DateTimeField(auto_now_add=True)
    actualitzada = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creada", "-id"]
        verbose_name_plural = "comandes"

    def __str__(self):
        return f"Comanda {self.pk} de {self.usuari} ({self.get_estat_display()})"


class LiniaComanda(models.Model):
    """Un llibre d'una comanda. Cada línia correspon a un exemplar."""

    comanda = models.ForeignKey(
        Comanda,
        on_delete=models.CASCADE,
        related_name="linies",
    )
    # PROTECT: un llibre que ha estat en una comanda no es pot esborrar.
    llibre = models.ForeignKey(
        Llibre,
        on_delete=models.PROTECT,
        related_name="linies_comanda",
    )

    class Meta:
        verbose_name = "línia de comanda"
        verbose_name_plural = "línies de comanda"
        constraints = [
            models.UniqueConstraint(
                fields=["comanda", "llibre"],
                name="un_llibre_per_comanda",
            ),
        ]

    def __str__(self):
        return f"{self.llibre} (comanda {self.comanda_id})"


class Prestec(models.Model):
    """Un llibre que l'usuari té en préstec (US19).

    Es crea un préstec per cada línia quan la comanda es lliura. El préstec dura
    fins que l'usuari torna el llibre (`data_devolucio`), i ho ha de fer abans de
    la data límit.
    """

    linia = models.OneToOneField(
        LiniaComanda,
        on_delete=models.PROTECT,
        related_name="prestec",
    )
    usuari = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="prestecs",
    )
    llibre = models.ForeignKey(
        Llibre,
        on_delete=models.PROTECT,
        related_name="prestecs",
    )
    biblioteca = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        limit_choices_to={"role": "biblioteca"},
        on_delete=models.PROTECT,
        related_name="prestecs_biblioteca",
    )
    data_inici = models.DateField()
    data_limit = models.DateField()
    # Buida mentre l'usuari encara té el llibre. La devolució és la US9.
    data_devolucio = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["data_limit", "id"]
        verbose_name = "préstec"
        verbose_name_plural = "préstecs"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(data_limit__gte=models.F("data_inici")),
                name="prestec_acaba_despres_de_comencar",
            ),
        ]

    def __str__(self):
        return f"{self.llibre} a {self.usuari} fins al {self.data_limit:%d/%m/%Y}"

    @property
    def retornat(self):
        return self.data_devolucio is not None

    def termini_superat(self, avui=None):
        """Diu si l'usuari encara té el llibre i ja ha passat la data límit."""
        avui = avui or timezone.localdate()
        return not self.retornat and self.data_limit < avui
