from django.conf import settings
from django.core.mail import send_mail


def test_en_desenvolupament_el_correu_s_envia_a_la_consola():
    assert settings.EMAIL_BACKEND == (
        "django.core.mail.backends.console.EmailBackend"
    )


def test_el_correu_de_consola_no_requereix_smtp():
    resultat = send_mail(
        subject="Prova de correu",
        message="Missatge de prova",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=["destinatari@example.test"],
    )

    assert resultat == 1  # El correu s'ha enviat correctament a la consola
