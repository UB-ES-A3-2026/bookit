# Contracte de l'API: franges de disponibilitat del repartidor (US14)

Acord entre backend i frontend sobre les franges horàries en què un repartidor pot treballar. El backend
l'implementa a US14-T2; el frontend s'hi connecta a US14-T5 i QA en treu els casos de prova. L'assignació de
comandes segons les franges és la US14-T3 i no té endpoint propi. Qualsevol canvi d'aquest document passa per pull
request i s'avisa les dues parts.

## Resum

| Mètode i ruta | Per a què serveix |
|---|---|
| `GET /api/usuaris/repartidor/franges/` | Retorna les franges del repartidor autenticat. |
| `PUT /api/usuaris/repartidor/franges/` | Desa les franges del repartidor i substitueix les que tenia. |

Peticions i respostes en JSON (`Content-Type: application/json`).

## Autenticació i permisos

Tots dos endpoints requereixen la capçalera `Authorization: Bearer <access>` (vegeu `docs/api-auth.md`) i només
els pot fer servir un repartidor actiu amb el perfil validat. Cada repartidor només veu i desa les seves franges.

| Cas | Estat | Resposta |
|---|---|---|
| Sense la capçalera `Authorization`, o amb un token invàlid o caducat | 401 | La de `docs/api-auth.md`. |
| Un usuari, una biblioteca, o un repartidor pendent, rebutjat o desactivat | 403 | `{"detail": "No té permisos per realitzar aquesta acció."}` |

## Franja

Una franja es repeteix cada setmana: per exemple, els dilluns de 9:00 a 13:00. Un repartidor en pot tenir diverses
el mateix dia, sempre que no es trepitgin.

| Camp | Tipus | Descripció |
|---|---|---|
| `id` | enter | Identificador de la franja. Només surt a les respostes. |
| `dia` | enter | Dia de la setmana, del `0` (dilluns) al `6` (diumenge). |
| `hora_inici` | text | Hora d'inici, `HH:MM` en hora local. |
| `hora_fi` | text | Hora de final, `HH:MM` en hora local. Ha de ser posterior a `hora_inici`. |

Dues franges es trepitgen si són del mateix dia i una comença abans que acabi l'altra. Dues franges que només es
toquen (de 9:00 a 13:00 i de 13:00 a 17:00) no es trepitgen.

## Consultar les franges

`GET /api/usuaris/repartidor/franges/`

**200 OK**. Les franges del repartidor, ordenades per dia i hora d'inici. Si no en té cap, `franges` és una llista
buida.

```json
{
  "franges": [
    { "id": 4, "dia": 0, "hora_inici": "09:00", "hora_fi": "13:00" },
    { "id": 5, "dia": 0, "hora_inici": "16:00", "hora_fi": "20:00" },
    { "id": 6, "dia": 4, "hora_inici": "09:00", "hora_fi": "14:30" }
  ]
}
```

## Desar les franges

`PUT /api/usuaris/repartidor/franges/`

El frontend envia sempre l'horari de la setmana sencer, i aquestes franges substitueixen totes les que tenia el
repartidor. Per treure una franja, s'envia la llista sense aquesta franja. Una llista buida vol dir que el
repartidor no està disponible cap dia.

### Petició

```json
{
  "franges": [
    { "dia": 0, "hora_inici": "09:00", "hora_fi": "13:00" },
    { "dia": 4, "hora_inici": "09:00", "hora_fi": "14:30" }
  ]
}
```

### Resposta correcta

**200 OK**. Les franges desades, amb el mateix format que la consulta. Els `id` són nous cada vegada que es desa.

### Errors

**400 Bad Request**. Si hi ha algun error, no es desa res i el repartidor manté les franges que tenia.

Els errors d'una franja concreta van dins de `franges`, en un objecte amb la posició de la franja a la llista
(començant per `"0"`) i els errors agrupats per camp:

```json
{
  "franges": {
    "1": { "hora_fi": ["La franja ha d'acabar després de començar."] }
  }
}
```

| Cas | On surt | Missatge |
|---|---|---|
| `franges` absent o `null` | `franges` | `Aquest camp és obligatori.` |
| `franges` no és una llista | `franges` | `Envia les franges en una llista.` |
| Falta `dia`, `hora_inici` o `hora_fi`, o és `null` | el camp de la franja | `Aquest camp és obligatori.` |
| `dia` no és un número del 0 al 6 | `dia` de la franja | `Tria un dia de la setmana, del 0 (dilluns) al 6 (diumenge).` |
| Una hora no té el format `HH:MM` | el camp de la franja | `Escriu l'hora amb el format HH:MM.` |
| `hora_fi` no és posterior a `hora_inici` | `hora_fi` de la franja | `La franja ha d'acabar després de començar.` |
| Dues franges del mateix dia es trepitgen | `franges` | `Les franges del dilluns de 09:00 a 13:00 i de 12:00 a 14:00 es trepitgen.` |

L'error de franges que es trepitgen només surt quan totes les franges són correctes una per una, i diu les dues
primeres franges que es trepitgen.

## Decisions pendents

- **F1. Format de les franges.** Mentre el Product Owner no ho decideixi, les franges són setmanals (dia de la
  setmana i hores) i no per dates concretes.
