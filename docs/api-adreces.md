# Contracte de l'API: adreces de lliurament (US3)

Acord entre backend i frontend sobre la gestió de les adreces de lliurament.

**Estat**: implementat T1–T4, subjecte a confirmació del Product Owner als punts indicats
a "Pendent de decisió".

## Introducció

Base de l'API:

```text
/api/usuaris/adreces/
```

Les peticions i respostes utilitzen JSON amb `Content-Type: application/json`.

Els endpoints requereixen un token JWT d'accés:

```text
Authorization: Bearer <access>
```

A la documentació no apareixen tokens reals.

## Resum dels endpoints

| Mètode | Ruta | Descripció | Autenticació | Resposta correcta |
|---|---|---|---|---|
| `GET` | `/api/usuaris/adreces/` | Llista les adreces pròpies | Sí | 200 OK |
| `POST` | `/api/usuaris/adreces/` | Crea una adreça pròpia | Sí | 201 Created |
| `GET` | `/api/usuaris/adreces/<id>/` | Retorna una adreça pròpia | Sí | 200 OK |
| `PUT` | `/api/usuaris/adreces/<id>/` | Reemplaça una adreça pròpia | Sí | 200 OK |
| `PATCH` | `/api/usuaris/adreces/<id>/` | Edita parcialment una adreça pròpia | Sí | 200 OK |
| `DELETE` | `/api/usuaris/adreces/<id>/` | Suprimeix una adreça pròpia | Sí | 204 No Content |
| `POST` | `/api/usuaris/adreces/<id>/predeterminada/` | Marca una adreça com a predeterminada | Sí | 200 OK |

## Camps del recurs

| Camp | Tipus | Obligatori | Longitud màxima | Només lectura | Descripció |
|---|---|---|---|---|---|
| `id` | enter | No | — | Sí | Identificador de l'adreça. |
| `municipi` | text | Sí | 100 | No | Municipi de lliurament. |
| `carrer` | text | Sí | 255 | No | Carrer de l'adreça. |
| `pis` | text | Sí | 20 | No | Pis, porta o escala. |
| `codi_postal` | text | Sí | 5 | No | Codi postal utilitzat per validar la zona de servei. |
| `predeterminada` | booleà | No | — | Sí | Indica si és l'adreça predeterminada de l'usuari. |
| `usuari` | enter | No | — | Sí | Propietari de l'adreça. No forma part del cos acceptat pel serializer. |

El camp `usuari` no s'exposa al serializer. El propietari sempre s'obté del token autenticat.

El camp `predeterminada` no es pot modificar mitjançant `POST`, `PUT` o `PATCH` normals.
S'ha de fer servir l'acció específica descrita més avall.

## Llistar les adreces

`GET /api/usuaris/adreces/`

### Petició

Capçalera:

```text
Authorization: Bearer <access>
```

No té cos.

### Resposta correcta

**200 OK**

El resultat és una llista JSON plana, sense paginació:

```json
[
  {
    "id": 1,
    "municipi": "Barcelona",
    "carrer": "C/ Major 1",
    "pis": "2n A",
    "codi_postal": "08001",
    "predeterminada": true
  }
]
```

Si l'usuari no té adreces, retorna una llista buida:

```json
[]
```

Les adreces s'ordenen per `id` de forma ascendent.

### Errors

**401 Unauthorized** quan no hi ha token, el token és invàlid o el token ha caducat.

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

## Afegir una adreça

`POST /api/usuaris/adreces/`

### Petició

```json
{
  "municipi": "Barcelona",
  "carrer": "C/ Major 1",
  "pis": "2n A",
  "codi_postal": "08001"
}
```

Els camps `municipi`, `carrer`, `pis` i `codi_postal` són obligatoris.

El camp `usuari` enviat al cos s'ignora i no s'ha d'enviar.
El camp `predeterminada` enviat al cos s'ignora i no modifica la base de dades.

### Resposta correcta

**201 Created**

```json
{
  "id": 1,
  "municipi": "Barcelona",
  "carrer": "C/ Major 1",
  "pis": "2n A",
  "codi_postal": "08001",
  "predeterminada": false
}
```

L'adreça queda associada al propietari del token d'accés.

### Errors

**400 Bad Request** quan falta o és invàlid algun camp.

Exemple de camp absent o buit:

```json
{
  "carrer": [
    "Aquest camp és obligatori."
  ]
}
```

Exemple de codi postal fora de la zona:

```json
{
  "codi_postal": [
    "Aquesta adreça està fora de la zona de servei, introdueix una adreça vàlida"
  ]
}
```

**401 Unauthorized** sense autenticació o amb un token invàlid.

**405 Method Not Allowed** amb un altre mètode.

## Consultar una adreça

`GET /api/usuaris/adreces/<id>/`

### Petició

```text
Authorization: Bearer <access>
```

### Resposta correcta

**200 OK**

```json
{
  "id": 1,
  "municipi": "Barcelona",
  "carrer": "C/ Major 1",
  "pis": "2n A",
  "codi_postal": "08001",
  "predeterminada": true
}
```

### Errors

**401 Unauthorized** sense autenticació o amb un token invàlid.

**404 Not Found** si la id no existeix o pertany a un altre usuari.

```json
{
  "detail": "No s'ha trobat."
}
```

## Editar una adreça

`PUT /api/usuaris/adreces/<id>/`

Substitueix tots els camps escrivibles.

