# Casos de prova: comanda llesta per a recollida (US15)

Casos de prova de la US15, elaborats a partir dels criteris d'acceptació de la
història i del contracte de `docs/api-comandes.md` (US15-T1). Serveixen de base
per als tests de l'API i E2E. Qualsevol canvi d'aquest document passa per pull
request.

## Història i criteris d'acceptació

> **COM A** bibliotecari
> **VULL** marcar una comanda com a "Llesta per a recollida"
> **PER AIXÍ** actualitzar l'estat intern de preparació del paquet.

- **CA1**: la comanda inclou un botó per canviar el seu estat a "Llesta per a
  recollida".
- **CA2**: l'estat de la comanda s'actualitza correctament a la base de dades i
  queda disponible per al servei de logística i assignació.

## Entorn i precondicions generals

- Aplicació disponible en un entorn de proves amb la base de dades migrada.
- Backend, frontend i PostgreSQL disponibles. Per executar-los en local, seguir
  les instruccions de configuració i `docker compose up -d --wait` del README.
- Biblioteca activa de prova amb un usuari autenticat amb rol `biblioteca`.
- L'usuari de biblioteca només pot actuar sobre les comandes pròpies.
- Repartidor, disponibilitat i comandes de prova amb dades sintètiques; no
  s'utilitzen dades personals reals.
- L'endpoint és
  `POST /api/prestecs/biblioteca/comandes/<id>/preparada/` i no porta cos.
- "Llesta per a recollida" correspon a l'estat `preparada` (decisió P4 del
  contracte). En marcar-la, el backend prova d'assignar-la a un repartidor
  segons la US14.

## Dades de prova

| Dada | Valor |
|---|---|
| Biblioteca A | Biblioteca activa autenticada |
| Biblioteca B | Una altra biblioteca activa |
| Comanda rebuda | Comanda de la biblioteca A en estat `rebuda` |
| Comanda preparada | Comanda de la biblioteca A en estat `preparada` |
| Comanda en camí | Comanda de la biblioteca A en estat `en_cami` |
| Comanda lliurada | Comanda de la biblioteca A en estat `lliurada` |
| Comanda cancel·lada | Comanda de la biblioteca A en estat `cancellada` |
| Repartidor disponible | Repartidor actiu i validat amb una franja elegible |
| Sense disponibilitat | Cap repartidor té un espai elegible per a l'entrega |

Cada cas parteix de les dades de prova indicades i no depèn dels canvis fets en
altres casos, tret que s'especifiqui el contrari.

## Resum

| ID | Cas | Criteri / contracte | Prioritat | Tipus | Execució proposada |
|---|---|---|---|---|---|
| CP-US15-01 | Mostrar l'acció per a una comanda rebuda de la biblioteca | CA1 | Alta | Correcte | E2E |
| CP-US15-02 | Marcar la comanda com a preparada i persistir el canvi | CA1, CA2 | Alta | Correcte | API i E2E |
| CP-US15-03 | Deixar la comanda disponible per a logística i assignació | CA2, contractes T1 i US14-T3 | Alta | Correcte | API |
| CP-US15-04 | Generar la notificació de l'estat `preparada` | Contractes US8-T2 i T1 | Alta | Correcte | API i E2E |
| CP-US15-05 | Rebutjar tornar a marcar una comanda preparada | Contracte T1 | Alta | Error | API i E2E |
| CP-US15-06 | Rebutjar comandes en camí, lliurades o cancel·lades | Contracte T1 | Alta | Error | API |
| CP-US15-07 | No permetre a una biblioteca marcar una comanda aliena | Contracte T1 | Alta | Error | API |
| CP-US15-08 | Rebutjar peticions sense autenticació o amb rol no autoritzat | Contracte T1 | Alta | Error | API |
| CP-US15-09 | Rebutjar mètodes HTTP diferents de POST | Contracte T1 | Mitjana | Error | API |
| CP-US15-10 | Mantenir la comanda preparada si no hi ha repartidor disponible | CA2, contracte US14-T3 | Alta | Correcte / sense assignació | API |

## Casos de prova

### CP-US15-01 · Mostrar l'acció per a una comanda rebuda de la biblioteca

- **Criteri d'acceptació**: CA1.
- **Precondicions**:
  - Les generals.
  - La biblioteca A té una comanda en estat `rebuda`.
