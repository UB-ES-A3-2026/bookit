# Casos de prova: registre de repartidor (US1.1)

Casos de prova de la US1.1 (tasca US1.1-T14), basats en els criteris d'acceptació de la història i en les
decisions ja reflectides en el frontend i el contracte de l'API. Els tests E2E amb Playwright (US1.1-T15) i la
prova manual amb el Product Owner (US1.1-T16) en surten. Qualsevol canvi d'aquest document passa per pull request.

## Història i criteris d'acceptació

> **COM A** persona que vol ser repartidora **VULL** registrar les meves dades personals i les dades del vehicle
> **PER AIXÍ** poder accedir a la vista de repartidor després de la validació.

- **CA1**: es sol·liciten i són obligatoris els camps Nom, cognoms, DNI/NIE, correu electrònic, telèfon, tipus de
  vehicle, matrícula si escau i número de seguretat social.
- **CA2**: es comprova que el correu electrònic, el telèfon i el DNI/NIE tinguin un format vàlid abans de
  permetre l'enviament.
- **CA3**: si el correu electrònic o el DNI/NIE ja estan registrats al sistema, es mostra el missatge
  "DNI/correu ja registrat" i s'impedeix el registre.
- **CA4**: si s'intenta enviar el formulari amb camps buits o dades incorrectes, es mostren missatges d'error
  visuals (inline) sota els camps afectats.
- **CA5**: en completar el registre, el compte es crea en estat "Pendent de validació" i es mostra una pantalla
  de confirmació de la sol·licitud.
- **CA6**: si les dades del repartidor són correctes després de la validació, el registre es realitza correctament
  i s'accedeix a la vista de repartidor.
- **CA7**: si les dades del repartidor són incorrectes després de la validació, el registre no es completa, es
  mostra el missatge "Validació incompleta" i es torna a la pantalla de registre.

### Decisions confirmades pel frontend i el contracte de l'API

Aquestes decisions no estan descrites amb aquest nivell de detall en els criteris d'acceptació, però sí en el
frontend, les validacions compartides i el contracte de l'API:

- Els únics tipus de vehicle disponibles són `bici`, `moto` i `cotxe`.
- La matrícula és obligatòria per a `moto` i `cotxe`.
- La matrícula no s'aplica a `bici`: el camp s'amaga i no s'envia a l'API.
- El DNI/NIE accepta un DNI amb 8 xifres i lletra de control o un NIE amb prefix `X`, `Y` o `Z`, 7 xifres i
  lletra de control.
- El telèfon és espanyol, té 9 xifres, comença per `6`, `7`, `8` o `9` i pot portar el prefix `+34`.
- La matrícula té 4 xifres i 3 consonants, sense vocals, `Ñ` ni `Q`.
- El número de la Seguretat Social té 12 xifres.
- Els espais, guions i barres es poden utilitzar com a separadors en els camps normalitzats.
- El registre correcte redirigeix a `/registre/confirmacio`.
- La pantalla de confirmació mostra l'estat "Pendent de validació".

La contrasenya i la confirmació de contrasenya existeixen actualment al formulari, però no apareixen en els criteris
d'acceptació proporcionats. Per tant, no es tracten com un criteri propi d'aquest document.

## Entorn i precondicions generals

- Aplicació disponible en un entorn de proves.
- La pantalla de registre de repartidor és accessible a `/registre`.
- Navegador sense cap sessió iniciada, excepte en els casos en què el flux de validació ho requereixi.
- Per als casos de duplicats, existeix prèviament un compte amb el correu electrònic i/o el DNI/NIE indicats.
- Les dades que no s'indiquin explícitament com a incorrectes són vàlides i completes.
- Quan s'indica que un camp queda buit, no es modifica cap altre camp del formulari.
- Per als casos que requereixen contrasenya, es fa servir una contrasenya vàlida i la confirmació corresponent,
  perquè el formulari actual la sol·licita abans d'enviar el registre.
