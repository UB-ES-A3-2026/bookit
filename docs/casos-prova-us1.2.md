# Casos de prova: registre de biblioteca (US1.2)

Casos de prova de la US1.2, escrits únicament a partir dels criteris d'acceptació
facilitats per al registre de biblioteca.

## Història i criteris d'acceptació

- **CA1**: a la pantalla de registre hi ha un botó "Registrar-se com a biblioteca".
- **CA2**: el formulari demana el nom de la biblioteca i un correu electrònic, tots dos obligatoris.
- **CA3**: si falta algun camp o el correu no té un format vàlid, no es pot enviar el formulari i es mostra el missatge:
  "Algún dels camps no és vàlid o no s'ha introduit, torna a intentar-ho".
- **CA4**: en enviar el formulari, s'envia un correu de verificació a l'adreça indicada.
- **CA5**: si el correu ja està registrat, es mostra l'error:
  "Aquest correu correspon a un compte existent, torna a probar amb un altre correu".
- **CA6**: el compte no queda actiu fins que no es verifica el correu.
- **CA7**: en clicar l'enllaç de verificació, el compte s'activa i la biblioteca ja pot accedir a l'aplicació.

## Entorn i precondicions generals

- Aplicació disponible i pantalla de registre accessible.
- Navegador sense una sessió iniciada, excepte en els casos en què s'indiqui el contrari.
- Per als casos de registre correcte, s'utilitza una adreça de correu que no està registrada.
- Per al cas de duplicat, existeix prèviament un compte associat al correu utilitzat.
- Per als casos de verificació, es pot consultar el correu rebut i clicar l'enllaç de verificació.

## Resum

| ID | Cas | Criteri | Tipus | Execució proposada |
|---|---|---|---|---|
| CP-US1.2-01 | Botó per registrar-se com a biblioteca | CA1 | correcte | E2E (Playwright) |
| CP-US1.2-02 | Formulari amb els camps obligatoris | CA2 | correcte | E2E (Playwright) |
| CP-US1.2-03 | Enviar sense el nom de la biblioteca | CA2, CA3 | error | E2E (Playwright) |
| CP-US1.2-04 | Enviar sense el correu electrònic | CA2, CA3 | error | E2E (Playwright) |
| CP-US1.2-05 | Enviar amb un correu de format invàlid | CA3 | error | E2E (Playwright) |
| CP-US1.2-06 | Registre correcte i enviament del correu de verificació | CA4 | correcte | E2E (Playwright) i pytest-django |
| CP-US1.2-07 | Correu ja registrat | CA5 | error | E2E (Playwright) i pytest-django |
| CP-US1.2-08 | Compte inactiu abans de verificar el correu | CA6 | correcte | pytest-django |
| CP-US1.2-09 | Verificar el correu i accedir a l'aplicació | CA7 | correcte | E2E (Playwright) i pytest-django |

No es defineixen casos de límit perquè els criteris no especifiquen longituds màximes,
longituds mínimes ni altres valors límit.

## Casos

### CP-US1.2-01 · Botó per registrar-se com a biblioteca

- **Criteri d'acceptació**: CA1.
- **Precondicions**: les generals.
- **Passos**:
  1. Obrir la pantalla de registre.
  2. Localitzar l'opció per registrar-se com a biblioteca.
- **Dades d'entrada**: cap.
- **Resultat esperat**:
  - Es mostra un botó amb el text exacte "Registrar-se com a biblioteca".

### CP-US1.2-02 · Formulari amb els camps obligatoris

- **Criteri d'acceptació**: CA2.
- **Precondicions**: les generals.
- **Passos**:
  1. Obrir el formulari de registre de biblioteca.
  2. Comprovar els camps disponibles.
- **Dades d'entrada**: cap.
- **Resultat esperat**:
  - El formulari demana el nom de la biblioteca.
  - El formulari demana un correu electrònic.
  - Tots dos camps estan indicats com a obligatoris.

### CP-US1.2-03 · Enviar sense el nom de la biblioteca

- **Criteri d'acceptació**: CA2 i CA3.
- **Precondicions**: les generals.
- **Passos**:
  1. Obrir el formulari de registre de biblioteca.
  2. Deixar buit el camp del nom de la biblioteca.
  3. Introduir un correu electrònic vàlid.
  4. Intentar enviar el formulari.
- **Dades d'entrada**:
  - Nom de la biblioteca: buit.
  - Correu electrònic: correu amb format vàlid.
- **Resultat esperat**:
  - El formulari no es pot enviar.
  - Es mostra el missatge exacte: "Algún dels camps no és vàlid o no s'ha introduït, torna a intentar-ho".

### CP-US1.2-04 · Enviar sense el correu electrònic

- **Criteri d'acceptació**: CA2 i CA3.
- **Precondicions**: les generals.
- **Passos**:
  1. Obrir el formulari de registre de biblioteca.
  2. Introduir un nom de biblioteca.
  3. Deixar buit el camp del correu electrònic.
  4. Intentar enviar el formulari.
- **Dades d'entrada**:
  - Nom de la biblioteca: nom no buit.
  - Correu electrònic: buit.
- **Resultat esperat**:
  - El formulari no es pot enviar.
  - Es mostra el missatge exacte: "Algún dels camps no és vàlid o no s'ha introduït, torna a intentar-ho".

