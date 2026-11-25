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
| `GET /api/prestecs/comandes/cost-enviament/` | Cost de cada tipus de lliurament. | US7-T1 |
| `GET /api/prestecs/comandes/` | Llista les comandes de l'usuari amb el seu estat. | US8-T3 |
| `POST /api/prestecs/comandes/<id>/cancellar/` | Cancel·la una comanda que encara no ha sortit. | US20-T1 |
| `GET /api/prestecs/biblioteca/comandes/` | Llista les comandes pendents de la biblioteca. | US10 (aquest document) |
| `POST /api/prestecs/biblioteca/comandes/<id>/preparada/` | Marca una comanda com a llesta per a recollida. | US15-T1 |
| `POST /api/prestecs/biblioteca/comandes/<id>/recollida/` | Lliura a l'usuari una comanda de recollida. | US7-T8 |
| `GET /api/prestecs/notificacions/` | Llista les notificacions de l'usuari. | US8-T3 |
| `POST /api/prestecs/notificacions/<id>/llegida/` | Marca una notificació com a llegida. | US8-T3 |
| `POST /api/prestecs/notificacions/llegides/` | Marca totes les notificacions com a llegides. | US8-T3 |

Peticions i respostes en JSON (`Content-Type: application/json`). Les rutes que es defineixen en altres tasques poden
canviar fins que la tasca les especifiqui en aquest document.

## Autenticació i permisos

Tots els endpoints requereixen la capçalera `Authorization: Bearer <access>` (vegeu `docs/api-auth.md`).

| Cas | Estat | Resposta |
|---|---|---|
| Sense la capçalera `Authorization`, o amb un token invàlid o caducat | 401 | La de `docs/api-auth.md`. |
| Fer servir les rutes de comandes (crear, llistar o cancel·lar) o de notificacions de l'usuari sense el rol `usuari` (biblioteca o repartidor) | 403 | `{"detail": "No té permisos per realitzar aquesta acció."}` |
| Fer servir una ruta `/biblioteca/` sense ser una biblioteca activa | 403 | `{"detail": "No té permisos per realitzar aquesta acció."}` |

## Estats de la comanda

| Valor | Text per a l'usuari | Quan hi passa |
|---|---|---|
| `rebuda` | Rebuda | En confirmar la comanda. És l'estat inicial. |
| `preparada` | Preparada | Quan la biblioteca la marca com a "Llesta per a recollida" (US15). |
| `en_cami` | En camí | Quan el repartidor la recull a la biblioteca (US12 i US13). |
| `lliurada` | Lliurada | Quan el repartidor marca el lliurament com a completat (US13) o, si és una recollida, quan la biblioteca la lliura a l'usuari (US7-T8). Es creen els préstecs dels llibres (US19). |
| `cancellada` | Cancel·lada | Quan l'usuari la cancel·la abans que surti (US20). |

### Canvis d'estat permesos

| Des de | Pot passar a |
|---|---|
| `rebuda` | `preparada`, `cancellada` |
| `preparada` | `en_cami`, `cancellada`. Si és una recollida a la biblioteca: `lliurada`, `cancellada` (US7-T8) |
| `en_cami` | `lliurada`, o tornar a `preparada` si la parada falla i cal tornar-la a planificar (US13) |
| `lliurada` | Cap: és un estat final. |
| `cancellada` | Cap: és un estat final. |

Qualsevol altre canvi es rebutja i la comanda es queda com estava. Cada canvi es guarda a l'historial de la
comanda amb el moment en què es fa, començant per `rebuda` en confirmar-la.

### Notificacions

Cada canvi d'estat, inclosa la confirmació de la comanda, crea una notificació per a l'usuari de la comanda dins de
l'aplicació. La notificació depèn de l'estat al qual passa la comanda:

| Estat nou | Text de la notificació |
|---|---|
| `rebuda` | `La teva comanda s'ha rebut correctament. La biblioteca ja l'està preparant` |
| `preparada` | `La teva comanda ja està preparada i aviat sortirà cap a casa teva` |
| `en_cami` | `En/Na {nom del repartidor} ja porta la teva comanda. Està en camí!` |
| `lliurada` | `La teva comanda s'ha lliurat correctament. Gaudeix del teu llibre!` |
| `cancellada` | `La teva comanda s'ha cancel·lat.` |

Els textos de `rebuda`, `preparada`, `en_cami` i `lliurada` són literals dels criteris de la US8. Mentre la comanda
no tingui repartidor assignat (US12), el text de `en_cami` és `El repartidor ja porta la teva comanda. Està en camí!`.
Si una parada falla i la comanda torna a `preparada` (P6), l'usuari rep un altre cop el text de `preparada`.

Per llistar-les i marcar-les com a llegides, vegeu [Notificacions de l'usuari](#notificacions-de-lusuari).

## Comanda

Totes les respostes amb una comanda fan servir aquest format.

| Camp | Tipus | Descripció |
|---|---|---|
| `id` | enter | Identificador de la comanda. |
| `estat` | text | Un dels valors de [Estats de la comanda](#estats-de-la-comanda). |
| `biblioteca` | objecte | La biblioteca que prepara la comanda: `id` i `nom`. |
| `llibres` | llista | Els llibres de la comanda: `id`, `titol`, `autor` i `portada` (`""` si no en té). |
| `tipus_lliurament` | text | `domicili` o `recollida` (US7). |
| `adreca_lliurament` | text | On es porta la comanda. `""` si és una recollida. |
| `cost_enviament` | text | Cost del lliurament en euros, amb dos decimals (`"2.50"`). `"0.00"` si és una recollida. |
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
  "tipus_lliurament": "domicili",
  "adreca_lliurament": "C/ de la Muntanya 12, 08035 Barcelona",
  "cost_enviament": "2.50",
  "data_lliurament": null,
  "creada": "2026-11-16T16:20:00Z"
}
```

El cost es desa en confirmar la comanda: si després canvia la tarifa, les comandes que ja estan fetes mantenen el
cost que l'usuari va veure.

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
| `tipus_lliurament` | text | No | `domicili` (per defecte) o `recollida`. |
| `adreca_lliurament` | text | No | Només per a `domicili`. Si no s'envia, és `null` o és buida, s'usa l'adreça del perfil de l'usuari. Amb `recollida` s'ignora. |

```json
{
  "biblioteca": 3,
  "llibres": [7, 9],
  "tipus_lliurament": "domicili",
  "adreca_lliurament": "C/ de la Muntanya 12, 08035 Barcelona"
}
```

La recollida es fa a la mateixa biblioteca de la comanda, la que té els llibres.

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
| `tipus_lliurament` no és `domicili` ni `recollida` | `tipus_lliurament` | `Tria lliurament a domicili o recollida a la biblioteca.` |
| `domicili` sense adreça, ni a la petició ni al perfil | `adreca_lliurament` | `Indica l'adreça de lliurament.` |

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
d'estoc. L'error de l'adreça només surt quan la resta de camps són correctes, i l'estoc es comprova al final de tot.

## Cost d'enviament

`GET /api/prestecs/comandes/cost-enviament/`

Retorna el cost de cada tipus de lliurament, perquè el frontend el mostri abans de confirmar la comanda (US7).
Requereix un usuari amb el rol `usuari`, igual que confirmar la comanda.

**200 OK**

```json
{
  "domicili": "2.50",
  "recollida": "0.00"
}
```

## Les meves comandes

`GET /api/prestecs/comandes/`

**200 OK**. Una llista amb totes les comandes de l'usuari, de la més nova a la més antiga, amb el format de
[Comanda](#comanda). Hi surten totes, també les lliurades i les cancel·lades, perquè l'usuari en vegi l'estat. Si no
en té cap, la llista és buida.

```json
[
  {
    "id": 12,
    "estat": "en_cami",
    "biblioteca": { "id": 3, "nom": "Biblioteca Montbau" },
    "llibres": [{ "id": 9, "titol": "Solitud", "autor": "Víctor Català", "portada": "" }],
    "data_lliurament": "2026-11-20",
    "creada": "2026-11-16T16:20:00Z"
  }
]
```

## Notificacions de l'usuari

### Llistar les notificacions

`GET /api/prestecs/notificacions/`

**200 OK**. Les notificacions de l'usuari, de la més nova a la més antiga. Si no en té cap, la llista és buida. Per
mostrar quantes n'hi ha de noves a la capçalera, el frontend compta les que tenen `llegida` a `false`.

| Camp | Tipus | Descripció |
|---|---|---|
| `id` | enter | Identificador de la notificació. |
| `comanda` | enter | `id` de la comanda a la qual fa referència. |
| `text` | text | El text de la notificació (vegeu [Notificacions](#notificacions)). |
| `llegida` | booleà | Si l'usuari ja l'ha llegida. |
| `creada` | text | Data i hora en què es va crear (ISO 8601). |

```json
[
  {
    "id": 31,
    "comanda": 12,
    "text": "La teva comanda ja està preparada i aviat sortirà cap a casa teva",
    "llegida": false,
    "creada": "2026-11-17T09:05:00Z"
  },
  {
    "id": 30,
    "comanda": 12,
    "text": "La teva comanda s'ha rebut correctament. La biblioteca ja l'està preparant",
    "llegida": true,
    "creada": "2026-11-16T16:20:00Z"
  }
]
```

### Marcar una notificació com a llegida

`POST /api/prestecs/notificacions/<id>/llegida/`

La petició no porta cos. **200 OK** amb la notificació, ja amb `llegida` a `true`. Si ja estava llegida, la resposta
és la mateixa. Una notificació que no existeix o que és d'un altre usuari rep un **404**.

### Marcar totes les notificacions com a llegides

`POST /api/prestecs/notificacions/llegides/`

La petició no porta cos. **200 OK** amb el nombre de notificacions que s'han marcat ara:

```json
{ "marcades": 3 }
```

## Comandes pendents de la biblioteca

`GET /api/prestecs/biblioteca/comandes/`

Només per a biblioteques. No té cos.

### Resposta correcta

**200 OK**. Una llista amb les comandes de la biblioteca autenticada que estan en estat `rebuda`, `preparada` o
`cancellada`. Les cancel·lades hi surten perquè la biblioteca sàpiga que ja no les ha de preparar (US20). Les que ja
han sortit (`en_cami`) o s'han lliurat no hi surten. Sense paginació. Si no n'hi ha cap, retorna `[]`.

Ordre: per `data_lliurament`, de la més propera a la més llunyana. Les que encara no tenen data surten al final. Amb
la mateixa data, primer la més antiga.

Cada comanda té el format de [Comanda](#comanda), però només amb el camp `tipus_lliurament` dels de la US7, perquè la
biblioteca sàpiga quines comandes es recullen a la biblioteca. També hi ha el camp `usuari` (`id` i `nom`), perquè
sàpiga de qui és.

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
    "tipus_lliurament": "domicili",
    "data_lliurament": "2026-11-20",
    "creada": "2026-11-16T16:20:00Z"
  }
]
```

Una biblioteca només veu les seves comandes.

## Marcar una comanda com a llesta per a recollida

`POST /api/prestecs/biblioteca/comandes/<id>/preparada/`

La biblioteca marca una comanda seva com a "Llesta per a recollida" (US15), que és l'estat `preparada` (P4). Només
ho pot fer una biblioteca amb el compte actiu; un usuari o un repartidor reben el 403 de
[Autenticació i permisos](#autenticació-i-permisos). La petició no porta cos.

Un cop preparada, l'usuari en rep la notificació (US8) i la comanda s'assigna a un repartidor si n'hi ha cap amb un
forat a les seves franges (vegeu [Assignació a un repartidor](#assignació-a-un-repartidor)). Si s'assigna, la
resposta ja porta la `data_lliurament`.

### Resposta correcta

**200 OK**. La comanda amb el format de [Comanda](#comanda) i l'estat `preparada`.

### Errors

| Cas | Estat | Resposta |
|---|---|---|
| La comanda no existeix o és d'una altra biblioteca | 404 | Cos sense contingut rellevant. |
| La comanda ja és `preparada` | 409 | `{"detail": "Aquesta comanda ja està llesta per a recollida."}` |
| La comanda és `en_cami`, `lliurada` o `cancellada` | 409 | `{"detail": "Aquesta comanda no es pot marcar com a llesta perquè està en camí."}` (o `lliurada`, `cancel·lada`) |

Una comanda d'una altra biblioteca rep el mateix 404 que una d'inexistent, perquè una biblioteca no pugui saber res
de les comandes de les altres.

## Lliurar una comanda de recollida

`POST /api/prestecs/biblioteca/comandes/<id>/recollida/`

Quan l'usuari ve a buscar una comanda de recollida, la biblioteca la marca com a lliurada (US7-T8). Només ho pot fer
la biblioteca de la comanda, amb el compte actiu; un usuari o un repartidor reben el 403 de
[Autenticació i permisos](#autenticació-i-permisos). La petició no porta cos.

Una comanda de recollida no passa per `en_cami`: va directament de `preparada` a `lliurada`. En lliurar-la, l'usuari
rep la notificació de lliurament (US8) i es creen els préstecs dels llibres (US19).

Al frontend, la pàgina de comandes pendents de la biblioteca mostra el botó "Lliurada a l'usuari" a les comandes de
recollida preparades (US7-T9). En marcar-la, la comanda surt de la llista.

### Resposta correcta

**200 OK**. La comanda amb el format de [Comanda](#comanda) i l'estat `lliurada`.

### Errors

| Cas | Estat | Resposta |
|---|---|---|
| La comanda no existeix o és d'una altra biblioteca | 404 | Cos sense contingut rellevant. |
| La comanda és a domicili | 409 | `{"detail": "Aquesta comanda és a domicili: la lliura el repartidor."}` |
| La comanda és `rebuda` | 409 | `{"detail": "Aquesta comanda encara no està llesta per a recollida."}` |
| La comanda ja és `lliurada` | 409 | `{"detail": "Aquesta comanda ja està lliurada."}` |
| La comanda és `cancellada` | 409 | `{"detail": "Aquesta comanda no es pot lliurar perquè està cancel·lada."}` |

Si la biblioteca la lliura alhora que l'usuari la cancel·la, només es fa una de les dues accions. L'altra rep el seu
409.

## Cancel·lar una comanda

`POST /api/prestecs/comandes/<id>/cancellar/`

L'usuari cancel·la una comanda seva mentre encara no ha sortit, és a dir, mentre és `rebuda` o `preparada` (US20). La
petició no porta cos. El frontend demana confirmació abans d'enviar-la: "Segur que vols cancel·lar aquesta comanda?".

### Resposta correcta

**200 OK**. La comanda amb el format de [Comanda](#comanda) i l'estat `cancellada`.

En cancel·lar-la, la biblioteca torna a tenir un exemplar més de cada llibre de la comanda, i la comanda li surt com
a cancel·lada a la llista de comandes pendents (US10). Si la biblioteca ha tret algun llibre del seu catàleg
mentrestant, aquell exemplar no s'hi torna.

### Errors

| Cas | Estat | Resposta |
|---|---|---|
| La comanda no existeix o és d'un altre usuari | 404 | Cos sense contingut rellevant. |
| La comanda és `en_cami` o `lliurada` | 409 | `{"detail": "Aquesta comanda ja ha sortit i no es pot cancel·lar"}` |
| La comanda ja és `cancellada` | 409 | `{"detail": "Aquesta comanda ja està cancel·lada."}` |

El missatge de quan la comanda ja ha sortit és literal dels criteris d'acceptació de la US20.

## Assignació a un repartidor

No té endpoint propi: el backend assigna les comandes `preparada` als repartidors (US14-T3), i la ruta del dia del
repartidor (US12) es farà a partir d'aquestes assignacions.

- Una comanda s'assigna quan la biblioteca la marca com a llesta. Les que en aquell moment no troben cap repartidor
  es queden `preparada` sense assignar, i l'ordre `python manage.py assigna_comandes` les torna a provar, de la més
  antiga a la més nova.
- Cada lliurament ocupa `DURADA_LLIURAMENT_MINUTS` minuts (30 per defecte) i ha de cabre sencer dins d'una franja
  de disponibilitat del repartidor (`docs/api-franges.md`), sense trepitjar els altres lliuraments que ja té aquell
  dia. Les comandes cancel·lades deixen el seu forat lliure.
- Es busca a partir de l'endemà i durant una setmana. Es tria el primer dia amb algun forat i, d'aquell dia, el
  forat que comença abans. Si dos repartidors poden començar a la mateixa hora, es tria el que té menys lliuraments
  aquell dia.
- Només es fan servir repartidors actius amb el perfil validat.

En assignar-la, la comanda guarda el repartidor, la `data_lliurament` i l'hora d'inici i de final del lliurament. De
moment, d'aquests camps les respostes de l'API només mostren la `data_lliurament`.

## Flux del frontend

1. L'usuari afegeix llibres a la comanda des del detall del llibre (US5), on cada biblioteca amb estoc té el seu botó
   "Afegir a la comanda". Des dels resultats de la cerca, el botó porta al detall, perquè la cerca no diu de quina
   biblioteca és cada llibre (US6-T12). Una comanda només pot tenir llibres d'una biblioteca: per demanar-ne d'una
   altra, cal confirmar-la o treure'n els llibres primer.
   La comanda es desa al navegador (`localStorage`) per a cada usuari, i es conserva encara que es tanqui la pestanya.
2. Abans d'enviar, el frontend avisa si se supera el límit amb el mateix missatge. L'usuari tria domicili (amb
   l'adreça del perfil o una altra) o recollida, i veu el cost de cada opció (US7-T3).
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
- **P6. Parada fallida.** Quan una parada falla (US13), la comanda torna de `en_cami` a `preparada` per tornar-la
  a planificar. Falta confirmar amb el Product Owner que tornar a planificar vol dir això.
- **P7. Comandes pendents.** La llista de la biblioteca inclou les rebudes, les preparades i les cancel·lades. Falta
  confirmar amb el Product Owner si les preparades hi han de sortir.
- **P8. Cost d'enviament.** Mentre el Product Owner no ho decideixi, l'enviament a domicili costa 2,50 € per comanda,
  sigui quina sigui la distància o el nombre de llibres, configurable amb la variable d'entorn
  `COST_ENVIAMENT_DOMICILI`. La recollida és gratuïta i es fa a la biblioteca de la comanda.
- **P9. Notificacions.** De moment les notificacions només es veuen dins de l'aplicació, no s'envien per correu. El
  text de la cancel·lació i el de les comandes que es recullen a la biblioteca (US7) els ha de confirmar el Product
  Owner; ara la recollida rep els mateixos textos que el lliurament a domicili.
- **P10. Assignació de comandes.** Mentre el Product Owner no digui qui assigna les comandes i quan, ho fa el
  sistema sol en marcar-les com a llestes, amb l'ordre `assigna_comandes` per a les que es queden sense repartidor.
  Cada lliurament ocupa 30 minuts i es busca a partir de l'endemà.