- Els casos de validació posterior requereixen que existeixi el flux d'acceptació o rebuig de sol·licituds.
  Aquest flux encara no està definit ni implementat completament.

## Estat actual conegut de la implementació

- El frontend envia el registre a `/api/auth/register/repartidor/`.
- Els tests E2E simulen les respostes d'aquest endpoint.
- El contracte de l'API defineix aquest endpoint, però la ruta backend encara no està exposada a
  `backend/usuaris/urls_auth.py`.
- El model defineix els estats `pendent`, `validat` i `rebutjat`.
- No existeix encara una vista de repartidor, una ruta protegida, un endpoint de validació ni un flux complet
  d'inici de sessió posterior.
- Per aquest motiu, els casos CP-US1.1-15 i CP-US1.1-16 queden especificats però bloquejats fins que es defineixi
  i implementi el flux de validació.

## Dades de prova

### Dades vàlides per a moto o cotxe

| Camp | Valor vàlid |
|---|---|
| Nom | `Pol` |
| Cognoms | `Ferrer Soler` |
| DNI/NIE | `12345678Z` |
| Correu electrònic | `repartidor@example.com` |
| Telèfon | `+34 612 345 678` |
| Tipus de vehicle | `moto` |
| Matrícula | `1234 BCD` |
| Número de seguretat social | `28/12345678/90` |
| Contrasenya del formulari | `Llibres-de-tardor-24` |
| Confirmació de contrasenya | `Llibres-de-tardor-24` |

### Dades vàlides per a bicicleta

| Camp | Valor vàlid |
|---|---|
| Nom | `Laia` |
| Cognoms | `Martí Roca` |
| DNI/NIE | `X1234567L` |
| Correu electrònic | `laia.marti@example.com` |
| Telèfon | `612345678` |
| Tipus de vehicle | `bici` |
| Matrícula | No s'informa ni s'envia |
| Número de seguretat social | `081234567890` |
| Contrasenya del formulari | `Llibres-de-tardor-24` |
| Confirmació de contrasenya | `Llibres-de-tardor-24` |

### Exemples de dades invàlides

| Camp | Valor invàlid | Motiu |
|---|---|---|
| Correu electrònic | `repartidor@` | Format incomplet |
| DNI/NIE | `12345678A` | Lletra de control incorrecta |
| DNI/NIE | `1234567Z` | Nombre incorrecte de xifres |
| Telèfon | `612345` | Menys de 9 xifres |
| Telèfon | `512345678` | Prefix inicial no permès |
| Telèfon | `+33 612345678` | Prefix internacional no permès |
| Matrícula | `1234 ABC` | Conté una vocal |
| Matrícula | `1234 BCÑ` | Conté `Ñ` |
| Matrícula | `1234 BCQ` | Conté `Q` |
| Número de Seguretat Social | `28123456789` | Menys de 12 xifres |
| Número de Seguretat Social | `2812345678901` | Més de 12 xifres |
| Número de Seguretat Social | `28/1234567A/90` | Conté una lletra |

## Resum

