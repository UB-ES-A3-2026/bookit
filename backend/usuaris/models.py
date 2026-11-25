from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from usuaris.validacions import (
    valida_codi_postal_zona,
    valida_dni_nie,
    valida_matricula,
    valida_num_seguretat_social,
    valida_telefon,
)


class GestorUsuari(BaseUserManager):
    def create_user(self, email, *args, **extra_fields):
        secret = args[0] if args else extra_fields.pop("password", None)
        field_values = args[1] if len(args) > 1 else {}
        if not email:
            raise ValueError("El correu electrònic és obligatori.")
        email = self.normalize_email(email)
        usuari = self.model(email=email, **field_values, **extra_fields)
        usuari.set_password(secret)
        usuari.save(using=self._db)
        return usuari

    def create_superuser(self, email, *args, **extra_fields):
        # La contrasenya pot arribar com a primer argument o amb el nom, que és com
        # la passa l'ordre createsuperuser de Django.
        secret = args[0] if args else extra_fields.pop("password", None)
        field_values = args[1] if len(args) > 1 else {}
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields["is_staff"]:
            raise ValueError("Un superusuari ha de tenir is_staff=True.")
        if not extra_fields["is_superuser"]:
            raise ValueError("Un superusuari ha de tenir is_superuser=True.")

        return self.create_user(email, secret, field_values, **extra_fields)


class Usuari(AbstractUser):
    class Role(models.TextChoices):
        USUARI = "usuari", "Usuari"
        REPARTIDOR = "repartidor", "Repartidor"
        BIBLIOTECA = "biblioteca", "Biblioteca"

    username = None
    first_name = None
    last_name = None
    email = models.EmailField(unique=True, verbose_name="correu electrònic")
    name = models.CharField(max_length=150)
    address = models.TextField()
    library_card_number = models.TextField(unique=True)
    objects = GestorUsuari()

    role = models.CharField(
        max_length=12,
        choices=Role.choices,
        default=Role.USUARI,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "address", "library_card_number"]

    def __str__(self):
        return self.name


class Biblioteca(models.Model):
    usuari = models.OneToOneField(
        Usuari,
        on_delete=models.CASCADE,
        related_name="biblioteca",
    )
    nom = models.CharField(max_length=150)
    carrer = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )
    numero_porta = models.CharField(
        max_length=20,
        blank=True,
        default="",
    )
    latitud = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(-90),
            MaxValueValidator(90),
        ],
    )
    longitud = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(-180),
            MaxValueValidator(180),
        ],
    )

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.usuari.role = Usuari.Role.BIBLIOTECA
            self.usuari.is_active = False
            self.usuari.save(update_fields=["role", "is_active"])
        return super().save(*args, **kwargs)


class PerfilRepartidor(models.Model):
    class Vehicle(models.TextChoices):
        BICI = "bici", "Bici"
        MOTO = "moto", "Moto"
        COTXE = "cotxe", "Cotxe"

    class Estat(models.TextChoices):
        PENDENT = "pendent", "Pendent de validació"
        VALIDAT = "validat", "Validat"
        REBUTJAT = "rebutjat", "Rebutjat"

    usuari = models.OneToOneField(
        Usuari,
        on_delete=models.CASCADE,
        related_name="perfil_repartidor",
    )
    cognoms = models.CharField(max_length=150)
    dni = models.CharField(max_length=9, unique=True, validators=[valida_dni_nie])
    telefon = models.CharField(max_length=12, validators=[valida_telefon])
    vehicle = models.CharField(max_length=5, choices=Vehicle.choices)
    matricula = models.CharField(
        max_length=7,
        blank=True,
        default="",
        validators=[valida_matricula],
    )
    num_seguretat_social = models.CharField(
        max_length=12,
        validators=[valida_num_seguretat_social],
    )
    estat = models.CharField(
        max_length=8,
        choices=Estat.choices,
        default=Estat.PENDENT,
    )

    def __str__(self):
        return f"{self.usuari} {self.cognoms}"


