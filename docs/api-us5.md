# Contracte de l'API: estoc i llista d'espera (US5)

Acord entre backend i frontend sobre les biblioteques que tenen estoc d'un
llibre i sobre apuntar-s'hi i desapuntar-s'hi de la llista d'espera.

**Estat**: T3, T4 i T5 estan implementades a la branca actual. Els punts
indicats com a "[proposat]" o a "Pendent de decisió" encara no estan tancats.

## Introducció

Base de l'API:

```text
/api/cataleg/
```

Les peticions i respostes utilitzen JSON.

Els endpoints protegits accepten un token JWT d'accés:

```text
Authorization: Bearer <access>
```

No apareixen tokens reals en aquesta documentació.

- `GET /api/cataleg/llibres/<id>/biblioteques/` és públic i accepta un usuari opcional.
- Els endpoints de llista d'espera exigeixen autenticació amb JWT.

## Resum dels endpoints

| Mètode | Ruta | Descripció | Autenticació | Resposta correcta |
|---|---|---|---|---|
| `GET` | `/api/cataleg/llibres/<id>/biblioteques/` | Llista les biblioteques actives amb estoc | Opcional | 200 OK |
| `POST` | `/api/cataleg/llibres/<id>/llista-espera/` | Apunta l'usuari autenticat a la llista | Sí | 201 Created; 200 OK si ja existia |
| `DELETE` | `/api/cataleg/llibres/<id>/llista-espera/` | Desapunta l'usuari autenticat | Sí | 204 No Content |

## Estat per tasca

| Tasca | Estat | Descripció |
|---|---|---|
| T3 | [implementat] | Model i restricció única d'usuari i llibre. |
| T4 | [implementat] | Cerca de biblioteques amb estoc i ordenació per distància. |
| T5 | [implementat] | Apuntar-se i desapuntar-se de la llista d'espera. |

## GET: biblioteques amb estoc d'un llibre

`GET /api/cataleg/llibres/<id>/biblioteques/`

### Petició

El paràmetre `id` és l'identificador global del `Llibre`.

La capçalera és opcional:

```text
Authorization: Bearer <access>
```

No té cos.

### Resposta correcta

**200 OK**

La resposta és un objecte sense paginació:

```json
{
  "biblioteques": [
    {
      "id": 3,
      "nom": "Biblioteca del Centre",
      "carrer": "C/ d'exemple",
      "numero_porta": "12",
      "latitud": 41.385064,
      "longitud": 2.173403,
      "exemplars": 4,
      "distancia_km": 1.2
    }
  ],
  "ordenada_per_distancia": true,
  "missatge": null
}
```

Només apareixen biblioteques actives amb perfil i amb
`ExemplarBiblioteca.quantitat > 0` per al llibre indicat.

### Exemple: usuari anònim

```json
{
  "biblioteques": [
    {
      "id": 3,
      "nom": "Biblioteca del Centre",
      "carrer": "C/ d'exemple",
      "numero_porta": "12",
      "latitud": 41.385064,
      "longitud": 2.173403,
      "exemplars": 4
    }
  ],
  "ordenada_per_distancia": false,
  "missatge": "Registrat per ordenar les biblioteques per distància"
}
```

L'anònim no rep distàncies.

### Exemple: usuari autenticat sense adreça predeterminada

```json
{
  "biblioteques": [
    {
      "id": 3,
      "nom": "Biblioteca del Centre",
      "carrer": "C/ d'exemple",
      "numero_porta": "12",
      "latitud": 41.385064,
      "longitud": 2.173403,
      "exemplars": 4
    }
  ],
  "ordenada_per_distancia": false,
  "missatge": "Afegeix una adreça per continuar"
}
```

### Exemple: usuari autenticat amb adreça predeterminada

```json
{
  "biblioteques": [
    {
      "id": 3,
      "nom": "Biblioteca Propera",
      "carrer": "Avinguda d'exemple",
      "numero_porta": "1",
      "latitud": 41.390000,
      "longitud": 2.175000,
      "exemplars": 2,
      "distancia_km": 0.6
    },
    {
      "id": 7,
      "nom": "Biblioteca Llunyana",
      "carrer": "Carrer d'exemple",
      "numero_porta": "9",
      "latitud": 41.979400,
      "longitud": 2.821400,
      "exemplars": 1,
      "distancia_km": 85.1
    }
  ],
  "ordenada_per_distancia": true,
  "missatge": null
}
```

