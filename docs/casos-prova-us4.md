# Casos de prova: cerca de llibres (US4)

Casos de prova de la US4, escrits a partir dels criteris d'acceptació de la història.
Els tests E2E amb Playwright i els tests de l'API amb pytest-django en poden sortir.
Qualsevol canvi d'aquest document passa per pull request.

## Història i criteris d'acceptació

- **CA1**: l'usuari pot cercar llibres pel títol.
- **CA2**: l'usuari pot cercar llibres per l'autor.
- **CA3**: l'usuari pot cercar llibres per l'ISBN.
- **CA4**: cada resultat mostra el títol, l'autor, la portada, si hi ha exemplars disponibles i les seves valoracions.
- **CA5**: si no hi ha cap resultat, es mostra el missatge informatiu:
  "No s'ha trobat el llibre cercat, assegura't que l'informació introduïda sigui correcta".

## Entorn i precondicions generals

- Aplicació aixecada en local amb `docker compose up -d` des de l'arrel.
- Frontend disponible a `http://localhost:5173` o al port definit a `.env`.
- Backend i base de dades disponibles.
- Usuari situat a la pantalla de cerca de llibres.
- El catàleg de proves conté els llibres necessaris per a cada cas.
- Les dades dels llibres de prova s'han de definir a l'entorn de proves sense utilitzar dades personals reals.

## Dades de prova

Per executar els casos cal disposar, com a mínim, de:

- Un llibre identificable pel seu títol.
- Un llibre identificable pel seu autor.
- Un llibre identificable pel seu ISBN.
- Un llibre amb portada i valoracions.
- Un llibre sense exemplars disponibles o amb la informació de disponibilitat que correspongui al cas.
- Un text que no coincideixi amb cap llibre del catàleg.

Els valors concrets dels llibres no formen part dels criteris d'acceptació i s'han de definir en la preparació de l'entorn de proves.

## Resum

| ID | Cas | Criteri d'acceptació que cobreix | Prioritat | Tipus | Execució proposada |
|---|---|---|---|---|---|
| CP-US4-01 | Cercar un llibre pel títol | CA1 | Alta | Correcte | E2E (Playwright) i API (pytest-django) |
| CP-US4-02 | Cercar un llibre per l'autor | CA2 | Alta | Correcte | E2E (Playwright) i API (pytest-django) |
| CP-US4-03 | Cercar un llibre per l'ISBN | CA3 | Alta | Correcte | E2E (Playwright) i API (pytest-django) |
| CP-US4-04 | Mostrar la informació completa d'un resultat | CA4 | Alta | Correcte | E2E (Playwright) i API (pytest-django) |
| CP-US4-05 | Mostrar la disponibilitat d'un llibre sense exemplars disponibles | CA4 | Alta | Correcte | E2E (Playwright) i API (pytest-django) |
| CP-US4-06 | Mostrar el missatge quan no hi ha resultats | CA5 | Alta | Error | E2E (Playwright) i API (pytest-django) |

## Casos

### CP-US4-01 · Cercar un llibre pel títol

- **Criteri d'acceptació**: CA1.
- **Precondicions**:
  - Les generals.
  - Hi ha almenys un llibre al catàleg amb un títol conegut per a la prova.
- **Passos**:
  1. Obrir la pantalla de cerca.
  2. Introduir el títol del llibre al camp de cerca.
  3. Executar la cerca.
- **Dades d'entrada**:
  - El títol del llibre definit en les dades de prova.
- **Resultat esperat**:
  - El llibre corresponent apareix entre els resultats.
  - El resultat mostra com a mínim el títol del llibre cercat.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: sí, comprovant el llibre visible a la interfície.
  - pytest-django: sí, comprovant que la resposta de la cerca inclou el llibre esperat.

### CP-US4-02 · Cercar un llibre per l'autor

- **Criteri d'acceptació**: CA2.
- **Precondicions**:
  - Les generals.
  - Hi ha almenys un llibre al catàleg associat a un autor conegut per a la prova.
- **Passos**:
  1. Obrir la pantalla de cerca.
  2. Introduir l'autor del llibre al camp de cerca.
  3. Executar la cerca.
- **Dades d'entrada**:
  - L'autor del llibre definit en les dades de prova.
- **Resultat esperat**:
  - El llibre associat a l'autor apareix entre els resultats.
  - El resultat mostra l'autor corresponent.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: sí, comprovant el resultat visible.
  - pytest-django: sí, comprovant que la resposta inclou el llibre esperat.

### CP-US4-03 · Cercar un llibre per l'ISBN

- **Criteri d'acceptació**: CA3.
- **Precondicions**:
  - Les generals.
  - Hi ha almenys un llibre amb un ISBN conegut per a la prova.
- **Passos**:
  1. Obrir la pantalla de cerca.
  2. Introduir l'ISBN del llibre al camp de cerca.
  3. Executar la cerca.
- **Dades d'entrada**:
  - L'ISBN del llibre definit en les dades de prova.
