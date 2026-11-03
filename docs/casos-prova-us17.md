# Casos de prova: catàleg de la biblioteca (US17)

Casos de prova de la US17, escrits únicament a partir dels criteris d'acceptació
proporcionats. Els tests E2E amb Playwright i els tests de l'API amb pytest-django
en poden sortir.

Qualsevol canvi d'aquest document passa per pull request.

## Història i criteris d'acceptació

- **CA1**: la biblioteca pot afegir un llibre nou indicant títol, autor, ISBN,
  portada i nombre d'exemplars.
- **CA2**: el títol, l'autor, l'ISBN i el nombre d'exemplars són obligatoris;
  si en falta algun, es mostra l'error:
  "Omple tots els camps obligatoris per continuar".
- **CA3**: si l'ISBN no té un format vàlid, es mostra l'error:
  "L'ISBN introduït no és vàlid".
- **CA4**: si l'ISBN ja existeix al catàleg de la biblioteca, es mostra l'avís:
  "Aquest llibre ja és al teu catàleg, actualitza'n els exemplars".
- **CA5**: la biblioteca pot editar les dades d'un llibre del seu catàleg.
- **CA6**: la biblioteca pot modificar el nombre d'exemplars d'un llibre.
- **CA7**: la biblioteca pot retirar un llibre del seu catàleg.
- **CA8**: els canvis del catàleg es reflecteixen a la cerca i a la disponibilitat
  que veuen els usuaris.

## Entorn i precondicions generals

- Aplicació disponible en un entorn de proves.
- Compte de biblioteca de prova amb accés al catàleg.
- Usuari de prova amb accés a la cerca.
- Base de dades disponible i preparada per a cada cas.
- Les dades creades en un cas no es reutilitzen en un altre, tret que el cas
  indiqui explícitament que parteix d'un llibre existent.
- Els llibres, ISBN, portades i quantitats d'exemplars són dades sintètiques de
  prova.
- Les dades concretes del catàleg s'han de definir abans d'executar els casos.

## Dades de prova

| Dada | Valor |
|---|---|
| Compte de biblioteca | Compte de biblioteca de prova autoritzat |
| Llibre nou | Llibre sintètic que no existeix al catàleg de la biblioteca |
| Llibre existent | Llibre sintètic que ja existeix al catàleg de la biblioteca |
| ISBN nou | ISBN de prova amb format vàlid, pendent de concretar |
| ISBN existent | ISBN de prova ja present al catàleg de la biblioteca |
| Portada | Dada de prova en el format que s'acordi |
| Nombre d'exemplars | Valor de prova no negatiu, pendent de concretar |
| Cerca d'usuari | Cerca que permeti localitzar el llibre de prova |

Els valors concrets de l'ISBN, la portada i el nombre d'exemplars no es fixen
en aquest document perquè els criteris no en defineixen el format ni els límits.

## Resum

| ID | Cas | Criteri d'acceptació | Prioritat | Tipus | Execució proposada |
|---|---|---|---|---|---|
| CP-US17-01 | Afegir un llibre nou amb totes les dades | CA1 | Alta | Correcte | E2E i API |
| CP-US17-02 | Afegir un llibre amb el títol buit | CA2 | Alta | Error | E2E i API |
| CP-US17-03 | Afegir un llibre amb l'autor buit | CA2 | Alta | Error | E2E i API |
| CP-US17-04 | Afegir un llibre amb l'ISBN buit | CA2 | Alta | Error | E2E i API |
| CP-US17-05 | Afegir un llibre amb els exemplars buits | CA2 | Alta | Error | E2E i API |
| CP-US17-06 | Afegir un llibre amb tots els camps obligatoris buits | CA2 | Alta | Error | E2E i API |
| CP-US17-07 | Afegir un llibre amb un ISBN invàlid | CA3 | Alta | Error | E2E i API |
| CP-US17-08 | Afegir un llibre amb un ISBN nou vàlid | CA1, CA3 | Alta | Correcte | E2E i API |
| CP-US17-09 | Afegir un llibre amb un ISBN duplicat | CA4 | Alta | Error | E2E i API |
| CP-US17-10 | Editar les dades d'un llibre | CA5 | Alta | Correcte | E2E i API |
| CP-US17-11 | Modificar el nombre d'exemplars | CA6 | Alta | Correcte | E2E i API |
| CP-US17-12 | Retirar un llibre del catàleg | CA7 | Alta | Correcte | E2E i API |
| CP-US17-13 | Reflectir a la cerca un llibre afegit | CA8 | Alta | Correcte | E2E i API |
| CP-US17-14 | Reflectir a la cerca les dades editades | CA8 | Alta | Correcte | E2E i API |
| CP-US17-15 | Reflectir a la disponibilitat el canvi d'exemplars | CA8 | Alta | Correcte | E2E i API |
| CP-US17-16 | Deixar de mostrar a la cerca un llibre retirat | CA8 | Alta | Correcte | E2E i API |

