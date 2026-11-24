# Casos de prova: tipus de lliurament (US7)

Casos de prova de la US7, elaborats a partir dels criteris d'acceptació de la
història i del contracte de `docs/api-comandes.md` (US7-T1). Serveixen de base
per als tests unitaris i E2E. Qualsevol canvi d'aquest document passa per pull
request.

## Història i criteris d'acceptació

> **COM A** usuari
> **VULL** poder seleccionar entre lliurament a domicili o recollida en una
> biblioteca
> **PER AIXÍ** adaptar-ho a com em convé.

- **CA1**: la recollida en una biblioteca no té despeses d'enviament.
- **CA2**: l'enviament a domicili mostra el cost de les despeses d'enviament
  abans de confirmar la comanda.

## Entorn i precondicions generals

- Aplicació disponible en un entorn de proves amb la base de dades migrada.
- Usuari de prova autenticat amb el rol `usuari` i una adreça de perfil definida.
- Biblioteca activa de prova amb llibres disponibles.
- Les dades de cada cas són independents, tret que s'indiqui el contrari.
- El cost a domicili és el valor de `COST_ENVIAMENT_DOMICILI`; el contracte
  estableix provisionalment `2.50` euros per comanda. No s'ha de tractar aquest
  valor provisional com un criteri immutable.
- La recollida és a la mateixa biblioteca de la comanda i el seu cost és
  `0.00`.

## Dades de prova

| Dada | Valor |
|---|---|
| Usuari | Compte de prova actiu amb rol `usuari` |
| Biblioteca de la comanda | Biblioteca activa de prova |
| Adreça del perfil | `C/ de la Muntanya 12, 08035 Barcelona` |
| Adreça alternativa | `C/ de Provença 123, 08029 Barcelona` |
| Tipus de lliurament invàlid | `bustia` |
| Cost a domicili | Valor configurat; `2.50` al contracte provisional |
| Cost de recollida | `0.00` |

## Resum

| ID | Cas | Criteri / contracte | Prioritat | Tipus | Execució proposada |
|---|---|---|---|---|---|
| CP-US7-01 | Lliurament a domicili mostra el cost abans de confirmar | CA2 | Alta | Correcte | E2E i API |
| CP-US7-02 | Recollida sense despeses d'enviament | CA1 | Alta | Correcte | E2E i API |
| CP-US7-03 | Fer servir l'adreça del perfil per al domicili | Contracte T1 | Alta | Correcte | API |
| CP-US7-04 | Substituir l'adreça del perfil per al domicili | Contracte T1 | Mitjana | Correcte | E2E i API |
| CP-US7-05 | Rebutjar un tipus de lliurament desconegut | Contracte T1 | Alta | Error | API |
| CP-US7-06 | Rebutjar domicili sense cap adreça disponible | Contracte T1 | Alta | Error | API |
| CP-US7-07 | Ignorar l'adreça en una recollida | Contracte T1 | Mitjana | Correcte | API |
| CP-US7-08 | Consultar els costos sense el rol requerit | Contracte T1 | Alta | Error | API |
| CP-US7-09 | Mantenir el cost acordat en una comanda existent | Contracte T1 | Mitjana | Correcte | API |

## Casos de prova

### CP-US7-01 · Lliurament a domicili mostra el cost abans de confirmar

- **Origen**: CA2.
- **Precondicions**: les generals; hi ha almenys un llibre disponible a la
  biblioteca seleccionada.
- **Passos**:
  1. Afegir el llibre a la comanda i seleccionar lliurament a domicili.
  2. Consultar el cost que mostra la interfície abans de confirmar.
  3. Confirmar la comanda.
- **Resultat esperat**:
  - Abans de confirmar, la interfície mostra el cost de domicili retornat per
    `GET /api/prestecs/comandes/cost-enviament/`.
  - El cost es mostra en euros i coincideix amb el valor configurat. Amb la
    configuració provisional del contracte, és `2.50` (2,50 €).
  - La comanda es crea amb `tipus_lliurament: "domicili"`, l'adreça de
    lliurament i aquest mateix `cost_enviament`.
- **Tipus**: correcte.
- **Automatització**: Playwright per verificar que el cost és visible abans de
  confirmar; API per verificar el tipus, l'adreça i el cost desats.

### CP-US7-02 · Recollida sense despeses d'enviament

- **Origen**: CA1.
- **Precondicions**: les generals.
- **Passos**:
  1. Afegir un llibre disponible a la comanda.
  2. Seleccionar recollida a la biblioteca.
  3. Comprovar el cost abans de confirmar i confirmar la comanda.
- **Resultat esperat**:
  - La interfície mostra `0.00` de despeses d'enviament abans de confirmar.
  - La comanda es crea amb `tipus_lliurament: "recollida"` i
    `cost_enviament: "0.00"`.
  - La recollida correspon a la biblioteca de la comanda; no es cobra cap
    despesa d'enviament.
