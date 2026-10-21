# Prova manual: registre d'usuari (US1)

Resultats de la prova manual de la US1 (tasca US1-T14), feta amb els casos de prova de `docs/casos-prova-us1.md`,
i acta de la validació amb el Product Owner.

**Estat**: execució parcial. El backend, la configuració (US1-T15 i US1-T17) i la maquetació de la caixa (US1-T7)
s'han provat. Els casos que necessiten la validació al client (US1-T8), la connexió amb l'API (US1-T9), la
redirecció (US1-T10) i l'avís dels tipus de compte (US1-T11 i US1-T18) queden bloquejats. Cal repetir-los quan
aquestes tasques estiguin fusionades, i la validació amb el Product Owner es fa després.

## Entorn

- **Data**: 21 d'octubre de 2026.
- **Responsable**: Biel Palomar (QA).
- **Codi**: integració local, no publicada, de la branca `US1-T13-tests-e2e-registre` (`21e957f`, que inclou
  `develop-frontend` a `678c137` i el backend de la US1) amb `US1-T15-migrate-automatic` (`841b1c7`) i
  `US1-T17-cors` (`1f015e6`).
- **Aplicació**: aixecada en local amb `docker compose up -d --build --wait`; `db`, `backend` i `frontend` en estat
  `healthy`. Frontend a http://localhost:5173 i backend a http://localhost:8000.
- **Configuració**: `.env` amb `CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`.
- **Execució**: casos de l'API amb peticions HTTP directes i amb el shell de Django; casos de la caixa amb Chromium
  156 i un perfil net.
- **Mides**: escriptori 1280 × 720 i mòbil 375 × 812.
- **Tests E2E**: `npm run test:e2e` a la branca de US1-T13, 9 en verd i 14 pendents (`test.fixme`) fins que arribin
  US1-T8 a US1-T11.
- **Tests del backend**: `docker compose exec backend pytest`, 60 de 60 en verd.

## Comprovacions de l'entorn

| Tasca | Comprovació | Resultat |
|---|---|---|
| US1-T15 | La primera arrencada del contenidor aplica totes les migracions, inclosa `usuaris.0001_initial`. | Correcte |
| US1-T15 | Quan es reinicia, el contenidor mostra "No migrations to apply." i el procés principal és `runserver`. | Correcte |
| US1-T17 | Un preflight des de `http://localhost:5173` rep `Access-Control-Allow-Origin: http://localhost:5173`. | Correcte |
| US1-T17 | Un preflight des de `http://altre-origen.test` no rep la capçalera. | Correcte |

## Resultats

| ID | Cas | Resultat | Comentaris |
|---|---|---|---|
| CP-US1-01 | Registre correcte com a Lector | Bloquejat | La caixa mostra els cinc camps de CA1 amb "Lector" triat. L'API respon `201` amb `"rol": "usuari"`. El formulari encara no crida l'API (US1-T9) ni redirigeix (US1-T10). |
| CP-US1-02 | Registre correcte en mòbil | Bloquejat | A 375 × 812, tots els elements es veuen sencers i no hi ha desplaçament horitzontal. El registre depèn de US1-T9 i US1-T10. |
| CP-US1-03 | Correu ja registrat | Bloquejat | L'API respon `400` amb "Aquest correu electrònic ja està registrat" al camp `correu`. Falta mostrar-lo a la caixa (US1-T9). |
| CP-US1-04 | Correu ja registrat amb majúscules diferents | Bloquejat | `Existent@Example.com` rep el mateix `400` que CP-US1-03. Falta US1-T9. |
| CP-US1-05 | Carnet ja registrat | Bloquejat | L'API respon `400` amb "Aquest usuari ja està registrat" al camp `num_carnet`. Falta US1-T9. |
| CP-US1-06 | Correu i carnet ja registrats alhora | Bloquejat | L'API retorna tots dos errors a la mateixa resposta. Falta US1-T9. |
| CP-US1-07 | Format de carnet incorrecte | Bloquejat | Els cinc carnets del cas reben `400` amb "El format d'aquest carnet no és vàlid". Falta US1-T9. |
| CP-US1-08 | Enviar el formulari amb camps buits | Bloquejat | L'API retorna "Aquest camp és obligatori." a cada camp i, sense adreça, només a `adreca`. A la caixa, enviar el formulari provoca D4. |
| CP-US1-09 | Clicar fora de la caixa la tanca | Fallat | El botó "Tancar" tanca la caixa i torna a `/`. Clicar al fons no fa res: CA6 no és a cap tasca (D5). |
| CP-US1-10 | Tipus de compte "Repartidor" | Bloquejat | En fer-hi clic no canvia la selecció ni apareix cap avís (US1-T11 i US1-T18). |
| CP-US1-11 | Tipus de compte "Biblioteca" | Bloquejat | Com CP-US1-10. |
| CP-US1-12 | Tornar a "Lector" després de l'avís | Bloquejat | Depèn de US1-T9, US1-T10 i US1-T11. |
| CP-US1-13 | Correu amb format incorrecte | Bloquejat | Els quatre correus reben `400` amb "Introduïu una adreça de correu electrònic vàlida.". Falta US1-T8 o US1-T9. |
| CP-US1-14 | Camps amb només espais | Bloquejat | L'API retorna "Aquest camp és obligatori." per al nom i per a l'adreça amb tres espais. Falta US1-T8 o US1-T9. |
| CP-US1-15 | Contrasenya rebutjada pel backend | Fallat | `12345678` rep `400` amb dos missatges en català. `curta1` rep el missatge en anglès (D1). `jordi.vila.example` amb el correu `jordi.vila@example.com` s'accepta amb `201` (D2). |
| CP-US1-16 | Les contrasenyes no coincideixen | No aplica | La caixa no té camp per repetir la contrasenya. |
| CP-US1-17 | L'API no deixa triar el rol | Correcte | Respon `201` amb `"rol": "usuari"`. Al shell, el compte mostra `usuari False False`. |
| CP-US1-18 | Contrasenya no retornada ni desada en clar | Correcte | La resposta no té `contrasenya` ni `password`. La contrasenya desada comença per `pbkdf2_sha256$`. |
| CP-US1-19 | Omplir i enviar el formulari amb el teclat | Bloquejat | L'ordre del Tab segueix l'ordre visual: "Tancar", les pestanyes, els tipus de compte, els cinc camps, la casella, els dos enllaços i "Completar Registre". L'enviament depèn de US1-T9 i US1-T10. |
| CP-US1-20 | Doble clic a "Completar Registre" | Fallat | Dues peticions iguals enviades alhora a l'API reben `201` i `500` (D3). Només es crea un compte. A la caixa, depèn de US1-T9. |

