# Contracte de l'API: gestió del catàleg de la biblioteca (US17)

Acord entre backend i frontend sobre els endpoints amb què una biblioteca gestiona el seu catàleg. El backend
l'implementa a US17-T1 (permisos), US17-T2 (validació de l'ISBN), US17-T3 (llistar i afegir), US17-T4 (editar,
canviar exemplars i retirar), US17-T5 (portada) i US17-T6 (tests); el frontend s'hi connecta a US17-T8, US17-T9 i
US17-T10 i QA en treu els casos de prova a US17-T12. Qualsevol canvi d'aquest document passa per pull request i
s'avisa les dues parts.

**Estat**: esborrany. Les decisions pendents són al final del document.

La cerca de llibres que fan els usuaris (US4) no forma part d'aquest contracte. Només s'hi indica què n'ha de veure.

## Resum

| Mètode i ruta | Per a què serveix |
|---|---|
| `GET /api/cataleg/biblioteca/llibres/` | Llista els llibres del catàleg de la biblioteca. |
| `POST /api/cataleg/biblioteca/llibres/` | Afegeix un llibre al catàleg. |
| `PATCH /api/cataleg/biblioteca/llibres/<id>/` | Edita les dades d'un llibre del catàleg. |
| `PATCH /api/cataleg/biblioteca/llibres/<id>/exemplars/` | Canvia el nombre d'exemplars d'un llibre. |
| `DELETE /api/cataleg/biblioteca/llibres/<id>/` | Retira un llibre del catàleg. |

Peticions i respostes en JSON (`Content-Type: application/json`). Les peticions amb un altre mètode HTTP reben
**405 Method Not Allowed**.

`<id>` és l'identificador del llibre (`id` de les respostes), no el de la fila d'exemplars. Com que una biblioteca
només té una fila d'exemplars per llibre, el llibre i la biblioteca autenticada identifiquen l'entrada del catàleg.

## Autenticació i permisos

Tots els endpoints requereixen la capçalera `Authorization: Bearer <access>` (vegeu `docs/api-auth.md`). Només hi
té accés un usuari amb el rol `biblioteca` i el compte actiu (US17-T1), i cada biblioteca només veu i modifica el
seu catàleg.

| Cas | Estat | Resposta |
|---|---|---|
| Sense la capçalera `Authorization`, o amb un token invàlid o caducat | 401 | La de `docs/api-auth.md`. |
| Usuari autenticat amb el rol `usuari` o `repartidor` | 403 | `{"detail": "No té permisos per realitzar aquesta acció."}` |
| `<id>` d'un llibre que no és al catàleg de la biblioteca (inexistent o només d'una altra biblioteca) | 404 | Cos sense contingut rellevant. |

