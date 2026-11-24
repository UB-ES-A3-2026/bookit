# Casos de prova: franges de disponibilitat del repartidor (US14)

Casos de prova de la US14, elaborats a partir dels criteris d'acceptació i dels
contractes de `docs/api-franges.md` (US14-T2) i `docs/api-comandes.md`
(US14-T3). Serveixen de base per als tests de l'API i E2E. Qualsevol canvi
d'aquest document passa per pull request.

## Història i criteris d'acceptació

> **COM A** repartidor
> **VULL** indicar les meves franges horàries de disponibilitat
> **PER AIXÍ** rebre només comandes que pugui realitzar segons el meu horari.

- **CA1**: el repartidor pot seleccionar i desar les franges horàries en què
  està disponible per treballar.
- **CA2**: el sistema només assigna comandes que s'ajustin estrictament a les
  franges de disponibilitat indicades.

## Entorn i precondicions generals

- Aplicació disponible en un entorn de proves amb la base de dades migrada.
- Backend, frontend i PostgreSQL disponibles. Per executar-los en local, seguir
  les instruccions de configuració i `docker compose up -d --wait` del README.
- Repartidor actiu amb el perfil validat i autenticat amb un token d'accés vàlid.
- Biblioteca activa de prova amb comandes en estat `preparada`.
- Les franges són setmanals i les hores es donen en hora local, segons la
  decisió provisional F1 de `docs/api-franges.md`.
- Les comandes i els comptes són dades sintètiques; no s'utilitzen dades
  personals reals.
- Les consultes i desaments de franges es fan a:
  - `GET /api/usuaris/repartidor/franges/`
  - `PUT /api/usuaris/repartidor/franges/`
- L'assignació no té endpoint propi. Es prova mitjançant el flux que marca una
  comanda com a preparada, definit a US15.

## Dades de prova

| Dada | Valor |
|---|---|
| Repartidor A | Compte actiu amb perfil validat |
| Repartidor B | Un altre compte actiu amb perfil validat |
| Compte no autoritzat | Usuari, biblioteca o repartidor pendent, rebutjat o desactivat |
| Dia de prova | `0` (dilluns); `6` representa diumenge |
| Franja vàlida | Dilluns de `09:00` a `13:00` |
| Franges adjacents | Dilluns de `09:00` a `13:00` i de `13:00` a `17:00` |
| Franges solapades | Dilluns de `09:00` a `13:00` i de `12:00` a `14:00` |
| Durada de lliurament | Valor de `DURADA_LLIURAMENT_MINUTS`; actualment 30 minuts per defecte |
| Comanda | Comanda de prova en estat `preparada`, sense repartidor assignat |

Per als casos d'assignació, les dades s'han de preparar de manera que hi hagi
una franja disponible dins del període de planificació. Si no s'indica el
contrari, la franja ha de tenir prou durada perquè hi càpiga l'entrega sencera.

## Resum

| ID | Cas | Criteri / contracte | Prioritat | Tipus | Execució proposada |
|---|---|---|---|---|---|
| CP-US14-01 | Consultar les franges quan no n'hi ha cap | Contracte T2 | Mitjana | Correcte | API |
| CP-US14-02 | Desar i consultar franges setmanals vàlides | CA1, contracte T2 | Alta | Correcte | API i E2E |
| CP-US14-03 | Substituir les franges desades i esborrar-les | CA1, contracte T2 | Alta | Correcte | API i E2E |
| CP-US14-04 | Acceptar franges adjacents i rebutjar solapaments | Contracte T2 | Alta | Correcte / error | API |
| CP-US14-05 | Rebutjar un dia fora del rang permès | Contracte T2 | Alta | Error | API |
| CP-US14-06 | Rebutjar hores amb format invàlid | Contracte T2 | Alta | Error | API |
| CP-US14-07 | Rebutjar una franja que no acaba després de començar | Contracte T2 | Alta | Error | API |
| CP-US14-08 | Rebutjar dades absents o una llista mal formada | Contracte T2 | Mitjana | Error | API |
| CP-US14-09 | No desar parcialment una petició invàlida | Contracte T2 | Alta | Error | API |
| CP-US14-10 | Rebutjar l'accés sense autenticació o sense perfil validat | Contracte T2 | Alta | Error | API |
| CP-US14-11 | Assignar una comanda si l'entrega sencera cap dins d'una franja | CA2, contracte T3 | Alta | Correcte | API |
| CP-US14-12 | No assignar si l'entrega no cap sencera dins d'una franja | CA2, contracte T3 | Alta | Error | API |
| CP-US14-13 | Deixar la comanda preparada si no hi ha cap franja disponible | CA2, contracte T3 | Alta | Correcte / sense assignació | API |
| CP-US14-14 | No solapar les entregues assignades a un repartidor | Contracte T3 | Alta | Error | API |

