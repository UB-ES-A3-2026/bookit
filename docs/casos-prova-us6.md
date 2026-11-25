# Casos de prova: comanda amb diversos llibres (US6)

Casos de prova de la US6, elaborats a partir dels criteris d'acceptació de la
història i del contracte de `docs/api-comandes.md` (US6-T5). Serveixen de base
per als tests unitaris i E2E. Qualsevol canvi d'aquest document passa per pull
request.

## Història i criteris d'acceptació

> **COM A** usuari registrat
> **VULL** poder afegir més d'un llibre a la meva comanda
> **PER AIXÍ** rebre'ls tots junts.

- **CA1**: l'usuari pot afegir diversos llibres a la mateixa comanda.
- **CA2**: no es pot afegir a la comanda un llibre sense estoc. Es mostra el
  missatge exacte: `Aquest llibre no te estoc en aquest moment. Pots apuntar-te a la llista d'espera`.
- **CA3**: no es pot superar el límit de llibres per usuari. Es mostra el
  missatge exacte: `Has superat el límit de llibres per aquesta comanda, elimina un per continuar`.
- **CA4**: si algun llibre no té estoc, s'ofereix l'opció d'apuntar-se a la
  llista d'espera.

## Entorn i precondicions generals

- Aplicació disponible en un entorn de proves amb la base de dades migrada.
- Usuari de prova autenticat amb el rol `usuari`; per als casos de permisos,
  també es disposa d'un usuari sense sessió i de comptes de biblioteca i
  repartidor.
- Biblioteca activa de prova i llibres sintètics associats a aquesta biblioteca.
- Les dades de cada cas són independents, tret que s'indiqui el contrari.
- El límit de llibres és el valor configurat a `LIMIT_LLIBRES_COMANDA`; no s'ha
  de donar per fet que sigui sempre 5.
- La comanda s'envia a `POST /api/prestecs/comandes/` quan l'usuari la confirma.
  Els llibres seleccionats abans de confirmar es mantenen al frontend.

## Dades de prova

| Dada | Valor |
|---|---|
| Usuari | Compte de prova actiu amb rol `usuari` |
| Biblioteca | Biblioteca activa de prova |
| Llibres disponibles | Diversos llibres diferents amb exemplars disponibles a la biblioteca |
| Llibre sense estoc | Llibre existent a la biblioteca, sense exemplars disponibles |
| Llibre inexistent | Identificador que no correspon a cap llibre |
| Límit | Valor configurat a `LIMIT_LLIBRES_COMANDA` |
| Llibres per superar el límit | `LIMIT_LLIBRES_COMANDA` més un llibre |

## Resum

| ID | Cas | Criteri / contracte | Prioritat | Tipus | Execució proposada |
|---|---|---|---|---|---|
| CP-US6-01 | Confirmar una comanda amb diversos llibres disponibles | CA1 | Alta | Correcte | E2E i API |
| CP-US6-02 | Mantenir separades les comandes de biblioteques diferents | P1 de T5 | Mitjana | Correcte | E2E |
| CP-US6-03 | Enviar una comanda sense biblioteca | Contracte T5 | Alta | Error | API |
| CP-US6-04 | Enviar una comanda sense llibres | Contracte T5 | Alta | Error | API |
| CP-US6-05 | Enviar una llista de llibres buida | Contracte T5 | Alta | Error | API |
| CP-US6-06 | Repetir un llibre a la mateixa comanda | Contracte T5 | Alta | Error | API |
| CP-US6-07 | Fer servir una biblioteca inexistent o inactiva | Contracte T5 | Alta | Error | API |
| CP-US6-08 | Incloure un identificador de llibre invàlid o inexistent | Contracte T5 | Alta | Error | API |
| CP-US6-09 | Superar el límit de llibres | CA3 | Alta | Error | E2E i API |
| CP-US6-10 | Incloure un llibre sense estoc | CA2, CA4 | Alta | Error | E2E i API |
| CP-US6-11 | Crear una comanda sense autenticació | Contracte T5 | Alta | Error | API |
| CP-US6-12 | Crear una comanda amb rol no autoritzat | Contracte T5 | Alta | Error | API |

## Casos de prova

### CP-US6-01 · Confirmar una comanda amb diversos llibres disponibles

- **Origen**: CA1.
- **Precondicions**: les generals; hi ha almenys dos llibres diferents amb
  exemplars disponibles a la mateixa biblioteca.
