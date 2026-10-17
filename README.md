# Biblioteca a domicili

Plataforma per demanar llibres i altres materials de la xarxa de biblioteques públiques de Catalunya i rebre'ls a casa.
Projecte d'Enginyeria del Software (UB), treballat amb Scrum i tauler Kanban.

## Contingut del repositori

| Ruta | Què hi ha |
|---|---|
| `backend/` | API REST (Django + DRF). Encara buida. |
| `frontend/` | SPA (Vue 3). Encara buida. |
| `AGENTS.md` | Instruccions del projecte per als agents d'IA |
| `docs/plantilla-especificacio.md` | Plantilla per especificar tasques als agents |
| `docs/api-registre.md` | Contracte de l'API de registre entre backend i frontend (US1) |
| `.github/pull_request_template.md` | Plantilla de PR amb la Definition of Done ampliada |
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

Abans de començar una US, porta-hi el que hi hagi de nou a `develop` (p. ex. la configuració): `git switch US1`, `git merge develop`.

### Etiquetes

- **Rol**: Backend, Frontend, QA, DevOps (columna "Rol").
- **Delegació** (es posa al Sprint Planning amb la matriu de decisió): **Delegable** (l'agent la fa de cap a cap, revisió lleugera), **Mixta** (l'agent en fa una part), **Humana** (no es delega).
- **Referències**: `US1-T2` vol dir la tasca T2 de la US1. Les `C` són tasques de configuració inicial.

### Camí crític