## Casos de prova

### CP-US14-01 · Consultar les franges quan no n'hi ha cap

- **Origen**: contracte T2.
- **Precondicions**:
  - Les generals.
  - El repartidor autenticat encara no té cap franja desada.
- **Passos**: enviar `GET /api/usuaris/repartidor/franges/`.
- **Resultat esperat**:
  - La resposta és `200 OK`.
  - El cos conté `{"franges": []}`.
- **Tipus**: correcte.
- **Automatització**: pytest-django.

### CP-US14-02 · Desar i consultar franges setmanals vàlides

- **Criteri d'acceptació**: CA1.
- **Precondicions**: les generals.
- **Passos**:
  1. Enviar `PUT /api/usuaris/repartidor/franges/` amb dues franges vàlides en
     dies diferents.
  2. Consultar-les amb `GET /api/usuaris/repartidor/franges/`.
- **Dades d'entrada**:

  ```json
  {
    "franges": [
      { "dia": 0, "hora_inici": "09:00", "hora_fi": "13:00" },
      { "dia": 4, "hora_inici": "09:00", "hora_fi": "14:30" }
    ]
  }
  ```

- **Resultat esperat**:
  - El `PUT` retorna `200 OK` amb les franges desades.
  - El `GET` retorna les franges del repartidor autenticat, ordenades per dia i
    hora d'inici.
  - Els valors de `dia`, `hora_inici` i `hora_fi` coincideixen amb els desats.
- **Tipus**: correcte.
- **Automatització**:
  - pytest-django: comprovar desament, consulta i ordenació.
  - Playwright: comprovar que les franges desades es mostren a la pàgina.

### CP-US14-03 · Substituir les franges desades i esborrar-les

- **Criteri d'acceptació**: CA1.
- **Precondicions**:
  - Les generals.
  - El repartidor ja té més d'una franja desada.
- **Passos**:
  1. Enviar un `PUT` amb una nova llista que contingui només una de les franges
     anteriors.
  2. Consultar les franges amb `GET`.
  3. Enviar un `PUT` amb `"franges": []` i tornar a consultar-les.
- **Resultat esperat**:
  - Cada `PUT` retorna `200 OK`.
  - El primer `PUT` substitueix l'horari sencer: les franges no incloses
    desapareixen.
  - La llista buida es desa correctament i el `GET` posterior retorna
    `{"franges": []}`.
- **Tipus**: correcte.
- **Automatització**: pytest-django i Playwright.

### CP-US14-04 · Acceptar franges adjacents i rebutjar solapaments

- **Origen**: contracte T2.
- **Precondicions**:
  - Les generals.
  - El repartidor té una franja vàlida desada, per comprovar que no es perd en
    cas d'error.
- **Passos**:
  1. Desar dues franges del mateix dia que només es toquin: `09:00–13:00` i
     `13:00–17:00`.
  2. Intentar desar `09:00–13:00` i `12:00–14:00` el mateix dia.
- **Resultat esperat**:
  - Les franges adjacents es desen amb `200 OK`.
  - Les franges solapades es rebutgen amb `400 Bad Request`.
  - `franges` conté exactament:
    `Les franges del dilluns de 09:00 a 13:00 i de 12:00 a 14:00 es trepitgen.`
  - La petició invàlida no canvia les franges prèviament desades.
- **Tipus**: correcte i error.
- **Automatització**: pytest-django.

### CP-US14-05 · Rebutjar un dia fora del rang permès