- **Passos**:
  1. Iniciar sessió com a biblioteca A.
  2. Obrir la llista de comandes pendents.
  3. Localitzar la comanda rebuda.
- **Resultat esperat**:
  - La comanda apareix a la llista de la biblioteca A en estat `Rebuda`.
  - Hi ha un botó amb el text exacte `Llesta per a recollida`.
  - L'acció no apareix per a comandes d'una altra biblioteca.
- **Tipus**: correcte.
- **Automatització**: Playwright, quan la pàgina de T3 estigui disponible.

### CP-US15-02 · Marcar la comanda com a preparada i persistir el canvi

- **Criteris d'acceptació**: CA1 i CA2.
- **Precondicions**:
  - Les generals.
  - La comanda és de la biblioteca A i està en estat `rebuda`.
- **Passos**:
  1. Fer clic al botó `Llesta per a recollida`; per a la prova de l'API, enviar
     `POST /api/prestecs/biblioteca/comandes/<id>/preparada/`.
  2. Tornar a consultar la comanda i la llista de pendents de la biblioteca.
- **Resultat esperat**:
  - La petició retorna `200 OK`.
  - La resposta conté la mateixa comanda amb estat `preparada`.
  - En tornar-la a consultar, la base de dades i l'API continuen mostrant
    l'estat `preparada`.
  - La comanda queda a la llista de pendents de la biblioteca perquè logística
    i assignació la puguin processar.
  - A la interfície, l'estat es mostra com `Preparada` i l'acció ja no es pot
    tornar a executar.
- **Tipus**: correcte.
- **Automatització**:
  - pytest-django: comprovar resposta, estat desat i historial.
  - Playwright: comprovar el botó i l'actualització de la llista.

### CP-US15-03 · Deixar la comanda disponible per a logística i assignació

- **Criteri d'acceptació**: CA2.
- **Precondicions**:
  - Les generals.
  - Hi ha un repartidor actiu i validat amb una franja que cobreix l'entrega
    sencera.
- **Passos**: marcar la comanda com a llesta per a recollida.
- **Resultat esperat**:
  - La comanda queda en estat `preparada`.
  - El servei d'assignació la processa i, si troba un espai elegible, hi assigna
    un repartidor i una data de lliurament.
  - La resposta de l'endpoint inclou la data de lliurament quan s'ha fet
    l'assignació.
  - L'assignació no posa la comanda fora de les franges del repartidor ni se
    solapa amb una altra entrega seva.
- **Tipus**: correcte.
- **Automatització**: pytest-django; comprovar l'assignació mitjançant les
  dades del backend.

### CP-US15-04 · Generar la notificació de l'estat `preparada`

- **Origen**: US15-T1 i criteri de notificacions de la US8.
- **Precondicions**:
  - Les generals.
  - L'usuari propietari de la comanda pot consultar les seves notificacions.
- **Passos**:
  1. Marcar una comanda rebuda com a llesta.
  2. Consultar les notificacions de l'usuari propietari.
- **Resultat esperat**:
  - Es crea una notificació associada a la comanda i al seu usuari.
  - El text és exactament:
    `La teva comanda ja està preparada i aviat sortirà cap a casa teva`
  - No es crea una notificació duplicada per a una transició rebutjada.
- **Tipus**: correcte.
- **Automatització**: pytest-django; Playwright si la notificació és visible a
  la interfície.

### CP-US15-05 · Rebutjar tornar a marcar una comanda preparada

- **Origen**: contracte T1.
- **Precondicions**: la comanda de la biblioteca A ja està en estat `preparada`.
- **Passos**: repetir `POST /api/prestecs/biblioteca/comandes/<id>/preparada/`.
- **Resultat esperat**:
  - La resposta és `409 Conflict`.
  - El cos és exactament:
    `{"detail": "Aquesta comanda ja està llesta per a recollida."}`
  - L'estat continua sent `preparada`.
  - No s'afegeix un altre canvi a l'historial ni una notificació duplicada.
  - La interfície no permet repetir l'acció.
- **Tipus**: error.
- **Automatització**: pytest-django i Playwright.

### CP-US15-06 · Rebutjar comandes en camí, lliurades o cancel·lades

- **Origen**: contracte T1.
- **Passos**: enviar el `POST` per separat a comandes de la biblioteca A en
  estat `en_cami`, `lliurada` i `cancellada`.
