import pytest


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