```json
{
  "municipi": "Girona",
  "carrer": "C/ Nou 5",
  "pis": "4t",
  "codi_postal": "17001"
}
```

`PATCH /api/usuaris/adreces/<id>/`

Només modifica els camps inclosos:

```json
{
  "carrer": "C/ Nova 8"
}
```

El `PATCH` conserva els camps no inclosos i valida el valor final de `codi_postal`.

### Resposta correcta

**200 OK**

```json
{
  "id": 1,
  "municipi": "Girona",
  "carrer": "C/ Nou 5",
  "pis": "4t",
  "codi_postal": "17001",
  "predeterminada": true
}
```

### Errors

**400 Bad Request** per validació.

Exemple de camp obligatori buit:

```json
{
  "municipi": [
    "Aquest camp és obligatori."
  ]
}
```

Exemple de codi postal fora de la zona:

```json
{
  "codi_postal": [
    "Aquesta adreça està fora de la zona de servei, introdueix una adreça vàlida"
  ]
}
```

**401 Unauthorized** sense autenticació o amb un token invàlid.

**404 Not Found** si la id no existeix o pertany a un altre usuari.

```json
{
  "detail": "No s'ha trobat."
}
```

## Suprimir una adreça

`DELETE /api/usuaris/adreces/<id>/`

No té cos.

### Resposta correcta

**204 No Content**

No retorna cos.

### Errors

**401 Unauthorized** sense autenticació o amb un token invàlid.

**404 Not Found** si la id no existeix o pertany a un altre usuari.

```json
{
  "detail": "No s'ha trobat."
}
```

## Marcar una adreça com a predeterminada

`POST /api/usuaris/adreces/<id>/predeterminada/`

### Petició

No té cos obligatori:

```json
{}
```

Capçalera:

```text
Authorization: Bearer <access>
```

### Resposta correcta

**200 OK**

```json
{
  "id": 1,
  "municipi": "Barcelona",
  "carrer": "C/ Major 1",
  "pis": "2n A",
  "codi_postal": "08001",
  "predeterminada": true
}
```

Si l'adreça ja era predeterminada, la resposta també és **200 OK** i no fa canvis.

En marcar una adreça, l'anterior deixa de ser predeterminada.

### Errors

**401 Unauthorized** sense autenticació o amb un token invàlid.

**404 Not Found** si la id no existeix o pertany a un altre usuari.

```json
{
  "detail": "No s'ha trobat."
}
```

**409 Conflict** si una excepció d'integritat impedeix completar la modificació.

```json
{
  "detail": "No s'ha pogut actualitzar l'adreça predeterminada."
}
```

## Regles de negoci

- Només un usuari autenticat pot gestionar adreces.
- Només es llisten i operen les adreces de `request.user`.
- Una adreça aliena retorna `404`.
- El propietari s'assigna al servidor i no es pot enviar pel cos.
- `predeterminada` és de només lectura als endpoints CRUD.
- En marcar una adreça predeterminada, les altres adreces predeterminades
  de l'usuari passen a `false`.
- Només pot haver una adreça predeterminada per usuari a la base de
  dades mitjançant la restricció condicional `una_adreca_predeterminada_per_usuari`.
- La zona es valida en crear i editar, a través de `codi_postal`.
- El missatge de zona s'associa a la clau `codi_postal`.
- Marcar una adreça predeterminada no torna a validar la zona.
- Suprimir una adreça no té una lògica especial.

## Missatges d'error exactes

Zona de servei:

```text
Aquesta adreça està fora de la zona de servei, introdueix una adreça vàlida
```

El missatge s'ha de copiar literalment i s'ha de retornar sota `"codi_postal"`.

Altres missatges existents al codi:

```text
Aquest camp és obligatori.
```

```text
No s'ha pogut actualitzar l'adreça predeterminada.
```

Aquests no substitueixen els missatges que generi el validador de Django o DRF
en casos no especificats.

## Pendent de decisió

- **Lista final de camps**: confirmar amb el Product Owner si aquesta és
  la llista definitiva o encara cal afegir o eliminar camps.
- **URL i mètode de la predeterminada**: actualment és
  `POST /api/usuaris/adreces/<id>/predeterminada/`; cal confirmar que és el
  contracte final del frontend.
- **Adreça aliena**: actualment retorna `404`; cal confirmar que és el
  comportament definit.
- **Suprimir una adreça predeterminada**: el codi ara fa un esborrat simple.
  Cal confirmar si no és permès, si se'n tria una altra o si queda sense
  predeterminada.
- **Primera adreça predeterminada**: ara no es marca automàticament.
- **Clau de l'error de zona**: actualment és `codi_postal`; cal confirmar-la
  amb el frontend.
- **Validació de zona en marcar predeterminada**: actualment no es torna a
  validar.
- **Límit d'adreces**: no existeix cap límit al codi actual.
- **Definició de la zona**: T2 defineix codis postals catalans pels prefixos
  `08`, `17`, `25` i `43`.
- **Llista final de codis postals**: el codi considera qualsevol codi de cinc
  dígits que comenci pels prefixos indicats. Cal confirmar si aquesta
  aproximació és suficient segons el PO.

## Registre d'estat

| Tasca | Estat |
|---|---|
| T1 — Model `Adreca` | [Implementat] |
| T2 — Validació de zona | [Implementat] |
| T3 — CRUD d'adreces | [Implementat] |
| T4 — Adreça predeterminada | [Implementat] |
| T5 — Tests del backend | [En execució o pendent] |
| T6 — Aquest contracte | [Implementat] |