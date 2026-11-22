# Casos de prova: parades completades o fallides (US13)

Casos de prova de la US13, elaborats a partir dels criteris d'acceptació de la
història. El contracte de l'API del repartidor i de les comandes encara no està
disponible; els casos no pressuposen camps, endpoints ni textos de validació
que no estiguin definits. Serveixen de base per als tests de l'API i E2E.
Qualsevol canvi d'aquest document passa per pull request.

## Història i criteris d'acceptació

> **COM A** repartidor
> **VULL** marcar cada parada com a completada o fallida,
> **PER AIXÍ** mantenir informats els usuaris i les biblioteques.

- **CA1**: el repartidor pot marcar una parada com a completada, i la comanda
  passa a l'estat `lliurada`.
- **CA2**: el repartidor pot marcar una parada com a fallida.
- **CA3**: en marcar una parada com a fallida, cal indicar-ne el motiu
  obligatòriament.
- **CA4**: quan una parada es marca com a fallida, la comanda es torna a
  planificar.
- **CA5**: l'usuari i la biblioteca poden veure l'estat actualitzat de la
  comanda.

## Entorn i precondicions generals

- Aplicació disponible en un entorn de proves amb les dades necessàries.
- Hi ha un compte de repartidor de prova autenticat i amb una parada assignada.
- Hi ha un usuari i una biblioteca de prova associats a la comanda.
- La comanda i les parades es troben en estats inicials vàlids per a l'acció
  provada, segons el contracte que s'acordi.
- Cada cas utilitza dades independents, tret que s'indiqui el contrari.
- Els comptes, les comandes i els motius són dades sintètiques; no s'utilitzen
  dades personals reals.
- L'API i els textos de validació s'han de concretar a US12-T5 i a les tasques
  de la US13 abans d'automatitzar les comprovacions dependents del contracte.

## Dades de prova

| Dada | Valor |
|---|---|
| Repartidor assignat | Compte actiu amb rol `repartidor` i accés a la parada |
| Usuari | Compte de prova associat a la comanda |
| Biblioteca | Biblioteca de prova associada a la comanda |
| Comanda de lliurament | Comanda amb una parada de lliurament en estat previ a completar-la |
| Comanda de parada fallida | Comanda amb una parada assignada que es pot marcar com a fallida |
| Motiu vàlid | Motiu de prova admès segons la regla que defineixi el Product Owner |
| Usuaris no autoritzats | Comptes de prova autenticats amb rol `usuari` i `biblioteca` |

El Product Owner ha de concretar si el motiu és text lliure o una llista
d'opcions. Fins aleshores, no s'assumeix cap conjunt de motius ni un text
concret.

## Resum

| ID | Cas | Criteri d'acceptació | Prioritat | Tipus | Execució proposada |
|---|---|---|---|---|---|
| CP-US13-01 | Completar una parada de lliurament | CA1 | Alta | Correcte | E2E i API |
| CP-US13-02 | Marcar una parada com a fallida amb un motiu vàlid | CA2, CA3 | Alta | Correcte | E2E i API |
| CP-US13-03 | Rebutjar una parada fallida sense motiu | CA3 | Alta | Error | E2E i API |
| CP-US13-04 | Tornar a planificar una comanda després d'una parada fallida | CA4 | Alta | Correcte | API |
| CP-US13-05 | Mostrar a l'usuari i a la biblioteca l'estat actualitzat | CA5 | Alta | Correcte | E2E i API |
| CP-US13-06 | Rebutjar una petició sense autenticació | Accés autenticat | Alta | Error | API |
| CP-US13-07 | Rebutjar una acció d'un rol diferent de repartidor | Accés de repartidor | Alta | Error | API |

## Casos de prova

### CP-US13-01 · Completar una parada de lliurament

- **Criteri d'acceptació**: CA1.
- **Precondicions**:
  - Les generals.
  - La parada correspon al lliurament d'una comanda i es pot completar.