- **Passos**:
  1. Afegir dos o més llibres disponibles de la biblioteca a la comanda.
  2. Confirmar la comanda.
- **Resultat esperat**:
  - Es crea una única comanda amb tots els llibres seleccionats.
  - La resposta és `201 Created` i conté la biblioteca, els llibres i l'estat
    inicial `rebuda`.
  - Es reserva un exemplar de cada llibre de la comanda.
- **Tipus**: correcte.
- **Automatització**: Playwright per al flux de selecció i confirmació; API i
  pytest-django per a la resposta i les reserves.

### CP-US6-02 · Mantenir separades les comandes de biblioteques diferents

- **Origen**: P1 de les decisions documentades a T5.
- **Precondicions**: hi ha llibres disponibles en dues biblioteques diferents.
- **Passos**:
  1. Afegir a la selecció llibres que ofereixen biblioteques diferents.
  2. Completar el flux de comanda per als llibres de cada biblioteca.
- **Resultat esperat**:
  - Cada comanda correspon a una sola biblioteca.
  - Els llibres de biblioteques diferents no es confirmen en una mateixa
    comanda.
- **Tipus**: correcte.
- **Automatització**: Playwright; el comportament d'una petició que només pot
  contenir una biblioteca es comprova també a l'API.

### CP-US6-03 · Enviar una comanda sense biblioteca

- **Origen**: contracte de T5, errors de `biblioteca` obligatòria.
- **Passos**: enviar la petició sense el camp `biblioteca` i repetir-la amb el
  camp a `null`.
- **Resultat esperat**:
  - La resposta és `400 Bad Request`.
  - El camp `biblioteca` conté exactament `Aquest camp és obligatori.`.
  - No es crea cap comanda ni es reserva cap exemplar.
- **Tipus**: error.
- **Automatització**: API.

### CP-US6-04 · Enviar una comanda sense llibres

- **Origen**: contracte de T5, errors de `llibres` obligatori.
- **Passos**: enviar la petició sense el camp `llibres` i repetir-la amb el camp
  a `null`.
- **Resultat esperat**:
  - La resposta és `400 Bad Request`.
  - El camp `llibres` conté exactament `Aquest camp és obligatori.`.
  - No es crea cap comanda ni es reserva cap exemplar.
- **Tipus**: error.
- **Automatització**: API.

### CP-US6-05 · Enviar una llista de llibres buida

- **Origen**: contracte de T5.
- **Passos**: enviar una petició vàlida excepte perquè `llibres` és una llista
  buida.
- **Resultat esperat**:
  - La resposta és `400 Bad Request`.
  - El camp `llibres` conté exactament `Afegeix almenys un llibre a la comanda.`.
  - No es crea cap comanda ni es reserva cap exemplar.
- **Tipus**: error.
- **Automatització**: API.

### CP-US6-06 · Repetir un llibre a la mateixa comanda

- **Origen**: contracte de T5.
- **Passos**: enviar una petició amb el mateix identificador de llibre més d'una
  vegada.
- **Resultat esperat**:
  - La resposta és `400 Bad Request`.
  - El camp `llibres` conté exactament `Un llibre no pot sortir dues vegades a la mateixa comanda.`.
  - No es crea cap comanda ni es reserva cap exemplar.
- **Tipus**: error.
- **Automatització**: API.

### CP-US6-07 · Fer servir una biblioteca inexistent o inactiva

- **Origen**: contracte de T5.
- **Passos**: enviar la petició amb un identificador que no correspon a una
  biblioteca activa.
- **Resultat esperat**:
  - La resposta és `400 Bad Request`.
  - El camp `biblioteca` conté exactament `La biblioteca no existeix.`.
  - No es crea cap comanda ni es reserva cap exemplar.
- **Tipus**: error.
- **Automatització**: API.

### CP-US6-08 · Incloure un identificador de llibre invàlid o inexistent

- **Origen**: contracte de T5.
- **Passos**: repetir la petició amb un identificador de llibre no numèric i
  amb un identificador numèric inexistent.
- **Resultat esperat**:
  - En tots dos casos, la resposta és `400 Bad Request`.
  - El camp `llibres` conté exactament `Algun dels llibres no existeix.`.
  - No es crea cap comanda ni es reserva cap exemplar.
- **Tipus**: error.
- **Automatització**: API.