**Resum**: 2 correctes, 3 fallats, 14 bloquejats i 1 que no aplica, de 20 casos.

## Defectes

| ID | Àrea | Gravetat | Descripció | Proposta |
|---|---|---|---|---|
| D1 | Backend (US1-T3) | Mitjana | La contrasenya massa curta retorna "This password is too short. It must contain at least 8 characters.", en anglès. Django 5.2 no té la traducció catalana d'aquest missatge. | Substituir el missatge al serializer per un text en català. |
| D2 | Backend (US1-T3) | Mitjana | El serializer crida `validate_password` sense l'usuari, i el validador `UserAttributeSimilarityValidator` no s'aplica mai. | Passar a `validate_password` un `Usuari` construït amb les dades de la petició (sense desar-lo). |
| D3 | Backend (US1-T4) | Baixa | Dos registres simultanis amb el mateix correu fan que el segon falli a la base de dades (`IntegrityError`) i respongui `500`. Amb `DEBUG=True`, la resposta inclou tota la traça. | Capturar l'`IntegrityError` en crear l'usuari i respondre `400` amb el missatge de CA3 o CA4. |
| D4 | Frontend (US1-T7) | Alta | El formulari no té gestor d'enviament: "Completar Registre" fa un enviament natiu per GET a `/registre?correu=…&contrasenya=…`. La contrasenya queda a la URL i a l'historial del navegador. | Evitar l'enviament natiu amb `@submit.prevent`. Com que la T7 ja és a `develop-frontend`, convé fer-ho abans de US1-T9. |
| D5 | Criteris | Alta | CA6 ("si l'usuari clica fora de la caixa, aquesta es tanca") no és a cap tasca de frontend. | Afegir-lo a una tasca de la US1, p. ex. US1-T7 o una tasca nova. |

## Observacions per a l'equip

- **`.env` existents**: cal afegir `CORS_ALLOWED_ORIGINS` als `.env` creats abans de US1-T17. Sense la variable,
  el navegador bloqueja totes les peticions del frontend.
- **Dades de prova a la base de dades local**: la prova ha creat els comptes `anna.puig@example.com`,
  `existent@example.com`, `rol.prova@example.com`, `jordi.vila@example.com` i `doble.clic@example.com`, i els tests
  E2E en creen de nous amb correus `e2e.<número>@example.com`.

## Validació amb el Product Owner

- **Data**: pendent. No es pot fer fins que US1-T8, US1-T9, US1-T10 i US1-T11 estiguin fusionades i D4 i D5 resolts.
- **Assistents**: pendent.
- **Demostració proposada**: CP-US1-01, CP-US1-03, CP-US1-05 i CP-US1-07 en escriptori, CP-US1-02 en mòbil, i
  CP-US1-09 i CP-US1-10, en directe.
- **Preguntes per al Product Owner**: els accents dels missatges de CA3 i CA5, l'exemple `BIB-00000000` del disseny
  i la casella dels termes d'ús (vegeu les observacions de `docs/casos-prova-us1.md`).
- **Resultat**: pendent (acceptada / acceptada amb canvis / rebutjada).
- **Comentaris del Product Owner**: pendent.