| ID | Cas | Criteri d'acceptació | Tipus | Execució proposada | Estat |
|---|---|---|---|---|---|
| CP-US1.1-01 | El formulari mostra els camps obligatoris | CA1 | Correcte | E2E (Playwright) | Preparat |
| CP-US1.1-02 | Registre correcte amb moto | CA1, CA5 | Correcte | E2E (Playwright) i pytest-django | Preparat |
| CP-US1.1-03 | Registre correcte amb bicicleta sense matrícula | CA1, CA5 | Límit | E2E (Playwright) i pytest-django | Preparat |
| CP-US1.1-04 | Formulari amb tots els camps obligatoris buits | CA1, CA4 | Error | E2E (Playwright) i pytest-django | Preparat |
| CP-US1.1-05 | Un camp personal obligatori buit | CA1, CA4 | Error | E2E (Playwright) i pytest-django | Preparat |
| CP-US1.1-06 | Un camp de repartidor obligatori buit | CA1, CA4 | Error | E2E (Playwright) i pytest-django | Preparat |
| CP-US1.1-07 | Correu electrònic amb format invàlid | CA2, CA4 | Error | E2E (Playwright) i pytest-django | Preparat |
| CP-US1.1-08 | Telèfon amb format invàlid | CA2, CA4 | Error | E2E (Playwright) i pytest-django | Preparat |
| CP-US1.1-09 | DNI/NIE amb format invàlid | CA2, CA4 | Error | E2E (Playwright) i pytest-django | Preparat |
| CP-US1.1-10 | Correu electrònic duplicat | CA3, CA4 | Error | E2E (Playwright) i pytest-django | Preparat |
| CP-US1.1-11 | DNI/NIE duplicat | CA3, CA4 | Error | E2E (Playwright) i pytest-django | Preparat |
| CP-US1.1-12 | Correu electrònic i DNI/NIE duplicats | CA3, CA4 | Error | E2E (Playwright) i pytest-django | Preparat |
| CP-US1.1-13 | Tipus de vehicle no permès | CA1, CA4 | Error | pytest-django | Preparat |
| CP-US1.1-14 | Matrícula absent per a moto o cotxe | CA1, CA4 | Error | E2E (Playwright) i pytest-django | Preparat |
| CP-US1.1-15 | Matrícula amb format invàlid | CA2, CA4 | Error | E2E (Playwright) i pytest-django | Preparat |
| CP-US1.1-16 | Número de Seguretat Social amb format invàlid | CA4 | Error | E2E (Playwright) i pytest-django | Preparat |
| CP-US1.1-17 | Errors inline sota els camps afectats | CA4 | Correcte | E2E (Playwright) | Preparat |
| CP-US1.1-18 | Confirmació del registre pendent de validació | CA5 | Correcte | E2E (Playwright) i pytest-django | Preparat |
| CP-US1.1-19 | Validació posterior correcta | CA6 | Correcte | E2E i pytest-django | Bloquejat |
| CP-US1.1-20 | Validació posterior incorrecta | CA7 | Error | E2E i pytest-django | Bloquejat |

## Casos

### CP-US1.1-01 · El formulari mostra els camps obligatoris

- **Origen**: CA1.
- **Precondicions**: les generals.
- **Passos**:
  1. Obrir `/registre`.
  2. Seleccionar el tipus de compte "Repartidor".
  3. Revisar els camps disponibles.
- **Dades d'entrada**: cap.
- **Resultat esperat**:
  - Es mostren els camps Nom, Cognoms, DNI/NIE, Correu electrònic i Telèfon.
  - Es mostra el camp Tipus de vehicle.
  - Es mostra el camp Número de la Seguretat Social.
  - El camp Matrícula es mostra quan se selecciona `moto` o `cotxe`.
  - Els camps obligatoris no es poden ometre del registre.
- **Tipus**: correcte.
- **Automatització proposada**: Playwright (E2E).

### CP-US1.1-02 · Registre correcte amb moto

- **Origen**: CA1 i CA5.
- **Precondicions**:
  - Les generals.
  - No existeix cap compte amb el correu electrònic ni el DNI/NIE de prova.
- **Passos**:
  1. Obrir `/registre`.
  2. Seleccionar "Repartidor".
  3. Informar tots els camps amb les dades vàlides per a moto.
  4. Enviar el formulari.
- **Dades d'entrada**: les dades vàlides per a moto.
- **Resultat esperat**:
  - El formulari permet l'enviament.
  - El compte es crea en estat "Pendent de validació".
  - Es mostra una pantalla de confirmació.
  - La URL passa a ser `/registre/confirmacio`.
- **Tipus**: correcte.
- **Automatització proposada**: Playwright (E2E) i pytest-django (backend).