C1 → C3 → **US1-T1** (model d'usuari) → C7 → US1-T2 (primera migració) → US2-T1 (JWT).
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
| C7 | Connectar Django amb PostgreSQL (`psycopg`) llegint les credencials del fitxer `.env`, i afegir un `.env.example` al repositori. | Backend | C3, C6 | | Backlog |
| C8 | Configurar la CI amb GitHub Actions: instal·lar dependències i executar els tests de backend i frontend a cada pull request. | DevOps | C3, C4 | | Backlog |
| C9 | Protegir les branques `main` i `develop` a GitHub: pull request obligatòria, 1 aprovació i CI en verd. | DevOps | C8 | | Backlog |
| C10 | Afegir tots els membres de l'equip com a col·laboradors del repositori. | DevOps | C1 | | Backlog |
| C11 | Crear el tauler Kanban (Trello) amb les columnes, els límits de WIP i les etiquetes d'aquest document. | Scrum Master | — | | Backlog |
| C12 | Triar l'eina d'agent de cada rol (Backend, Frontend, QA, DevOps) i instal·lar-la a VS Code. | Tot l'equip | — | | Backlog |
| C13 | Consensuar l'`AGENTS.md`. *(Esborrany al repositori.)* | Tot l'equip | C1 | | Code Review |
| C14 | Acordar la plantilla d'especificació de tasques per a l'agent. *(Esborrany a `docs/plantilla-especificacio.md`.)* | Tot l'equip | — | | Code Review |
| C15 | Acordar la Definition of Done ampliada. *(Esborrany a la plantilla de PR.)* | Tot l'equip | — | | Code Review |
| C16 | Tasca trivial de cap a cap amb un agent: `GET /api/health/` amb test. L'especificació és a `docs/plantilla-especificacio.md`. | Backend | C3, C7, C12, C13, C14 | | Backlog |
| C17 | Lliurar l'entregable del Sprint 0: eines per rol, AGENTS.md, plantilla d'especificació, DoD ampliada i enllaç a la PR de C16. | Scrum Master | C12–C16 | | Backlog |

### US0 — Navegació com a convidat

Comença a T9 per mantenir la numeració del document de tasques; T1–T8 són ara C1–C8.

**Abast al Sprint 0**: la pàgina principal només té el botó "Registra't". El cercador, els filtres, "Buscar llibres" i "Veure tot el catàleg" queden fora i tornaran a la US de cerca del catàleg; per això s'ha eliminat la T12.

| ID | Tasca | Rol | Depèn de | Delegació | Estat |
|---|---|---|---|---|---|
| T9 | Configurar el router amb rutes públiques: `/` (inici), `/login`, `/registre`. | Frontend | C4 | Pau Albert| Backlog |
| T10 | Maquetar la pantalla d'inici (responsive) amb la capçalera i el botó "Registra't". | Frontend | T9 | Pau Albert| Backlog |
| T11 | Crear un component reutilitzable de missatge/avís (toast o modal) per a "Funcionalitat no implementada". | Frontend | C4 | Pau Albert | Backlog |
| T13 | Connectar el botó "Registra't" a la pantalla de registre (US1). Si encara no existeix, crear una pàgina buida (placeholder). | Frontend | T9, T10 | Pau Albert| Backlog |
| T14 | Guard de rutes: les accions de comanda redirigeixen a login/registre si no hi ha sessió (preparat per a quan existeixin). | Frontend | T9 | Pau Albert | Backlog |
| T15 | Configurar els permisos per defecte de DRF: endpoints de consulta públics (`AllowAny`) i endpoints de comanda autenticats. | Backend | C3 | | Backlog |
| T16 | Escriure els casos de prova a partir dels criteris d'acceptació. | QA | — | | Backlog |
| T17 | Tests E2E de navegació (Playwright): cada botó porta a la pantalla correcta o mostra l'avís correcte. | QA | T10, T13, T16 | | Backlog |
| T18 | Prova manual en local i validació amb el Product Owner. | QA | T9–T17 | | Backlog |

### US1 — Registre d'usuari

| ID | Tasca | Rol | Depèn de | Delegació | Estat |
|---|---|---|---|---|---|
| T1 | Model d'usuari personalitzat (`AbstractUser`) amb correu únic com a identificador, nom, adreça, número de carnet únic i rol. S'ha de fer abans de la primera migració del projecte. | Backend | C3 | | Backlog |
| T2 | Crear i aplicar la migració inicial a la base de dades PostgreSQL (taula d'usuaris). | Backend | T1, C7 | | Backlog |
| T3 | Serializer de registre amb validacions: camps obligatoris, format del correu, format del carnet, unicitat del correu i del carnet, i contrasenya. | Backend | T1 | | Backlog |
| T4 | Endpoint `POST /api/auth/register/` amb els missatges d'error exactes dels criteris ("Aquest correu electrònic ja està registrat", "Aquest usuari ja està registrat"). | Backend | T2, T3 | | Backlog |
| T5 | Retornar els tokens JWT en el registre correcte (si decidiu login automàtic). | Backend | T4, US2-T1 | | Backlog |
| T6 | Tests unitaris del backend: registre correcte, correu duplicat, carnet duplicat, camps buits, format invàlid. | Backend | T4 | | Backlog |
| T7 | Maquetar el formulari de registre (responsive) amb el selector de tipus de compte (Usuari / Repartidor / Biblioteca). | Frontend | US0-T9 | Sergi Garcia | Backlog |
| T8 | Validació al client: camps obligatoris, format del correu, coincidència de contrasenyes. | Frontend | T7 | Sergi Garcia | Backlog |
| T9 | Connectar el formulari amb l'endpoint i mostrar els errors del backend al camp corresponent. | Frontend | T4, T8 | Sergi Garcia | Backlog |
| T10 | Desar els tokens i redirigir a la pàgina principal si el registre és correcte. | Frontend | T5, T9 | Sergi Garcia | Backlog |
| T11 | Opcions "Repartidor" i "Biblioteca" mostren "Funcionalitat no implementada" (component de la US0). | Frontend | T7, US0-T11 | Sergi Garcia | Backlog |
| T12 | Casos de prova a partir dels criteris d'acceptació. | QA | — | | Backlog |
| T13 | Tests E2E (Playwright): registre correcte amb redirecció, correu duplicat, carnet duplicat, Repartidor/Biblioteca. | QA | T10, T11, T12 | | Backlog |
| T14 | Validació manual en local amb el Product Owner. | QA | T1–T13 | | Backlog |
| T15 | Afegir l'execució automàtica de migracions en arrencar el contenidor del backend i una base de dades PostgreSQL temporal a la CI per als tests. | DevOps | C5, C8, T2 | | Backlog |
| T15 | Comprovar que una petició protegida sense token retorna 401 i amb token funciona. | QA | T3, T9 | | Backlog |
| T16 | Validació manual en local amb el Product Owner. | QA | T1–T15 | | Backlog |
| T17 | Gestionar la clau de signatura del JWT (`SECRET_KEY`) i la configuració de CORS amb variables d'entorn al fitxer `.env`, mai al repositori. | DevOps | C3 | | Backlog |
