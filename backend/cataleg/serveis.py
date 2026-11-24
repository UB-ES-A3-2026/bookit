import math


RADI_TERRA_KM = 6371.0


def distancia_haversine_km(
    latitud_origen,
    longitud_origen,
    latitud_destinacio,
    longitud_destinacio,
):
    latitud_origen = math.radians(float(latitud_origen))
    longitud_origen = math.radians(float(longitud_origen))
    latitud_destinacio = math.radians(float(latitud_destinacio))
    longitud_destinacio = math.radians(float(longitud_destinacio))

    delta_latitud = latitud_destinacio - latitud_origen
    delta_longitud = longitud_destinacio - longitud_origen
    haversine = (
        math.sin(delta_latitud / 2) ** 2
        + math.cos(latitud_origen)
        * math.cos(latitud_destinacio)
        * math.sin(delta_longitud / 2) ** 2
    )
    haversine = min(1.0, max(0.0, haversine))

    angle_central = 2 * math.atan2(
        math.sqrt(haversine),
        math.sqrt(1 - haversine),
    )
    return RADI_TERRA_KM * angle_central
