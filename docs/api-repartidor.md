# Contracte de l'API del repartidor (US12, US13 i US14)

Acord entre backend i frontend sobre la ruta del dia, les parades i les
franges horàries del repartidor.

**Estat**:

- `[implementat]` la consulta de la ruta del dia (US12-T3);
- `[implementat]` la consulta i substitució de les franges del repartidor (US14-T2);
- `[proposat]` els endpoints per consultar i actualitzar parades (US13);
- `[pendent]` la confirmació de les accions i els estats definitius de les parades.

Qualsevol canvi d'aquest document ha de passar per pull request i cal avisar
backend i frontend abans de modificar noms de camps, rutes o codis HTTP.

## Introducció

Totes les peticions i respostes utilitzen JSON:

```text
Content-Type: application/json
```

Base de l'API:

```text
/api/
```

Els endpoints del repartidor requereixen un token JWT d'accés:

```text
Authorization: Bearer <access>
```

No apareixen tokens reals en aquesta documentació.

Un repartidor autenticat, actiu i amb el perfil validat pot accedir als
endpoints indicats com a restringits al repartidor. Un usuari sense sessió rep
`401`; un usuari autenticat sense el rol `repartidor`, o un repartidor
pendent, rebutjat o desactivat, rep `403`.

## Resum dels endpoints

| Estat | Mètode | Ruta | Descripció | Permís |
|---|---|---|---|---|
| `[implementat]` | `GET` | `/api/prestecs/repartidor/ruta-avui/` | Ruta i parades del dia del repartidor autenticat | Repartidor validat |
| `[implementat]` | `GET` | `/api/usuaris/repartidor/franges/` | Consulta les franges setmanals del repartidor | Repartidor validat |
| `[implementat]` | `PUT` | `/api/usuaris/repartidor/franges/` | Substitueix totes les franges setmanals del repartidor | Repartidor validat |
| `[proposat]` | `GET` | `/api/prestecs/repartidor/parades/<id>/` | Detall d'una parada pròpia | Repartidor validat |
| `[proposat]` | `POST` | `/api/prestecs/repartidor/parades/<id>/completar/` | Completa una recollida o un lliurament | Repartidor validat |
| `[proposat]` | `POST` | `/api/prestecs/repartidor/parades/<id>/incidencia/` | Registra una incidència i la seva resolució | Repartidor validat |

La gestió concreta de les parades és de US13 i encara no existeix al backend.
Aquestes rutes i accions només són una proposta perquè frontend i PO les
puguin revisar.

No existeix cap endpoint propi per assignar una comanda a un repartidor.
L'assignació de US14-T3 es fa quan una comanda passa a `preparada`, mitjançant
el flux `POST /api/prestecs/biblioteca/comandes/<id>/preparada/`.

# Bloc 1 — Ruta del dia (US12)

## Quan es crea la ruta

La ruta no es crea amb cap endpoint. Quan una comanda s'assigna a un repartidor
(US14-T3), entra a la ruta d'aquell repartidor per al dia del lliurament
(US12-T12):

- si el repartidor encara no té ruta per a aquell dia, es crea;
- s'hi afegeixen dues parades de la comanda: la recollida a la biblioteca i el
  lliurament;
- es torna a calcular l'ordre de tota la ruta (US12-T2).

L'assignació i la ruta van en la mateixa transacció: si no es pot posar la
comanda a la ruta, la comanda tampoc queda assignada. Com que l'assignació busca
a partir de l'endemà, la ruta d'avui només té les comandes que es van assignar
abans d'avui.

Si una parada falla, la comanda es torna a planificar:

- si ha fallat el lliurament (comanda `en_cami`), la comanda torna a
  `preparada` (US13-T3);
- si ha fallat abans de sortir de la biblioteca, per exemple la recollida
  (comanda `preparada`), la comanda continua `preparada` (US13-T12).

En tots dos casos, les altres parades pendents de la comanda es cancel·len, la
comanda es queda sense repartidor ni horari i es torna a assignar. Si no troba
cap forat, es queda `preparada` sense repartidor fins que l'ordre
`assigna_comandes` la pugui assignar. Si torna al mateix repartidor i al mateix
dia, es reaprofiten les seves parades d'aquella ruta i tornen a estar pendents.

Errors de les parades: completar una parada fallida o cancel·lada retorna **409**
amb `{"detail": "La parada no es pot completar."}`, i marcar com a fallida una
parada completada o cancel·lada retorna **409** amb
`{"detail": "La parada no es pot marcar com a fallida."}`.

## Consultar la ruta del dia

`GET /api/prestecs/repartidor/ruta-avui/`

### Permisos

Requereix un repartidor actiu amb el perfil validat.

