# Contracte de l'API: llibres en préstec (US19)

Acord entre backend i frontend sobre els llibres que l'usuari té en préstec. El backend l'implementa a US19-T1 (model)
i US19-T2 (endpoint); el frontend s'hi connecta a la pàgina "Els meus préstecs" (US19-T4) i QA en treu els casos de
prova. Qualsevol canvi d'aquest document passa per pull request i s'avisa les dues parts.

## Resum

| Mètode i ruta | Per a què serveix |
|---|---|
| `GET /api/prestecs/prestecs/` | Llista els llibres que l'usuari té en préstec. |

Respostes en JSON.

## Autenticació i permisos

Requereix la capçalera `Authorization: Bearer <access>` (vegeu `docs/api-auth.md`) i un usuari actiu amb el rol
`usuari`. Cada usuari només veu els seus préstecs.

| Cas | Estat | Resposta |
|---|---|---|
| Sense la capçalera `Authorization`, o amb un token invàlid o caducat | 401 | La de `docs/api-auth.md`. |
| Una biblioteca, un repartidor o un usuari desactivat | 403 | `{"detail": "No té permisos per realitzar aquesta acció."}` |

## Quan hi ha un préstec

Quan una comanda es lliura, es crea un préstec per cada llibre de la comanda. El préstec comença el dia del
lliurament i la data límit és 30 dies després (decisió D1). Quan l'usuari torna el llibre (US9), el préstec deixa de
sortir a la llista.

Els préstecs es creen quan la comanda passa a `lliurada`, dins de `canvia_estat` (US8) i en la mateixa transacció
que el canvi d'estat (US19-T9). Si no es poden crear, la comanda no queda lliurada. Per això no importa qui marqui el
lliurament (la parada completada de la US13 o qualsevol altre camí): sempre hi haurà els préstecs. Cap altre canvi
d'estat en crea.

## Els meus préstecs

`GET /api/prestecs/prestecs/`

**200 OK**. Una llista amb els llibres que l'usuari encara no ha tornat, ordenats per data límit, del més proper al
més llunyà. Si dos préstecs tenen la mateixa data límit, surt primer el més antic. Si l'usuari no té cap llibre en préstec, la
llista és buida i el frontend mostra "No tens cap llibre en préstec".

| Camp | Tipus | Descripció |
|---|---|---|
| `id` | enter | Identificador del préstec. Servirà per programar-ne la devolució (US9). |
| `llibre` | objecte | `id`, `titol`, `autor` i `portada` (`""` si no en té). |
| `biblioteca` | objecte | La biblioteca a la qual pertany el llibre: `id` i `nom`. |
| `data_inici` | text | Dia en què es va lliurar el llibre (`AAAA-MM-DD`). |
| `data_limit` | text | Últim dia per tornar el llibre (`AAAA-MM-DD`). |
| `termini_superat` | booleà | `true` si avui ja ha passat la data límit. El mateix dia de la data límit encara és `false`. |

Quan `termini_superat` és `true`, el frontend destaca el llibre amb l'avís "Termini de devolució superat". El
backend no retorna aquest text perquè és part de la pantalla.

```json
[
  {
    "id": 21,
    "llibre": {
      "id": 7,
      "titol": "La plaça del Diamant",
      "autor": "Mercè Rodoreda",
      "portada": "https://example.com/portades/placa.jpg"
    },
    "biblioteca": { "id": 3, "nom": "Biblioteca Montbau" },
    "data_inici": "2026-10-10",
    "data_limit": "2026-11-09",
    "termini_superat": true
  },
  {
    "id": 22,
    "llibre": { "id": 9, "titol": "Solitud", "autor": "Víctor Català", "portada": "" },
    "biblioteca": { "id": 3, "nom": "Biblioteca Montbau" },
    "data_inici": "2026-11-18",
    "data_limit": "2026-12-18",
    "termini_superat": false
  }
]
```

La llista no està paginada: un usuari no tindrà mai gaires llibres en préstec alhora.

## Decisions pendents

- **D1. Durada del préstec.** Mentre el Product Owner no ho decideixi, un préstec dura 30 dies des del lliurament,
  configurable amb la variable d'entorn `DURADA_PRESTEC_DIES`.
- **D2. Programar la devolució.** La US9 no és en aquest sprint. Mentre no es faci, el frontend pot mostrar el botó
  desactivat o no mostrar-lo.
