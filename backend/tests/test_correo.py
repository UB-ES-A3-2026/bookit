from contextlib import redirect_stdout
from io import StringIO

from django.conf import settings
from django.core.mail import get_connection, send_mail
from django.test import override_settings


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend"
)
def test_el_backend_de_correu_local_es_de_consola():
    connexio = get_connection()

    assert (
        connexio.__class__.__module__
        == "django.core.mail.backends.console"
    )


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend"
)
def test_el_correu_de_consola_no_requereix_smtp():
    sortida = StringIO()

    with redirect_stdout(sortida):
        resultat = send_mail(
            subject="Prova de correu",
            message="Missatge de prova",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["destinatari@example.test"],
        )

    assert resultat == 1
    assert "Subject: Prova de correu" in sortida.getvalue()
    assert "Missatge de prova" in sortida.getvalue()
