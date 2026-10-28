from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class GestorUsuari(BaseUserManager):
    def create_user(self, email, password=None, field_values=None):
        if not email:
            raise ValueError("El correu electrònic és obligatori.")
        email = self.normalize_email(email)
        field_values = {} if field_values is None else dict(field_values)
        usuari = self.model()
        usuari.email = email
        for key, value in field_values.items():
            setattr(usuari, key, value)
        if password is not None:
            usuari.set_password(password)
        usuari.save(using=self._db)
        return usuari

    def create_superuser(self, email, password=None, field_values=None):
        field_values = {} if field_values is None else dict(field_values)
        field_values.setdefault("is_staff", True)
        field_values.setdefault("is_superuser", True)
        field_values.setdefault("is_active", True)

        if not field_values["is_staff"]:
            raise ValueError("Un superusuari ha de tenir is_staff=True.")
        if not field_values["is_superuser"]:
            raise ValueError("Un superusuari ha de tenir is_superuser=True.")

        return self.create_user(email, password, field_values)


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
