import json
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "Biblioteca-a-domicili/1.0"


def geocodifica_adreca(adreca):
    """Retorna una tupla (latitud, longitud), o None si no es pot geocodificar."""

    consulta = (
        f"{adreca.carrer}, {adreca.pis}, "
        f"{adreca.codi_postal} {adreca.municipi}, Catalunya, Espanya"
    )
    return geocodifica_text(consulta)


def geocodifica_text(consulta):
    """Geocodifica una adreça escrita com a text lliure (US12-T13).

    Retorna una tupla (latitud, longitud), o None si el text és buit o no es pot
    geocodificar.
    """

    if not consulta or not consulta.strip():
        return None

    parametres = urlencode(
        {
            "q": consulta,
            "format": "jsonv2",
            "limit": 1,
            "countrycodes": "es",
        }
    )
    peticio = Request(
        f"{NOMINATIM_URL}?{parametres}",
        headers={"User-Agent": USER_AGENT},
    )

    try:
        with urlopen(peticio, timeout=5) as resposta:
            dades = json.loads(resposta.read().decode("utf-8"))
    except (
        HTTPError,
        URLError,
        TimeoutError,
        json.JSONDecodeError,
        UnicodeDecodeError,
    ):
        return None

    if not dades:
        return None

    try:
        latitud = Decimal(str(dades[0]["lat"])).quantize(
            Decimal("0.000001")
        )
        longitud = Decimal(str(dades[0]["lon"])).quantize(
            Decimal("0.000001")
        )
    except (KeyError, InvalidOperation, TypeError):
        return None

    if not -90 <= latitud <= 90:
        return None
    if not -180 <= longitud <= 180:
        return None

    return latitud, longitud