## Casos

### CP-US17-01 · Afegir un llibre nou amb totes les dades

- **Criteri d'acceptació**: CA1.
- **Precondicions**:
  - Les generals.
  - El llibre no existeix al catàleg de la biblioteca.
- **Passos**:
  1. Accedir a la gestió del catàleg amb el compte de biblioteca.
  2. Seleccionar l'opció per afegir un llibre.
  3. Introduir el títol, l'autor, l'ISBN, la portada i el nombre d'exemplars.
  4. Confirmar l'alta del llibre.
- **Dades d'entrada**:
  - Títol, autor, ISBN, portada i nombre d'exemplars de prova.
- **Resultat esperat**:
  - El llibre s'afegeix al catàleg de la biblioteca.
  - El llibre apareix amb les dades introduïdes.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: sí, comprovant l'alta visible a la interfície.
  - pytest-django: sí, comprovant el registre creat a l'API i la base de dades.

### CP-US17-02 · Afegir un llibre amb el títol buit

- **Criteri d'acceptació**: CA2.
- **Precondicions**:
  - Les generals.
  - La resta de dades obligatòries són vàlides.
- **Passos**:
  1. Obrir el formulari d'alta.
  2. Deixar buit el títol.
  3. Omplir l'autor, l'ISBN i el nombre d'exemplars amb dades vàlides.
  4. Intentar continuar.
- **Dades d'entrada**:
  - Títol buit.
  - Autor, ISBN i nombre d'exemplars de prova.
- **Resultat esperat**:
  - No s'afegeix el llibre.
  - Es mostra exactament:
    "Omple tots els camps obligatoris per continuar".
- **Tipus**: error.
- **Automatització**:
  - Playwright: sí.
  - pytest-django: sí.

### CP-US17-03 · Afegir un llibre amb l'autor buit

- **Criteri d'acceptació**: CA2.
- **Precondicions**:
  - Les generals.
  - La resta de dades obligatòries són vàlides.
- **Passos**:
  1. Obrir el formulari d'alta.
  2. Deixar buit l'autor.
  3. Omplir el títol, l'ISBN i el nombre d'exemplars amb dades vàlides.
  4. Intentar continuar.
- **Dades d'entrada**:
  - Autor buit.
  - Títol, ISBN i nombre d'exemplars de prova.
- **Resultat esperat**:
  - No s'afegeix el llibre.
  - Es mostra exactament:
    "Omple tots els camps obligatoris per continuar".
- **Tipus**: error.
- **Automatització**:
  - Playwright: sí.
  - pytest-django: sí.

### CP-US17-04 · Afegir un llibre amb l'ISBN buit

- **Criteri d'acceptació**: CA2.
- **Precondicions**:
  - Les generals.
  - La resta de dades obligatòries són vàlides.
- **Passos**:
  1. Obrir el formulari d'alta.
  2. Deixar buit l'ISBN.
  3. Omplir el títol, l'autor i el nombre d'exemplars amb dades vàlides.
  4. Intentar continuar.
- **Dades d'entrada**:
  - ISBN buit.
  - Títol, autor i nombre d'exemplars de prova.
- **Resultat esperat**:
  - No s'afegeix el llibre.
  - Es mostra exactament:
    "Omple tots els camps obligatoris per continuar".
- **Tipus**: error.
- **Automatització**:
  - Playwright: sí.
  - pytest-django: sí.

