from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
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
    class TipusLliurament(models.TextChoices):
        # La recollida es fa a la mateixa biblioteca de la comanda (US7).
        DOMICILI = "domicili", "Lliurament a domicili"
        RECOLLIDA = "recollida", "Recollida a la biblioteca"

    tipus_lliurament = models.CharField(
        max_length=9,
        choices=TipusLliurament.choices,
        default=TipusLliurament.DOMICILI,
    )
    # On es porta la comanda. Buida si l'usuari la recull a la biblioteca.
    adreca_lliurament = models.TextField(blank=True, default="")
    # Ubicació de `adreca_lliurament` per al mapa de la ruta (US12-T13). Es
    # geocodifica en confirmar la comanda; queda buida si no s'ha pogut fer.
    latitud_lliurament = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitud_lliurament = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    # En euros. Es desa en confirmar la comanda, perquè no canviï si després
    # canvia la tarifa.
    cost_enviament = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    # La biblioteca ordena les comandes pendents per aquesta data (US10).
    data_lliurament = models.DateField(null=True, blank=True)
    # Qui porta la comanda i a quina hora, dins d'una franja de disponibilitat
    # seva (US14). Es decideix en assignar-la (`prestecs.assignacio`).
    repartidor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        limit_choices_to={"role": "repartidor"},
        on_delete=models.PROTECT,
        related_name="comandes_assignades",
    )
    hora_inici_lliurament = models.TimeField(null=True, blank=True)
    hora_fi_lliurament = models.TimeField(null=True, blank=True)
    creada = models.DateTimeField(auto_now_add=True)
    actualitzada = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creada", "-id"]
        verbose_name_plural = "comandes"

    def __str__(self):
        return f"Comanda {self.pk} de {self.usuari} ({self.get_estat_display()})"

    def pot_passar_a(self, nou_estat):
        """Diu si la comanda pot canviar de l'estat actual a `nou_estat`."""
        if self.tipus_lliurament == self.TipusLliurament.RECOLLIDA and self.estat == self.Estat.PREPARADA:
            # Una comanda de recollida no surt de la biblioteca: la biblioteca la
            # lliura a l'usuari quan la ve a buscar (US7-T8).
            return nou_estat in TRANSICIONS_RECOLLIDA_PREPARADA
        return nou_estat in TRANSICIONS[self.estat]


# Canvis d'estat permesos (US8). Una comanda es pot cancel·lar mentre no surti
# de la biblioteca (US20). Si una parada falla (US13), la comanda torna a
# "preparada" per tornar-la a planificar. Lliurada i cancel·lada són finals.
TRANSICIONS = {
    Comanda.Estat.REBUDA: {Comanda.Estat.PREPARADA, Comanda.Estat.CANCELLADA},
    Comanda.Estat.PREPARADA: {Comanda.Estat.EN_CAMI, Comanda.Estat.CANCELLADA},
    Comanda.Estat.EN_CAMI: {Comanda.Estat.LLIURADA, Comanda.Estat.PREPARADA},
    Comanda.Estat.LLIURADA: set(),
    Comanda.Estat.CANCELLADA: set(),
}
# Una comanda de recollida preparada no passa per "en camí".
TRANSICIONS_RECOLLIDA_PREPARADA = {Comanda.Estat.LLIURADA, Comanda.Estat.CANCELLADA}


class CanviEstat(models.Model):
    """Historial de la comanda: cada estat pel qual passa i quan (US8).

    El primer registre és el de `rebuda`, quan es confirma la comanda.
    """

    comanda = models.ForeignKey(
        Comanda,
        on_delete=models.CASCADE,
        related_name="canvis_estat",
    )
    estat = models.CharField(max_length=10, choices=Comanda.Estat.choices)
    moment = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["moment", "id"]
        verbose_name = "canvi d'estat"
        verbose_name_plural = "canvis d'estat"

    def __str__(self):
        return f"Comanda {self.comanda_id}: {self.get_estat_display()}"


class Notificacio(models.Model):
    """Avís a l'usuari quan la seva comanda canvia d'estat (US8).

    Es crea a cada canvi d'estat, inclosa la confirmació de la comanda. El text
    es desa ja escrit, amb el nom del repartidor si n'hi ha.
    """

    usuari = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notificacions",
    )
    comanda = models.ForeignKey(
        Comanda,
        on_delete=models.CASCADE,
        related_name="notificacions",
    )
    text = models.TextField()
    llegida = models.BooleanField(default=False)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creada", "-id"]
        verbose_name = "notificació"
        verbose_name_plural = "notificacions"

    def __str__(self):
        return f"{self.usuari}: {self.text}"


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

class Ruta(models.Model):
    repartidor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        limit_choices_to={"role": "repartidor"},
        on_delete=models.PROTECT,
        related_name="rutes",
    )
    data = models.DateField()

    class Meta:
        verbose_name = "ruta"
        verbose_name_plural = "rutes"
        constraints = [
            models.UniqueConstraint(
                fields=["repartidor", "data"],
                name="una_ruta_per_repartidor_i_data",
            ),
        ]

    def __str__(self):
        return f"Ruta de {self.repartidor} - {self.data:%d/%m/%Y}"


class Parada(models.Model):
    class Tipus(models.TextChoices):
        RECOLLIDA = "recollida", "Recollida"
        LLIVRAMENT = "lliurament", "Lliurament"

    ruta = models.ForeignKey(
        Ruta,
        on_delete=models.CASCADE,
        related_name="parades",
    )
    comanda = models.ForeignKey(
        Comanda,
        on_delete=models.PROTECT,
        related_name="parades",
    )
    tipus = models.CharField(
        max_length=11,
        choices=Tipus.choices,
    )
    ordre = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["ordre", "id"]
        verbose_name = "parada"
        verbose_name_plural = "parades"
        constraints = [
            models.UniqueConstraint(
                fields=["ruta", "ordre"],
                name="una_parada_per_ordre_i_ruta",
            ),
            models.UniqueConstraint(
                fields=["ruta", "comanda", "tipus"],
                name="una_parada_per_comanda_tipus_i_ruta",
            ),
        ]

    def __str__(self):
        return f"{self.get_tipus_display()} - comanda {self.comanda_id} ({self.ordre})"


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