### CP-US1.1-03 · Registre correcte amb bicicleta sense matrícula

- **Origen**: CA1 i CA5.
- **Precondicions**:
  - Les generals.
  - No existeix cap compte amb el correu electrònic ni el DNI/NIE de prova.
- **Passos**:
  1. Obrir `/registre`.
  2. Seleccionar "Repartidor".
  3. Seleccionar el tipus de vehicle `bici`.
  4. Informar totes les dades obligatòries excepte la matrícula.
  5. Enviar el formulari.
- **Dades d'entrada**:
  - Tipus de vehicle: `bici`.
  - Matrícula: no s'informa.
  - Resta de dades: vàlides.
- **Resultat esperat**:
  - El camp Matrícula no es mostra.
  - La matrícula no s'envia a l'API.
  - No es mostra cap error de matrícula.
  - El compte es crea en estat "Pendent de validació".
  - Es mostra la pantalla de confirmació a `/registre/confirmacio`.
- **Tipus**: límit.
- **Automatització proposada**: Playwright (E2E) i pytest-django (backend).

### CP-US1.1-04 · Formulari amb tots els camps obligatoris buits

- **Origen**: CA1 i CA4.
- **Precondicions**: les generals.
- **Passos**:
  1. Obrir `/registre`.
  2. Seleccionar "Repartidor".
  3. No informar cap camp.
  4. Intentar enviar el formulari.
- **Dades d'entrada**:
  - Tots els camps obligatoris buits.
- **Resultat esperat**:
  - El registre no es completa.
  - Es mostra un missatge d'error inline sota cada camp afectat.
  - No es crida l'API.
  - No es mostra la pantalla de confirmació.
- **Tipus**: error.
- **Automatització proposada**: Playwright (E2E) i pytest-django (backend).

### CP-US1.1-05 · Un camp personal obligatori buit

- **Origen**: CA1 i CA4.
- **Precondicions**: les generals. Tots els camps són vàlids excepte un camp personal obligatori.
- **Passos**:
  1. Obrir `/registre`.
  2. Seleccionar "Repartidor".
  3. Informar dades vàlides a tots els camps.
  4. Deixar buit un dels camps Nom, Cognoms, DNI/NIE, Correu electrònic o Telèfon.
  5. Enviar el formulari.
- **Dades d'entrada**:
  - Un camp personal obligatori buit.
  - Resta de camps amb dades vàlides.
- **Resultat esperat**:
  - El registre no es completa.
  - Es mostra un missatge d'error inline sota el camp buit.
  - No es crida l'API.
  - No es mostra la pantalla de confirmació.
- **Tipus**: error.
- **Automatització proposada**: Playwright (E2E) i pytest-django (backend).

### CP-US1.1-06 · Un camp de repartidor obligatori buit

- **Origen**: CA1 i CA4.
- **Precondicions**: les generals. Tots els camps són vàlids excepte un camp de repartidor obligatori.
- **Passos**:
  1. Obrir `/registre`.
  2. Seleccionar "Repartidor".
  3. Informar dades vàlides a tots els camps.
  4. Deixar buit el tipus de vehicle o el número de la Seguretat Social.
  5. Enviar el formulari.
- **Dades d'entrada**:
  - Tipus de vehicle buit o número de la Seguretat Social buit.
  - Resta de camps amb dades vàlides.
- **Resultat esperat**:
  - El registre no es completa.
  - Es mostra un missatge d'error inline sota el camp buit.
  - No es crida l'API.
  - No es mostra la pantalla de confirmació.
- **Tipus**: error.
- **Automatització proposada**: Playwright (E2E) i pytest-django (backend).

### CP-US1.1-07 · Correu electrònic amb format invàlid

- **Origen**: CA2 i CA4.
- **Precondicions**: les generals. La resta de dades són vàlides.
- **Passos**:
  1. Obrir `/registre`.
  2. Seleccionar "Repartidor".
  3. Informar totes les dades.
  4. Introduir `repartidor@` al camp de correu.
  5. Enviar el formulari.
