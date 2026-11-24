# Casos de prova: llibres en préstec (US19)

Casos de prova de la US19, elaborats a partir dels criteris d'acceptació i del
contracte de `docs/api-prestecs.md` (US19-T2). Serveixen de base per als tests
de l'API i E2E. Qualsevol canvi d'aquest document passa per pull request.

## Història i criteris d'acceptació

> **COM A** usuari registrat
> **VULL** veure els llibres que tinc en préstec i la seva data límit de devolució
> **PER AIXÍ** saber quan els he de tornar.

- **CA1**: l'usuari pot veure la llista dels llibres que té en préstec.
- **CA2**: cada llibre mostra el títol, la biblioteca a la qual pertany i la
  data límit de devolució.
- **CA3**: els llibres apareixen ordenats per data límit de devolució, del més
  proper al més llunyà.
- **CA4**: els llibres amb la data límit superada es destaquen amb l'avís exacte
  `Termini de devolució superat`.
- **CA5**: des de cada llibre es pot accedir a programar-ne la devolució (US9).
- **CA6**: si l'usuari no té cap llibre en préstec, es mostra exactament
  `No tens cap llibre en préstec`.

## Entorn i precondicions generals

- Aplicació disponible en un entorn de proves amb la base de dades migrada.
- Backend, frontend i PostgreSQL disponibles. Per executar-los en local, seguir
  les instruccions de configuració i `docker compose up -d --wait` del README.
- Usuari A de prova amb rol `usuari`, autenticat amb un token d'accés vàlid.
- Usuari B de prova diferent d'A, per comprovar que cadascú només veu els seus
  préstecs.
- Llibres, biblioteques i comptes de prova amb dades sintètiques; no s'utilitzen
  dades personals reals.
- L'endpoint és `GET /api/prestecs/prestecs/`.
- Les dates de prova han de ser controlables o fixades perquè el cas del dia de
  venciment no depengui de la data real en què s'executen les proves.

## Dades de prova

| Dada | Valor |
|---|---|
| Usuari A | Usuari actiu de prova amb rol `usuari` |
| Usuari B | Un altre usuari actiu, amb préstecs diferents |
| Biblioteques | Biblioteca A i Biblioteca B, totes dues amb llibres de prova |
| Préstec vençut | Data límit anterior a la data de prova |
| Préstec que venç avui | Data límit igual a la data de prova |
| Préstec pròxim | Data límit posterior a avui i anterior a les altres dates futures |
| Préstec futur | Data límit posterior a la data del préstec pròxim |
| Empat de data límit | Dos préstecs amb la mateixa data límit i dates d'inici diferents |
| Préstec retornat | Préstec amb data de devolució informada, si es pot preparar al model |

Els valors de les dates es poden fixar abans d'executar els casos. La durada del
préstec no forma part de la verificació de la llista: el contracte manté de
manera provisional 30 dies fins que el Product Owner decideixi una altra cosa.

## Resum

| ID | Cas | Criteri / contracte | Prioritat | Tipus | Execució proposada |
|---|---|---|---|---|---|
| CP-US19-01 | Mostrar la llista de préstecs actius de l'usuari | CA1 | Alta | Correcte | API i E2E |
| CP-US19-02 | Mostrar el títol, la biblioteca i la data límit | CA2 | Alta | Correcte | API i E2E |
| CP-US19-03 | Ordenar per data límit i desfer empats per data d'inici | CA3, contracte T2 | Alta | Correcte | API i E2E |
| CP-US19-04 | Destacar préstecs vençuts amb el missatge exacte | CA4 | Alta | Correcte | API i E2E |
| CP-US19-05 | Accedir a programar la devolució del llibre corresponent | CA5, decisió D2 | Alta | Correcte / pendent de definició | E2E |
| CP-US19-06 | Mostrar el missatge quan no hi ha préstecs | CA6 | Alta | Correcte | API i E2E |
| CP-US19-07 | Mostrar només préstecs actius de l'usuari autenticat | Contracte T2 | Alta | Correcte | API |
| CP-US19-08 | Rebutjar la consulta sense autenticació o amb rol no autoritzat | Contracte T2 | Alta | Error | API |

