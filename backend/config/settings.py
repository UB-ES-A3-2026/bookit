"""Configuració del projecte Django.

Referència: https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from datetime import timedelta
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

# Rutes dins del projecte: BASE_DIR / 'subdirectori'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR.parent / ".env")


# Seguretat: tot es configura amb variables d'entorn i, sense cap variable, s'aplica
# la configuració de producció. En local, DJANGO_DEBUG=True la desactiva.
# Vegeu https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# Mai DEBUG activat en producció.
DEBUG = env.bool("DJANGO_DEBUG", default=False)

# La clau es llegeix de l'entorn; el valor per defecte només serveix en local.
SECRET_KEY = env(
    "DJANGO_SECRET_KEY", default="django-insecure-nomes-per-desenvolupament"
)

# Sense DEBUG, el servidor no arrenca amb una clau curta o d'exemple.
if not DEBUG and (
    len(SECRET_KEY) < 32 or SECRET_KEY.startswith(("canvieu-", "django-insecure-"))
):
    raise ImproperlyConfigured(
        "Cal definir un DJANGO_SECRET_KEY real, de 32 caràcters com a mínim, en "
        "producció. En local, afegiu DJANGO_DEBUG=True al .env."
    )

# En producció no hi ha valor per defecte: sense el domini real no s'accepta cap petició.
ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"] if DEBUG else []
)

# Orígens (el frontend) que poden cridar l'API des del navegador. Es llegeixen del .env;
# sense la variable no se n'accepta cap.
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])

# Orígens de confiança per a les peticions amb CSRF, amb l'esquema inclòs (https://...).
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# HTTPS i cookies segures: actius sempre que DEBUG estigui desactivat.
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=not DEBUG)
SECURE_HSTS_SECONDS = env.int(
    "DJANGO_SECURE_HSTS_SECONDS", default=0 if DEBUG else 3600
)
SESSION_COOKIE_SECURE = env.bool("DJANGO_SESSION_COOKIE_SECURE", default=not DEBUG)
CSRF_COOKIE_SECURE = env.bool("DJANGO_CSRF_COOKIE_SECURE", default=not DEBUG)

# Lax, Strict o None. None permet enviar les cookies entre dominis diferents.
SESSION_COOKIE_SAMESITE = env("DJANGO_COOKIE_SAMESITE", default="Lax")
CSRF_COOKIE_SAMESITE = SESSION_COOKIE_SAMESITE

# Només s'activa darrere d'un proxy que acabi l'HTTPS i controli aquesta capçalera:
# si no, un client podria fer passar una petició HTTP per HTTPS.
if env.bool("DJANGO_PROXY_HTTPS", default=False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

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
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# Tokens JWT: el frontend renova l'accés sol quan caduca i els desa a sessionStorage,
# que es buida en tancar la pestanya. Sense rotació ni llista negra.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "TOKEN_OBTAIN_SERIALIZER": "usuaris.serializers.IniciSessioSerializer",
    "TOKEN_REFRESH_SERIALIZER": "usuaris.serializers.RenovacioTokenSerializer",
}

PASSWORD_RESET_TIMEOUT = env.int("PASSWORD_RESET_TIMEOUT", default=86400)

# Adreça del frontend, sense / al final. Es fa servir per als enllaços dels correus,
# com el de verificació del compte de biblioteca.
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:5173").rstrip("/")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
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
        # En producció (Neon) la connexió ha d'anar xifrada; en local no hi ha SSL.
        "OPTIONS": {
            "sslmode": env(
                "POSTGRES_SSLMODE", default="prefer" if DEBUG else "require"
            ),
        },
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
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Tipus de clau primària per defecte
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