- **Dades d'entrada**:
  - Correu electrònic: `repartidor@`.
  - Resta de camps: vàlids.
- **Resultat esperat**:
  - No es permet l'enviament.
  - Es mostra un error inline sota el camp de correu electrònic.
  - No es crida l'API.
  - No es crea cap compte.
- **Tipus**: error.
- **Automatització proposada**: Playwright (E2E) i pytest-django (backend).

### CP-US1.1-08 · Telèfon amb format invàlid

- **Origen**: CA2 i CA4.
- **Precondicions**: les generals. La resta de dades són vàlides.
- **Passos**:
  1. Obrir `/registre`.
  2. Seleccionar "Repartidor".
  3. Informar totes les dades.
  4. Introduir `512345678` al camp de telèfon.
  5. Enviar el formulari.
- **Dades d'entrada**:
  - Telèfon: `512345678`.
  - Resta de camps: vàlids.
- **Resultat esperat**:
  - No es permet l'enviament.
  - Es mostra un error inline sota el camp de telèfon.
  - No es crida l'API.
  - No es crea cap compte.
- **Tipus**: error.
- **Automatització proposada**: Playwright (E2E) i pytest-django (backend).

### CP-US1.1-09 · DNI/NIE amb format invàlid

- **Origen**: CA2 i CA4.
- **Precondicions**: les generals. La resta de dades són vàlides.
- **Passos**:
  1. Obrir `/registre`.
  2. Seleccionar "Repartidor".
  3. Informar totes les dades.
  4. Introduir `12345678A` al camp DNI/NIE.
  5. Enviar el formulari.
- **Dades d'entrada**:
  - DNI/NIE: `12345678A`.
  - Resta de camps: vàlids.
- **Resultat esperat**:
  - No es permet l'enviament.
  - Es mostra un error inline sota el camp DNI/NIE.
  - No es crida l'API.
  - No es crea cap compte.
- **Tipus**: error.
- **Automatització proposada**: Playwright (E2E) i pytest-django (backend).

### CP-US1.1-10 · Correu electrònic duplicat

- **Origen**: CA3 i CA4.
- **Precondicions**: ja existeix un compte amb el correu electrònic de prova.
- **Passos**:
  1. Obrir `/registre`.
  2. Seleccionar "Repartidor".
  3. Informar dades vàlides i utilitzar el correu duplicat.
  4. Enviar el formulari.
- **Dades d'entrada**:
  - Correu electrònic ja registrat.
  - DNI/NIE i resta de camps vàlids i no duplicats.
- **Resultat esperat**:
  - El registre no es completa.
  - Es mostra el missatge exacte "DNI/correu ja registrat" sota el camp afectat.
  - No es mostra la pantalla de confirmació.
  - No es crea cap compte nou.
- **Tipus**: error.
- **Automatització proposada**: Playwright (E2E) i pytest-django (backend).

### CP-US1.1-11 · DNI/NIE duplicat

- **Origen**: CA3 i CA4.
- **Precondicions**: ja existeix un compte amb el DNI/NIE de prova.
- **Passos**:
  1. Obrir `/registre`.
  2. Seleccionar "Repartidor".
  3. Informar dades vàlides i utilitzar el DNI/NIE duplicat.
  4. Enviar el formulari.
- **Dades d'entrada**:
  - DNI/NIE ja registrat.
  - Correu electrònic i resta de camps vàlids i no duplicats.
- **Resultat esperat**:
  - El registre no es completa.
  - Es mostra el missatge exacte "DNI/correu ja registrat" sota el camp afectat.
  - No es mostra la pantalla de confirmació.
  - No es crea cap compte nou.
- **Tipus**: error.
- **Automatització proposada**: Playwright (E2E) i pytest-django (backend).

### CP-US1.1-12 · Correu electrònic i DNI/NIE duplicats