La distància s'obté amb la fórmula de Haversine i el radi mitjà de la Terra
de `6371,0 km`. El codi arrodoneix el resultat a una xifra decimal.

### Exemple: llibre sense estoc

```json
{
  "biblioteques": [],
  "ordenada_per_distancia": false,
  "missatge": "Cap biblioteca te aquest llibre en estoc"
}
```

### Exemple: token invàlid o caducat

```json
{
  "biblioteques": [
    {
      "id": 3,
      "nom": "Biblioteca del Centre",
      "carrer": "C/ d'exemple",
      "numero_porta": "12",
      "latitud": 41.385064,
      "longitud": 2.173403,
      "exemplars": 4
    }
  ],
  "ordenada_per_distancia": false,
  "missatge": "Registrat per ordenar les biblioteques per distància"
}
```

El comportament és idèntic al d'un usuari anònim i no retorna 401.

### Errors

**404 Not Found** si el llibre no existeix:

```json
{
  "detail": "No s'ha trobat."
}
```

## POST: apuntar-se a la llista d'espera

`POST /api/cataleg/llibres/<id>/llista-espera/`

### Petició

```text
Authorization: Bearer <access>
Content-Type: application/json
```

L'usuari s'obté de la sessió JWT. No s'ha d'enviar al cos.

El cos pot estar buit. Si s'envia un camp `usuari`, el codi l'ignora i la
entrada queda associada a l'usuari autenticat.

### Exemple de petició

```text
POST /api/cataleg/llibres/12/llista-espera/
Authorization: Bearer <access>
```

### Resposta quan es crea

**201 Created**

```json
{
  "llibre": 12,
  "data_alta": "2026-11-24T12:00:00Z"
}
```

### Resposta quan ja existia

**200 OK**

```json
{
  "llibre": 12,
  "data_alta": "2026-11-24T12:00:00Z"
}
```

[implementat] La segona petició no duplica l'entrada perquè usa
`get_or_create` i la restricció única de base de dades.

### Errors

**401 Unauthorized** sense token:

```json
{
  "detail": "Credencials d'autenticació no disponibles."
}
```

**401 Unauthorized** amb token invàlid o caducat:

```json
{
  "detail": "Given token not valid for any token type",
  "code": "token_not_valid",
  "messages": []
}
```

**404 Not Found** si el llibre no existeix:

```json
{
  "detail": "No s'ha trobat."
}
```

## DELETE: desapuntar-se de la llista d'espera

`DELETE /api/cataleg/llibres/<id>/llista-espera/`

### Petició

```text
Authorization: Bearer <access>
```

No té cos. S'esborra només l'entrada de l'usuari autenticat i del llibre
indicat.

### Exemple de petició

```text
DELETE /api/cataleg/llibres/12/llista-espera/
Authorization: Bearer <access>
```

### Resposta correcta

**204 No Content**

No retorna cos.

[implementat] Si l'usuari no estava apuntat, retorna igualment 204.

### Errors

**401 Unauthorized** sense token o amb token invàlid o caducat.

**404 Not Found** si el llibre no existeix:

```json
{
  "detail": "No s'ha trobat."
}
```

## Camps de les respostes

### Biblioteca amb estoc

| Camp | Tipus | Nul | Només lectura | Descripció |
|---|---|---|---|---|
| `id` | enter | No | Sí | Identificador de l'usuari que representa la biblioteca. |
| `nom` | text | No | Sí | Nom públic de la biblioteca. |
| `carrer` | text | No | Sí | Carrer de la biblioteca; pot ser una cadena buida. |
| `numero_porta` | text | No | Sí | Número de porta de la biblioteca; pot ser una cadena buida. |
| `latitud` | decimal o `null` | Sí | Sí | Latitud pública de la biblioteca. |
| `longitud` | decimal o `null` | Sí | Sí | Longitud pública de la biblioteca. |
| `exemplars` | enter | No | Sí | Quantitat de `ExemplarBiblioteca.quantitat`. |
| `distancia_km` | decimal o omès | Sí | Sí | Distància en quilòmetres des de l'adreça predeterminada, arrodonida a una xifra decimal. Només apareix quan es pot calcular. |