### CP-US17-05 · Afegir un llibre amb el nombre d'exemplars buit

- **Criteri d'acceptació**: CA2.
- **Precondicions**:
  - Les generals.
  - La resta de dades obligatòries són vàlides.
- **Passos**:
  1. Obrir el formulari d'alta.
  2. Deixar buit el nombre d'exemplars.
  3. Omplir el títol, l'autor i l'ISBN amb dades vàlides.
  4. Intentar continuar.
- **Dades d'entrada**:
  - Nombre d'exemplars buit.
  - Títol, autor i ISBN de prova.
- **Resultat esperat**:
  - No s'afegeix el llibre.
  - Es mostra exactament:
    "Omple tots els camps obligatoris per continuar".
- **Tipus**: error.
- **Automatització**:
  - Playwright: sí.
  - pytest-django: sí.

### CP-US17-06 · Afegir un llibre amb tots els camps obligatoris buits

- **Criteri d'acceptació**: CA2.
- **Precondicions**:
  - Les generals.
- **Passos**:
  1. Obrir el formulari d'alta.
  2. Deixar buits el títol, l'autor, l'ISBN i el nombre d'exemplars.
  3. Intentar continuar.
- **Dades d'entrada**:
  - Títol buit.
  - Autor buit.
  - ISBN buit.
  - Nombre d'exemplars buit.
- **Resultat esperat**:
  - No s'afegeix el llibre.
  - Es mostra exactament:
    "Omple tots els camps obligatoris per continuar".
- **Tipus**: error.
- **Automatització**:
  - Playwright: sí.
  - pytest-django: sí.

### CP-US17-07 · Afegir un llibre amb un ISBN invàlid

- **Criteri d'acceptació**: CA3.
- **Precondicions**:
  - Les generals.
  - La resta de dades obligatòries són vàlides.
- **Passos**:
  1. Obrir el formulari d'alta.
  2. Introduir un ISBN amb un format que el Product Owner confirmi com a invàlid.
  3. Omplir la resta de camps obligatoris.
  4. Intentar continuar.
- **Dades d'entrada**:
  - Exemple provisional: ISBN amb una longitud incorrecta.
  - Exemple provisional: ISBN amb caràcters no permesos.
  - Exemple provisional: ISBN amb dígit de control incorrecte.
- **Resultat esperat**:
  - No s'afegeix el llibre.
  - Es mostra exactament:
    "L'ISBN introduït no és vàlid".
- **Tipus**: error.
- **Automatització**:
  - Playwright: sí, quan es confirmi el format.
  - pytest-django: sí, quan es confirmi el format.

### CP-US17-08 · Afegir un llibre amb un ISBN nou vàlid

- **Criteri d'acceptació**: CA1 i CA3.
- **Precondicions**:
  - Les generals.
  - L'ISBN no existeix al catàleg de la biblioteca.
  - El format que es farà servir ha estat confirmat com a vàlid.
- **Passos**:
  1. Obrir el formulari d'alta.
  2. Introduir totes les dades del llibre, inclòs un ISBN nou i vàlid.
  3. Confirmar l'alta.
- **Dades d'entrada**:
  - Llibre sintètic amb ISBN nou i vàlid.
- **Resultat esperat**:
  - El llibre s'afegeix al catàleg.
  - No es mostra l'avís de duplicat.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: sí.
  - pytest-django: sí.

### CP-US17-09 · Afegir un llibre amb un ISBN duplicat

- **Criteri d'acceptació**: CA4.
- **Precondicions**:
  - Les generals.
  - Hi ha un llibre al catàleg de la biblioteca amb l'ISBN de prova.
- **Passos**:
  1. Obrir el formulari d'alta.
  2. Introduir un llibre amb l'ISBN existent.
  3. Introduir la resta de dades necessàries.
  4. Intentar confirmar l'alta.
- **Dades d'entrada**:
  - ISBN ja existent al catàleg de la biblioteca.
- **Resultat esperat**:
  - No es crea un segon llibre amb el mateix ISBN al catàleg.
  - Es mostra exactament l'avís:
    "Aquest llibre ja és al teu catàleg, actualitza'n els exemplars".