- **Passos**:
  1. Iniciar sessió com a repartidor assignat.
  2. Obrir la parada de lliurament.
  3. Marcar-la com a completada.
- **Resultat esperat**:
  - La parada queda marcada com a completada.
  - La comanda corresponent passa a l'estat exacte `lliurada`.
  - El canvi queda desat i és visible en tornar a consultar la comanda.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: comprovar l'acció i els estats visibles.
  - pytest-django: comprovar els estats desats i la resposta de l'API quan el
    contracte estigui disponible.

### CP-US13-02 · Marcar una parada com a fallida amb un motiu vàlid

- **Criteris d'acceptació**: CA2 i CA3.
- **Precondicions**:
  - Les generals.
  - Hi ha un motiu admès segons la regla acordada pel Product Owner.
- **Passos**:
  1. Iniciar sessió com a repartidor assignat.
  2. Obrir la parada.
  3. Seleccionar l'acció per marcar-la com a fallida.
  4. Indicar un motiu vàlid i confirmar.
- **Resultat esperat**:
  - La parada queda marcada com a fallida.
  - El motiu indicat queda associat al resultat de la parada segons el
    contracte.
  - S'inicia la replanificació de la comanda, comprovada a CP-US13-04.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: comprovar el formulari i el resultat visible.
  - pytest-django: comprovar la resposta i la persistència del motiu quan el
    contracte estigui disponible.

### CP-US13-03 · Rebutjar una parada fallida sense motiu

- **Criteri d'acceptació**: CA3.
- **Precondicions**: les generals.
- **Passos**:
  1. Iniciar sessió com a repartidor assignat.
  2. Obrir l'acció per marcar una parada com a fallida.
  3. Deixar el motiu buit o no enviar-lo i intentar confirmar.
- **Resultat esperat**:
  - No es completa l'acció de marcar la parada com a fallida.
  - La parada conserva l'estat anterior.
  - No s'inicia la replanificació de la comanda.
  - Es comunica l'error de validació; el text exacte no està definit als
    criteris i queda pendent del contracte.
- **Tipus**: error.
- **Automatització**:
  - Playwright: comprovar que no es pot confirmar sense motiu.
  - pytest-django: comprovar el rebuig de l'API per motiu absent o buit i que no
    hi ha canvis parcials.

### CP-US13-04 · Tornar a planificar una comanda després d'una parada fallida

- **Criteri d'acceptació**: CA4.
- **Precondicions**:
  - Les generals.
  - La parada es pot marcar com a fallida i hi ha un motiu vàlid.
- **Passos**:
  1. Marcar la parada com a fallida amb un motiu vàlid.
  2. Consultar el resultat de la replanificació de la comanda segons el
     contracte.
- **Resultat esperat**:
  - La comanda es torna a planificar.
  - El nou pla reflecteix la parada fallida i el resultat de la replanificació
    definit pel Product Owner.
  - No s'assumeix si la comanda passa a la ruta de l'endemà o s'assigna de nou
    a un altre repartidor.
- **Tipus**: correcte.
- **Automatització**: pytest-django per comprovar la replanificació i la
  relació entre comanda i ruta quan la regla i el contracte estiguin definits.

### CP-US13-05 · Mostrar a l'usuari i a la biblioteca l'estat actualitzat

- **Criteri d'acceptació**: CA5.
- **Precondicions**:
  - Les generals.
  - Hi ha dues comandes independents associades a l'usuari i a la biblioteca
    de prova: una per completar el lliurament i una altra per replanificar
    després d'una fallada.
- **Passos**:
  1. Marcar la parada de lliurament de la primera comanda com a completada.
  2. Consultar aquesta comanda amb el compte d'usuari i amb el compte de
     biblioteca.
  3. Marcar una parada de la segona comanda com a fallida i completar-ne la
     replanificació.
  4. Consultar la segona comanda amb el compte d'usuari i amb el compte de
     biblioteca.
