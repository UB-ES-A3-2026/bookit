# Casos de prova: ruta del dia del repartidor (US12)

Casos de prova de la US12, elaborats a partir dels criteris d'acceptació de la
història. El contracte de l'API del repartidor (US12-T5) encara no està
disponible; els casos no pressuposen camps de resposta ni una llibreria de
mapes concreta. Serveixen de base per als tests de l'API i E2E. Qualsevol canvi
d'aquest document passa per pull request.

## Història i criteris d'acceptació

> **COM A** repartidor
> **VULL** veure la ruta del dia amb l'ordre de les parades,
> **PER AIXÍ** fer els lliuraments sense perdre temps.

- **CA1**: es mostren totes les parades del dia (biblioteques, domicilis i
  punts de recollida) en l'ordre en què s'han de fer.
- **CA2**: les parades es mostren sobre un mapa.
- **CA3**: la recollida d'un llibre a la biblioteca sempre apareix abans del
  seu lliurament.

## Entorn i precondicions generals

- Aplicació disponible en un entorn de proves.
- Hi ha un compte de repartidor de prova actiu i autenticat.
- La ruta del dia inclou parades de prova de tots tres tipus: biblioteca,
  domicili i punt de recollida.
- Cada parada de prova té una ubicació coneguda i distingible de les altres;
  les ubicacions són sintètiques.
- Hi ha almenys un llibre amb una parada de recollida a la biblioteca i una
  parada de lliurament associada a la mateixa comanda.
- Les dades de cada cas són independents, tret que s'indiqui el contrari.
- La ruta i l'ordre de prova són fixats pel servei o pel mock del cas. No
  s'assumeix que l'ordre sigui òptim per proximitat.

## Dades de prova

| Dada | Valor |
|---|---|
| Repartidor | Compte de prova actiu amb rol `repartidor` |
| Ruta del dia | Ruta de prova amb una seqüència coneguda de parades |
| Parada de biblioteca | Punt de recollida d'un llibre de la comanda |
| Parada de domicili | Lloc de lliurament d'un llibre de la comanda |
| Punt de recollida | Punt de recollida diferent d'una biblioteca |
| Ubicacions | Coordenades de prova diferents per a cada parada |
| Comanda | Comanda de prova que relaciona la recollida i el lliurament del mateix llibre |
| Altres rols | Comptes de prova autenticats amb rol `usuari` i `biblioteca` |

El contracte US12-T5 ha de concretar el format de la ruta i les ubicacions. Els
casos validen la correspondència entre les parades i les ubicacions retornades,
sense fixar noms de camps que encara no estan acordats.

## Resum

| ID | Cas | Criteri d'acceptació | Prioritat | Tipus | Execució proposada |
|---|---|---|---|---|---|
| CP-US12-01 | Mostrar totes les parades del dia en l'ordre previst | CA1 | Alta | Correcte | E2E i API |
| CP-US12-02 | Mostrar al mapa totes les parades de la ruta | CA2 | Alta | Correcte | E2E |
| CP-US12-03 | Posar la recollida a la biblioteca abans del lliurament corresponent | CA3 | Alta | Correcte | E2E i API |
| CP-US12-04 | Consultar la ruta sense autenticació | Accés autenticat | Alta | Error | API |
| CP-US12-05 | Consultar la ruta amb un rol diferent de repartidor | Accés de repartidor | Alta | Error | API |

## Casos de prova

### CP-US12-01 · Mostrar totes les parades del dia en l'ordre previst

- **Criteri d'acceptació**: CA1.
- **Precondicions**:
  - Les generals.
  - La seqüència de parades esperada és coneguda i conté com a mínim una
    biblioteca, un domicili i un punt de recollida.
- **Passos**:
  1. Iniciar sessió com a repartidor.
  2. Obrir la ruta del dia.
  3. Comparar les parades visibles amb el conjunt i la seqüència esperats.
- **Resultat esperat**:
  - Es mostren totes les parades de la ruta del dia.
  - Hi són representats els tres tipus: biblioteques, domicilis i punts de
    recollida.
  - Les parades apareixen en el mateix ordre que la seqüència de ruta
    preparada per a la prova.
  - Cada parada mostra la seva ubicació o adreça segons el contracte de la
    pàgina i de l'API.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: comprovar el conjunt, el tipus i l'ordre de les parades visibles.
  - pytest-django: comprovar que l'API retorna la seqüència de parades definida
    per al cas, quan el contracte estigui disponible.

### CP-US12-02 · Mostrar al mapa totes les parades de la ruta

- **Criteri d'acceptació**: CA2.
- **Precondicions**:
  - Les generals.
  - Totes les parades de prova tenen ubicacions vàlides i diferents.
