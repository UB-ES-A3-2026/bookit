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
- Tota PR necessita l'aprovació d'una persona diferent de l'autora abans del merge (norma de l'equip, C9).
- Commits `<tipus>(<àmbit>): <descripció en imperatiu>`, p. ex. `feat(usuaris): afegeix l'endpoint de registre`.
- Tot el codi del backend va a `backend/` i tot el del frontend a `frontend/`. Totes les rutes de l'API van sota `/api/`.

## Restriccions permanents
- No afegeixis dependències noves si la tasca no ho indica explícitament.
- Mai escriguis secrets al codi ni facis commit del `.env`. Les variables noves s'afegeixen al `.env.example`
  amb un valor d'exemple.
- Res de SQL escrit a mà: models i migracions de Django.

## Tests i qualitat
- Backend: pytest-django. Frontend: Vitest. Cada funcionalitat nova té tests del cas correcte i dels casos d'error.
- Les ordres de test i lint s'afegiran aquí quan es creïn els projectes.

## Build i execució
- Backend (des de `backend/`): `python -m venv .venv`, activar-lo i `pip install -r requirements.txt`.
  Comprovació: `python manage.py check`. Servidor: `python manage.py runserver`.
- Apps del backend (una per mòdul): `usuaris`, `cataleg`, `prestecs`. Cada app té el seu `urls.py`
  inclòs a `config/urls.py` sota `/api/<app>/`.
- No executeu `migrate` fins que existeixi el model d'usuari (US1-T1).
- Base de dades (des de l'arrel): `cp .env.example .env` (canvieu la contrasenya) i `docker compose up -d --wait db`.
  `docker compose ps` ha de mostrar `healthy`. Connexió a `localhost:5432` (o el `POSTGRES_PORT` del `.env`).
- Frontend: s'afegirà més endavant.

## Àrees sensibles
Explica el pla i espera confirmació abans de tocar:
- El model d'usuari i qualsevol migració ja fusionada a `develop` (quan existeixin).
- Autenticació i permisos dels endpoints.