class FranjaDisponibilitat(models.Model):
    """Franja horària setmanal en què un repartidor pot treballar (US14).

    Es repeteix cada setmana: per exemple, els dilluns de 9:00 a 13:00. Un
    repartidor en pot tenir diverses el mateix dia, sempre que no es trepitgin.
    """

    class Dia(models.IntegerChoices):
        # Els mateixos números que `date.weekday()`: el dilluns és 0.
        DILLUNS = 0, "Dilluns"
        DIMARTS = 1, "Dimarts"
        DIMECRES = 2, "Dimecres"
        DIJOUS = 3, "Dijous"
        DIVENDRES = 4, "Divendres"
        DISSABTE = 5, "Dissabte"
        DIUMENGE = 6, "Diumenge"

    repartidor = models.ForeignKey(
        PerfilRepartidor,
        on_delete=models.CASCADE,
        related_name="franges",
    )
    dia = models.PositiveSmallIntegerField(choices=Dia.choices)
    hora_inici = models.TimeField()
    hora_fi = models.TimeField()

    class Meta:
        ordering = ["dia", "hora_inici"]
        verbose_name = "franja de disponibilitat"
        verbose_name_plural = "franges de disponibilitat"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(hora_fi__gt=models.F("hora_inici")),
                name="franja_acaba_despres_de_comencar",
            ),
        ]

    def __str__(self):
        return (
            f"{self.get_dia_display()} de {self.hora_inici:%H:%M} "
            f"a {self.hora_fi:%H:%M}"
        )

    def clean(self):
        """Comprova que la franja acabi després de començar i no se'n trepitgi cap altra."""
        if self.hora_inici is None or self.hora_fi is None:
            return
        if self.hora_fi <= self.hora_inici:
            raise ValidationError(
                {"hora_fi": "La franja ha d'acabar després de començar."}
            )

        trepitjades = FranjaDisponibilitat.objects.filter(
            repartidor_id=self.repartidor_id,
            dia=self.dia,
            hora_inici__lt=self.hora_fi,
            hora_fi__gt=self.hora_inici,
        ).exclude(pk=self.pk)
        if trepitjades.exists():
            raise ValidationError(
                "Aquesta franja es trepitja amb una altra del mateix dia."
            )

    def cobreix(self, inici, fi):
        """Diu si un lliurament d'`inici` a `fi` cap sencer dins de la franja.

        Serveix per assignar només comandes que s'ajustin estrictament a la
        disponibilitat del repartidor (US14-T3). `inici` i `fi` són dates i hores
        del mateix dia en hora local (`timezone.localtime`), perquè les franges són
        hores de rellotge i no UTC.
        """
        return (
            inici.weekday() == self.dia
            and fi.date() == inici.date()
            and self.hora_inici <= inici.time()
            and fi.time() <= self.hora_fi
        )


class Adreca(models.Model):
    usuari = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="adreces",
    )
    municipi = models.CharField(max_length=100, verbose_name="municipi")
    carrer = models.CharField(max_length=255, verbose_name="carrer")
    pis = models.CharField(max_length=20, verbose_name="pis")
    codi_postal = models.CharField(max_length=5, verbose_name="codi postal", validators=[valida_codi_postal_zona])
    latitud = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(-90),
            MaxValueValidator(90),
        ],
    )
    longitud = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(-180),
            MaxValueValidator(180),
        ],
    )
    predeterminada = models.BooleanField(
        default=False,
        verbose_name="predeterminada",
    )

    class Meta:
        verbose_name = "adreça"
        verbose_name_plural = "adreces"
        constraints = [
            models.UniqueConstraint(
                fields=["usuari"],
                condition=models.Q(predeterminada=True),
                name="una_adreca_predeterminada_per_usuari",
            ),
        ]

    def __str__(self):
        return f"{self.carrer}, pis {self.pis}, {self.municipi}"