- **Tipus**: correcte.
- **Automatització**: Playwright i API.

### CP-US7-03 · Fer servir l'adreça del perfil per al domicili

- **Origen**: contracte de T1.
- **Precondicions**: el perfil de l'usuari té una adreça definida.
- **Passos**: confirmar una comanda amb `tipus_lliurament: "domicili"` sense
  enviar `adreca_lliurament`.
- **Resultat esperat**:
  - La comanda es crea correctament.
  - `adreca_lliurament` conté l'adreça del perfil de l'usuari.
  - `cost_enviament` conté el cost de domicili configurat.
- **Tipus**: correcte.
- **Automatització**: API.

### CP-US7-04 · Substituir l'adreça del perfil per al domicili

- **Origen**: contracte de T1.
- **Precondicions**: les generals.
- **Passos**: confirmar una comanda a domicili enviant una adreça diferent de la
  del perfil.
- **Resultat esperat**:
  - La comanda es crea correctament.
  - `adreca_lliurament` conté l'adreça enviada a la petició.
  - `cost_enviament` conté el cost de domicili configurat.
- **Tipus**: correcte.
- **Automatització**: Playwright i API.

### CP-US7-05 · Rebutjar un tipus de lliurament desconegut

- **Origen**: contracte de T1.
- **Passos**: enviar una petició de confirmació amb `tipus_lliurament: "bustia"`.
- **Resultat esperat**:
  - La resposta és `400 Bad Request`.
  - El camp `tipus_lliurament` conté exactament
    `Tria lliurament a domicili o recollida a la biblioteca.`.
  - No es crea cap comanda.
- **Tipus**: error.
- **Automatització**: API.

### CP-US7-06 · Rebutjar domicili sense cap adreça disponible

- **Origen**: contracte de T1.
- **Precondicions**: el perfil de l'usuari no té adreça.
- **Passos**: enviar una petició amb `tipus_lliurament: "domicili"` sense
  `adreca_lliurament`, i repetir-la amb l'adreça buida.
- **Resultat esperat**:
  - En tots dos casos, la resposta és `400 Bad Request`.
  - El camp `adreca_lliurament` conté exactament
    `Indica l'adreça de lliurament.`.
  - No es crea cap comanda.
- **Tipus**: error.
- **Automatització**: API.

### CP-US7-07 · Ignorar l'adreça en una recollida

- **Origen**: contracte de T1.
- **Passos**: enviar una petició amb `tipus_lliurament: "recollida"` i una
  `adreca_lliurament` diferent de l'adreça del perfil.
- **Resultat esperat**:
  - La comanda es crea com a recollida a la biblioteca de la comanda.
  - `adreca_lliurament` és `""`; no s'utilitza l'adreça enviada.
  - `cost_enviament` és `"0.00"`.
- **Tipus**: correcte.
- **Automatització**: API.

### CP-US7-08 · Consultar els costos sense el rol requerit

- **Origen**: contracte de T1 i `docs/api-auth.md`.
- **Passos**:
  1. Consultar `GET /api/prestecs/comandes/cost-enviament/` sense token.
  2. Repetir la petició amb un usuari autenticat amb rol biblioteca i amb un
     usuari amb rol repartidor.
- **Resultat esperat**:
  - Sense token, la resposta és `401 Unauthorized`, amb el format definit a
    `docs/api-auth.md`.
  - Amb rol biblioteca o repartidor, la resposta és `403 Forbidden` amb el cos
    exacte `{"detail": "No té permisos per realitzar aquesta acció."}`.
  - No es retorna el cost a cap petició no autoritzada.
- **Tipus**: error.
- **Automatització**: API.

### CP-US7-09 · Mantenir el cost acordat en una comanda existent

- **Origen**: contracte de T1.
- **Precondicions**: s'ha creat una comanda a domicili amb el cost configurat
  inicialment.
- **Passos**:
  1. Canviar `COST_ENVIAMENT_DOMICILI` a un altre valor a l'entorn de prova.
  2. Consultar la comanda existent.
- **Resultat esperat**:
  - El cost de la comanda existent no canvia.
  - Les comandes noves fan servir el valor de cost actualitzat.
- **Tipus**: correcte.
- **Automatització**: API.

## Decisions i abast

- El cost a domicili de `2.50` euros és provisional i configurable amb
  `COST_ENVIAMENT_DOMICILI`, fins que el Product Owner decideixi si l'import és
  fix o depèn d'altres factors.
- La recollida es fa a la biblioteca que conté els llibres de la comanda i no
  té cost d'enviament, segons la decisió provisional del contracte de T1.
- El document comprova que el cost es mostra abans de confirmar i queda desat a
  la comanda. No valida l'import final del Product Owner si aquest canvia la
  decisió provisional.