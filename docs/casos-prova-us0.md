# Casos de prova: navegació com a convidat (US0)

Casos de prova de la US0 (tasca US0-T16), escrits a partir del criteri d'acceptació de la història. Els tests E2E
amb Playwright (US0-T17) i la prova manual amb el Product Owner (US0-T18) en surten. La US0-T24 hi afegeix els
elements nous de la pàgina d'inici: el botó "Inicia sessió" (US2-T7) i el cercador (US4-T7).
Qualsevol canvi d'aquest document passa per pull request.

## Història i criteri d'acceptació

> **COM A** usuari no registrat **VULL** poder accedir a l'aplicació sense registrar-me
> **PER AIXÍ** veure els llibres disponibles.

- **CA1**: si l'usuari fa clic a "Registra't", apareix la pantalla de registre (US1).
- **Abast al Sprint 0**: la pàgina d'inici només tenia el botó "Registra't".
- **Des del sprint 2**: la capçalera també té el botó "Inicia sessió" (US2-T7) i la pàgina té el cercador de
  llibres (US4-T7), que és com un convidat veu els llibres disponibles.

## Entorn i precondicions generals

- Aplicació aixecada en local amb `docker compose up -d` des de l'arrel. Frontend a http://localhost:5173
  (o el `FRONTEND_PORT` del `.env`).
- Navegador sense cap sessió iniciada: finestra privada o perfil net.
- Mida d'escriptori: 1280 × 720. Mida de mòbil: 375 × 812.
- Des de US1-T7, la pantalla de registre és la caixa amb el títol "Crear un compte" (abans era la pàgina
  provisional de US0-T13, amb el títol "Registre"). Els casos comproven la ruta `/registre` i aquest títol.

## Resum

| ID | Cas | Origen | Prioritat | Execució proposada |
|---|---|---|---|---|
| CP-US0-01 | Un convidat obre la pàgina d'inici | Història | Alta | E2E (T17) i manual (T18) |
| CP-US0-02 | Clic a "Registra't" obre la pantalla de registre | CA1 | Alta | E2E (T17) i manual (T18) |
| CP-US0-03 | "Registra't" en mòbil | CA1 | Alta | E2E (T17) i manual (T18) |
| CP-US0-04 | Tornar enrere des del registre | CA1 | Mitjana | E2E (T17) |
| CP-US0-05 | Obrir `/registre` directament o recarregar-la | CA1 | Mitjana | E2E (T17) |
| CP-US0-06 | Activar "Registra't" amb el teclat | CA1 | Baixa | Manual (T18) |
| CP-US0-07 | Clic a "Inicia sessió" obre la caixa d'inici de sessió | Història | Alta | E2E (T24) |
| CP-US0-08 | La capçalera en mòbil | Història | Alta | E2E (T24) |
| CP-US0-09 | Un convidat veu el cercador | Història | Alta | E2E (US4, `e2e/cerca.spec.js`) |
| CP-US0-10 | Un convidat pot cercar llibres sense iniciar sessió | Història | Alta | E2E (US4, `e2e/cerca.spec.js`) |

## Casos

### CP-US0-01 · Un convidat obre la pàgina d'inici

- **Origen**: història ("accedir a l'aplicació sense registrar-me").
- **Precondicions**: les generals.
- **Passos**:
  1. Obrir `/`.
- **Resultat esperat**:
  - La URL continua sent `/`: no redirigeix al registre ni a cap pantalla d'inici de sessió.
  - Es veu la capçalera amb la marca "bookit." i els botons "Inicia sessió" i "Registra't".
  - No apareix cap missatge d'error a la pàgina ni a la consola del navegador.

### CP-US0-02 · Clic a "Registra't" obre la pantalla de registre

- **Origen**: CA1.
- **Precondicions**: les generals, en mida d'escriptori.
- **Passos**:
  1. Obrir `/`.
  2. Fer clic al botó "Registra't" de la capçalera.
- **Resultat esperat**:
  - La URL passa a ser `/registre`.
  - Es mostra la pantalla de registre, amb el títol "Crear un compte".

### CP-US0-03 · "Registra't" en mòbil

- **Origen**: CA1, amb la pantalla d'inici responsive de US0-T10.
- **Precondicions**: les generals, en mida de mòbil.
- **Passos**:
  1. Obrir `/`.
  2. Comprovar el botó "Registra't" sense desplaçar la pàgina.
  3. Tocar el botó "Registra't".
- **Resultat esperat**:
  - Al pas 2, el botó es veu sencer, sense quedar tapat ni tallat, i la pàgina no té desplaçament horitzontal.
  - Al pas 3, la URL passa a ser `/registre` i es mostra el títol "Crear un compte".

### CP-US0-04 · Tornar enrere des del registre

