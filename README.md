# Biblioteca a domicili

Plataforma per demanar llibres i altres materials de la xarxa de biblioteques públiques de Catalunya i rebre'ls a casa.
Projecte d'Enginyeria del Software (UB), treballat amb Scrum i tauler Kanban.

## Contingut del repositori

| Ruta | Què hi ha |
|---|---|
| `backend/` | API REST (Django + DRF). Encara buida. |
| `frontend/` | SPA (Vue 3). Encara buida. |
| `docker-compose.yml` | Entorn de desenvolupament: PostgreSQL 16, backend (Django) i frontend (Vite) |
| `.env.example` | Variables d'entorn d'exemple (Django i base de dades) |
| `AGENTS.md` | Instruccions del projecte per als agents d'IA |
| `docs/plantilla-especificacio.md` | Plantilla per especificar tasques als agents |
| `docs/api-registre.md` | Contracte de l'API de registre entre backend i frontend (US1) |
| `.github/pull_request_template.md` | Plantilla de PR amb la Definition of Done ampliada |
| `.github/workflows/ci.yml` | CI amb GitHub Actions: tests del backend i build i tests del frontend a cada PR |
| `.vscode/` | Configuració compartida de VS Code: extensions recomanades i format en desar |

## Stack tecnològic

- **Backend**: API RESTful amb Python (framework Django + Django REST Framework), autenticació amb JWT (`djangorestframework-simplejwt`).
- **Frontend**: framework Vue 3 (Vite, Vue Router, Pinia, axios).
- **Base de dades**: PostgreSQL 16, executat amb Docker. Accés amb l'ORM de Django i migracions.
- **Entorn de desenvolupament**: VS Code com a IDE, Docker Compose (backend + frontend + PostgreSQL) i variables d'entorn en un fitxer `.env`.
- **Control de versions i CI**: GitHub i GitHub Actions per executar els tests a cada pull request (sense desplegament de moment).
- **Tests**: pytest-django (backend), Vitest (frontend) i Playwright (E2E).

### Configuració de VS Code

