"""Configuració del projecte Django.

Referència: https://docs.djangoproject.com/en/5.2/ref/settings/
"""

import os
from pathlib import Path

# Rutes dins del projecte: BASE_DIR / 'subdirectori'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Seguretat: valors per a desenvolupament, configurables amb variables d'entorn.
# Vegeu https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# La clau es llegeix de l'entorn; el valor per defecte només serveix en local.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "django-insecure-nomes-per-desenvolupament"
)

# Mai DEBUG activat en producció.
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

ALLOWED_HOSTS = os.environ.get(
    "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1"
).split(",")


# Aplicacions

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Tercers
    "rest_framework",
    # Mòduls del projecte
    "usuaris",
    "cataleg",
    "prestecs",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Base de dades
# Provisional: C7 la substituirà per PostgreSQL llegint les credencials del .env.
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Validació de contrasenyes
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internacionalització
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "ca"

TIME_ZONE = "Europe/Madrid"

USE_I18N = True

USE_TZ = True


# Fitxers estàtics (CSS, JavaScript, imatges)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"

# Tipus de clau primària per defecte
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
