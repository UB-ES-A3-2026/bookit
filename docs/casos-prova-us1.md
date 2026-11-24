# Casos de prova: registre d'usuari (US1)

Casos de prova de la US1 (tasca US1-T12), escrits a partir dels criteris d'acceptació i del disseny de la història
(issue #3) i del contracte de `docs/api-registre.md`. Els tests E2E amb Playwright (US1-T13) i la validació manual
amb el Product Owner (US1-T14) en surten. Qualsevol canvi d'aquest document passa per pull request.

## Història i criteris d'acceptació

> **COM A** nou usuari **VULL** registrar-me a l'aplicació amb el meu carnet de biblioteca i dades personals
> **PER A** poder demanar llibres en línia.

- **CA1**: el formulari de registre requereix els camps Nom, Correu electrònic, Adreça física, Número de carnet de
  biblioteca i Contrasenya.
- **CA2**: un registre correcte crea el compte d'usuari i redirigeix automàticament l'usuari a la pàgina principal.
- **CA3**: el registre falla i mostra "Aquest correu electrònic ja està registrat" si el correu ja està associat a
  un compte existent.
- **CA4**: el registre falla i mostra "Aquest usuari ja està registrat" si el número de carnet ja està registrat.
- **CA5**: si el número de carnet no respecta el format, es mostra "El format d'aquest carnet no és vàlid".
- **CA6**: si l'usuari clica fora de la caixa, aquesta es tanca.

Els missatges de CA3 i CA5 segueixen el contracte i el backend. L'issue els escriu "correu electronic", sense accent,
i "no es vàlid". Vegeu les observacions al final del document.

També es proven aquests requisits de les tasques i del contracte:

- **US1-T7**: la caixa de registre és responsive i té el selector de tipus de compte.
- **US1-T8**: validació al client dels camps obligatoris, del format del correu i de la coincidència de contrasenyes.
- **US1-T9**: els errors del backend es mostren sota el camp corresponent.
- **US1-T11**: les opcions "Repartidor" i "Biblioteca" mostren "Funcionalitat no implementada" i no criden l'API.
- **Contracte**: el carnet té exactament 10 dígits, el registre sempre crea un compte amb rol `usuari`, la
  contrasenya passa els validadors de Django i no es retorna mai.

## Disseny de referència

El disseny adjunt a l'issue #3 mostra el registre com una caixa sobre la pàgina d'inici, amb:

- El títol "Crear un compte", el botó de tancar (X) i les pestanyes "Inicia Sessió" i "Registrar-se".
- El selector "Com et vols registrar?" amb les opcions "Lector", "Repartidor" i "Biblioteca".
- Els camps "Correu electrònic", "Nom complet", "Adreça física", "Número de carnet de biblioteca" i "Contrasenya".
- La casella "Accepto els termes d'ús i la política de privacitat" i el botó "Completar Registre".

Aquest document fa servir aquests textos. Si US1-T7 en fa servir uns altres, cal actualitzar-lo.

## Entorn i precondicions generals

- Aplicació aixecada en local amb `docker compose up -d --build --wait` des de l'arrel. Frontend a
  http://localhost:5173 i backend a http://localhost:8000 (o el `FRONTEND_PORT` i el `BACKEND_PORT` del `.env`).
- El backend de la US1 (a `develop` des de la PR #84) i la caixa de registre de US1-T7 a US1-T11 a la mateixa branca.
- Base de dades migrada. Fins que no es faci US1-T15, cal executar
  `docker compose exec backend python manage.py migrate` després d'aixecar l'entorn.
- CORS configurat (US1-T17). Sense CORS, el navegador bloqueja les peticions del frontend al backend.
- Navegador sense cap sessió iniciada: finestra privada o perfil net.
- Mida d'escriptori: 1280 × 720. Mida de mòbil: 375 × 812.
- **Obrir la caixa de registre** vol dir obrir `/` i fer clic al botó "Registra't" de la capçalera. Segons US1-T7
  (PR #86), la caixa és a la ruta `/registre`, sobre una imatge de fons enfosquida, i tancar-la torna a `/`.
- Per comprovar les peticions a mà, cal obrir la pestanya Xarxa de les eines de desenvolupador abans d'enviar el
  formulari.

## Dades de prova

| Camp | Valor vàlid |
|---|---|
| Com et vols registrar? | `Lector` |
| Correu electrònic | `anna.puig@example.com` |
| Nom complet | `Anna Puig` |
| Adreça física | `C/ Major 1, 08001 Barcelona` |
| Número de carnet de biblioteca | `1234567890` |
| Contrasenya | `Llibres-de-tardor-24` |
| Termes d'ús | Marcada |

- **Compte existent**: un compte ja registrat amb el correu `existent@example.com` i el carnet `0987654321`. És la
  precondició de CP-US1-03 a 06. Es crea abans del cas amb la mateixa caixa o amb una petició
  `POST /api/auth/register/`.
- La base de dades local es conserva entre execucions. Per repetir un registre correcte, cal fer servir un correu i
  un carnet nous. Els tests E2E (T13) han de generar un correu i un carnet únics a cada execució.

## Resum

| ID | Cas | Origen | Prioritat | Execució proposada |
|---|---|---|---|---|
| CP-US1-01 | Registre correcte com a Lector | CA1, CA2 | Alta | E2E (T13) i manual (T14) |
| CP-US1-02 | Registre correcte en mòbil | CA2, T7 | Alta | E2E (T13) i manual (T14) |
| CP-US1-03 | Correu ja registrat | CA3, T9 | Alta | E2E (T13) i manual (T14) |
| CP-US1-04 | Correu ja registrat amb majúscules diferents | CA3 | Mitjana | E2E (T13) |
| CP-US1-05 | Carnet ja registrat | CA4, T9 | Alta | E2E (T13) i manual (T14) |
| CP-US1-06 | Correu i carnet ja registrats alhora | CA3, CA4, T9 | Mitjana | E2E (T13) |
| CP-US1-07 | Format de carnet incorrecte | CA5, T9 | Alta | E2E (T13) i manual (T14) |
| CP-US1-08 | Enviar el formulari amb camps buits | CA1, T8 | Alta | E2E (T13) i manual (T14) |
| CP-US1-09 | Clicar fora de la caixa la tanca | CA6 | Alta | E2E (T13) i manual (T14) |
| CP-US1-10 | Tipus de compte "Repartidor" | T11 | Alta | E2E (T13) i manual (T14) |
| CP-US1-11 | Tipus de compte "Biblioteca" | T11 | Alta | E2E (T13) i manual (T14) |
| CP-US1-12 | Tornar a "Lector" després de l'avís | CA2, T11 | Mitjana | E2E (T13) |
| CP-US1-13 | Correu amb format incorrecte | T8, T9 | Mitjana | E2E (T13) |
| CP-US1-14 | Camps amb només espais | CA1, T8 | Baixa | Manual (T14) |
| CP-US1-15 | Contrasenya rebutjada pel backend | Contracte, T9 | Mitjana | E2E (T13) |
| CP-US1-16 | Les contrasenyes no coincideixen | T8 | Baixa | E2E (T13), si hi ha el camp |
| CP-US1-17 | L'API no deixa triar el rol | Contracte | Alta | Backend (T6, ja cobert) i manual (T14) |
| CP-US1-18 | Contrasenya no retornada ni desada en clar | Contracte | Alta | Backend (T6, ja cobert) i manual (T14) |
| CP-US1-19 | Omplir i enviar el formulari amb el teclat | CA2 | Baixa | Manual (T14) |
| CP-US1-20 | Doble clic a "Completar Registre" | CA2 | Baixa | Manual (T14) |

Els tests del backend de la US1-T6 ja comproven a nivell d'API el registre correcte, els duplicats (també amb
majúscules), els camps buits o amb espais, els formats i les contrasenyes febles. Els E2E comproven que la caixa
mostra el resultat a l'usuari.

## Casos

### CP-US1-01 · Registre correcte com a Lector

- **Origen**: CA1 i CA2.
- **Precondicions**: les generals, en mida d'escriptori. No hi ha cap compte amb el correu ni el carnet de les dades
  de prova.
- **Passos**:
  1. Obrir la caixa de registre.
  2. Comprovar que es veuen els cinc camps de CA1 i que "Lector" està triat (o triar-lo).
  3. Omplir tots els camps amb les dades de prova i marcar la casella dels termes d'ús.
  4. Fer clic a "Completar Registre".
- **Resultat esperat**:
  - La caixa es tanca, la URL és `/` i es veu la pàgina d'inici.
  - La petició `POST /api/auth/register/` respon `201` amb el `nom`, el `correu`, l'`adreca` i el `num_carnet`
    enviats i `"rol": "usuari"`.
  - No apareix cap missatge d'error a la pàgina ni a la consola del navegador.

### CP-US1-02 · Registre correcte en mòbil

- **Origen**: CA2, amb la caixa responsive de US1-T7.
- **Precondicions**: les generals, en mida de mòbil. Un correu i un carnet nous.
- **Passos**:
  1. Obrir la caixa de registre.
  2. Desplaçar-se per la caixa fins al botó "Completar Registre".
  3. Omplir tots els camps, marcar la casella i tocar "Completar Registre".
- **Resultat esperat**:
  - Al pas 2, les opcions del selector, tots els camps, la casella i el botó es veuen sencers i es poden tocar, i la
    pàgina no té desplaçament horitzontal.
  - Al pas 3, la caixa es tanca i la URL és `/`.

### CP-US1-03 · Correu ja registrat

- **Origen**: CA3. El missatge es mostra sota el camp (US1-T9).
- **Precondicions**: les generals. Existeix el compte existent.
- **Passos**:
  1. Obrir la caixa de registre.
  2. Omplir el formulari amb les dades de prova, però amb el correu `existent@example.com`.
  3. Fer clic a "Completar Registre".
- **Resultat esperat**:
  - La caixa continua oberta.
  - Sota el camp "Correu electrònic" apareix exactament "Aquest correu electrònic ja està registrat".
  - La petició respon `400` i no es crea cap compte.

### CP-US1-04 · Correu ja registrat amb majúscules diferents

- **Origen**: CA3. El backend desa el correu en minúscules i no distingeix majúscules en comprovar si ja existeix.
- **Precondicions**: les generals. Existeix el compte existent.
- **Passos**:
  1. Obrir la caixa de registre.
  2. Omplir el formulari amb les dades de prova, però amb el correu `Existent@Example.com`.
  3. Fer clic a "Completar Registre".
- **Resultat esperat**: el de CP-US1-03.

### CP-US1-05 · Carnet ja registrat

- **Origen**: CA4. El missatge es mostra sota el camp (US1-T9).
- **Precondicions**: les generals. Existeix el compte existent.
- **Passos**:
  1. Obrir la caixa de registre.
  2. Omplir el formulari amb les dades de prova, però amb el carnet `0987654321`.
  3. Fer clic a "Completar Registre".
- **Resultat esperat**:
  - La caixa continua oberta.
  - Sota el camp "Número de carnet de biblioteca" apareix exactament "Aquest usuari ja està registrat".
  - La petició respon `400` i no es crea cap compte.

### CP-US1-06 · Correu i carnet ja registrats alhora

- **Origen**: CA3 i CA4. El backend retorna tots els errors alhora (`docs/api-registre.md`).
- **Precondicions**: les generals. Existeix el compte existent.
- **Passos**:
  1. Obrir la caixa de registre.
  2. Omplir el formulari amb les dades de prova, però amb el correu `existent@example.com` i el carnet `0987654321`.
  3. Fer clic a "Completar Registre".
- **Resultat esperat**:
  - Apareixen tots dos missatges, cadascun sota el seu camp: el de CA3 sota "Correu electrònic" i el de CA4 sota
    "Número de carnet de biblioteca".
  - La caixa continua oberta.

### CP-US1-07 · Format de carnet incorrecte

- **Origen**: CA5. El contracte fixa el format: exactament 10 dígits.
- **Precondicions**: les generals. Un correu nou.
- **Passos**:
  1. Obrir la caixa de registre.
  2. Omplir el formulari amb les dades de prova, però amb el carnet `123456789` (9 dígits).
  3. Fer clic a "Completar Registre".
  4. Repetir els passos 2 i 3 amb `12345678901` (11 dígits), `123456789A` (una lletra), `BIB-12345678` (l'exemple
     del disseny) i ` 1234567890` (amb un espai al davant).
- **Resultat esperat**:
  - En cada intent, sota el camp "Número de carnet de biblioteca" apareix exactament "El format d'aquest carnet no
    és vàlid", la caixa continua oberta i no es crea cap compte.
- **Nota**: el carnet `0000000001` és vàlid: un carnet pot començar per zero.

### CP-US1-08 · Enviar el formulari amb camps buits

- **Origen**: CA1 i US1-T8 (camps obligatoris).
- **Precondicions**: les generals.
- **Passos**:
  1. Obrir la caixa de registre.
  2. Sense omplir cap camp, fer clic a "Completar Registre".
  3. Omplir tots els camps amb dades vàlides menys "Adreça física" i tornar a fer clic a "Completar Registre".
- **Resultat esperat**:
  - Al pas 2 apareix un missatge d'obligatorietat sota cada camp de CA1.
  - Al pas 3 el missatge només es veu sota "Adreça física".
  - En cap dels dos passos es crea cap compte, i la caixa continua oberta.
- **Nota**: si el missatge arriba del backend, el text és "Aquest camp és obligatori.". La validació al client
  (US1-T8) pot fer servir el mateix text i evitar la petició.

### CP-US1-09 · Clicar fora de la caixa la tanca

- **Origen**: CA6.
- **Precondicions**: les generals, en mida d'escriptori.
- **Passos**:
  1. Obrir la caixa de registre.
  2. Fer clic en una zona buida de dins de la caixa, p. ex. al costat del títol "Crear un compte".
  3. Escriure alguna cosa al camp "Nom complet", seleccionar el text arrossegant el ratolí i deixar anar el botó a
     fora de la caixa.
  4. Fer clic al fons enfosquit, fora de la caixa.
  5. Tornar a obrir la caixa i fer clic al botó de tancar (X), que els lectors de pantalla anomenen "Tancar".
- **Resultat esperat**:
  - Als passos 2 i 3, la caixa continua oberta.
  - Al pas 4, la caixa es tanca, la URL torna a ser `/` i no es crea cap compte.
  - Al pas 5, la caixa també es tanca i la URL torna a ser `/`.
- **Nota**: el pas 3 evita un defecte habitual de les caixes modals, que es tanquen quan el clic comença a dins i
  acaba a fora.

### CP-US1-10 · Tipus de compte "Repartidor"

- **Origen**: US1-T11.
- **Precondicions**: les generals.
- **Passos**:
  1. Obrir la caixa de registre.
  2. Triar "Repartidor" a "Com et vols registrar?".
  3. Omplir tots els camps amb dades vàlides i, si el botó "Completar Registre" està actiu, fer-hi clic.
- **Resultat esperat**:
  - Al pas 2 apareix l'avís "Funcionalitat no implementada".
  - Al pas 3 no s'envia cap petició a `/api/auth/register/` i no es crea cap compte.

### CP-US1-11 · Tipus de compte "Biblioteca"

- **Origen**: US1-T11.
- **Precondicions**: les generals.
- **Passos**: els de CP-US1-10, triant "Biblioteca" al pas 2.
- **Resultat esperat**: el de CP-US1-10.

### CP-US1-12 · Tornar a "Lector" després de l'avís

- **Origen**: CA2 i US1-T11. Qui tria una opció per error s'ha de poder registrar igualment.
- **Precondicions**: les generals. Un correu i un carnet nous.
- **Passos**:
  1. Obrir la caixa de registre.
  2. Triar "Repartidor" i, si cal, tancar l'avís.
  3. Tornar a triar "Lector".
  4. Omplir tots els camps amb dades vàlides, marcar la casella i fer clic a "Completar Registre".
- **Resultat esperat**:
  - Al pas 3, l'avís ja no es veu i la caixa de registre continua oberta.
  - Al pas 4, la caixa es tanca, la URL és `/` i la petició respon `201` amb `"rol": "usuari"`.

### CP-US1-13 · Correu amb format incorrecte

- **Origen**: US1-T8 (format del correu) i US1-T9.
- **Precondicions**: les generals.
- **Passos**:
  1. Obrir la caixa de registre.
  2. Omplir el formulari amb les dades de prova, però amb el correu `anna.example.com`, i fer clic a "Completar
     Registre".
  3. Repetir el pas 2 amb `anna@`, `anna@example` i `anna puig@example.com`.
- **Resultat esperat**:
  - En cada intent apareix un missatge sota el camp "Correu electrònic", la caixa continua oberta i no es crea cap
    compte.
- **Nota**: el navegador accepta `anna@example` en un camp `type="email"`, però el backend el rebutja perquè el domini
  no té punt. Si el frontend el deixa passar, el missatge arriba del backend ("Introduïu una adreça de correu
  electrònic vàlida.") i també s'ha de mostrar sota el camp.

### CP-US1-14 · Camps amb només espais

- **Origen**: CA1 i US1-T8.
- **Precondicions**: les generals. Un correu i un carnet nous.
- **Passos**:
  1. Obrir la caixa de registre.
  2. Omplir el formulari amb dades vàlides, però amb tres espais al camp "Nom complet", i fer clic a "Completar
     Registre".
  3. Repetir el pas 2 amb tres espais al camp "Adreça física".
- **Resultat esperat**:
  - En cada intent apareix "Aquest camp és obligatori." (o el missatge del client) sota el camp amb espais, i no es
    crea cap compte.

### CP-US1-15 · Contrasenya rebutjada pel backend

- **Origen**: contracte (validadors de contrasenya de Django) i US1-T9.
- **Precondicions**: les generals. Un correu i un carnet nous.
- **Passos**:
  1. Obrir la caixa de registre.
  2. Omplir el formulari amb dades vàlides, però amb la contrasenya `curta1`, i fer clic a "Completar Registre".
  3. Repetir el pas 2 amb `12345678` (només números i massa comuna).
  4. Repetir el pas 2 amb el correu `jordi.vila@example.com` i la contrasenya `jordi.vila.example` (massa semblant
     al correu).
- **Resultat esperat**:
  - En cada intent apareix almenys un missatge sota el camp "Contrasenya", la petició respon `400` i no es crea cap
    compte.
  - Els missatges són en català.
- **Nota**: avui els passos 2 i 4 no compleixen el resultat esperat. Vegeu les observacions.

### CP-US1-16 · Les contrasenyes no coincideixen

- **Origen**: US1-T8 (coincidència de contrasenyes).
- **Precondicions**: les generals. Només s'aplica si US1-T7 afegeix un camp per repetir la contrasenya, que el
  disseny no té.
- **Passos**:
  1. Obrir la caixa de registre.
  2. Omplir el formulari amb les dades de prova, però amb `Llibres-de-tardor-25` al camp de repetició.
  3. Fer clic a "Completar Registre".
- **Resultat esperat**:
  - Apareix un missatge que indica que les contrasenyes no coincideixen, sota el camp de repetició.
  - No s'envia cap petició a `/api/auth/register/` i la caixa continua oberta.

### CP-US1-17 · L'API no deixa triar el rol

- **Origen**: contracte ("el registre sempre crea un compte amb rol `usuari`"). Si l'API acceptés el rol, qualsevol
  persona podria crear-se un compte de biblioteca o d'administració sense passar pel formulari.
- **Precondicions**: backend aixecat i migrat. Un correu i un carnet nous.
- **Passos**:
  1. Enviar una petició al backend amb dades vàlides i, a més, els camps `rol`, `role`, `is_staff` i `is_superuser`:

     ```bash
     curl -i -X POST http://localhost:8000/api/auth/register/ \
       -H "Content-Type: application/json" \
       -d '{"nom": "Rol Prova", "correu": "rol.prova@example.com", "adreca": "C/ Major 1, 08001 Barcelona", "num_carnet": "1122334455", "contrasenya": "Llibres-de-tardor-24", "rol": "biblioteca", "role": "biblioteca", "is_staff": true, "is_superuser": true}'
     ```

  2. Consultar el compte creat:

     ```bash
     docker compose exec backend python manage.py shell -c "from usuaris.models import Usuari; u = Usuari.objects.get(email='rol.prova@example.com'); print(u.role, u.is_staff, u.is_superuser)"
     ```

- **Resultat esperat**:
  - Al pas 1, la petició respon `201` amb `"rol": "usuari"`.
  - Al pas 2 es mostra `usuari False False`.

### CP-US1-18 · Contrasenya no retornada ni desada en clar

- **Origen**: contracte ("No es retorna mai").
- **Precondicions**: el registre de CP-US1-17, amb el correu `rol.prova@example.com`.
- **Passos**:
  1. Mirar el cos de la resposta `201` del registre.
  2. Consultar la contrasenya desada:

     ```bash
     docker compose exec backend python manage.py shell -c "from usuaris.models import Usuari; print(Usuari.objects.get(email='rol.prova@example.com').password[:14])"
     ```

- **Resultat esperat**:
  - Al pas 1, la resposta no conté cap camp `contrasenya` ni `password`.
  - Al pas 2 es mostra el prefix d'un hash (`pbkdf2_sha256$`), no la contrasenya enviada.

### CP-US1-19 · Omplir i enviar el formulari amb el teclat

- **Origen**: CA2, per a usuaris que no fan servir el ratolí.
- **Precondicions**: les generals, en mida d'escriptori. Un correu i un carnet nous.
- **Passos**:
  1. Obrir la caixa de registre.
  2. Recórrer la caixa amb Tab, triar "Lector" i omplir cada camp només amb el teclat.
  3. Marcar la casella dels termes d'ús amb la barra d'espai.
  4. Prémer Retorn al botó "Completar Registre".
- **Resultat esperat**:
  - Al pas 2, el focus segueix l'ordre visual, es veu clarament i no surt de la caixa mentre és oberta.
  - Al pas 4, la caixa es tanca i la URL és `/`.

### CP-US1-20 · Doble clic a "Completar Registre"

- **Origen**: CA2. Un doble clic no ha de crear dos comptes ni mostrar errors.
- **Precondicions**: les generals. Un correu i un carnet nous.
- **Passos**:
  1. Obrir la caixa de registre.
  2. Omplir tots els camps amb dades vàlides i marcar la casella.
  3. Fer doble clic ràpid a "Completar Registre".
- **Resultat esperat**:
  - La caixa es tanca, la URL és `/` i no apareix cap missatge d'error.
  - Es crea un sol compte. Si a la pestanya Xarxa hi ha dues peticions, la segona respon `400` (correu ja registrat),
    mai `500`.

## Fora d'abast

- La pestanya "Inicia Sessió" i els tokens JWT: arribaran amb la US d'inici de sessió (P3 de `docs/api-registre.md`).
- Registre de repartidors i biblioteques: de moment només mostren l'avís (US1-T11).
- Verificació del correu i recuperació de la contrasenya: no són a cap tasca.
- Navegació de la pàgina d'inici a la pantalla de registre: és a `docs/casos-prova-us0.md`.

## Observacions per a l'equip

- **Textos dels criteris**: l'issue #3 diu "Aquest correu electronic ja està registrat" i "El format d'aquest carnet
  no es vàlid". El contracte i el backend fan servir "electrònic" i "no és vàlid". Cal que el Product Owner confirmi
  les correccions, perquè els tests comparen el text exacte. L'issue també diu "quatre camps", però en llista cinc.
- **Format del carnet**: el disseny té l'exemple `BIB-00000000`, però el contracte i el backend demanen exactament
  10 dígits. Amb el disseny actual, un usuari que copiï l'exemple rep l'error de CA5. Cal canviar el text d'exemple a
  US1-T7 o el format al backend.
- **Contrasenya massa curta**: el backend retorna el missatge de Django en anglès ("This password is too short. It
  must contain at least 8 characters."), perquè Django 5.2 no té la traducció catalana d'aquest text. Els altres
  validadors responen en català. Afecta CP-US1-15.
- **Contrasenya semblant al correu**: el serializer crida `validate_password` sense l'usuari, de manera que el
  validador `UserAttributeSimilarityValidator` no es fa servir mai i `jordi.vila.example` s'accepta. Afecta
  CP-US1-15.
- **Repetir la contrasenya**: US1-T8 demana validar que les contrasenyes coincideixen, però el disseny no té cap camp
  de repetició. Cal decidir si US1-T7 l'afegeix (CP-US1-16).
- **Termes d'ús**: el disseny té la casella "Accepto els termes d'ús i la política de privacitat", però no surt als
  criteris ni al contracte. Cal decidir si és obligatòria; si ho és, cal afegir-ne el cas.
- **Tipus de compte**: el disseny anomena "Lector" l'opció que les tasques anomenen "Usuari". Per a l'API, el rol
  continua sent `usuari`.
- **Clicar fora de la caixa (CA6)**: cap tasca de frontend no ho inclou. US1-T7 només hi ha posat el botó de
  tancar (X). Cal assignar CA6 a una tasca, perquè sense això la US1 no compleix els criteris.
- **Títol del registre**: US1-T7 ha substituït la pàgina provisional per la caixa "Crear un compte". Els casos de
  la US0 i `frontend/e2e/navegacio.spec.js` comprovaven el títol "Registre"; s'actualitzen a US1-T13.
- **Backend no disponible**: cap tasca diu què ha de passar si el backend no respon. Proposta: un missatge genèric
  (p. ex. "No s'ha pogut completar el registre. Torna-ho a provar.") a la caixa, sense tancar-la. Si s'accepta, cal
  afegir-ne el cas.
