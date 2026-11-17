# Contracte de l'API: comandes (US6)

Acord entre backend i frontend sobre les comandes de llibres. El backend l'implementa a US6-T2 (crear la comanda),
US6-T3 (reservar els exemplars) i US6-T4 (tests); el frontend s'hi connecta a US6-T6 i US6-T7 i QA en treu els casos
de prova a US6-T9. Qualsevol canvi d'aquest document passa per pull request i s'avisa les dues parts.

**Estat**: esborrany. Les decisions pendents del Product Owner són al final del document.

Aquest document és la base de les comandes. Les US7 (tipus de lliurament), US8 (estat i notificacions), US10
(comandes de la biblioteca), US15 (comanda llesta) i US20 (cancel·lar) hi afegeixen els seus endpoints quan es facin.

## Resum

| Mètode i ruta | Per a què serveix | Es defineix a |
|---|---|---|
| `POST /api/prestecs/comandes/` | Confirma una comanda amb un o més llibres. | US6 (aquest document) |
| `GET /api/prestecs/comandes/` | Llista les comandes de l'usuari amb el seu estat. | US8-T3 |
| `POST /api/prestecs/comandes/<id>/cancellar/` | Cancel·la una comanda que encara no ha sortit. | US20-T1 |
| `GET /api/prestecs/biblioteca/comandes/` | Llista les comandes pendents de la biblioteca. | US10 (aquest document) |
| `POST /api/prestecs/biblioteca/comandes/<id>/preparada/` | Marca una comanda com a llesta per a recollida. | US15-T1 |
| `GET /api/prestecs/notificacions/` | Llista les notificacions de l'usuari. | US8-T3 |

Peticions i respostes en JSON (`Content-Type: application/json`). Les rutes que es defineixen en altres tasques poden
canviar fins que la tasca les especifiqui en aquest document.

## Autenticació i permisos

Tots els endpoints requereixen la capçalera `Authorization: Bearer <access>` (vegeu `docs/api-auth.md`).

| Cas | Estat | Resposta |
|---|---|---|
| Sense la capçalera `Authorization`, o amb un token invàlid o caducat | 401 | La de `docs/api-auth.md`. |
| Crear una comanda amb un usuari que no té el rol `usuari` (biblioteca o repartidor) | 403 | `{"detail": "No té permisos per realitzar aquesta acció."}` |
| Consultar les comandes de la biblioteca sense ser una biblioteca activa | 403 | `{"detail": "No té permisos per realitzar aquesta acció."}` |

## Estats de la comanda

| Valor | Text per a l'usuari | Quan hi passa |
|---|---|---|
| `rebuda` | Rebuda | En confirmar la comanda. És l'estat inicial. |
| `preparada` | Preparada | Quan la biblioteca la marca com a "Llesta per a recollida" (US15). |
| `en_cami` | En camí | Quan el repartidor la recull a la biblioteca (US12 i US13). |
| `lliurada` | Lliurada | Quan el repartidor marca el lliurament com a completat (US13). |
| `cancellada` | Cancel·lada | Quan l'usuari la cancel·la abans que surti (US20). |

Els canvis d'estat permesos i les notificacions que generen es defineixen a la US8.

## Comanda

Totes les respostes amb una comanda fan servir aquest format.

