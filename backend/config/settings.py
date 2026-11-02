"""Configuració del projecte Django.

Referència: https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

import environ

# Rutes dins del projecte: BASE_DIR / 'subdirectori'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR.parent / ".env")


# Seguretat: valors per a desenvolupament, configurables amb variables d'entorn.
# Vegeu https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# La clau es llegeix de l'entorn; el valor per defecte només serveix en local.
SECRET_KEY = env(
    "DJANGO_SECRET_KEY", default="django-insecure-nomes-per-desenvolupament"
)

# Mai DEBUG activat en producció.
DEBUG = env.bool("DJANGO_DEBUG", default=True)

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Orígens (el frontend) que poden cridar l'API des del navegador. Es llegeixen del .env;
# sense la variable no se n'accepta cap.
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])

# Correu electrònic
# En desenvolupament els missatges es mostren a la consola.
# En producció es requereix una configuració SMTP completa.
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@localhost")
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = env("EMAIL_HOST", default="")
    EMAIL_PORT = env.int("EMAIL_PORT", default=587)
    EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
    EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
    EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
    DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="")

    if not EMAIL_HOST:
        raise ImproperlyConfigured(
            "Cal definir EMAIL_HOST en producció."
        )

    if not DEFAULT_FROM_EMAIL:
        raise ImproperlyConfigured(
            "Cal definir DEFAULT_FROM_EMAIL en producció."
        )

    if EMAIL_USE_TLS and EMAIL_USE_SSL:
        raise ImproperlyConfigured(
            "EMAIL_USE_TLS i EMAIL_USE_SSL no es poden activar alhora."
        )


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
    "corsheaders",
    # Mòduls del projecte
    "usuaris",
    "cataleg",
    "prestecs",
]

AUTH_USER_MODEL = "usuaris.Usuari"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@bookit.local")
PASSWORD_RESET_TIMEOUT = env.int("PASSWORD_RESET_TIMEOUT", default=86400)

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Abans del CommonMiddleware, perquè les respostes que genera també portin les capçaleres CORS.
    "corsheaders.middleware.CorsMiddleware",
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
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="biblioteca"),
        "USER": env("POSTGRES_USER", default="biblioteca"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST", default="127.0.0.1"),
        "PORT": env("POSTGRES_PORT", default="5432"),
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
