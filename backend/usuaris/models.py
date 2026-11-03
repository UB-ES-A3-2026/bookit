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
        password_args = args[:1]
        field_values = args[1] if len(args) > 1 else {}
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields["is_staff"]:
            raise ValueError("Un superusuari ha de tenir is_staff=True.")
        if not extra_fields["is_superuser"]:
            raise ValueError("Un superusuari ha de tenir is_superuser=True.")

        if password_args:
            return self.create_user(email, *password_args, field_values, **extra_fields)
        return self.create_user(email, None, field_values, **extra_fields)


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

class Biblioteca(models.Model):
    usuari = models.OneToOneField(
        Usuari,
        on_delete=models.CASCADE,
        related_name="biblioteca",
    )
    nom = models.CharField(max_length=150)

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.usuari.role = Usuari.Role.BIBLIOTECA
            self.usuari.is_active = False
            self.usuari.save(update_fields=["role", "is_active"])
        return super().save(*args, **kwargs)