```text
Authorization: Bearer <access>
```

No té paràmetres de ruta ni cos de petició. Els paràmetres de query no formen
part del contracte i no permeten seleccionar un altre repartidor.

### Resposta correcta

**200 OK**.

Retorna una llista plana sense paginació. Les parades estan ordenades pel camp
`ordre` calculat per US12-T2 i desat a la base de dades.

Les parades d'una comanda que l'usuari ha cancel·lat (US20) no hi surten. En
consultar la ruta, les que encara estaven pendents es marquen com a
`cancellada` (US13-T11). Si es prova de completar-ne una, es retorna el 409 de
parada en estat final.

Si no existeix una ruta creada per al repartidor i la data local actual, retorna
una llista buida:

```json
[]
```

Exemple amb dues parades d'una mateixa comanda:

```json
[
  {
    "id": 18,
    "ordre": 1,
    "tipus": "recollida",
    "comanda": 12,
    "estat": "preparada",
    "estat_parada": "pendent",
    "motiu": "",
    "llibres": [
      {
        "id": 7,
        "titol": "La plaça del Diamant",
        "autor": "Mercè Rodoreda",
        "portada": ""
      }
    ],
    "adreca": {
      "biblioteca": {
        "id": 3,
        "nom": "Biblioteca Central"
      },
      "text": null,
      "latitud": null,
      "longitud": null
    }
  },
  {
    "id": 19,
    "ordre": 2,
    "tipus": "lliurament",
    "comanda": 12,
    "estat": "preparada",
    "estat_parada": "pendent",
    "motiu": "",
    "llibres": [
      {
        "id": 7,
        "titol": "La plaça del Diamant",
        "autor": "Mercè Rodoreda",
        "portada": ""
      }
    ],
    "adreca": {
      "biblioteca": null,
      "text": "C/ Major 1",
      "latitud": null,
      "longitud": null
    }
  }
]
```

### Camps d'una parada

| Camp | Tipus | Nul | Només lectura | Descripció |
|---|---|---|---|---|
| `id` | enter | No | Sí | Identificador de la parada. |
| `ordre` | enter | No | Sí | Posició calculada dins de la ruta, començant per `1`. |
| `tipus` | text | No | Sí | `recollida` o `lliurament`. |
| `comanda` | enter | No | Sí | Identificador de la comanda associada. |
| `estat` | text | No | Sí | Estat actual de la comanda. |
| `estat_parada` | text | No | Sí | Estat de la parada: `pendent`, `completada`, `fallida` o `cancellada`. |
| `motiu` | text | No | Sí | Motiu d'una parada fallida; text buit en els altres casos. |
| `llibres` | llista | No | Sí | Llibres de la comanda: `id`, `titol`, `autor` i `portada`. |
| `adreca` | objecte | No | Sí | Ubicació de la parada i dades de biblioteca quan correspon. |

### Camps de `adreca`

| Camp | Tipus | Nul | Només lectura | Descripció |
|---|---|---|---|---|
| `biblioteca` | objecte o `null` | Sí | Sí | Identificador i nom de la biblioteca en una recollida. |
| `text` | text o `null` | Sí | Sí | Adreça textual del lliurament. Actualment prové de `Usuari.address`. |
| `latitud` | decimal o `null` | Sí | Sí | Coordenada de la parada. Actualment sempre `null`. |
| `longitud` | decimal o `null` | Sí | Sí | Coordenada de la parada. Actualment sempre `null`. |

La separació entre recollida i lliurament és explícita:

- una recollida porta `biblioteca` i `text = null`;
- un lliurament porta `biblioteca = null` i `text` amb la direcció de l'usuari.

En una recollida no s'exposen camps personals de la biblioteca més enllà de
`id` i `nom`.

### Ordenació i precedència

La ruta usa el camp `ordre` desat per US12-T2. Per a una mateixa comanda,
`recollida.ordre < lliurament.ordre`.

El desempat secundari implementat a US12-T2 és:

1. `hora_inici_lliurament`;
2. identificador de comanda;
3. identificador de parada.

No s'ha acordat que aquest desempat sigui el resultat definitiu per proximitat
o zones geogràfiques.

### Errors

**401 Unauthorized** sense autenticació o amb un token invàlid/caducat:

```json
{
  "detail": "Credencials d'autenticació no disponibles."
}
```

**403 Forbidden** si l'usuari no és un repartidor actiu amb perfil validat:

```json
{
  "detail": "No té permisos per realitzar aquesta acció."
}
```

**409 Conflict** si les parades contenen dades incoherents i el càlcul no pot
generar una seqüència vàlida:

```json
{
  "detail": "La ruta conté dades inconsistents."
}
```

