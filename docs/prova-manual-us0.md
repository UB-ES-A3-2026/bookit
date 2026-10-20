# Prova manual: navegació com a convidat (US0)

Resultats de la prova manual de la US0 (tasca US0-T18), feta amb els casos de prova de `docs/casos-prova-us0.md`,
i acta de la validació amb el Product Owner.

## Entorn

- **Data**: 20 d'octubre de 2026.
- **Responsable**: Biel Palomar (QA).
- **Codi**: branca `develop-QA`, commit `59acfe3`.
- **Aplicació**: aixecada en local amb `docker compose up -d --build --wait`; `db`, `backend` i `frontend` en estat
  `healthy`. Frontend a http://localhost:5173.
- **Navegador**: Chromium 152 amb un perfil net, sense cap sessió iniciada.
- **Mides**: escriptori 1280 × 720 i mòbil 375 × 812.
- **Tests E2E**: `npm run test:e2e` al mateix entorn, 6 de 6 en verd.

## Resultats

| ID | Cas | Resultat | Comentaris |
|---|---|---|---|
| CP-US0-01 | Un convidat obre la pàgina d'inici | Correcte | La URL es queda a `/`. Es veuen "bookit." i "Registra't". Cap error a la consola. |
| CP-US0-02 | Clic a "Registra't" obre la pantalla de registre | Correcte | La URL passa a `/registre` i es mostra el títol "Registre". |
| CP-US0-03 | "Registra't" en mòbil | Correcte | El botó es veu sencer a la capçalera sense desplaçar la pàgina, i no hi ha desplaçament horitzontal. En tocar-lo, passa a `/registre`. |
| CP-US0-04 | Tornar enrere des del registre | Correcte | La URL torna a `/` i es veu el botó "Registra't". |
| CP-US0-05 | Obrir `/registre` directament o recarregar-la | Correcte | En tots dos passos es mostra "Registre", sense 404. Cal repetir-lo quan hi hagi entorn desplegat. |
| CP-US0-06 | Activar "Registra't" amb el teclat | Correcte | El focus arriba al botó al segon Tab, després del logotip. Es veu amb el contorn del navegador i el fons més fosc. Retorn porta a `/registre`. |

**Resum**: 6 de 6 casos correctes. Cap defecte afecta el criteri d'acceptació.

## Observacions per a l'equip

No bloquegen la US0; cal decidir si es fan i en quina tasca.

- La pestanya del navegador mostra el títol "frontend" (`<title>` de `frontend/index.html`). Proposta: "bookit.".
- `frontend/index.html` declara `lang="en"`, però els textos són en català, i els lectors de pantalla els llegeixen
  amb pronúncia anglesa. Proposta: `lang="ca"`.
- La pàgina provisional de registre no té capçalera ni cap enllaç a l'inici: només s'hi torna amb el botó "Enrere"
  del navegador. Cal tenir-ho en compte a US1-T7.
- El contorn de focus del botó "Registra't" és el per defecte del navegador: és prim i canvia d'un navegador a
  l'altre.
- Una adreça inexistent (p. ex. `/no-existeix`) continua mostrant una pàgina en blanc, com ja s'indica a
  `docs/casos-prova-us0.md`.

## Validació amb el Product Owner

- **Data**: pendent.
- **Assistents**: pendent.
- **Demostració**: CP-US0-02 en escriptori i CP-US0-03 en mòbil, en directe.
- **Resultat**: pendent (acceptada / acceptada amb canvis / rebutjada).
- **Comentaris del Product Owner**: pendent.