- **Origen**: contracte T2.
- **Passos**: enviar una franja amb `dia: -1` i repetir-la amb `dia: 7`.
- **Resultat esperat**:
  - Cada petició retorna `400 Bad Request`.
  - El camp `dia` de la franja conté exactament:
    `Tria un dia de la setmana, del 0 (dilluns) al 6 (diumenge).`
  - No es desa cap canvi de l'horari.
- **Tipus**: error.
- **Automatització**: pytest-django.

### CP-US14-06 · Rebutjar hores amb format invàlid

- **Origen**: contracte T2.
- **Passos**: enviar una franja amb una hora que no segueixi `HH:MM`, per
  exemple `9:00`, i repetir-la amb una hora impossible, per exemple `25:00`.
- **Resultat esperat**:
  - Cada petició retorna `400 Bad Request`.
  - El camp de l'hora invàlida conté exactament:
    `Escriu l'hora amb el format HH:MM.`
  - No es desa cap canvi de l'horari.
- **Tipus**: error.
- **Automatització**: pytest-django.

### CP-US14-07 · Rebutjar una franja que no acaba després de començar

- **Origen**: contracte T2.
- **Passos**: enviar una franja amb `hora_inici: "13:00"` i `hora_fi: "13:00"`;
  repetir-la amb `hora_fi: "12:00"`.
- **Resultat esperat**:
  - Cada petició retorna `400 Bad Request`.
  - `hora_fi` conté exactament:
    `La franja ha d'acabar després de començar.`
  - No es desa cap canvi de l'horari.
- **Tipus**: error.
- **Automatització**: pytest-django.

### CP-US14-08 · Rebutjar dades absents o una llista mal formada

- **Origen**: contracte T2.
- **Passos**: provar per separat:
  1. Ometre `franges` o enviar `franges: null`.
  2. Enviar `franges` amb un valor que no sigui una llista.
  3. Ometre `dia`, `hora_inici` o `hora_fi` d'una franja; repetir-ho enviant el
     camp corresponent a `null`.
- **Resultat esperat**:
  - Cada petició retorna `400 Bad Request`.
  - Si falta `franges` o és `null`, `franges` conté exactament:
    `Aquest camp és obligatori.`
  - Si `franges` no és una llista, `franges` conté exactament:
    `Envia les franges en una llista.`
  - Si falta o és nul un camp de la franja, el camp afectat conté exactament:
    `Aquest camp és obligatori.`
  - No es desa cap canvi de l'horari.
- **Tipus**: error.
- **Automatització**: pytest-django.

### CP-US14-09 · No desar parcialment una petició invàlida

- **Origen**: contracte T2.
- **Precondicions**:
  - Les generals.
  - El repartidor té un horari vàlid desat.
- **Passos**:
  1. Enviar un `PUT` amb una franja vàlida i una altra d'invàlida.
  2. Tornar a consultar les franges amb `GET`.
- **Resultat esperat**:
  - El `PUT` retorna `400 Bad Request` amb els errors del camp invàlid.
  - Cap de les franges noves no es desa.
  - L'horari anterior es manté íntegre.
- **Tipus**: error.
- **Automatització**: pytest-django.

### CP-US14-10 · Rebutjar l'accés sense autenticació o sense perfil validat

- **Origen**: contractes T2 i `docs/api-auth.md`.
- **Passos**:
  1. Consultar i desar franges sense capçalera `Authorization`; repetir-ho amb
     un token invàlid o caducat.
  2. Repetir les operacions amb un usuari, una biblioteca i un repartidor
     pendent, rebutjat o desactivat.
- **Resultat esperat**:
  - Les peticions sense autenticació retornen `401 Unauthorized`, amb el format
    definit a `docs/api-auth.md`.
  - Les peticions amb un rol o perfil no autoritzat retornen `403 Forbidden`
    amb el cos exacte:
    `{"detail": "No té permisos per realitzar aquesta acció."}`
  - No es retornen ni es modifiquen les franges del repartidor autoritzat.
- **Tipus**: error.
- **Automatització**: pytest-django.

### CP-US14-11 · Assignar una comanda si l'entrega sencera cap dins d'una franja

- **Criteri d'acceptació**: CA2.
- **Precondicions**:
  - Les generals.
  - Hi ha una comanda llesta per a recollida.
  - Un repartidor actiu i validat té una franja lliure prou llarga per a
    l'entrega completa.
