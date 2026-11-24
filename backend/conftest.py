from pathlib import Path

import pytest
from django.conf import settings


def pytest_configure():
    """Els tests no executen collectstatic, així que la carpeta dels fitxers estàtics
    no existeix i WhiteNoise avisa a cada petició que no la troba. N'hi ha prou que hi
    sigui, encara que estigui buida (és al .gitignore)."""
    Path(settings.STATIC_ROOT).mkdir(parents=True, exist_ok=True)


@pytest.fixture(autouse=True)
def estatics_sense_manifest(settings):
    """Els tests no executen collectstatic, així que no hi ha el manifest que
    fa servir WhiteNoise en producció. Sense aquest canvi, les pàgines de
    l'admin fallen en buscar-hi els fitxers estàtics."""
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
