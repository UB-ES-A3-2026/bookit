# AGENTS.md — Instruccions del projecte

Plataforma de lliurament a domicili de llibres de les biblioteques públiques de Catalunya.
Monòlit modular: API REST amb Django a `backend/` i SPA amb Vue 3 a `frontend/`.
Ja hi ha els projectes de backend i frontend i la base de dades PostgreSQL; Django es connecta a PostgreSQL amb les credencials del fitxer `.env` carregades amb `django-environ` (C7).

## Llenguatge i estil
- Backend: Python 3.12, Django 5.2 + Django REST Framework.
- Frontend: JavaScript, Vue 3 amb Composition API i `<script setup>`, Vite, Vue Router, Pinia i axios.
- Base de dades: PostgreSQL 16 amb Docker Compose, accedida només a través de l'ORM de Django.
- Quan existeixin, no modifiquis els fitxers de configuració de format i lint sense acord de l'equip.

## Convencions de l'equip
- Noms de domini (models, apps, rutes) en català sense accents: `Usuari`, `Llibre`, `Prestec`, `cataleg`.
  Comentaris, docstrings i textos per a l'usuari en català, amb accents.
- Branques: `main` (versió estable) ← `develop` (integració) ← una branca per bloc ← una branca per tasca.
  - Branques de bloc, creades des de `develop`: `config` (tasques C) i una per història d'usuari (`US0`, `US1`, `US2`...).
  - Branques de tasca, creades des de la branca del seu bloc: `C<n>-<descripcio>` o `US<n>-T<m>-<descripcio>`.
    P. ex. `C13-agents-readme` (des de `config`) o `US1-T4-endpoint-registre` (des de `US1`).
- Pull requests: tasca → branca del seu bloc; `config` → `develop` quan s'hi tanca una tasca que necessita una US;
  US acabada → `develop`; `develop` → `main` al final de cada sprint. Mai es fa push directe a `main`, `develop`
  ni a les branques de bloc.
- Tota PR necessita l'aprovació d'una persona diferent de l'autora i la CI en verd abans del merge (norma de l'equip, C9).
- Commits `<tipus>(<àmbit>): <descripció en imperatiu>`, p. ex. `feat(usuaris): afegeix l'endpoint de registre`.
- Tot el codi del backend va a `backend/` i tot el del frontend a `frontend/`. Totes les rutes de l'API van sota `/api/`.

## Restriccions permanents
- No afegeixis dependències noves si la tasca no ho indica explícitament.
- Mai escriguis secrets al codi ni facis commit del `.env`. Les variables noves s'afegeixen al `.env.example`
  amb un valor d'exemple.
- Res de SQL escrit a mà: models i migracions de Django.

## Tests i qualitat
- Backend: pytest-django. Frontend: Vitest. Cada funcionalitat nova té tests del cas correcte i dels casos d'error.
- Tests del backend (des de `backend/`, amb la base de dades aixecada i el `.env` a l'arrel):
  `pip install -r requirements-dev.txt` i `pytest`. pytest-django crea i esborra una base de dades `test_<nom>`.
  Tests de projecte a `backend/tests/`; els de cada app, al `tests.py` de l'app o en fitxers `test_*.py`.
- Les ordres de lint i les de test del frontend s'afegiran quan es configurin.
- CI (`.github/workflows/ci.yml`): a cada PR executa `manage.py check` i `pytest` amb un PostgreSQL 16 temporal,
  i `npm ci`, `npm run build` i `npm run test` (quan existeixi l'script) al frontend. Ha d'acabar en verd abans del merge.

## Build i execució
- Backend (des de `backend/`): `python -m venv .venv`, activar-lo i `pip install -r requirements.txt`.
  Comprovació: `python manage.py check`. Servidor: `python manage.py runserver`.
- Apps del backend (una per mòdul): `usuaris`, `cataleg`, `prestecs`. Cada app té el seu `urls.py`
  inclòs a `config/urls.py` sota `/api/<app>/`.
- El contenidor del backend executa `migrate` en arrencar (US1-T15). Fora de Docker, cal executar
  `python manage.py migrate` després d'aixecar la base de dades.
- Base de dades (des de l'arrel): `cp .env.example .env` (canvieu la contrasenya) i `docker compose up -d --wait db`.
  `docker compose ps` ha de mostrar `healthy`. Connexió a `127.0.0.1:5432` (o el `POSTGRES_PORT` del `.env`).
- Frontend (des de `frontend/`): `npm ci` i `npm run dev` (http://localhost:5173).
- Entorn complet amb Docker (des de l'arrel): `docker compose up -d --build --wait` aixeca `db`, `backend`
  (http://localhost:8000) i `frontend` (http://localhost:5173). Dins de Docker el backend usa `POSTGRES_HOST=db`.
  Tests del backend al contenidor: `docker compose exec backend pytest`.

## Àrees sensibles
Explica el pla i espera confirmació abans de tocar:
- El model d'usuari i qualsevol migració ja fusionada a `develop` (quan existeixin).
- Autenticació i permisos dels endpoints.