- **Tipus**: error.
- **Automatització**:
  - Playwright: sí.
  - pytest-django: sí.

### CP-US17-10 · Editar les dades d'un llibre

- **Criteri d'acceptació**: CA5.
- **Precondicions**:
  - Les generals.
  - Hi ha un llibre al catàleg de la biblioteca.
- **Passos**:
  1. Obrir el llibre existent.
  2. Seleccionar l'opció d'edició.
  3. Modificar les dades que es vulguin comprovar.
  4. Desar els canvis.
- **Dades d'entrada**:
  - Dades actualitzades del llibre de prova.
- **Resultat esperat**:
  - Les dades modificades es mostren al catàleg.
  - Les dades que no s'han modificat es mantenen.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: sí.
  - pytest-django: sí.

### CP-US17-11 · Modificar el nombre d'exemplars

- **Criteri d'acceptació**: CA6.
- **Precondicions**:
  - Les generals.
  - Hi ha un llibre al catàleg amb un nombre conegut d'exemplars.
- **Passos**:
  1. Obrir el llibre existent.
  2. Seleccionar l'opció per modificar els exemplars.
  3. Introduir una quantitat diferent.
  4. Desar el canvi.
- **Dades d'entrada**:
  - Nombre inicial d'exemplars de prova.
  - Nombre nou d'exemplars de prova.
- **Resultat esperat**:
  - El catàleg mostra el nombre nou d'exemplars.
  - El nombre anterior deixa de ser el valor mostrat.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: sí.
  - pytest-django: sí.

### CP-US17-12 · Retirar un llibre del catàleg

- **Criteri d'acceptació**: CA7.
- **Precondicions**:
  - Les generals.
  - Hi ha un llibre al catàleg de la biblioteca que es pugui retirar.
- **Passos**:
  1. Obrir el llibre existent.
  2. Seleccionar l'opció per retirar-lo.
  3. Confirmar la retirada, si el flux ho demana.
- **Dades d'entrada**:
  - Llibre de prova existent al catàleg.
- **Resultat esperat**:
  - El llibre deixa de formar part del catàleg de la biblioteca.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: sí, comprovant que desapareix del catàleg.
  - pytest-django: sí, comprovant l'estat a l'API o a la base de dades.

### CP-US17-13 · Reflectir a la cerca un llibre afegit

- **Criteri d'acceptació**: CA8.
- **Precondicions**:
  - Les generals.
  - El llibre no existeix inicialment al catàleg de la biblioteca.
- **Passos**:
  1. Afegir el llibre al catàleg amb dades vàlides.
  2. Accedir a la cerca com a usuari.
  3. Cercar el llibre afegit.
- **Dades d'entrada**:
  - Títol o altra dada que identifiqui el llibre afegit.
- **Resultat esperat**:
  - El llibre apareix als resultats de la cerca.
  - La informació visible correspon al llibre afegit.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: sí, cobrint el flux de biblioteca i usuari.
  - pytest-django: sí, comprovant la resposta de cerca.

### CP-US17-14 · Reflectir a la cerca les dades editades

- **Criteri d'acceptació**: CA8.
- **Precondicions**:
  - Les generals.
  - Hi ha un llibre al catàleg i es coneixen les seves dades inicials.
- **Passos**:
  1. Editar les dades del llibre.
  2. Desar els canvis.
  3. Accedir a la cerca com a usuari.
  4. Cercar el llibre amb les dades actualitzades.
- **Dades d'entrada**:
  - Dades inicials i dades actualitzades del llibre de prova.
- **Resultat esperat**:
  - La cerca mostra les dades actualitzades.
  - Les dades antigues ja no es mostren com a dades actuals del llibre.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: sí.
  - pytest-django: sí.

### CP-US17-15 · Reflectir a la disponibilitat el canvi d'exemplars

- **Criteri d'acceptació**: CA8.
- **Precondicions**:
  - Les generals.
  - Hi ha un llibre amb una quantitat inicial d'exemplars coneguda.
- **Passos**:
  1. Consultar la disponibilitat del llibre com a usuari.
  2. Modificar el nombre d'exemplars des del catàleg de la biblioteca.
  3. Tornar a consultar el llibre des de la cerca.