## Casos de prova

### CP-US19-01 · Mostrar la llista de préstecs actius de l'usuari

- **Criteri d'acceptació**: CA1.
- **Precondicions**:
  - Les generals.
  - L'usuari A té més d'un préstec actiu.
- **Passos**:
  1. Iniciar sessió com a usuari A.
  2. Obrir la pàgina "Els meus préstecs" o consultar
     `GET /api/prestecs/prestecs/`.
- **Resultat esperat**:
  - L'API retorna `200 OK` i una llista amb els préstecs actius de l'usuari A.
  - A la pàgina es mostra una entrada per cada llibre en préstec.
  - Els préstecs retornats corresponen a l'usuari A.
- **Tipus**: correcte.
- **Automatització**:
  - pytest-django: comprovar els préstecs retornats.
  - Playwright: comprovar que la llista es mostra a la pàgina.

### CP-US19-02 · Mostrar el títol, la biblioteca i la data límit

- **Criteri d'acceptació**: CA2.
- **Precondicions**:
  - Les generals.
  - L'usuari A té un préstec d'un llibre d'una biblioteca coneguda.
- **Passos**: consultar els préstecs de l'usuari A i localitzar el llibre de
  prova.
- **Resultat esperat**:
  - El préstec mostra el títol del llibre.
  - Mostra el nom de la biblioteca a la qual pertany.
  - Mostra la data límit de devolució amb el format de data acordat a la
    interfície.
  - Les dades corresponen al mateix préstec; no es barregen llibres,
    biblioteques o dates.
- **Tipus**: correcte.
- **Automatització**:
  - pytest-django: comprovar els camps `llibre.titol`, `biblioteca.nom` i
    `data_limit` de la resposta.
  - Playwright: comprovar les dades visibles.

### CP-US19-03 · Ordenar per data límit i desfer empats per data d'inici

- **Criteri d'acceptació**: CA3.
- **Precondicions**:
  - Les generals.
  - L'usuari A té préstecs amb dates límit vençudes, d'avui i futures.
  - Dos préstecs tenen la mateixa data límit però dates d'inici diferents.
- **Passos**: consultar els préstecs de l'usuari A.
- **Resultat esperat**:
  - Els préstecs apareixen per data límit ascendent, del més proper al més
    llunyà segons el contracte.
  - Si dos préstecs tenen la mateixa data límit, surt primer el que té la data
    d'inici més antiga.
  - La interfície conserva el mateix ordre que la resposta de l'API.
- **Tipus**: correcte.
- **Automatització**:
  - pytest-django: comprovar l'ordre de la resposta.
  - Playwright: comprovar l'ordre dels elements visibles.

### CP-US19-04 · Destacar préstecs vençuts amb el missatge exacte

- **Criteri d'acceptació**: CA4.
- **Precondicions**:
  - Les generals.
  - L'usuari A té un préstec vençut, un que venç avui i un amb data futura.
- **Passos**: obrir la pàgina "Els meus préstecs" i revisar les tres entrades.
- **Resultat esperat**:
  - El préstec amb data límit anterior a avui té `termini_superat: true` a
    l'API i es mostra destacat.
  - Al préstec vençut es mostra exactament l'avís
    `Termini de devolució superat`.
  - El préstec que venç avui té `termini_superat: false` i no mostra l'avís.
  - El préstec futur tampoc mostra l'avís.
- **Tipus**: correcte.
- **Automatització**:
  - pytest-django: comprovar `termini_superat` amb dates controlades.
  - Playwright: comprovar el missatge exacte només al préstec vençut.

### CP-US19-05 · Accedir a programar la devolució del llibre corresponent

- **Criteri d'acceptació**: CA5.
- **Precondicions**:
  - Les generals.
  - L'usuari A té almenys dos préstecs actius.
- **Passos**:
  1. Localitzar l'acció per programar la devolució en cada préstec.
  2. Activar-la per a un llibre concret, quan el flux de la US9 estigui
     disponible.
- **Resultat esperat**:
  - L'acció correspon al préstec del llibre seleccionat i transmet el seu
    identificador, no el d'un altre llibre de la llista.
  - Quan la US9 estigui implementada, es pot accedir al flux de programació de
    la devolució d'aquell préstec.
