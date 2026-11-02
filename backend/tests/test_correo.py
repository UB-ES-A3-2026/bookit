from django.conf import settings
from django.core import mail
from django.core.mail import send_mail


def test_en_desenvolupament_el_correu_s_envia_a_la_consola():
    assert settings.EMAIL_BACKEND == (
        "django.core.mail.backends.locmem.EmailBackend"
    )


def test_el_correu_de_consola_no_requereix_smtp(capsys):
    send_mail(
        subject="Prova de correu",
        message="Missatge de prova",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=["destinatari@example.test"],
    )

    sortida = capsys.readouterr().out

    assert "Subject: Prova de correu" in sortida
    assert "Missatge de prova" in sortida
    assert len(mail.outbox) == 0