| Camp | Tipus | Descripció |
|---|---|---|
| `id` | enter | Identificador de la comanda. |
| `estat` | text | Un dels valors de [Estats de la comanda](#estats-de-la-comanda). |
| `biblioteca` | objecte | La biblioteca que prepara la comanda: `id` i `nom`. |
| `llibres` | llista | Els llibres de la comanda: `id`, `titol`, `autor` i `portada` (`""` si no en té). |
| `data_lliurament` | text o `null` | Data prevista de lliurament (`AAAA-MM-DD`). És `null` fins que es planifica. |
| `creada` | text | Data i hora en què es va confirmar (ISO 8601). |

```json
{
  "id": 12,
  "estat": "rebuda",
  "biblioteca": { "id": 3, "nom": "Biblioteca Montbau" },
  "llibres": [
    {
      "id": 7,
      "titol": "La plaça del Diamant",
      "autor": "Mercè Rodoreda",
      "portada": "https://example.com/portades/placa.jpg"
    },
    { "id": 9, "titol": "Solitud", "autor": "Víctor Català", "portada": "" }
  ],
  "data_lliurament": null,
  "creada": "2026-11-16T16:20:00Z"
}
```

La US7 hi afegirà el tipus de lliurament i el cost d'enviament.

## Confirmar una comanda

`POST /api/prestecs/comandes/`

La llista de llibres que l'usuari va afegint la guarda el frontend. Quan l'usuari confirma la comanda, el frontend
l'envia sencera amb aquesta petició, i és llavors quan es comprova l'estoc i es reserven els exemplars.

Les biblioteques que tenen cada llibre en estoc les dona l'endpoint de la US5.

### Petició

| Camp | Tipus | Obligatori | Validació |
|---|---|---|---|
| `biblioteca` | enter | Sí | `id` d'una biblioteca activa. |
| `llibres` | llista d'enters | Sí | `id` dels llibres, entre 1 i el límit de llibres per comanda, sense repetir. |

```json
{
  "biblioteca": 3,
  "llibres": [7, 9]
}
```

### Resposta correcta

**201 Created**. La comanda creada, amb el format de [Comanda](#comanda) i l'estat `rebuda`.

En crear-la, la biblioteca té un exemplar menys de cada llibre de la comanda (US6-T3). Si dues comandes demanen
alhora l'últim exemplar d'un llibre, només se'n crea una; l'altra rep l'error de llibre sense estoc.

### Errors

**400 Bad Request**. Els errors s'agrupen per camp, amb una llista de missatges per a cada camp, com als altres
contractes.

| Cas | Camp | Missatge |
|---|---|---|
| `biblioteca` o `llibres` absent o `null` | el camp | `Aquest camp és obligatori.` |
| `llibres` és una llista buida | `llibres` | `Afegeix almenys un llibre a la comanda.` |
| Un llibre surt més d'una vegada | `llibres` | `Un llibre no pot sortir dues vegades a la mateixa comanda.` |
| `biblioteca` no és una biblioteca activa | `biblioteca` | `La biblioteca no existeix.` |
| Un `id` de llibre no existeix o no és un número | `llibres` | `Algun dels llibres no existeix.` |
| Més llibres que el límit per comanda | `llibres` | `Has superat el límit de llibres per aquesta comanda, elimina un per continuar` |
| Algun llibre no té exemplars disponibles a la biblioteca | `llibres` | `Aquest llibre no te estoc en aquest moment. Pots apuntar-te a la llista d'espera` |

Els missatges del límit i de l'estoc són literals dels criteris d'acceptació de la US6 i els tests els comproven
exactament (US6-T4). Es mantenen tal com els va escriure el Product Owner.

Quan hi ha llibres sense estoc, la resposta també inclou `sense_estoc` amb els `id` d'aquests llibres, perquè el
frontend pugui marcar-los i oferir d'apuntar-s'hi a la llista d'espera (US5). La comanda no es crea, ni amb els
llibres que sí que tenen estoc.

```json
{
  "llibres": ["Aquest llibre no te estoc en aquest moment. Pots apuntar-te a la llista d'espera"],
  "sense_estoc": [9]
}
```

Les validacions es fan en aquest ordre i s'aturen al primer error de cada camp: camps obligatoris, llista buida,
llibres repetits, llibres inexistents, límit i estoc. Així, una comanda que supera el límit no rep també l'error
d'estoc.

## Comandes pendents de la biblioteca

`GET /api/prestecs/biblioteca/comandes/`

Només per a biblioteques. No té cos.

### Resposta correcta

**200 OK**. Una llista amb les comandes de la biblioteca autenticada que estan en estat `rebuda`, `preparada` o
`cancellada`. Les cancel·lades hi surten perquè la biblioteca sàpiga que ja no les ha de preparar (US20). Les que ja
han sortit (`en_cami`) o s'han lliurat no hi surten. Sense paginació. Si no n'hi ha cap, retorna `[]`.

Ordre: per `data_lliurament`, de la més propera a la més llunyana. Les que encara no tenen data surten al final. Amb
la mateixa data, primer la més antiga.

Cada comanda té el format de [Comanda](#comanda) més el camp `usuari` (`id` i `nom`), perquè la biblioteca sàpiga de
qui és.

```json
[
  {
    "id": 12,
    "estat": "rebuda",
    "usuari": { "id": 25, "nom": "Anna Puig" },
    "biblioteca": { "id": 3, "nom": "Biblioteca Montbau" },
    "llibres": [
      { "id": 9, "titol": "Solitud", "autor": "Víctor Català", "portada": "" }
    ],
    "data_lliurament": "2026-11-20",
    "creada": "2026-11-16T16:20:00Z"
  }
]
```

Una biblioteca només veu les seves comandes.

## Flux del frontend

1. L'usuari afegeix llibres a la comanda des dels resultats de la cerca o del detall del llibre (US6-T6). Cada llibre
   s'afegeix amb la biblioteca que l'ofereix; si n'hi ha de biblioteques diferents, es fan comandes diferents.
2. Abans d'enviar, el frontend avisa si se supera el límit amb el mateix missatge.
3. En confirmar, envia el `POST`. Si rep un 400, mostra els missatges i marca els llibres de `sense_estoc` amb l'opció
   d'apuntar-se a la llista d'espera (US6-T7).

## Decisions pendents

Decisions preses mentre el Product Owner no respongui els dubtes de la US6 i la US8. Si en decideix una altra cosa,
s'actualitzen aquí i al model abans d'implementar la resta d'endpoints.

- **P1. Una biblioteca per comanda.** Cada comanda és d'una sola biblioteca, que és la que la prepara (US10). Per
  demanar llibres de dues biblioteques, cal fer dues comandes.
- **P2. Límit de llibres.** El límit encara no està decidit. Mentre tant és de 5 llibres per comanda, configurable
  amb la variable d'entorn `LIMIT_LLIBRES_COMANDA`. Falta decidir si també compten els llibres que l'usuari ja té en
  préstec (US19).
- **P3. Quan es reserven els exemplars.** En confirmar la comanda, no en afegir els llibres. Mentre l'usuari prepara
  la comanda, un altre la pot avançar.
- **P4. "Llesta per a recollida".** És l'estat `preparada` de la US8, no un estat a part (US15).
- **P5. Un exemplar per llibre.** Cada llibre de la comanda és un exemplar; no se'n poden demanar dos del mateix.
- **P7. Comandes pendents.** La llista de la biblioteca inclou les rebudes, les preparades i les cancel·lades. Falta
  confirmar amb el Product Owner si les preparades hi han de sortir.
