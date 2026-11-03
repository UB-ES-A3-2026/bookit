from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

from usuaris.validacions import (
    valida_dni_nie,
    valida_matricula,
    valida_num_seguretat_social,
    valida_telefon,
)


class GestorUsuari(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El correu electrònic és obligatori.")
        email = self.normalize_email(email)
        usuari = self.model(email=email, **extra_fields)
        usuari.set_password(password)
        usuari.save(using=self._db)
        return usuari

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields["is_staff"]:
            raise ValueError("Un superusuari ha de tenir is_staff=True.")
        if not extra_fields["is_superuser"]:
            raise ValueError("Un superusuari ha de tenir is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


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