- **Origen**: CA3 i CA4.
- **Precondicions**: ja existeix un compte amb el correu electrònic i el DNI/NIE de prova.
- **Passos**:
  1. Obrir `/registre`.
  2. Seleccionar "Repartidor".
  3. Informar dades vàlides i utilitzar el correu i el DNI/NIE duplicats.
  4. Enviar el formulari.
- **Dades d'entrada**:
  - Correu electrònic duplicat.
  - DNI/NIE duplicat.
  - Resta de camps vàlids.
- **Resultat esperat**:
  - El registre no es completa.
  - Es mostra el missatge exacte "DNI/correu ja registrat" sota cada camp afectat.
  - No es mostra la pantalla de confirmació.
  - No es crea cap compte nou.
- **Tipus**: error.
- **Automatització proposada**: Playwright (E2E) i pytest-django (backend).

### CP-US1.1-13 · Tipus de vehicle no permès

- **Origen**: CA1 i CA4.
- **Precondicions**: les generals.
- **Passos**:
  1. Preparar una petició de registre amb totes les dades vàlides.
  2. Informar un tipus de vehicle diferent de `bici`, `moto` o `cotxe`.
  3. Enviar la petició.
- **Dades d'entrada**:
  - Tipus de vehicle: valor diferent de `bici`, `moto` o `cotxe`.
- **Resultat esperat**:
  - El registre no es completa.
  - Es mostra un error associat al camp Tipus de vehicle.
  - No es crea cap compte.
- **Tipus**: error.
- **Automatització proposada**: pytest-django (backend).

### CP-US1.1-14 · Matrícula absent per a moto o cotxe

- **Origen**: CA1 i CA4.
- **Precondicions**: les generals. El tipus de vehicle és `moto` o `cotxe`.
- **Passos**:
  1. Informar totes les dades vàlides excepte la matrícula.
  2. Deixar la matrícula buida.
  3. Enviar el formulari.
- **Dades d'entrada**:
  - Tipus de vehicle: `moto` o `cotxe`.
  - Matrícula: buida.
- **Resultat esperat**:
  - El registre no es completa.
  - Es mostra un error inline sota el camp Matrícula.
  - No es crea cap compte.
- **Tipus**: error.
- **Automatització proposada**: Playwright (E2E) i pytest-django (backend).

### CP-US1.1-15 · Matrícula amb format invàlid

- **Origen**: CA4.
- **Precondicions**: les generals. El tipus de vehicle és `moto` o `cotxe`.
- **Passos**:
  1. Informar totes les dades vàlides.
  2. Introduir `1234 ABC` com a matrícula.
  3. Enviar el formulari.
- **Dades d'entrada**:
  - Matrícula: `1234 ABC`.
- **Resultat esperat**:
  - No es permet l'enviament.
  - Es mostra un error inline sota el camp Matrícula.
  - No es crea cap compte.
- **Tipus**: error.
- **Automatització proposada**: Playwright (E2E) i pytest-django (backend).

### CP-US1.1-16 · Número de Seguretat Social amb format invàlid

- **Origen**: CA4.
- **Precondicions**: les generals. La resta de dades són vàlides.
- **Passos**:
  1. Informar totes les dades obligatòries.
  2. Introduir `28123456789` al camp de Seguretat Social.
  3. Enviar el formulari.
- **Dades d'entrada**:
  - Número de Seguretat Social: `28123456789`.
- **Resultat esperat**:
  - No es permet l'enviament.
  - Es mostra un error inline sota el camp de Seguretat Social.
  - No es crea cap compte.
- **Tipus**: error.
- **Automatització proposada**: Playwright (E2E) i pytest-django (backend).

### CP-US1.1-17 · Errors inline sota els camps afectats

- **Origen**: CA4.
- **Precondicions**: les generals. El formulari conté com a mínim un camp buit o una dada incorrecta.
- **Passos**:
  1. Obrir `/registre`.
  2. Seleccionar "Repartidor".
  3. Introduir una dada incorrecta o deixar un camp buit.
  4. Enviar el formulari.
  5. Observar la ubicació del missatge d'error.