# Bloc 2 — Parades de la ruta (US13)

Els endpoints i els estats d'aquesta secció no existeixen a la branca actual.
Totes les definicions marcades `[proposat]` estan pendents d'implementació i
d'acord amb el frontend i el Product Owner.

## Estat d'una parada

L'US12-T1 només defineix el tipus i l'ordre de cada parada:

| Camp | Valors | Descripció |
|---|---|---|
| `tipus` | `recollida`, `lliurament` | Operació que representa la parada. |
| `ordre` | enter positiu | Posició dins de la ruta. |

No existeix actualment un camp `estat` a `Parada`. Per tant, l'objecte
`Parada` no té encara estats persistits de parada. `estat` a la resposta de la
ruta és l'estat actual de la comanda associada.

Els estats de comanda ja definits són:

| Valor | Descripció |
|---|---|
| `rebuda` | Comanda confirmada. |
| `preparada` | Comanda llesta per a recollida. |
| `en_cami` | Comanda en trajecte després d'una recollida exitosa. |
| `lliurada` | Comanda lliurada. |
| `cancellada` | Comanda cancel·lada. |

## `[proposat]` Consultar una parada

`GET /api/prestecs/repartidor/parades/<id>/`

Resposta proposta:

**200 OK**

```json
{
  "id": 19,
  "ordre": 2,
  "tipus": "lliurament",
  "comanda": 12,
  "estat": "en_cami",
  "adreca": {
    "biblioteca": null,
    "text": "C/ Major 1",
    "latitud": null,
    "longitud": null
  }
}
```

**404 Not Found** si la parada no existeix o no pertany a una ruta del
repartidor autenticat.

## `[proposat]` Completar una parada

`POST /api/prestecs/repartidor/parades/<id>/completar/`

Aquest endpoint no existeix i el nom definitiu, el payload i els estats cal
confirmar-los amb US13.

Exemple provisional sense cos:

```text
POST /api/prestecs/repartidor/parades/19/completar/
Authorization: Bearer <access>
```

Resposta proposada:

**200 OK**

```json
{
  "id": 19,
  "ordre": 2,
  "tipus": "lliurament",
  "comanda": 12,
  "estat": "lliurada",
  "adreca": {
    "biblioteca": null,
    "text": "C/ Major 1",
    "latitud": null,
    "longitud": null
  }
}
```

Regles proposades:

- una parada de recollida pot passar la comanda a `en_cami`;
- una parada de lliurament pot passar la comanda a `lliurada`;
- no es pot completar una parada fora de la ruta del repartidor;
- no es pot completar una parada que ja no correspon a l'estat actual;
- no es pot saltar la recollida quan es té una comanda amb aquesta dependència.

Canvi d'estat de la comanda en completar una parada (US13-T10):

- completar la recollida passa la comanda de `preparada` a `en_cami`, i l'usuari
  rep la notificació amb el nom del repartidor de la ruta;