- **Dades d'entrada**:
  - Quantitat inicial d'exemplars.
  - Quantitat nova d'exemplars.
- **Resultat esperat**:
  - La disponibilitat visible a la cerca reflecteix la quantitat nova.
  - Si el canvi fa que no hi hagi exemplars disponibles, la cerca ho reflecteix.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: sí.
  - pytest-django: sí.

### CP-US17-16 · Deixar de mostrar a la cerca un llibre retirat

- **Criteri d'acceptació**: CA7 i CA8.
- **Precondicions**:
  - Les generals.
  - Hi ha un llibre del catàleg que també és visible a la cerca.
- **Passos**:
  1. Comprovar que el llibre apareix a la cerca.
  2. Retirar el llibre del catàleg de la biblioteca.
  3. Tornar a cercar el llibre com a usuari.
- **Dades d'entrada**:
  - Llibre de prova existent i visible a la cerca.
- **Resultat esperat**:
  - El llibre deixa de formar part del catàleg de la biblioteca.
  - La cerca ja no mostra el llibre retirat, segons el comportament definit per CA8.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: sí.
  - pytest-django: sí.

## Matriu de traçabilitat

| Criteri d'acceptació | Casos que el cobreixen | Cobertura |
|---|---|---|
| CA1: afegir un llibre nou | CP-US17-01, CP-US17-08 | Cobert |
| CA2: camps obligatoris i missatge d'error | CP-US17-02, CP-US17-03, CP-US17-04, CP-US17-05, CP-US17-06 | Cobert |
| CA3: ISBN amb format invàlid | CP-US17-07, CP-US17-08 | Cobert |
| CA4: ISBN duplicat i avís | CP-US17-08, CP-US17-09 | Cobert |
| CA5: editar dades d'un llibre | CP-US17-10, CP-US17-14 | Cobert |
| CA6: modificar exemplars | CP-US17-11, CP-US17-15 | Cobert |
| CA7: retirar un llibre | CP-US17-12, CP-US17-16 | Cobert |
| CA8: reflectir canvis a la cerca i disponibilitat | CP-US17-13, CP-US17-14, CP-US17-15, CP-US17-16 | Cobert |

No hi ha criteris d'acceptació sense cobertura.

## Fora d'abast

- Gestió de llibres per rols diferents del de biblioteca.
- Permisos concrets d'accés al catàleg.
- Préstecs i comandes.
- Paginació, ordenació o filtres de la cerca.
- Format visual concret dels formularis.
- Missatges diferents dels especificats als criteris.
- Validacions de portada no indicades als criteris.
- Validacions del nombre d'exemplars no indicades als criteris.
- Comportament de llibres amb exemplars prestats o demanats.

## Dubtes i criteris ambigus per confirmar

1. Quin format d'ISBN és vàlid: ISBN-10, ISBN-13 o tots dos?
2. S'accepten ISBN amb guions o espais?
3. Cal validar el dígit de control de l'ISBN?
4. La portada és obligatòria o opcional?
5. Quins formats i mides de portada s'accepten?
6. Quins valors accepta el nombre d'exemplars?
   - S'accepta el valor zero?
   - S'accepten valors negatius?
   - S'accepten decimals?
   - Hi ha un màxim?
7. El duplicat d'ISBN només s'ha de comprovar dins del catàleg de la mateixa biblioteca?
8. Quins camps es poden editar a CA5?
9. Es pot editar l'ISBN?
10. CA5 aplica les mateixes validacions de camps obligatoris i ISBN que CA2 i CA3?
11. Què passa si es retira un llibre amb exemplars prestats o demanats?
12. Després de retirar un llibre, ha de desaparèixer sempre de la cerca dels usuaris?
13. En quin moment i pantalla s'ha de verificar CA8?
14. Com es mostra exactament la disponibilitat als usuaris?
15. La cerca ha de reflectir els canvis immediatament o després d'actualitzar la pàgina?
16. Quin rol pot gestionar el catàleg i què veuen els altres rols?
17. En CA4, després de detectar un ISBN duplicat, l'usuari ha de poder actualitzar
    els exemplars en el mateix flux o només ha de veure l'avís?