1. Obriu la carpeta arrel del repositori (no `backend/` ni `frontend/` per separat); si no, VS Code no aplica la configuració de `.vscode/`.
2. Instal·leu les extensions recomanades quan VS Code ho proposi (o a la vista d'extensions, filtre `@recommended`): Python, Ruff, Vue (Official), ESLint, Prettier i Docker.
3. El codi es formata en desar: Ruff per a Python i Prettier per a JavaScript, Vue, JSON, CSS, HTML i YAML. ESLint corregeix el que pot en desar.

Les preferències personals (tema, tipus de lletra...) van a la configuració d'usuari, no a `.vscode/settings.json`.

## Aixecar la base de dades

Requisits: Docker Desktop en marxa.

```bash
cp .env.example .env              # canvieu la contrasenya
docker compose up -d --wait db    # espera fins que la BD està llesta
docker compose ps                 # ha de sortir "healthy"
```

Per entrar a la consola de PostgreSQL: `docker compose exec db psql -U biblioteca -d biblioteca` (o l'usuari i la BD del vostre `.env`).
Per aturar-la: `docker compose down` (les dades es conserven al volum). Per esborrar-ho tot, dades incloses: `docker compose down -v`.

## Aixecar tot l'entorn amb Docker

Aixeca la base de dades, el backend i el frontend alhora, sense instal·lar Python ni Node a la màquina local.

```bash
cp .env.example .env               # si encara no el teniu
docker compose up -d --build --wait
docker compose ps                  # els tres serveis han de sortir "healthy"
```

| Servei | URL |
|---|---|
| Backend | http://localhost:8000/api/health/ (o el `BACKEND_PORT` del `.env`) |
| Frontend | http://localhost:5173 (o el `FRONTEND_PORT` del `.env`) |

- El codi de `backend/` i `frontend/` es munta als contenidors: en desar, Django i Vite es recarreguen sols.
- Dins de Docker el backend es connecta a la BD pel servei `db`; el `POSTGRES_HOST` del `.env` només s'aplica quan Django corre fora de Docker.
- El frontend només pot cridar l'API des dels orígens de `CORS_ALLOWED_ORIGINS` del `.env`. Si el vostre `.env`
  és anterior a US1-T17, afegiu-hi la variable de `.env.example`.
- Tests del backend dins del contenidor: `docker compose exec backend pytest`.
- Logs: `docker compose logs -f backend` (o `frontend`).
- Si canvieu `requirements*.txt` o `package.json`, reconstruïu la imatge: `docker compose up -d --build -V`.
- El contenidor no executa `migrate`: no s'ha de fer fins que existeixi el model d'usuari (US1-T1).

---

## Tauler Kanban

Format de referència del tauler (Trello). L'estat viu es porta al tauler; aquest document es revisa a cada Sprint Planning.

### Columnes i límits de WIP

| Columna | Què hi ha | Límit de WIP |
|---|---|---|
| **Backlog** | Tasques definides, encara no seleccionades per al sprint. | — |
| **To Do** | Seleccionades al Sprint Planning, amb les dependències resoltes i l'etiqueta de delegació posada. | — |
| **In Progress** | Algú hi treballa i té la branca de la tasca creada. | 1 per persona |
| **Code Review** | PR oberta, esperant la revisió d'una persona (no de l'agent). | 3 |
| **Testing** | QA comprova els criteris d'acceptació. | 3 |
| **Done** | Compleix la Definition of Done ampliada i està fusionada a la branca del seu bloc (`config` o la seva US). | — |

### Regles

- **Branques**: una per bloc (`config`, `US0`, `US1`...) i una per tasca, creada des de la branca del seu bloc. Vegeu "Flux de branques".
- **Pull, no push**: només s'agafa una tasca de To Do si no superes el teu límit d'In Progress.
- **Columna plena = ajudar a buidar-la**: si Code Review o Testing estan al límit, abans d'agafar feina nova cal revisar o provar.
- **Dependències**: una tasca no passa a To Do fins que totes les de "Depèn de" són a Done.
- **Done** només si es compleix la DoD ampliada (checklist de la plantilla de PR). Una US es tanca quan totes les seves tasques són a Done i la seva branca s'ha fusionat a `develop`.
- **Bloquejos**: una tasca bloquejada es marca en vermell i es comenta al seguiment.

### Flux de branques

```
main  ←  develop  ←  config  ←  C13-agents-readme
                             ←  C3-projecte-django
                  ←  US0     ←  US0-T10-pagina-inici
                  ←  US1     ←  US1-T3-serializer-registre
                             ←  US1-T4-endpoint-registre
```

| Branca | Es crea des de | La PR va cap a | Quan |
|---|---|---|---|
| `config` | `develop` | `develop` | Cada cop que s'hi tanca una tasca que necessita alguna US (p. ex. C3, C6, C7) |
| `US<n>` | `develop` | `develop` | Quan totes les tasques de la US són a Done |
| `C<n>-<descripcio>` | `config` | `config` | Quan la tasca està acabada |
| `US<n>-T<m>-<descripcio>` | `US<n>` | `US<n>` | Quan la tasca està acabada |
| `develop` | — | `main` | Al final de cada sprint |

Les branques de tasca no porten barra (`config/C13` no és vàlid si ja existeix la branca `config`: git no permet una branca i una "carpeta" amb el mateix nom).
Ningú fa push directe a `main`, `develop` ni a les branques de bloc.

**Norma de fusió** (C9): tota PR necessita l'aprovació d'una persona diferent de l'autora i els checks de la CI (C8)
en verd abans de fer el merge. GitHub no ho bloqueja: les regles de
protecció de branques no estan disponibles en repositoris privats amb el pla gratuït, així que és una norma de l'equip.

Abans de començar una US, porta-hi el que hi hagi de nou a `develop` (p. ex. la configuració): `git switch US1`, `git merge develop`.

### Etiquetes

- **Rol**: Backend, Frontend, QA, DevOps (columna "Rol").
- **Delegació** (es posa al Sprint Planning amb la matriu de decisió): **Delegable** (l'agent la fa de cap a cap, revisió lleugera), **Mixta** (l'agent en fa una part), **Humana** (no es delega).
- **Referències**: `US1-T2` vol dir la tasca T2 de la US1. Les `C` són tasques de configuració inicial.

### Camí crític

C1 → C3 → **US1-T1** (model d'usuari) → C7 → US1-T2 (primera migració) → US1-T4 (endpoint de registre).
El model d'usuari ha d'existir abans de la primera migració: no executeu `migrate` abans de US1-T1.

---

## Tasques

### Configuració inicial (tasques d'un sol cop)

Es fan una única vegada al Sprint 0 i no pertanyen a cap història d'usuari. C1–C8 són les antigues T1–T8 de la US0.

| ID | Tasca | Rol | Depèn de | Delegació | Estat |
|---|---|---|---|---|---|
| C1 | Crear el repositori a GitHub amb l'estructura `backend/` i `frontend/`, `.gitignore`, README i normes de branques i pull requests. | DevOps | — | | Done |
| C2 | Configurar VS Code per a l'equip: extensions recomanades (Python, Vue, Docker, ESLint, Prettier) i format automàtic compartit (`.vscode/settings.json`). | DevOps | C1 | | Backlog |
| C3 | Crear el projecte Django amb Django REST Framework i l'estructura d'apps per mòduls (usuaris, catàleg, préstecs...). | Backend | C1 | | Backlog |
| C4 | Crear el projecte Vue 3 amb Vite, Vue Router, Pinia i axios. | Frontend | C1 | Sergi Garcia | Backlog |
| C5 | Crear el `docker-compose.yml` amb els serveis backend, frontend i PostgreSQL 16. | DevOps | C3, C4 | | Backlog |
| C6 | Crear la base de dades PostgreSQL (usuari, contrasenya i nom de la base de dades) amb volum persistent per no perdre les dades. | DevOps | C1 | | Backlog |
| C7 | Connectar Django amb PostgreSQL (`psycopg`) llegint les credencials del fitxer `.env`, i afegir un `.env.example` al repositori. Instal·lar la dependència `django-environ` per llegir el fitxer `.env`. | Backend | C3, C6 | | Backlog |
| C8 | Configurar la CI amb GitHub Actions: instal·lar dependències i executar els tests de backend i frontend a cada pull request. | DevOps | C3, C4 | | Backlog |
| C9 | Norma d'equip per a `main`, `develop` i les branques de bloc: pull request obligatòria, 1 aprovació d'una altra persona i CI en verd (vegeu "Norma de fusió"). GitHub no permet protegir branques en repositoris privats amb el pla gratuït. | DevOps | — | | Code Review |
| C10 | Afegir tots els membres de l'equip com a col·laboradors del repositori. | DevOps | C1 | | Backlog |
| C11 | Crear el tauler Kanban (Trello) amb les columnes, els límits de WIP i les etiquetes d'aquest document. | Scrum Master | — | | Backlog |
| C12 | Triar l'eina d'agent de cada rol (Backend, Frontend, QA, DevOps) i instal·lar-la a VS Code. | Tot l'equip | — | | Backlog |
| C13 | Consensuar l'`AGENTS.md`. *(Esborrany al repositori.)* | Tot l'equip | C1 | | Code Review |
| C14 | Acordar la plantilla d'especificació de tasques per a l'agent. *(Esborrany a `docs/plantilla-especificacio.md`.)* | Tot l'equip | — | | Code Review |
| C15 | Acordar la Definition of Done ampliada. *(Esborrany a la plantilla de PR.)* | Tot l'equip | — | | Code Review |
| C16 | Tasca trivial de cap a cap amb un agent: `GET /api/health/` amb test. L'especificació és a `docs/plantilla-especificacio.md`. | Backend | C3, C7, C12, C13, C14 | | Code Review |
| C17 | Lliurar l'entregable del Sprint 0: eines per rol, AGENTS.md, plantilla d'especificació, DoD ampliada i enllaç a la PR de C16. | Scrum Master | C12–C16 | | Backlog |
| C19 | Configurar els tests del backend amb pytest-django (`requirements-dev.txt` amb `pytest` i `pytest-django`, `pytest.ini` i un test de configuració). | Backend | C7 | | Done |

### US0 — Navegació com a convidat

Comença a T9 per mantenir la numeració del document de tasques; T1–T8 són ara C1–C8.

**Abast al Sprint 0**: la pàgina principal només té el botó "Registra't". El cercador, els filtres, "Buscar llibres" i "Veure tot el catàleg" queden fora i tornaran a la US de cerca del catàleg; per això s'ha eliminat la T12.
Amb aquest abast, la T11 (component d'avís) passa a la US1 com a US1-T18, la T15 (permisos de DRF) passa a la US1 com a US1-T19 i la T14 (guard de rutes de comanda) queda fora de la planificació fins que hi hagi comandes i inici de sessió.

| ID | Tasca | Rol | Depèn de | Delegació | Estat |
|---|---|---|---|---|---|
| T9 | Configurar el router amb rutes públiques: `/` (inici) i `/registre`. | Frontend | C4 | Pau Albert | Backlog |
| T10 | Maquetar la pantalla d'inici (responsive) amb la capçalera i el botó "Registra't". | Frontend | T9 | Pau Albert | Backlog |
| T13 | Connectar el botó "Registra't" a la pantalla de registre (US1). Si encara no existeix, crear una pàgina buida (placeholder). | Frontend | T9, T10 | Pau Albert | Backlog |
| T16 | Escriure els casos de prova a partir dels criteris d'acceptació. | QA | — | | Backlog |
| T17 | Tests E2E de navegació (Playwright): el botó "Registra't" porta a la pantalla de registre. | QA | T10, T13, T16, T20 | | Backlog |
| T18 | Prova manual en local i validació amb el Product Owner. | QA | T9–T20 | | Backlog |
| T19 | Configurar Vitest al frontend (script `npm run test`, que ja executa la CI) amb un test d'exemple. | Frontend | C4 | | Backlog |
| T20 | Configurar Playwright per als tests E2E amb un test d'exemple. | QA | C4 | | Backlog |

### US1 — Registre d'usuari

El contracte de l'endpoint de registre és a `docs/api-registre.md`. La T5 (tokens JWT al registre) s'ha eliminat: el criteri només demana redirigir a la pàgina principal, i el JWT arribarà amb la US d'inici de sessió.

| ID | Tasca | Rol | Depèn de | Delegació | Estat |
|---|---|---|---|---|---|
| T1 | Model d'usuari personalitzat (`AbstractUser`) amb correu únic com a identificador, nom, adreça, número de carnet únic i rol (Usuari / Repartidor / Biblioteca). S'ha de fer abans de la primera migració del projecte. | Backend | C3 | Roger | Backlog |
| T2 | Crear i aplicar la migració inicial a la base de dades PostgreSQL (taula d'usuaris). | Backend | T1, C7 | Roger | Backlog |
| T3 | Serializer de registre amb validacions segons `docs/api-registre.md`: camps obligatoris, format del correu, format del carnet, unicitat del correu i del carnet, i contrasenya. | Backend | T1 | Alejandro | Backlog |
| T4 | Endpoint `POST /api/auth/register/` segons `docs/api-registre.md`, amb els missatges d'error exactes dels criteris ("Aquest correu electrònic ja està registrat", "Aquest usuari ja està registrat", "El format d'aquest carnet no és vàlid"). | Backend | T2, T3 | Alejandro | Backlog |
| T6 | Tests unitaris del backend: registre correcte, correu duplicat, carnet duplicat, camps buits, format invàlid. | Backend | T4 | Alejandro | Backlog |
| T7 | Maquetar el formulari de registre (responsive) amb el selector de tipus de compte (Usuari / Repartidor / Biblioteca). | Frontend | US0-T9 | Sergi Garcia | Backlog |
| T8 | Validació al client: camps obligatoris, format del correu, coincidència de contrasenyes. | Frontend | T7 | Sergi Garcia | Backlog |
| T9 | Connectar el formulari amb l'endpoint i mostrar els errors del backend al camp corresponent. | Frontend | T4, T8, T17 | Sergi Garcia | Backlog |
| T10 | Redirigir a la pàgina principal si el registre és correcte. | Frontend | T9 | Sergi Garcia | Backlog |
| T11 | Opcions "Repartidor" i "Biblioteca" mostren "Funcionalitat no implementada" (component de la T18). | Frontend | T7, T18 | Sergi Garcia | Backlog |
| T12 | Casos de prova a partir dels criteris d'acceptació. | QA | — | | Backlog |
| T13 | Tests E2E (Playwright): registre correcte amb redirecció, correu duplicat, carnet duplicat, Repartidor/Biblioteca. | QA | T10, T11, T12, US0-T20 | | Backlog |
| T14 | Validació manual en local amb el Product Owner. | QA | T1–T19 | | Backlog |
| T15 | Executar `migrate` automàticament en arrencar el contenidor del backend. | DevOps | C5, T2 | | Backlog |
| T17 | Configurar CORS amb `django-cors-headers` i els orígens permesos al fitxer `.env` (mai al repositori). | DevOps | C3 | | Backlog |
| T18 | Crear un component reutilitzable de missatge/avís (toast o modal) per a "Funcionalitat no implementada". *(Abans US0-T11.)* | Frontend | C4 | Pau Albert | Backlog |
| T19 | Configurar els permisos per defecte de DRF: `IsAuthenticated` per defecte i `AllowAny` explícit als endpoints públics (registre i salut). *(Abans US0-T15.)* | Backend | C3 | Alejandro | Backlog |