Un llibre del catàleg d'una altra biblioteca rep el mateix 404 que un llibre inexistent, de manera que una
biblioteca no pot saber què tenen les altres a través d'aquests endpoints. Els textos de 401, 403 i 404 no es
mostren a l'usuari: el frontend només mira l'estat (401: renova el token o tanca la sessió; 403: redirigeix a
l'inici; 404: refresca la llista).

## Llibre del catàleg

Totes les respostes amb un llibre fan servir aquest format.

| Camp | Tipus | Descripció |
|---|---|---|
| `id` | enter | Identificador del llibre. |
| `titol` | text | Títol. |
| `autor` | text | Autor. |
| `isbn` | text | ISBN normalitzat: sense guions ni espais i amb la `X` final de l'ISBN-10 en majúscula. |
| `portada` | text | Enllaç a la imatge de la portada, o `""` si no en té (vegeu P1). |
| `exemplars` | enter | Nombre d'exemplars que en té la biblioteca autenticada. |

```json
{
  "id": 7,
  "titol": "Mecanoscrit del segon origen",
  "autor": "Manuel de Pedrolo",
  "isbn": "9788466421126",
  "portada": "https://example.com/portades/mecanoscrit.jpg",
  "exemplars": 3
}
```

Els noms dels camps d'aquest contracte són els de l'API. El model `Llibre` (US4-T1) té `titol`, `autor`, `isbn` i
`portada`; `exemplars` correspon al camp `quantitat` del model `ExemplarBiblioteca` de la biblioteca autenticada.

## Llistar el catàleg

`GET /api/cataleg/biblioteca/llibres/`

No té cos.

### Resposta correcta

**200 OK**. Una llista amb els llibres del catàleg de la biblioteca, ordenada per títol. Sense paginació. Si el
catàleg és buit, retorna `[]`.

```json
[
  {
    "id": 7,
    "titol": "Mecanoscrit del segon origen",
    "autor": "Manuel de Pedrolo",
    "isbn": "9788466421126",
    "portada": "",
    "exemplars": 3
  }
]
```

## Afegir un llibre

`POST /api/cataleg/biblioteca/llibres/`

### Petició

| Camp | Tipus | Obligatori | Validació |
|---|---|---|---|
| `titol` | text | Sí | No pot ser buit. Màxim 255 caràcters. S'ignoren els espais del voltant. |
| `autor` | text | Sí | No pot ser buit. Màxim 255 caràcters. S'ignoren els espais del voltant. |
| `isbn` | text | Sí | ISBN-10 o ISBN-13 amb el dígit de control correcte. Accepta guions i espais (US17-T2). |
| `exemplars` | enter | Sí | Enter més gran o igual a 1. |
| `portada` | text | No | Enllaç vàlid (vegeu P1). Si no s'envia o és buit, el llibre queda sense portada. |

```json
{
  "titol": "Mecanoscrit del segon origen",
  "autor": "Manuel de Pedrolo",
  "isbn": "978-84-664-2112-6",
  "exemplars": 3,
  "portada": "https://example.com/portades/mecanoscrit.jpg"
}
```

### Resposta correcta

**201 Created**. El llibre afegit, amb el format de [Llibre del catàleg](#llibre-del-catàleg).

L'ISBN es normalitza abans de comprovar si el llibre ja existeix. Hi ha tres casos:

1. **L'ISBN no existeix a cap biblioteca.** Es crea el llibre amb les dades enviades i la fila d'exemplars de la
   biblioteca.
2. **El llibre ja existeix perquè el té una altra biblioteca.** Es reaprofita: només es crea la fila d'exemplars de
   la biblioteca. El títol, l'autor i la portada enviats s'ignoren i la resposta porta les dades desades (vegeu P2).
3. **El llibre ja és al catàleg de la biblioteca.** Error de duplicat (vegeu la taula d'errors).

### Errors

**400 Bad Request**. Els errors s'agrupen per camp, amb una llista de missatges per a cada camp, com als altres
contractes.

```json
{
  "titol": ["Omple tots els camps obligatoris per continuar"],
  "exemplars": ["Omple tots els camps obligatoris per continuar"]
}
```

| Cas | Camp | Missatge |
|---|---|---|
| Camp obligatori absent, buit, només amb espais o `null` | el camp | `Omple tots els camps obligatoris per continuar` |
| ISBN amb un format o un dígit de control incorrecte | `isbn` | `L'ISBN introduït no és vàlid` |
| ISBN que ja és al catàleg de la biblioteca | `isbn` | `Aquest llibre ja és al teu catàleg, actualitza'n els exemplars` |
| `exemplars` no és un enter | `exemplars` | `Es requereix un nombre enter vàlid.` |
| `exemplars` és més petit que 1 | `exemplars` | `Aquest valor ha de ser més gran o igual a 1.` |
| `titol` o `autor` amb més de 255 caràcters | el camp | Missatge per defecte de Django REST Framework |
| `portada` no és un enllaç vàlid | `portada` | `Introdueixi una URL vàlida.` |

Els tres primers missatges són literals dels criteris d'acceptació de la US17 i els tests els comproven exactament
(US17-T6). Els altres són els de Django REST Framework en català.

L'ISBN només es comprova contra el catàleg si té un format vàlid, i només es comprova el format si no és buit: cada
camp rep com a màxim un missatge. El missatge de camps obligatoris és el mateix per a tots els camps, de manera que
el frontend el mostra una sola vegada a sobre del formulari i marca els camps afectats (US17-T9).

## Editar les dades d'un llibre

`PATCH /api/cataleg/biblioteca/llibres/<id>/`

### Petició

Només cal enviar els camps que canvien.

| Camp | Tipus | Validació |
|---|---|---|
| `titol` | text | Com en afegir: si s'envia, no pot ser buit. |
| `autor` | text | Com en afegir: si s'envia, no pot ser buit. |
| `portada` | text | Com en afegir. `""` treu la portada. |

`isbn` i `exemplars` no s'editen aquí: l'ISBN no es pot canviar (vegeu P3) i els exemplars tenen el seu endpoint.
Si s'envien, s'ignoren. Qualsevol altre camp desconegut també s'ignora.

```json
{
  "titol": "Mecanoscrit del segon origen (edició revisada)"
}
```

### Resposta correcta

**200 OK**. El llibre actualitzat, amb el format de [Llibre del catàleg](#llibre-del-catàleg).

### Errors

**400 Bad Request**, agrupats per camp.

| Cas | Camp | Missatge |
|---|---|---|
| `titol` o `autor` enviat buit, només amb espais o `null` | el camp | `Omple tots els camps obligatoris per continuar` |
| `titol` o `autor` amb més de 255 caràcters | el camp | Missatge per defecte de Django REST Framework |
| `portada` no és un enllaç vàlid | `portada` | `Introdueixi una URL vàlida.` |

També hi apliquen el 401, el 403 i el 404 de [Autenticació i permisos](#autenticació-i-permisos).

## Canviar el nombre d'exemplars

`PATCH /api/cataleg/biblioteca/llibres/<id>/exemplars/`

### Petició

| Camp | Tipus | Obligatori | Validació |
|---|---|---|---|
| `exemplars` | enter | Sí | Enter més gran o igual a 0. |

El valor és el nombre total d'exemplars, no un increment. Amb 0 el llibre continua al catàleg, però no n'hi ha cap
de disponible; per treure'l del catàleg, cal retirar-lo.

```json
{
  "exemplars": 5
}
```

### Resposta correcta

**200 OK**. El llibre amb el nombre d'exemplars nou, amb el format de [Llibre del catàleg](#llibre-del-catàleg).

### Errors

**400 Bad Request**, agrupats per camp.

| Cas | Camp | Missatge |
|---|---|---|
| `exemplars` absent, buit o `null` | `exemplars` | `Omple tots els camps obligatoris per continuar` |
| `exemplars` no és un enter | `exemplars` | `Es requereix un nombre enter vàlid.` |
| `exemplars` és negatiu | `exemplars` | `Aquest valor ha de ser més gran o igual a 0.` |

També hi apliquen el 401, el 403 i el 404 de [Autenticació i permisos](#autenticació-i-permisos).

## Retirar un llibre

`DELETE /api/cataleg/biblioteca/llibres/<id>/`

No té cos.

### Resposta correcta

**204 No Content**, sense cos.

S'esborra la fila d'exemplars de la biblioteca. El llibre (`Llibre`) es manté perquè el poden tenir altres
biblioteques, i les seves dades no canvien (vegeu P4). Si la biblioteca el torna a afegir, es reaprofita com en el
cas 2 d'[Afegir un llibre](#afegir-un-llibre).

### Errors

Només els 401, 403 i 404 de [Autenticació i permisos](#autenticació-i-permisos). Retirar un llibre que ja s'ha
retirat rep un 404.

## Efecte a la cerca

Els canvis es reflecteixen a la cerca i a la disponibilitat que veuen els usuaris (US4) sense cap pas addicional,
perquè la cerca llegeix els mateixos models:

- Un llibre afegit apareix a la cerca amb la biblioteca que l'ofereix.
- Les dades editades es veuen a la cerca.
- El nombre d'exemplars nou és el que compta per a la disponibilitat; amb 0, la biblioteca no el té disponible.
- Un llibre retirat ja no apareix com a disponible a la biblioteca que l'ha retirat.

## Flux del frontend

1. La pàgina "El meu catàleg" (US17-T8) carrega la llista amb `GET` i mostra cada llibre amb els seus exemplars.
2. El formulari d'afegir (US17-T9) valida al client els camps obligatoris i el format de l'ISBN amb els mateixos
   missatges, fa el `POST` i, si rep un 400, mostra els missatges del backend.
3. Les accions de la llista (US17-T10) fan el `PATCH` de dades, el `PATCH` d'exemplars o el `DELETE` (després d'un
   pas de confirmació) i actualitzen la fila amb la resposta, o la treuen en rebre el 204.

## Decisions pendents

- **P1. Portada.** El Product Owner ha de decidir si la portada és una imatge que es puja o un enllaç (US17-T5).
  Aquest contracte fa servir un enllaç, que és el que admet el model actual (`URLField`). Si es puja una imatge, la
  petició d'afegir i d'editar passarà a ser `multipart/form-data` i la resposta portarà l'enllaç on se serveix.
- **P2. Dades compartides entre biblioteques.** El model `Llibre` és únic per ISBN i el comparteixen totes les
  biblioteques que el tenen. Mentre el Product Owner no respongui el dubte de la US17, editar les dades d'un llibre
  les canvia per a totes, i afegir un llibre que ja existeix no en sobreescriu les dades.
- **P3. Canviar l'ISBN.** Com que l'ISBN identifica el llibre compartit, no es pot editar. Per corregir un ISBN
  equivocat, cal retirar el llibre i tornar-lo a afegir.
- **P4. Retirar un llibre.** El Product Owner ha de decidir si retirar l'esborra o només el treu de la cerca. Aquest
  contracte esborra la fila d'exemplars de la biblioteca i manté el llibre. Quan hi hagi préstecs (US de préstecs),
  caldrà revisar què passa si es retira un llibre amb préstecs en curs.