- **Resultat esperat**:
  - Cada petició retorna `409 Conflict`.
  - La resposta conté exactament el missatge corresponent a l'estat:
    - `{"detail": "Aquesta comanda no es pot marcar com a llesta perquè està en camí."}`
    - `{"detail": "Aquesta comanda no es pot marcar com a llesta perquè està lliurada."}`
    - `{"detail": "Aquesta comanda no es pot marcar com a llesta perquè està cancel·lada."}`
  - L'estat, l'historial i les notificacions no canvien.
- **Tipus**: error.
- **Automatització**: pytest-django.

### CP-US15-07 · No permetre a una biblioteca marcar una comanda aliena

- **Origen**: contracte T1.
- **Passos**:
  1. Autenticar-se com a biblioteca B.
  2. Enviar el `POST` amb l'identificador d'una comanda de la biblioteca A.
  3. Repetir-ho amb un identificador de comanda inexistent.
- **Resultat esperat**:
  - Les dues peticions retornen `404 Not Found`.
  - La resposta no revela si la comanda existeix en una altra biblioteca.
  - La comanda de la biblioteca A manté l'estat original.
- **Tipus**: error.
- **Automatització**: pytest-django.

### CP-US15-08 · Rebutjar peticions sense autenticació o amb rol no autoritzat

- **Origen**: contracte T1 i `docs/api-auth.md`.
- **Passos**:
  1. Enviar el `POST` sense capçalera `Authorization` i repetir-lo amb un token
     invàlid o caducat.
  2. Repetir-lo autenticat com a usuari, repartidor i biblioteca inactiva.
- **Resultat esperat**:
  - Les peticions sense autenticació retornen `401 Unauthorized`, amb el format
    definit a `docs/api-auth.md`.
  - Les peticions amb rol no autoritzat o biblioteca inactiva retornen
    `403 Forbidden` amb el cos exacte:
    `{"detail": "No té permisos per realitzar aquesta acció."}`
  - La comanda no canvia d'estat.
- **Tipus**: error.
- **Automatització**: pytest-django.

### CP-US15-09 · Rebutjar mètodes HTTP diferents de POST

- **Origen**: contracte T1.
- **Passos**: provar `GET` a
  `/api/prestecs/biblioteca/comandes/<id>/preparada/`.
- **Resultat esperat**:
  - La resposta és `405 Method Not Allowed`.
  - La comanda manté l'estat original.
- **Tipus**: error.
- **Automatització**: pytest-django.

### CP-US15-10 · Mantenir la comanda preparada si no hi ha repartidor disponible

- **Criteri d'acceptació**: CA2.
- **Precondicions**:
  - Les generals.
  - Cap repartidor actiu i validat no té un espai lliure dins de les seves
    franges que cobreixi l'entrega sencera.
- **Passos**: marcar la comanda com a llesta per a recollida.
- **Resultat esperat**:
  - La petició es completa i la comanda passa a `preparada`.
  - La comanda no s'assigna a cap repartidor ni rep una data de lliurament fora
    de disponibilitat.
  - La comanda queda disponible perquè el procés de planificació la torni a
    provar quan hi hagi franges elegibles.
- **Tipus**: correcte / sense assignació.
- **Automatització**: pytest-django amb l'assignació de la US14.

## Matriu de traçabilitat

| Criteri d'acceptació | Casos que el cobreixen | Cobertura |
|---|---|---|
| CA1: mostrar el botó per marcar la comanda com a llesta | CP-US15-01, CP-US15-02 | Cobert |
| CA2: persistir `preparada` i deixar-la disponible per logística/assignació | CP-US15-02, CP-US15-03, CP-US15-10 | Cobert |
| Canvis d'estat, permisos i errors del contracte T1 | CP-US15-04 a CP-US15-09 | Cobert |

## Decisions i abast

- "Llesta per a recollida" és l'estat `preparada` (P4 de
  `docs/api-comandes.md`), no un estat nou.
- L'assignació a repartidor es prova segons la decisió provisional de US14-T3:
  es busca un espai des de l'endemà fins a una setmana i l'entrega sencera ha
  de cabre dins de la franja. Si no n'hi ha, la comanda queda preparada sense
  assignació i es pot tornar a provar amb el procés de planificació.
- El contracte encara indica que el text de la notificació per a recollida a
  la biblioteca s'ha de confirmar amb el Product Owner; fins aleshores es prova
  el missatge literal definit per a `preparada`.