- **Origen**: CA1.
- **Precondicions**: les generals.
- **Passos**:
  1. Obrir `/`.
  2. Fer clic a "Registra't".
  3. Prémer el botó "Enrere" del navegador.
- **Resultat esperat**:
  - La URL torna a ser `/` i es veu la pàgina d'inici amb el botó "Registra't".

### CP-US0-05 · Obrir `/registre` directament o recarregar-la

- **Origen**: CA1. L'usuari pot arribar al registre amb un enllaç o recarregar-lo.
- **Precondicions**: les generals.
- **Passos**:
  1. Escriure `/registre` a la barra d'adreces i prémer Retorn.
  2. Recarregar la pàgina (F5).
- **Resultat esperat**:
  - En tots dos passos es mostra la pantalla de registre amb el títol "Crear un compte", sense pàgina en blanc ni
    error 404.
- **Nota**: en local, Vite serveix l'aplicació per a qualsevol ruta. Quan hi hagi desplegament, cal repetir aquest cas
  a l'entorn desplegat.

### CP-US0-06 · Activar "Registra't" amb el teclat

- **Origen**: CA1, per a usuaris que no fan servir el ratolí.
- **Precondicions**: les generals, en mida d'escriptori.
- **Passos**:
  1. Obrir `/`.
  2. Prémer Tab fins que el focus arribi al botó "Registra't".
  3. Prémer Retorn.
- **Resultat esperat**:
  - Al pas 2, es veu clarament que el botó "Registra't" té el focus.
  - Al pas 3, la URL passa a ser `/registre` i es mostra el títol "Crear un compte".

### CP-US0-07 · Clic a "Inicia sessió" obre la caixa d'inici de sessió

- **Origen**: història, amb el botó nou de la capçalera (US2-T7).
- **Precondicions**: les generals, en mida d'escriptori.
- **Passos**:
  1. Obrir `/`.
  2. Fer clic al botó "Inicia sessió" de la capçalera.
- **Resultat esperat**:
  - La URL passa a ser `/inicia-sessio`.
  - Es mostra la caixa d'inici de sessió, amb el títol "Inicia Sessió".

### CP-US0-08 · La capçalera en mòbil

- **Origen**: història, amb la pantalla d'inici responsive.
- **Precondicions**: les generals, en mida de mòbil.
- **Passos**:
  1. Obrir `/`.
  2. Comprovar els botons "Inicia sessió" i "Registra't" sense desplaçar la pàgina.
- **Resultat esperat**:
  - Tots dos botons es veuen sencers, sense quedar tapats ni tallats, i la pàgina no té desplaçament horitzontal.

### CP-US0-09 · Un convidat veu el cercador

- **Origen**: història ("veure els llibres disponibles"), amb el cercador de US4-T7.
- **Precondicions**: les generals.
- **Passos**:
  1. Obrir `/` sense haver iniciat sessió.
- **Resultat esperat**:
  - Es veu el cercador amb el text "Quin llibre busques?" i el botó "Buscar llibres".
- **Execució**: el cobreixen els tests E2E del cercador de la US4 (`e2e/cerca.spec.js`), també en mida de mòbil.

### CP-US0-10 · Un convidat pot cercar llibres sense iniciar sessió

- **Origen**: història ("veure els llibres disponibles sense registrar-me").
- **Precondicions**: les generals.
- **Passos**:
  1. Obrir `/` sense haver iniciat sessió.
  2. Escriure un títol al cercador i prémer "Buscar llibres".
- **Resultat esperat**:
  - La URL passa a ser `/cerca?q=...` i es mostra la pàgina de resultats, sense demanar iniciar sessió.
- **Execució**: el cobreixen els tests E2E de la cerca de la US4 (`e2e/cerca.spec.js`): el cercador, la pàgina de
  resultats i el missatge quan no hi ha resultats.

## Fora d'abast

- Els filtres de cerca i "Veure tot el catàleg" del disseny: no són a cap criteri d'acceptació.
- El formulari d'inici de sessió i la capçalera amb la sessió iniciada: casos de prova de US2-T14 (`docs/casos-prova-us2.md`).
- El formulari de registre i les seves validacions: casos de prova de US1-T12 (`docs/casos-prova-us1.md`).
- L'avís "Funcionalitat no implementada": ara és US1-T18.
- El guard de rutes de comanda (antiga US0-T14): fora de la planificació fins que hi hagi comandes i inici de sessió.

## Observacions per a l'equip

- El router no té cap ruta per a adreces inexistents (p. ex. `/no-existeix`), i ara es mostra una pàgina buida. No
  forma part del criteri d'acceptació; cal acordar si es vol una pàgina 404 i, si és així, afegir-ne el cas.