- completar el lliurament la passa d'`en_cami` a `lliurada`;
- si la comanda no pot fer aquest canvi (per exemple, perquè encara no s'ha
  recollit o perquè s'ha cancel·lat), la parada no es completa i es retorna
  **409** amb `{"detail": "La comanda no permet completar aquest lliurament."}`.

## `[proposat]` Reportar una incidència

`POST /api/prestecs/repartidor/parades/<id>/incidencia/`

Payload provisional:

```json
{
  "motiu": "Destinatari absent",
  "observacions": "S'ha intentat el lliurament."
}
```

Els noms dels camps, els motius i la resposta encara no existeixen al
backend i no formen part d'un contracte implementat.

Segons el contracte actual de comandes, una parada fallida pot tornar la
comanda a `preparada` per poder-la tornar a planificar. Aquesta transició ja
està documentada a `docs/api-comandes.md`, però no té implementació específica
d'endpoint de parada.

# Bloc 3 — Franges horàries (US14)

Les franges són setmanals: identifiquen un dia de la setmana i una hora local.
No representen dates concretes.

El model real és `FranjaDisponibilitat` i té aquests camps:

| Camp | Tipus | Descripció |
|---|---|---|
| `id` | enter | Identificador de la franja. |
| `dia` | enter | `0` dilluns fins a `6` diumenge. |
| `hora_inici` | text | Hora d'inici amb format `HH:MM`. |
| `hora_fi` | text | Hora de final amb format `HH:MM`. |

## Consultar les franges

`GET /api/usuaris/repartidor/franges/`

### Resposta correcta

**200 OK**

```json
{
  "franges": [
    {
      "id": 4,
      "dia": 0,
      "hora_inici": "09:00",
      "hora_fi": "13:00"
    },
    {
      "id": 5,
      "dia": 4,
      "hora_inici": "09:00",
      "hora_fi": "14:30"
    }
  ]
}
```

Si no n'hi ha cap:

```json
{
  "franges": []
}
```

## Substituir les franges

`PUT /api/usuaris/repartidor/franges/`

### Petició

```json
{
  "franges": [
    {
      "dia": 0,
      "hora_inici": "09:00",
      "hora_fi": "13:00"
    },
    {
      "dia": 4,
      "hora_inici": "09:00",
      "hora_fi": "14:30"
    }
  ]
}
```

Una llista buida elimina totes les franges i significa que el repartidor no
declara disponibilitat:

```json
{
  "franges": []
}
```

### Resposta correcta

**200 OK**. Retorna les franges substituïdes amb els nous `id`:

```json
{
  "franges": [
    {
      "id": 8,
      "dia": 0,
      "hora_inici": "09:00",
      "hora_fi": "13:00"
    }
  ]
}
```

### Errors

**400 Bad Request** si les dades no són vàlides. No es guarda cap canvi parcial.

Exemples:

```json
{
  "hora_fi": [
    "La franja ha d'acabar després de començar."
  ]
}
```

```json
{
  "franges": [
    "Envia les franges en una llista."
  ]
}
```

```json
{
  "franges": {
    "1": {
      "hora_fi": [
        "La franja ha d'acabar després de començar."
      ]
    }
  }
}
```

Les franges adjacents són vàlides. Les que se solapen del mateix dia són
invàlides.

### Assignació

`[implementat]` L'assignació es fa a partir de les franges i no té endpoint
propi. Quan una comanda passa a `preparada`, el backend cerca un repartidor
validat i un forat en què la durada configurada de lliurament càpiga sencera
dins d'una franja.

Si no hi ha repartidor o no hi ha forat disponible, la comanda queda
`preparada` sense repartidor assignat.

# Catàleg d'errors

## Autenticació

**401 Unauthorized** sense token o amb un token invàlid/caducat:

```json
{
  "detail": "Credencials d'autenticació no disponibles."
}
```

Exemple simpleJWT, també vàlid per als endpoints protegits:

```json
{
  "detail": "Given token not valid for any token type",
  "code": "token_not_valid",
  "messages": []
}
```

## Permís de repartidor

**403 Forbidden** per usuari lector, biblioteca, repartidor no validat,
repartidor rebutjat o usuari desactivat:

```json
{
  "detail": "No té permisos per realitzar aquesta acció."
}
```

## Validació

**400 Bad Request** per dades mal formades o camps invàlids. Els errors van
agrupats per camp, igual que als altres contractes del projecte:

```json
{
  "hora_inici": [
    "Aquest camp és obligatori."
  ]
}
```

## Recurs inexistent

**404 Not Found** quan una parada o un altre recurs no existeix o no pertany al
repartidor autenticat:

```json
{
  "detail": "No s'ha trobat."
}
```

## Conflicte de transició

**409 Conflict** quan una acció sobre una comanda o parada no correspon a la
transició permesa:

```json
{
  "detail": "La ruta conté dades inconsistents."
}
```

Altres missatges de transició es poden trobar a `docs/api-comandes.md`.

# Decisions i Pendent de decisió

## Coordenades i adreces

Actualment no existeix un model de lliurament amb coordenades a la branca
US12:

- les recollides exposen `biblioteca.id` i `biblioteca.nom`;
- els lliuraments exposen `Usuari.address` a `adreca.text`;
- `latitud` i `longitud` sempre són `null`.

Cal decidir quan s'afegiran els camps geogràfics reals i si s'ha d'exposar
`municipi`, `codi_postal`, `carrer` i `numero_porta`.

## Estats i accions de parada US13

Els models actuals no tenen estat de parada. Cal definir:

- endpoints definitius;
- camps i motius d'incidència;
- transicions de la comanda;
- comportament quan una recollida falla;
- comportament quan un lliurament falla;
- possibilitat d'afegir proves o fotos.

## Algoritme i criteri de ruta

US12-T2 garanteix que la recollida d'una comanda va abans del seu lliurament.
El desempat actual usa hora d'inici, id de comanda i id de parada. Cal decidir
si el Product Owner exigeix una ruta per proximitat o un altre criteri secundari.

## Cas sense ruta

La ruta sense parades, o sense ruta creada per avui, retorna `200 OK` i `[]`.
Passa quan el repartidor no té cap comanda assignada per a avui.
No té un missatge d'estat propi.

## Franges

Les franges són setmanals i no tenen camps de capacitat o disponibilitat
concreta. La durada de cada lliurament és configurada per
`DURADA_LLIURAMENT_MINUTS`.
