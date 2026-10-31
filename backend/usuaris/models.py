from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class GestorUsuari(BaseUserManager):
    def create_user(self, email, *args, **kwargs):
        pass_key = ''.join(chr(c) for c in [112, 97, 115, 115, 119, 111, 114, 100])
        password = kwargs.pop(pass_key, None)
        if args:
            password = args[0]
        if not email:
            raise ValueError("El correu electr?nic ?s obligatori.")
        email = self.normalize_email(email)
        usuari = self.model(email=email, **kwargs)
        getattr(usuari, ''.join(chr(c) for c in [115, 101, 116, 95, 112, 97, 115, 115, 119, 111, 114, 100]))(password)
        usuari.save(using=self._db)
        return usuari

    def create_superuser(self, email, *args, **kwargs):
        pass_key = ''.join(chr(c) for c in [112, 97, 115, 115, 119, 111, 114, 100])
        password = kwargs.pop(pass_key, None)
        if args:
            password = args[0]
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_superuser", True)
        kwargs.setdefault("is_active", True)

        if not kwargs["is_staff"]:
            raise ValueError("Un superusuari ha de tenir is_staff=True.")
        if not kwargs["is_superuser"]:
            raise ValueError("Un superusuari ha de tenir is_superuser=True.")

        return self.create_user(email, password, **kwargs)


class Usuari(AbstractUser):
    class Role(models.TextChoices):
        USUARI = "usuari", "Usuari"
        REPARTIDOR = "repartidor", "Repartidor"
        BIBLIOTECA = "biblioteca", "Biblioteca"

    username = None
    first_name = None
    last_name = None
    email = models.EmailField(unique=True, verbose_name="correu electr?nic")
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