- **Dades d'entrada**: un camp buit o amb dades incorrectes.
- **Resultat esperat**:
  - El missatge es mostra visualment sota el camp afectat.
  - L'error no es mostra únicament com una notificació general.
  - El registre no es completa.
- **Tipus**: correcte.
- **Automatització proposada**: Playwright (E2E).

### CP-US1.1-18 · Confirmació del registre pendent de validació

- **Origen**: CA5.
- **Precondicions**:
  - Les dades són vàlides.
  - El correu electrònic i el DNI/NIE no estan registrats.
  - L'endpoint de registre respon correctament.
- **Passos**:
  1. Completar tots els camps obligatoris.
  2. Enviar el formulari.
  3. Observar la resposta i la pantalla mostrada.
- **Dades d'entrada**: les dades vàlides de la taula de prova.
- **Resultat esperat**:
  - El compte es crea en estat "Pendent de validació".
  - La URL passa a ser `/registre/confirmacio`.
  - Es mostra el text "Sol·licitud enviada".
  - Es mostra el text "Hem rebut la teva sol·licitud per ser repartidor de bookit.".
  - Es mostra l'estat "Pendent de validació".
  - Es mostra l'opció "Tornar a l'inici".
- **Tipus**: correcte.
- **Automatització proposada**: Playwright (E2E) i pytest-django (backend).

### CP-US1.1-19 · Validació posterior correcta

- **Origen**: CA6.
- **Precondicions**:
  - Existeix una sol·licitud en estat "Pendent de validació".
  - Existeix un flux de validació disponible.
  - Les dades es consideren correctes.
- **Passos**:
  1. Obrir la sol·licitud pendent.
  2. Completar la validació com a correcta.
  3. Continuar el flux posterior definit per l'aplicació.
- **Dades d'entrada**:
  - Sol·licitud amb dades correctes.
  - Resultat de validació: correcte.
- **Resultat esperat**:
  - El registre es considera completat correctament.
  - No es mostra el missatge "Validació incompleta".
  - S'accedeix a la vista de repartidor segons el flux d'autenticació definit.
- **Tipus**: correcte.
- **Automatització proposada**: E2E i pytest-django.
- **Estat**: bloquejat fins que existeixin la validació, l'autenticació i la vista de repartidor.

### CP-US1.1-20 · Validació posterior incorrecta

- **Origen**: CA7.
- **Precondicions**:
  - Existeix una sol·licitud en estat "Pendent de validació".
  - Existeix un flux de validació disponible.
  - Les dades es consideren incorrectes.
- **Passos**:
  1. Obrir la sol·licitud pendent.
  2. Completar la validació com a incorrecta.
  3. Observar el resultat del procés.
- **Dades d'entrada**:
  - Sol·licitud amb dades incorrectes.
  - Resultat de validació: incorrecte.
- **Resultat esperat**:
  - El registre no es completa.
  - Es mostra el missatge exacte "Validació incompleta".
  - Es torna a la pantalla de registre.
  - No s'accedeix a la vista de repartidor.
  - El comportament posterior de la sol·licitud queda pendent de definició.
- **Tipus**: error.
- **Automatització proposada**: E2E i pytest-django.
- **Estat**: bloquejat fins que existeixi el flux de validació.

## Matriu de traçabilitat