### CP-US1.2-05 · Enviar amb un correu de format invàlid

- **Criteri d'acceptació**: CA3.
- **Precondicions**: les generals.
- **Passos**:
  1. Obrir el formulari de registre de biblioteca.
  2. Introduir un nom de biblioteca.
  3. Introduir un correu electrònic amb format invàlid.
  4. Intentar enviar el formulari.
- **Dades d'entrada**:
  - Nom de la biblioteca: nom no buit.
  - Correu electrònic: valor amb format de correu invàlid.
- **Resultat esperat**:
  - El formulari no es pot enviar.
  - Es mostra el missatge exacte: "Algún dels camps no és vàlid o no s'ha introduït, torna a intentar-ho".

### CP-US1.2-06 · Registre correcte i enviament del correu de verificació

- **Criteri d'acceptació**: CA4.
- **Precondicions**: les generals. El correu utilitzat no està registrat.
- **Passos**:
  1. Obrir el formulari de registre de biblioteca.
  2. Introduir un nom de biblioteca.
  3. Introduir un correu electrònic vàlid i no registrat.
  4. Enviar el formulari.
  5. Consultar la bústia de l'adreça indicada.
- **Dades d'entrada**:
  - Nom de la biblioteca: nom no buit.
  - Correu electrònic: correu amb format vàlid i no registrat.
- **Resultat esperat**:
  - El formulari s'envia correctament.
  - Es rep un correu de verificació a l'adreça indicada.

### CP-US1.2-07 · Correu ja registrat

- **Criteri d'acceptació**: CA5.
- **Precondicions**: les generals. El correu utilitzat ja està associat a un compte.
- **Passos**:
  1. Obrir el formulari de registre de biblioteca.
  2. Introduir un nom de biblioteca.
  3. Introduir el correu ja registrat.
  4. Enviar el formulari.
- **Dades d'entrada**:
  - Nom de la biblioteca: nom no buit.
  - Correu electrònic: adreça ja registrada.
- **Resultat esperat**:
  - Es mostra l'error exacte: "Aquest correu correspon a un compte existent, torna a probar amb un altre correu".
  - El registre no es completa.

### CP-US1.2-08 · Compte inactiu abans de verificar el correu

- **Criteri d'acceptació**: CA6.
- **Precondicions**: s'ha completat un registre correcte i s'ha rebut el correu de verificació, però encara no s'ha clicat l'enllaç.
- **Passos**:
  1. Consultar l'estat del compte creat abans de clicar l'enllaç de verificació.
- **Dades d'entrada**: compte creat amb un correu vàlid.
- **Resultat esperat**:
  - El compte no està actiu abans de verificar el correu.

### CP-US1.2-09 · Verificar el correu i accedir a l'aplicació

- **Criteri d'acceptació**: CA7.
- **Precondicions**: s'ha completat un registre correcte i el compte encara no està verificat.
- **Passos**:
  1. Obrir el correu de verificació rebut.
  2. Clicar l'enllaç de verificació.
  3. Intentar accedir a l'aplicació amb el compte de biblioteca.
- **Dades d'entrada**: enllaç de verificació rebut al correu indicat durant el registre.
- **Resultat esperat**:
  - El compte s'activa.
  - La biblioteca pot accedir a l'aplicació.

## Fora d'abast

- Longituds màximes o mínimes dels camps.
- Missatges diferents dels especificats als criteris d'acceptació.
- Comportament d'un enllaç de verificació invàlid o caducat.
- Comportament d'un correu duplicat amb diferències de majúscules o espais.
- Detalls de la interfície o de la resposta que no apareixen als criteris.

## Matriu de traçabilitat

| Criteri | Descripció resumida | Casos que el cobreixen | Cobertura |
|---|---|---|---|
| CA1 | Botó "Registrar-se com a biblioteca" | CP-US1.2-01 | Cobert |
| CA2 | Nom i correu obligatoris | CP-US1.2-02, CP-US1.2-03, CP-US1.2-04 | Cobert |
| CA3 | Camps absents o correu invàlid impedeixen l'enviament i mostren el missatge | CP-US1.2-03, CP-US1.2-04, CP-US1.2-05 | Cobert |
| CA4 | Enviament del correu de verificació | CP-US1.2-06 | Cobert |
| CA5 | Error per correu ja registrat | CP-US1.2-07 | Cobert |
| CA6 | Compte inactiu abans de verificar | CP-US1.2-08 | Cobert |
| CA7 | Verificació activa el compte i permet accedir | CP-US1.2-09 | Cobert |

No hi ha criteris sense cobertura.

## Dubtes

- Els criteris no indiquen el format concret que s'ha de considerar invàlid per al correu.
- Els criteris no indiquen com s'ha d'observar que el compte està actiu o inactiu.
- Els criteris no especifiquen quina pantalla, ruta o resposta confirma que la biblioteca pot accedir a l'aplicació.
- Els criteris no especifiquen si el correu de verificació ha d'arribar immediatament ni cap contingut concret del missatge.
- Els criteris no especifiquen què ha de passar si l'enllaç de verificació és invàlid o ha caducat.
- No hi ha cap criteri que defineixi valors límit dels camps.