- **Passos**:
  1. Iniciar sessió com a repartidor.
  2. Obrir la ruta del dia.
  3. Revisar els punts representats al mapa i comparar-los amb les parades de
     la ruta.
- **Resultat esperat**:
  - El mapa es mostra a la pàgina de la ruta.
  - Cada parada de la ruta té una representació al mapa a la seva ubicació
    corresponent.
  - Hi ha representació per a les parades de biblioteca, domicili i punt de
    recollida.
  - No es pressuposen una llibreria de mapes, un estil de marcador ni una
    interacció concreta, perquè encara no estan acordats.
- **Tipus**: correcte.
- **Automatització**: Playwright, comprovant la presència del mapa i la
  representació de totes les ubicacions de prova segons la implementació
  acordada.

### CP-US12-03 · Posar la recollida a la biblioteca abans del lliurament corresponent

- **Criteri d'acceptació**: CA3.
- **Precondicions**:
  - Les generals.
  - La ruta conté una parada per recollir un llibre a una biblioteca i una
    parada per lliurar aquell mateix llibre al destinatari.
  - Les dues parades es poden relacionar amb la mateixa comanda.
- **Passos**:
  1. Iniciar sessió com a repartidor.
  2. Obrir la ruta del dia.
  3. Localitzar la recollida a la biblioteca i el lliurament corresponent.
- **Resultat esperat**:
  - La parada de recollida a la biblioteca apareix abans que la parada de
    lliurament del mateix llibre.
  - El lliurament no apareix abans de la recollida que el fa possible.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: comparar les posicions de les dues parades a la llista ordenada.
  - pytest-django: validar la precedència de les parades quan la lògica i el
    contracte de ruta estiguin disponibles.

### CP-US12-04 · Consultar la ruta sense autenticació

- **Origen**: contracte d'autenticació a `docs/api-auth.md` i tasca US12-T3, que
  defineix l'endpoint per al repartidor autenticat.
- **Passos**: sol·licitar la ruta del dia sense capçalera
  `Authorization`.
- **Resultat esperat**:
  - L'API respon `401 Unauthorized`.
  - El cos de la resposta és
    `{"detail": "Credencials d'autenticació no disponibles."}`.
  - No es retornen dades de la ruta.
- **Tipus**: error.
- **Automatització**: pytest-django quan l'endpoint estigui disponible.

### CP-US12-05 · Consultar la ruta amb un rol diferent de repartidor

- **Origen**: l'actor de la història és un repartidor i l'endpoint de US12-T3
  s'adreça al repartidor autenticat.
- **Precondicions**: hi ha comptes de prova autenticats amb rol `usuari` i
  `biblioteca`.
- **Passos**:
  1. Sol·licitar la ruta del dia amb el compte d'usuari.
  2. Repetir la sol·licitud amb el compte de biblioteca.
- **Resultat esperat**:
  - Les dues sol·licituds es rebutgen amb `403 Forbidden`.
  - D'acord amb el missatge de permisos existent al projecte, el cos és
    `{"detail": "No té permisos per realitzar aquesta acció."}`.
  - No es retornen dades de la ruta.
- **Tipus**: error.
- **Automatització**: pytest-django quan el contracte US12-T5 confirmi el rol
  permès i la resposta d'error.

## Matriu de traçabilitat

| Criteri d'acceptació | Casos que el cobreixen | Cobertura |
|---|---|---|
| CA1: totes les parades del dia en ordre | CP-US12-01 | Cobert |
| CA2: parades sobre un mapa | CP-US12-02 | Cobert |
| CA3: recollida a la biblioteca abans del lliurament | CP-US12-03 | Cobert |

## Decisions i abast

- La llibreria de mapes del frontend encara s'ha d'acordar. CP-US12-02 comprova
  la representació de totes les parades sense imposar una llibreria concreta.
- L'algoritme d'ordre de les parades és una pregunta pendent per al Product
  Owner. Els casos comproven l'ordre preparat per a la ruta i la precedència de
  recollida abans de lliurament; no exigeixen una ruta òptima per proximitat.
- La generació de la ruta del dia i el moment en què es crea depenen de la
  decisió sobre l'assignació de la US14. No s'inventa un resultat per a una
  ruta encara no generada ni un missatge d'estat buit.
- Els criteris no defineixen missatges d'èxit ni d'error de la ruta. Els casos
  d'accés fan servir els errors literals ja documentats per a l'autenticació i
  els permisos; el contracte US12-T5 haurà de confirmar-los per a aquest
  endpoint.
- El contracte US12-T5 ha de concretar el format de les parades, les
  coordenades i la resposta quan una ubicació no estigui disponible.