- **Resultat esperat**:
  - L'usuari i la biblioteca poden consultar la comanda associada.
  - Després del lliurament completat, tots dos veuen l'estat exacte `lliurada`.
  - Després d'una parada fallida, tots dos veuen l'estat actual de la comanda
    resultant de la replanificació.
  - El text de l'estat posterior a una fallada no queda fixat aquí perquè no
    està definit als criteris ni al contracte.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: comprovar les vistes de l'usuari i la biblioteca.
  - pytest-django: comprovar que totes dues consultes retornen l'estat actual
    de la mateixa comanda.

### CP-US13-06 · Rebutjar una petició sense autenticació

- **Origen**: contracte d'autenticació a `docs/api-auth.md`; l'acció de
  completar o fallar una parada és per al repartidor autenticat.
- **Passos**: intentar marcar una parada com a completada i, en un cas
  independent, com a fallida sense capçalera `Authorization`.
- **Resultat esperat**:
  - Les dues peticions responen `401 Unauthorized`.
  - El cos és `{"detail": "Credencials d'autenticació no disponibles."}`.
  - No canvien l'estat de la parada ni de la comanda i no s'inicia cap
    replanificació.
- **Tipus**: error.
- **Automatització**: pytest-django quan els endpoints estiguin disponibles.

### CP-US13-07 · Rebutjar una acció d'un rol diferent de repartidor

- **Origen**: la història s'adreça al repartidor; missatge de permisos existent
  al projecte.
- **Precondicions**: hi ha comptes de prova autenticats amb rol `usuari` i
  `biblioteca`.
- **Passos**:
  1. Intentar marcar una parada com a completada amb el compte d'usuari.
  2. Repetir-ho amb el compte de biblioteca.
  3. Repetir les dues peticions intentant marcar la parada com a fallida.
- **Resultat esperat**:
  - Les accions es rebutgen amb `403 Forbidden`.
  - D'acord amb el missatge de permisos existent al projecte, el cos és
    `{"detail": "No té permisos per realitzar aquesta acció."}`.
  - No canvien la parada ni la comanda i no s'inicia cap replanificació.
- **Tipus**: error.
- **Automatització**: pytest-django quan el contracte de permisos per a les
  parades estigui disponible.

## Matriu de traçabilitat

| Criteri d'acceptació | Casos que el cobreixen | Cobertura |
|---|---|---|
| CA1: completar una parada i passar la comanda a `lliurada` | CP-US13-01, CP-US13-05 | Cobert |
| CA2: marcar una parada com a fallida | CP-US13-02, CP-US13-03 | Cobert |
| CA3: exigir un motiu per a una parada fallida | CP-US13-02, CP-US13-03 | Cobert |
| CA4: replanificar després d'una parada fallida | CP-US13-02, CP-US13-03, CP-US13-04 | Cobert |
| CA5: l'usuari i la biblioteca veuen l'estat actualitzat | CP-US13-05 | Cobert |

## Decisions i abast

- El Product Owner ha de decidir si el motiu de fallada és text lliure o una
  llista d'opcions. Fins aleshores, els casos no fixen valors ni validacions
  específiques del motiu, excepte que sigui obligatori.
- El Product Owner ha de concretar què significa replanificar: afegir la
  comanda a la ruta de l'endemà, reassignar-la o aplicar una altra regla.
- No s'inventa l'estat de la comanda després d'una parada fallida; l'usuari i
  la biblioteca han de veure el valor actualitzat segons el contracte.
- Els criteris no defineixen el text del missatge quan falta el motiu ni les
  notificacions que es generen. Aquests literals s'han d'afegir quan es
  defineixin als contractes o a la història corresponent.
- El contracte de l'API del repartidor encara no està disponible. Les rutes,
  camps de resposta i permisos s'han de confirmar a `docs/api-repartidor.md`
  abans de convertir les comprovacions d'API en tests executables.