- **Passos**: marcar la comanda com a llesta per a recollida mitjançant el flux
  de la biblioteca.
- **Resultat esperat**:
  - La comanda s'assigna a un repartidor actiu amb perfil validat.
  - L'hora d'inici i la durada completa de l'entrega queden dins de la franja
    d'aquest repartidor.
  - La comanda no queda assignada a un repartidor que no tingui una franja que
    la cobreixi.
- **Tipus**: correcte.
- **Automatització**: pytest-django; E2E quan el flux de biblioteca i
  repartidor estigui disponible.

### CP-US14-12 · No assignar si l'entrega no cap sencera dins d'una franja

- **Criteri d'acceptació**: CA2.
- **Precondicions**:
  - Les generals.
  - Hi ha una comanda llesta per a recollida.
  - Les franges disponibles no tenen cap interval lliure prou llarg per cobrir
    la durada completa de l'entrega.
- **Passos**: marcar la comanda com a llesta per a recollida.
- **Resultat esperat**:
  - El sistema no assigna la comanda a cap repartidor per una franja que només
    en cobreixi una part o que acabi abans que finalitzi l'entrega.
  - Si no hi ha cap altra franja elegible, la comanda es manté en estat
    `preparada` i sense repartidor assignat.
- **Tipus**: error / no assignació.
- **Automatització**: pytest-django.

### CP-US14-13 · Deixar la comanda preparada si no hi ha cap franja disponible

- **Criteri d'acceptació**: CA2.
- **Precondicions**:
  - Les generals.
  - Cap repartidor actiu i validat no té un espai lliure que cobreixi l'entrega
    sencera dins del període de planificació.
- **Passos**: marcar la comanda com a llesta per a recollida.
- **Resultat esperat**:
  - La comanda es manté en estat `preparada`.
  - No s'assigna cap repartidor ni cap hora de lliurament fora de disponibilitat.
  - Quan s'afegeixin franges vàlides, es pot tornar a provar l'assignació
    mitjançant el procés de planificació definit a T3.
- **Tipus**: correcte / sense assignació.
- **Automatització**: pytest-django.

### CP-US14-14 · No solapar les entregues assignades a un repartidor

- **Origen**: regles d'assignació de T3.
- **Precondicions**:
  - Les generals.
  - El repartidor té una entrega assignada en una franja.
  - Hi ha una segona comanda llesta per a recollida.
- **Passos**: provocar l'assignació de la segona comanda mentre l'únic espai que
  podria ocupar se solapa amb la primera entrega.
- **Resultat esperat**:
  - Les dues entregues no se solapen.
  - Si no hi ha cap altre espai elegible, la segona comanda queda sense
    repartidor assignat i es manté `preparada`.
- **Tipus**: error / no assignació.
- **Automatització**: pytest-django amb dades d'assignació controlades.

## Matriu de traçabilitat

| Criteri / comportament | Casos que el cobreixen | Cobertura |
|---|---|---|
| CA1: seleccionar, desar i consultar franges | CP-US14-01 a CP-US14-10 | Cobert |
| CA2: assignar només dins d'una franja que cobreixi tota l'entrega | CP-US14-11 a CP-US14-14 | Cobert |
| Missatges literals de validació de T2 | CP-US14-04 a CP-US14-10 | Cobert |

## Decisions i abast

- Fins que el Product Owner decideixi una altra cosa, les franges es repeteixen
  cada setmana i es defineixen per dia (0 dilluns a 6 diumenge) i hora local.
- L'assignació es prova com a part del flux de marcar una comanda com a llesta
  per a recollida; T3 no defineix cap endpoint d'assignació propi.
- L'entrega ha de cabre sencera dins d'una franja i no pot solapar una altra
  entrega del mateix repartidor. La durada prové de
  `DURADA_LLIURAMENT_MINUTS` (30 minuts per defecte).
- La implementació actual torna a buscar assignacions des de l'endemà fins a
  una setmana. Si no hi ha cap espai elegible, la comanda queda preparada sense
  repartidor; aquesta regla segueix la decisió provisional de T3.
- El Product Owner encara ha de confirmar si les franges són setmanals o per
  dates concretes, i qui/quan assigna les comandes. Cal actualitzar els casos
  si aquestes decisions canvien.