### CP-US6-09 · Superar el límit de llibres

- **Origen**: CA3.
- **Precondicions**: la petició conté més llibres que el valor configurat a
  `LIMIT_LLIBRES_COMANDA`.
- **Passos**: confirmar una comanda que supera el límit; fer servir almenys un
  llibre sense estoc per verificar que el límit es valida abans que l'estoc.
- **Resultat esperat**:
  - Abans d'enviar, la interfície avisa amb el missatge exacte `Has superat el límit de llibres per aquesta comanda, elimina un per continuar`.
  - Si s'envia la petició igualment, la resposta és `400 Bad Request` i el camp
    `llibres` conté exactament el mateix missatge.
  - No es crea la comanda ni es reserva cap exemplar.
  - No es retorna també l'error d'estoc, perquè la validació del límit té
    prioritat.
- **Tipus**: error.
- **Automatització**: Playwright per a l'avís abans d'enviar; API per a la
  validació del servidor.

### CP-US6-10 · Incloure un llibre sense estoc

- **Origen**: CA2 i CA4.
- **Precondicions**: la llista inclou un llibre sense exemplars disponibles i,
  opcionalment, llibres amb estoc.
- **Passos**:
  1. Des dels resultats de cerca o el detall del llibre, intentar afegir a la
     comanda un llibre sense exemplars disponibles.
  2. Comprovar si el llibre queda a la selecció i si es mostra l'opció de llista
     d'espera.
  3. Per comprovar la protecció del servidor davant d'un canvi d'estoc, afegir
     un llibre quan encara està disponible i esgotar-ne l'estoc abans de
     confirmar la comanda.
  4. Confirmar la comanda. Si la petició inclou altres llibres amb estoc,
     comprovar que tampoc no es confirmen parcialment.
- **Resultat esperat**:
  - Un llibre que ja no té estoc no queda afegit a la selecció de la comanda.
  - Es mostra exactament el missatge `Aquest llibre no te estoc en aquest moment. Pots apuntar-te a la llista d'espera`.
  - La interfície ofereix l'opció d'apuntar-se a la llista d'espera per al
    llibre indicat.
  - Si l'estoc s'esgota després d'afegir el llibre a la selecció, la confirmació
    retorna `400 Bad Request`; `llibres` conté el mateix missatge i
    `sense_estoc` identifica el llibre.
  - No es crea cap comanda ni es reserva cap exemplar, inclosos els llibres que
    sí que tenien estoc.
- **Tipus**: error.
- **Automatització**: Playwright per a l'intent d'afegir, el missatge i l'opció
  de llista d'espera; API per a la resposta quan l'estoc s'esgota abans de
  confirmar i per comprovar que no hi ha reserves parcials.
- **Abast**: aquest cas comprova que s'ofereix l'opció. La subscripció efectiva a
  la llista d'espera queda fora del contracte de T5.

### CP-US6-11 · Crear una comanda sense autenticació

- **Origen**: contracte de T5 i `docs/api-auth.md`.
- **Passos**: enviar una petició sense capçalera `Authorization`.
- **Resultat esperat**:
  - La resposta és `401 Unauthorized`, amb el format definit a
    `docs/api-auth.md`.
  - No es crea cap comanda ni es reserva cap exemplar.
- **Tipus**: error.
- **Automatització**: API.

### CP-US6-12 · Crear una comanda amb rol no autoritzat

- **Origen**: contracte de T5.
- **Passos**: enviar una petició autenticada amb un compte de biblioteca i
  repetir-la amb un compte de repartidor.
- **Resultat esperat**:
  - La resposta és `403 Forbidden`.
  - El cos conté exactament `{"detail": "No té permisos per realitzar aquesta acció."}`.
  - No es crea cap comanda ni es reserva cap exemplar.
- **Tipus**: error.
- **Automatització**: API.

## Notes pendents

- El contracte de T5 continua marcat com a esborrany. Si el Product Owner canvia
  les decisions de biblioteca única o el límit, cal actualitzar les dades i els
  casos afectats.
- La selecció del frontend és provisional: l'estoc es torna a validar en
  confirmar la comanda, ja que pot canviar mentre l'usuari l'està preparant.
- El contracte defineix l'opció d'oferir la llista d'espera, però no l'endpoint
  ni el flux per completar-hi la subscripció. Aquest document no pressuposa
  aquest comportament.