### Entrada de la llista d'espera

| Camp | Tipus | Nul | Només lectura | Descripció |
|---|---|---|---|---|
| `llibre` | enter | No | Sí | Identificador global del llibre. |
| `data_alta` | data i hora ISO 8601 | No | Sí | Moment en què es va crear l'entrada. |

El camp d'usuari no forma part de la resposta.

## Missatges literals

- `"Cap biblioteca te aquest llibre en estoc"`
- `"Afegeix una adreça per continuar"`
- `"Registrat per ordenar les biblioteques per distància"`

## Regles de negoci

- [implementat] El GET d'estoc és públic i accepta un usuari opcional.
- [implementat] Només apareixen biblioteques actives, amb perfil i amb estoc.
- [implementat] Si no hi ha estoc, la resposta retorna el missatge d'estoc.
- [implementat] Si l'usuari té una adreça predeterminada amb coordenades,
  la resposta s'ordena per Haversine.
- [implementat] Les biblioteques sense coordenades van al final i no tenen
  `distancia_km`.
- [implementat] Una adreça predeterminada sense coordenades no permet calcular
  distàncies i mostra el missatge d'adreça.
- [implementat] Les entrades pertanyen a l'usuari autenticat.
- [implementat] Només es pot crear o esborrar l'entrada pròpia.
- [implementat] La restricció única impedeix un duplicat per usuari i llibre.
- [implementat] La resposta no inclou l'adreça ni les coordenades de l'usuari.
- [implementat] Els POST i DELETE no validen estoc ni zona de repartiment.

## Pendent de decisió

### Zona de repartiment i CA6

[proposat] La zona de repartiment encara no està definida. El backend no té
codi que la comprovi i no afecta els endpoints actuals.

### Quan permetre apuntar-se

[proposat] No està decidit si només cal permetre-ho sense estoc o sempre.
Ara mateix el `POST` no comprova l'estoc i sempre el permet.

### Saber si l'usuari ja és a la llista

[proposat] No existeix cap endpoint de consulta ni cap camp que indiqui si
l'usuari autenticat ja està apuntat. Cal una decisió abans d'implementar el
botó de llista d'espera.

### Estoc disponible

[implementat] Ara mateix es considera disponible
`ExemplarBiblioteca.quantitat > 0`.

[proposat] No s'ha decidit si cal descomptar comandes o préstecs en curs.

### Missatges literals

[proposat] Els textos segueixen els criteris literalment. S'ha de confirmar
si cal corregir els possibles errors ortogràfics sense alterar el contracte.

### Precisió i arrodoniment

[implementat] El resultat s'arrodoneix a una xifra decimal.

[proposat] S'ha de confirmar si aquesta precisió és suficient per al frontend.

### Codis de casos repetits i resposta POST

[implementat] El `POST` repetit retorna `200 OK`, el nou `201 Created` i el
`DELETE` absent `204 No Content`.

[proposat] S'ha de confirmar que aquests codis compleixen el contracte del
frontend.

### Notificació quan torna l'estoc

[proposat] No existeix cap lògica de notificació.

### Retirada del llibre i entrades

[proposat] Si es retira físicament el `Llibre`, el `CASCADE` pot eliminar les
entrades. No està decidit si la retirada ha de preservar-les.

### Límit d'entrades

[proposat] No existeix cap límit d'entrades per usuari.

## Per al frontend

### Tractament de la resposta d'estoc

- Si `biblioteques` és buida i `missatge` és
  `"Cap biblioteca te aquest llibre en estoc"`, mostra el missatge de sense estoc.
- Si `ordenada_per_distancia` és `true`, les biblioteques ja estan ordenades i
  poden mostrar `distancia_km`.
- Si `ordenada_per_distancia` és `false`, no ha de presentar distàncies.
- Si `missatge` és `"Afegeix una adreça per continuar"`, demana afegir una
  adreça predeterminada amb coordenades.
- Si `missatge` és `"Registrat per ordenar les biblioteques per distància"`,
  mostra el missatge i la llista sense distàncies.

### Estat de la llista d'espera

[proposat] Aquesta API no permet saber si l'usuari ja està apuntat. Cal afegir
un camp o endpoint per decidir el botó del frontend; no s'ha inventat aquí.
