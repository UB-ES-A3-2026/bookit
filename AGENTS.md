# AGENTS.md — Instruccions del projecte

Plataforma de lliurament a domicili de llibres de les biblioteques públiques de Catalunya.
Monòlit modular: API REST amb Django a `backend/` i SPA amb Vue 3 a `frontend/`.
Ara mateix només hi ha l'estructura del repositori; la base de dades i els projectes encara s'han de crear.

## Llenguatge i estil
- Backend: Python 3.12, Django 5.2 + Django REST Framework.
- Frontend: JavaScript, Vue 3 amb Composition API i `<script setup>`, Vite, Vue Router, Pinia i axios.
- Base de dades: PostgreSQL 16 amb Docker Compose, accedida només a través de l'ORM de Django.
- Quan existeixin, no modifiquis els fitxers de configuració de format i lint sense acord de l'equip.

## Convencions de l'equip
- Noms de domini (models, apps, rutes) en català sense accents: `Usuari`, `Llibre`, `Prestec`, `cataleg`.
  Comentaris, docstrings i textos per a l'usuari en català, amb accents.
- Branques `<tipus>/US<n>-<descripcio>` (tipus: `feat`, `fix`, `test`, `docs`, `chore`, `refactor`).
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
- S'afegirà a mesura que es creïn la base de dades i els projectes de backend i frontend.

## Àrees sensibles
Explica el pla i espera confirmació abans de tocar:
- El model d'usuari i qualsevol migració ja fusionada a `main` (quan existeixin).
- Autenticació i permisos dels endpoints.