- **Tipus**: correcte.
- **Automatització**: Playwright quan el flux de la US9 estigui disponible.
- **Abast provisional**: la decisió D2 de `docs/api-prestecs.md` permet que,
  mentre la US9 no estigui implementada, el control es mostri desactivat o no
  es mostri. Cal confirmar amb el Product Owner quin comportament aplicar abans
  de donar per validat aquest criteri.

### CP-US19-06 · Mostrar el missatge quan no hi ha préstecs

- **Criteri d'acceptació**: CA6.
- **Precondicions**:
  - Les generals.
  - L'usuari A no té cap préstec actiu.
- **Passos**: consultar `GET /api/prestecs/prestecs/` i obrir la pàgina "Els
  meus préstecs".
- **Resultat esperat**:
  - L'API retorna `200 OK` amb una llista buida: `[]`.
  - La pàgina mostra exactament `No tens cap llibre en préstec`.
  - No es mostren entrades de préstec ni el missatge d'error.
- **Tipus**: correcte.
- **Automatització**:
  - pytest-django: comprovar la llista buida.
  - Playwright: comprovar el missatge exacte i l'absència d'entrades.

### CP-US19-07 · Mostrar només préstecs actius de l'usuari autenticat

- **Origen**: contracte T2.
- **Precondicions**:
  - Els usuaris A i B tenen préstecs diferents.
  - Si el model ho permet, hi ha un préstec retornat de l'usuari A.
- **Passos**:
  1. Consultar els préstecs autenticat com a usuari A.
  2. Repetir-ho autenticat com a usuari B.
- **Resultat esperat**:
  - Cada usuari només veu els seus propis préstecs.
  - Un préstec retornat no apareix a la llista.
  - No s'exposen títols, biblioteques ni dates de préstecs d'un altre usuari.
- **Tipus**: correcte / permisos.
- **Automatització**: pytest-django.

### CP-US19-08 · Rebutjar la consulta sense autenticació o amb rol no autoritzat

- **Origen**: contractes T2 i `docs/api-auth.md`.
- **Passos**:
  1. Consultar `GET /api/prestecs/prestecs/` sense capçalera
     `Authorization`.
  2. Repetir-ho amb un token invàlid o caducat.
  3. Repetir-ho autenticat com a biblioteca, repartidor i usuari desactivat.
- **Resultat esperat**:
  - Les peticions sense autenticació retornen `401 Unauthorized`, amb el format
    definit a `docs/api-auth.md`.
  - Les peticions amb rol no autoritzat o usuari desactivat retornen
    `403 Forbidden` amb el cos exacte:
    `{"detail": "No té permisos per realitzar aquesta acció."}`
  - No es retorna cap préstec.
- **Tipus**: error.
- **Automatització**: pytest-django.

## Matriu de traçabilitat

| Criteri d'acceptació | Casos que el cobreixen | Cobertura |
|---|---|---|
| CA1: veure la llista de llibres en préstec | CP-US19-01, CP-US19-06 | Cobert |
| CA2: mostrar títol, biblioteca i data límit | CP-US19-02 | Cobert |
| CA3: ordenar per data límit | CP-US19-03 | Cobert |
| CA4: destacar el termini superat | CP-US19-04 | Cobert |
| CA5: accedir a programar la devolució | CP-US19-05 | Pendent de la US9 i de confirmar D2 |
| CA6: missatge quan la llista és buida | CP-US19-06 | Cobert |

## Decisions i abast

- La durada del préstec és provisionalment de 30 dies des del lliurament,
  configurable amb `DURADA_PRESTEC_DIES`. Aquests casos comproven la data límit
  retornada i mostrada, no fixen una durada de negoci definitiva.
- El mateix dia de la data límit encara no es considera vençut; només ho és si
  la data límit ja ha passat.
- Només es llisten els préstecs que no s'han retornat.
- La US9 encara no està implementada. Segons D2, el control per programar la
  devolució pot estar desactivat o no aparèixer; cal confirmar amb el Product
  Owner quin comportament s'espera.