| Criteri | Descripció | Casos | Cobertura |
|---|---|---|---|
| CA1 | Camps personals i de repartidor obligatoris | CP-US1.1-01, CP-US1.1-02, CP-US1.1-03, CP-US1.1-04, CP-US1.1-05, CP-US1.1-06, CP-US1.1-13, CP-US1.1-14 | Cobert |
| CA2 | Format vàlid del correu, telèfon i DNI/NIE | CP-US1.1-07, CP-US1.1-08, CP-US1.1-09 | Cobert |
| CA3 | Duplicats de correu electrònic o DNI/NIE | CP-US1.1-10, CP-US1.1-11, CP-US1.1-12 | Cobert |
| CA4 | Errors inline per camps buits o dades incorrectes | CP-US1.1-04, CP-US1.1-05, CP-US1.1-06, CP-US1.1-07, CP-US1.1-08, CP-US1.1-09, CP-US1.1-10, CP-US1.1-11, CP-US1.1-12, CP-US1.1-13, CP-US1.1-14, CP-US1.1-15, CP-US1.1-16, CP-US1.1-17 | Cobert |
| CA5 | Estat pendent de validació i confirmació | CP-US1.1-02, CP-US1.1-03, CP-US1.1-18 | Cobert |
| CA6 | Validació correcta i accés a la vista de repartidor | CP-US1.1-19 | Cobertura bloquejada |
| CA7 | Validació incorrecta, missatge i retorn al registre | CP-US1.1-20 | Cobertura bloquejada |

No hi ha cap criteri sense un cas definit. Els criteris CA6 i CA7 tenen casos, però la seva execució queda bloquejada
perquè el flux de validació posterior encara no està definit ni implementat.

## Fora d'abast

- Codi de tests Playwright, pytest-django o Vitest.
- Modificacions del backend, frontend, CI, configuració o dependències.
- Creació o configuració d'entorns virtuals, inclòs `.venv`.
- Flux d'inici de sessió, tancament de sessió o recuperació de contrasenya.
- Ruta i contingut definitius de la vista de repartidor.
- Endpoint i pantalla definitius per a la validació administrativa.
- Persistència concreta d'una sol·licitud rebutjada.
- Formats diferents dels documentats en aquest document o en el contracte de l'API.
- Missatges d'error diferents de "DNI/correu ja registrat" i "Validació incompleta", excepte quan el criteri o el
  contracte defineixi explícitament el comportament.

## Dubtes i punts pendents de confirmació

1. Els formats detallats del correu, telèfon, DNI/NIE, matrícula i número de Seguretat Social estan definits al codi i
   al contracte de l'API, però cal confirmar que formen part del comportament oficial de la US1.1.
2. El contracte i el frontend indiquen que la matrícula és obligatòria per a `moto` i `cotxe`, i no aplicable per a
   `bici`. Cal confirmar aquesta decisió amb el Product Owner.
3. Els únics tipus de vehicle disponibles són `bici`, `moto` i `cotxe` segons el frontend i el model.
4. El model defineix els estats `pendent`, `validat` i `rebutjat`, però no existeix encara el flux per canviar entre
   aquests estats.
5. El codi actual indica que un administrador revisa les dades, però no defineix el moment exacte, la pantalla,
   l'endpoint ni el procediment per acceptar o rebutjar una sol·licitud.
6. No existeix encara cap ruta ni component de vista de repartidor. Cal confirmar la ruta, el contingut i el
   mecanisme d'accés.
7. La pantalla de confirmació actual és `/registre/confirmacio` i mostra "Pendent de validació", però cal confirmar
   que aquesta ruta i aquests textos són els definitius.
8. Els textos d'error del frontend i els del contracte/backend no coincideixen exactament en alguns camps. Cal
   confirmar quina versió és contractual.
9. El model defineix l'estat intern `rebutjat`, però no s'ha definit si una sol·licitud rebutjada es conserva, es
   modifica, s'elimina o es pot tornar a enviar.
10. La pantalla de confirmació indica que, després de la validació, el repartidor podrà iniciar sessió. No existeixen
    encara la pantalla d'inici de sessió, els tokens ni els guards de ruta.
11. La contrasenya i la confirmació de contrasenya formen part del formulari actual, però no consten en els criteris
    d'acceptació proporcionats. Cal confirmar si s'han d'incorporar formalment a CA1.
