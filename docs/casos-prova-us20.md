# Casos de prova: cancel·lació d'una comanda (US20)

Casos de prova de la US20, elaborats a partir dels criteris d'acceptació i del
contracte de `docs/api-comandes.md` (US20-T1). Serveixen de base per als tests
de l'API i E2E. Qualsevol canvi d'aquest document passa per pull request.

## Història i criteris d'acceptació

> **COM A** usuari registrat
> **VULL** poder cancel·lar una comanda que encara no ha sortit
> **PER AIXÍ** no rebre llibres que ja no necessito.

- **CA1**: l'usuari pot cancel·lar una comanda mentre no estigui en estat
  `en_cami`.
- **CA2**: abans de cancel·lar, es demana confirmació amb el text exacte
  `Segur que vols cancel·lar aquesta comanda?`.
- **CA3**: un cop cancel·lada, la comanda passa a l'estat `cancel·lada`
  (`cancellada` a l'API).
- **CA4**: els exemplars de la comanda cancel·lada tornen a estar disponibles.
- **CA5**: la biblioteca veu la comanda com a cancel·lada a la llista de
  comandes pendents (US10).
- **CA6**: si la comanda ja és `en_cami` o `lliurada`, no es pot cancel·lar i
  es mostra exactament l'avís
  `Aquesta comanda ja ha sortit i no es pot cancel·lar`.

## Entorn i precondicions generals

- Aplicació disponible en un entorn de proves amb la base de dades migrada.
- Backend, frontend i PostgreSQL disponibles. Per executar-los en local, seguir
  les instruccions de configuració i `docker compose up -d --wait` del README.
- Usuari A de prova amb rol `usuari`, autenticat amb un token d'accés vàlid.
- Biblioteca activa de prova amb llibres i exemplars disponibles.
- Usuari B i biblioteca B per als casos de propietat i permisos.
- Comandes i comptes de prova amb dades sintètiques; no s'utilitzen dades
  personals reals.
- L'endpoint és `POST /api/prestecs/comandes/<id>/cancellar/` i no porta cos.
- Només es poden cancel·lar comandes pròpies en estat `rebuda` o `preparada`;
  aquestes són les comandes que encara no han sortit segons el contracte.

## Dades de prova

| Dada | Valor |
|---|---|
| Usuari A | Usuari actiu de prova amb rol `usuari` |
| Usuari B | Un altre usuari actiu, propietari d'una comanda diferent |
| Biblioteca A | Biblioteca activa propietària dels llibres de la comanda |
| Biblioteca B | Una altra biblioteca activa |
| Comanda rebuda | Comanda de l'usuari A en estat `rebuda` |
| Comanda preparada | Comanda de l'usuari A en estat `preparada` |
| Comanda en camí | Comanda de l'usuari A en estat `en_cami` |
| Comanda lliurada | Comanda de l'usuari A en estat `lliurada` |
| Comanda cancel·lada | Comanda de l'usuari A en estat `cancellada` |
| Estoc inicial | Dos exemplars de cada llibre; la comanda n'ha reservat un |

Cada cas parteix de les dades de prova indicades i no depèn dels canvis fets en
altres casos, tret que s'especifiqui el contrari.

## Resum

| ID | Cas | Criteri / contracte | Prioritat | Tipus | Execució proposada |
|---|---|---|---|---|---|
| CP-US20-01 | Demanar confirmació abans de cancel·lar | CA2 | Alta | Correcte | E2E |
| CP-US20-02 | No cancel·lar si l'usuari rebutja la confirmació | CA2 | Alta | Error / cancel·lació avortada | E2E |
| CP-US20-03 | Cancel·lar una comanda rebuda | CA1, CA3 | Alta | Correcte | API i E2E |
| CP-US20-04 | Cancel·lar una comanda preparada | CA1, CA3 | Alta | Correcte | API |
| CP-US20-05 | Tornar els exemplars i permetre una nova comanda | CA4 | Alta | Correcte | API |
| CP-US20-06 | Mostrar la comanda cancel·lada a la biblioteca | CA5 | Alta | Correcte | API i E2E |
| CP-US20-07 | Rebutjar la cancel·lació si la comanda és en camí o lliurada | CA6 | Alta | Error | API i E2E |
| CP-US20-08 | No tornar els exemplars dues vegades | Contracte T1 | Alta | Error | API |
| CP-US20-09 | Rebutjar una comanda inexistent o d'un altre usuari | Contracte T1 | Alta | Error | API |
| CP-US20-10 | Rebutjar peticions sense autenticació o amb rol no autoritzat | Contracte T1 | Alta | Error | API |
| CP-US20-11 | Rebutjar mètodes HTTP diferents de POST | Contracte T1 | Mitjana | Error | API |

## Casos de prova

### CP-US20-01 · Demanar confirmació abans de cancel·lar

- **Criteri d'acceptació**: CA2.
- **Precondicions**:
  - Les generals.
  - L'usuari A té una comanda cancel·lable en estat `rebuda` o `preparada`.
- **Passos**:
  1. Obrir la llista "Les meves comandes".
  2. Activar l'acció per cancel·lar la comanda.
- **Resultat esperat**:
  - Abans d'enviar cap petició de cancel·lació, la interfície demana
    confirmació.
  - El text de confirmació és exactament:
    `Segur que vols cancel·lar aquesta comanda?`
  - La comanda continua en el seu estat original mentre la confirmació és
    oberta.
- **Tipus**: correcte.
- **Automatització**: Playwright.

### CP-US20-02 · No cancel·lar si l'usuari rebutja la confirmació

- **Criteri d'acceptació**: CA2.
- **Precondicions**:
  - Les generals.
  - L'usuari A té una comanda en estat `rebuda` o `preparada`.
- **Passos**:
  1. Obrir la confirmació de cancel·lació.
  2. Rebutjar-la o tancar-la sense confirmar.
- **Resultat esperat**:
  - No s'envia `POST /api/prestecs/comandes/<id>/cancellar/`.
  - La comanda manté l'estat original.
  - Els exemplars reservats no tornen a estar disponibles.
  - No es crea una notificació de cancel·lació.
- **Tipus**: error / cancel·lació avortada.
- **Automatització**: Playwright; comprovar que no es fa cap petició de
  cancel·lació.

### CP-US20-03 · Cancel·lar una comanda rebuda

- **Criteris d'acceptació**: CA1 i CA3.
- **Precondicions**:
  - Les generals.
  - La comanda és de l'usuari A i està en estat `rebuda`.
- **Passos**:
  1. Confirmar la cancel·lació a la interfície; per a la prova de l'API, enviar
     `POST /api/prestecs/comandes/<id>/cancellar/`.
  2. Tornar a consultar la comanda.
- **Resultat esperat**:
  - La petició retorna `200 OK`.
  - La comanda passa a `cancellada` a l'API i es mostra com a `Cancel·lada` a
    la interfície.
  - L'estat queda desat i es registra el canvi a l'historial.
- **Tipus**: correcte.
- **Automatització**:
  - pytest-django: comprovar resposta, estat desat i historial.
  - Playwright: comprovar confirmació i estat visible.

### CP-US20-04 · Cancel·lar una comanda preparada

- **Criteris d'acceptació**: CA1 i CA3.
- **Precondicions**:
  - Les generals.
  - La comanda és de l'usuari A i està en estat `preparada`, però encara no és
    `en_cami`.
- **Passos**: confirmar la cancel·lació de la comanda.
- **Resultat esperat**:
  - La resposta és `200 OK`.
  - La comanda passa a `cancellada`.
  - L'operació retorna els exemplars reservats, d'acord amb CP-US20-05.
- **Tipus**: correcte.
- **Automatització**: pytest-django.

### CP-US20-05 · Tornar els exemplars i permetre una nova comanda

- **Criteri d'acceptació**: CA4.
- **Precondicions**:
  - Les generals.
  - La biblioteca A té dos exemplars de cada llibre inclòs a la comanda.
  - En confirmar-la, n'ha quedat un de disponible per cada llibre.
- **Passos**:
  1. Cancel·lar la comanda.
  2. Consultar la disponibilitat dels llibres a la biblioteca A.
  3. Intentar demanar un dels exemplars alliberats amb l'usuari B.
- **Resultat esperat**:
  - Després de cancel·lar, la disponibilitat torna al valor inicial per a cada
    llibre que la biblioteca encara ofereix.
  - La biblioteca B, si també té aquests llibres, manté la seva disponibilitat
    sense canvis.
  - L'usuari B pot confirmar una comanda amb l'exemplar alliberat.
- **Tipus**: correcte.
- **Automatització**: pytest-django.

### CP-US20-06 · Mostrar la comanda cancel·lada a la biblioteca

- **Criteri d'acceptació**: CA5.
- **Precondicions**:
  - Les generals.
  - L'usuari A i la biblioteca A tenen una comanda en estat `rebuda` o
    `preparada`.
- **Passos**:
  1. Cancel·lar la comanda com a usuari A.
  2. Consultar la llista de comandes pendents autenticat com a biblioteca A.
- **Resultat esperat**:
  - La resposta de `GET /api/prestecs/biblioteca/comandes/` inclou la comanda.
  - L'estat de la comanda és `cancellada` (text visible: `Cancel·lada`).
  - La biblioteca no la confon amb una comanda que encara s'ha de preparar.
- **Tipus**: correcte.
- **Automatització**:
  - pytest-django: comprovar l'estat i la biblioteca propietària.
  - Playwright: comprovar que la comanda apareix a la llista de pendents.

### CP-US20-07 · Rebutjar la cancel·lació si la comanda és en camí o lliurada

- **Criteri d'acceptació**: CA6.
- **Precondicions**: la comanda és de l'usuari A i està en estat `en_cami` o
  `lliurada`.
- **Passos**:
  1. Intentar cancel·lar la comanda des de la interfície.
  2. Provar també l'endpoint directament amb
     `POST /api/prestecs/comandes/<id>/cancellar/`.
- **Resultat esperat**:
  - La interfície mostra exactament:
    `Aquesta comanda ja ha sortit i no es pot cancel·lar`
  - L'API retorna `409 Conflict` amb el cos exacte:
    `{"detail": "Aquesta comanda ja ha sortit i no es pot cancel·lar"}`
  - L'estat de la comanda, l'historial i la disponibilitat dels exemplars no
    canvien.
- **Tipus**: error.
- **Automatització**:
  - pytest-django: provar tots dos estats i comprovar que no es retornen
    exemplars.
  - Playwright: comprovar l'avís visible.

### CP-US20-08 · No tornar els exemplars dues vegades

- **Origen**: contracte T1.
- **Precondicions**: la comanda de l'usuari A ja és en estat `cancellada`.
- **Passos**: repetir `POST /api/prestecs/comandes/<id>/cancellar/`.
- **Resultat esperat**:
  - L'API retorna `409 Conflict`.
  - El cos és exactament:
    `{"detail": "Aquesta comanda ja està cancel·lada."}`
  - La quantitat d'exemplars no augmenta una segona vegada.
  - L'estat continua sent `cancellada` i no es crea un altre canvi d'estat.
- **Tipus**: error.
- **Automatització**: pytest-django.

### CP-US20-09 · Rebutjar una comanda inexistent o d'un altre usuari

- **Origen**: contracte T1.
- **Passos**:
  1. Autenticar-se com a usuari B i intentar cancel·lar una comanda de l'usuari A.
  2. Intentar cancel·lar un identificador de comanda inexistent.
- **Resultat esperat**:
  - Cada petició retorna `404 Not Found`.
  - La resposta no revela si la comanda existeix per a un altre usuari.
  - La comanda de l'usuari A no canvia d'estat i els exemplars no es retornen.
- **Tipus**: error.
- **Automatització**: pytest-django.

### CP-US20-10 · Rebutjar peticions sense autenticació o amb rol no autoritzat

- **Origen**: contracte T1 i `docs/api-auth.md`.
- **Passos**:
  1. Enviar el `POST` sense capçalera `Authorization` i repetir-lo amb un token
     invàlid o caducat.
  2. Repetir-lo autenticat com a biblioteca, repartidor o usuari desactivat.
- **Resultat esperat**:
  - Les peticions sense autenticació retornen `401 Unauthorized`, amb el format
    definit a `docs/api-auth.md`.
  - Les peticions amb rol no autoritzat retornen `403 Forbidden` amb el cos
    exacte:
    `{"detail": "No té permisos per realitzar aquesta acció."}`
  - La comanda i els exemplars no canvien.
- **Tipus**: error.
- **Automatització**: pytest-django.

### CP-US20-11 · Rebutjar mètodes HTTP diferents de POST

- **Origen**: contracte T1.
- **Passos**: provar `GET` a
  `/api/prestecs/comandes/<id>/cancellar/`.
- **Resultat esperat**:
  - La resposta és `405 Method Not Allowed`.
  - L'estat de la comanda i la disponibilitat dels exemplars no canvien.
- **Tipus**: error.
- **Automatització**: pytest-django.

## Matriu de traçabilitat

| Criteri d'acceptació | Casos que el cobreixen | Cobertura |
|---|---|---|
| CA1: cancel·lar abans que la comanda surti | CP-US20-03, CP-US20-04, CP-US20-07 | Cobert |
| CA2: confirmar abans de cancel·lar | CP-US20-01, CP-US20-02 | Cobert |
| CA3: passar a l'estat cancel·lada | CP-US20-03, CP-US20-04 | Cobert |
| CA4: tornar els exemplars disponibles | CP-US20-05, CP-US20-07, CP-US20-08 | Cobert |
| CA5: mostrar la comanda cancel·lada a la biblioteca | CP-US20-06 | Cobert |
| CA6: avís si ja és en camí o lliurada | CP-US20-07 | Cobert |

## Decisions i abast

- Les comandes en estat `rebuda` o `preparada` es poden cancel·lar; les que són
  `en_cami` o `lliurada` no.
- Si la comanda ja és `cancellada`, repetir l'operació no torna els exemplars a
  l'estoc.
- Si un llibre ja s'ha tret del catàleg de la biblioteca, no se'n crea un
  exemplar nou en cancel·lar la comanda.
- El dubte del Product Owner sobre treure una comanda cancel·lada d'una ruta
  (US12) continua pendent. Aquests casos comproven la cancel·lació abans que la
  comanda estigui `en_cami`, no la replanificació de rutes.
