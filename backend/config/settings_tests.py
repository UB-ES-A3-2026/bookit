"""Configuració dels tests: la de settings.py amb una clau fixa.

Els tokens JWT es signen amb el SECRET_KEY. Si depengués del DJANGO_SECRET_KEY del .env
de cadascú, que en local pot ser curt, PyJWT avisaria a cada test que la clau és massa
curta (en recomana 32 bytes com a mínim). Amb una clau fixa, a més, tots els tests
s'executen amb la mateixa configuració a qualsevol màquina i a la CI.
"""

from .settings import *  # noqa: F401, F403

SECRET_KEY = "clau-nomes-per-als-tests-no-serveix-en-produccio"