- **Resultat esperat**:
  - El llibre associat a l'ISBN apareix entre els resultats.
  - El resultat correspon al llibre que té l'ISBN introduït.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: sí, comprovant el resultat visible.
  - pytest-django: sí, comprovant que la resposta inclou el llibre esperat.

### CP-US4-04 · Mostrar la informació completa d'un resultat

- **Criteri d'acceptació**: CA4.
- **Precondicions**:
  - Les generals.
  - Hi ha un llibre de prova que tingui títol, autor, portada, informació de disponibilitat i valoracions.
- **Passos**:
  1. Cercar el llibre mitjançant una dada que el pugui identificar.
  2. Localitzar el llibre entre els resultats.
  3. Revisar la informació que mostra el resultat.
- **Dades d'entrada**:
  - Una dada de cerca del llibre de prova.
- **Resultat esperat**:
  - El resultat mostra el títol.
  - El resultat mostra l'autor.
  - El resultat mostra la portada.
  - El resultat mostra si hi ha exemplars disponibles.
  - El resultat mostra les seves valoracions.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: sí, comprovant els elements visibles del resultat.
  - pytest-django: sí, comprovant les dades retornades per al resultat.

### CP-US4-05 · Mostrar la disponibilitat d'un llibre sense exemplars disponibles

- **Criteri d'acceptació**: CA4.
- **Precondicions**:
  - Les generals.
  - Hi ha un llibre de prova sense exemplars disponibles.
- **Passos**:
  1. Cercar el llibre mitjançant una dada que el pugui identificar.
  2. Localitzar el llibre entre els resultats.
  3. Revisar la informació de disponibilitat.
- **Dades d'entrada**:
  - Una dada de cerca del llibre de prova sense exemplars disponibles.
- **Resultat esperat**:
  - El llibre apareix entre els resultats.
  - El resultat indica que no hi ha exemplars disponibles.
  - La resta de dades que corresponguin al resultat es mantenen visibles segons el CA4.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: sí, comprovant la informació de disponibilitat visible.
  - pytest-django: sí, comprovant el valor de disponibilitat retornat per l'API.

### CP-US4-06 · Mostrar el missatge quan no hi ha resultats

- **Criteri d'acceptació**: CA5.
- **Precondicions**:
  - Les generals.
  - El catàleg no conté cap llibre que coincideixi amb el text de cerca.
- **Passos**:
  1. Obrir la pantalla de cerca.
  2. Introduir un text que no coincideixi amb cap llibre del catàleg.
  3. Executar la cerca.
- **Dades d'entrada**:
  - Un text de cerca sense cap coincidència al catàleg.
- **Resultat esperat**:
  - No es mostra cap resultat de llibre.
  - Es mostra exactament el missatge:
    "No s'ha trobat el llibre cercat, assegura't que l'informació introduïda sigui correcta"
- **Tipus**: error.
- **Automatització**:
  - Playwright: sí, comprovant el missatge visible i l'absència de resultats.
  - pytest-django: sí, comprovant que la cerca no retorna resultats.
  
## Matriu de traçabilitat

| Criteri d'acceptació | Casos que el cobreixen | Cobertura |
|---|---|---|
| CA1: cerca pel títol | CP-US4-01 | Cobert |
| CA2: cerca per l'autor | CP-US4-02 | Cobert |
| CA3: cerca per l'ISBN | CP-US4-03 | Cobert |
| CA4: informació completa de cada resultat | CP-US4-04, CP-US4-05 | Cobert |
| CA5: missatge quan no hi ha resultats | CP-US4-06 | Cobert |

No hi ha criteris d'acceptació sense cobertura.

## Fora d'abast

- Distinció entre majúscules i minúscules.
- Tractament dels accents.
- Cerca amb camps buits o només amb espais.
- Caràcters especials.
- Límits de longitud del text de cerca.
- Paginació.
- Ordenació dels resultats.
- Filtres o combinacions de filtres.
- Missatges d'error diferents del missatge indicat al CA5.
- Contingut concret del catàleg de proves.

## Dubtes i criteris ambigus per confirmar

1. La cerca es fa amb un únic camp o hi ha camps separats per títol, autor i ISBN?
2. La cerca distingeix majúscules i minúscules?
3. La cerca distingeix accents?
4. Què ha de passar si el camp de cerca és buit o només conté espais?
5. Què ha de passar amb caràcters especials?
6. Hi ha un límit de caràcters per al text de cerca?
7. Els resultats es paginen? Si és així, quin és el nombre de resultats per pàgina?
8. Quin ordre han de seguir els resultats?
9. Hi ha filtres addicionals o combinacions de filtres?
10. Com es representa visualment que no hi ha exemplars disponibles?
11. Com es mostren exactament les valoracions quan un llibre no en té?
12. La portada és obligatòria per a tots els llibres? Què es mostra si un llibre no té portada?
13. El criteri CA5 exigeix que el missatge aparegui també quan el camp és buit, o només quan una cerca vàlida no troba coincidències?
