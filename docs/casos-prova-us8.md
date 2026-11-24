# Casos de prova: estat i notificacions de la comanda (US8)

Casos de prova de la US8, elaborats a partir dels criteris d'acceptació de la
història i dels endpoints de `docs/api-comandes.md` (US8-T3). Serveixen de base
per als tests de l'API i E2E. Qualsevol canvi d'aquest document passa per pull
request.

## Història i criteris d'acceptació

> **COM A** usuari registrat
> **VULL** saber l'estat de la meva comanda
> **PER AIXÍ** saber quan m'arribarà.

- **CA1**: els estats de la comanda són `rebuda`, `preparada`, `en camí` i
  `lliurada`.
- **CA2**: cada canvi d'estat genera una notificació.
- **CA3**: en rebre la comanda, es notifica exactament:
  `La teva comanda s'ha rebut correctament. La biblioteca ja l'està preparant`
- **CA4**: en passar de `rebuda` a `preparada`, es notifica exactament:
  `La teva comanda ja està preparada i aviat sortirà cap a casa teva`
- **CA5**: en passar de `preparada` a `en camí`, es notifica exactament:
  `En/Na {nom_repartidor(a)} ja porta la teva comanda. Està en camí!`
- **CA6**: en passar de `en camí` a `lliurada`, es notifica exactament:
  `La teva comanda s'ha lliurat correctament. Gaudeix del teu llibre!`

## Entorn i precondicions generals

- Aplicació disponible en un entorn de proves amb la base de dades migrada.
- Backend, frontend i PostgreSQL disponibles. Per executar-los en local, seguir
  les instruccions de configuració i `docker compose up -d --wait` del README.
- Usuari A de prova amb rol `usuari`, autenticat amb un token d'accés vàlid.
- Usuari B de prova diferent d'A, per comprovar que les dades són privades.
- Biblioteca activa de prova i repartidor de prova.
- Comandes i comptes de prova amb dades sintètiques; no s'utilitzen dades
  personals reals.
- L'usuari consulta les comandes a `GET /api/prestecs/comandes/` i les
  notificacions a `GET /api/prestecs/notificacions/`. Les notificacions del
  contracte inclouen `text`, `llegida` i `comanda`.
- Les transicions es provoquen mitjançant les accions disponibles per a cada
  rol en el flux de la biblioteca o del repartidor. No s'assumeix una ruta
  d'API de transició que no estigui especificada al contracte corresponent.

## Dades de prova

| Dada | Valor |
|---|---|
| Usuari A | Usuari actiu de prova amb rol `usuari` |
| Usuari B | Un altre usuari actiu, sense cap relació amb la comanda d'A |
| Biblioteca | Biblioteca activa de prova |
| Repartidor | Repartidor actiu de prova amb nom visible `Jordi` |
| Comanda | Comanda de prova d'A, inicialment en estat `rebuda` |
| Comanda per a transicions prohibides | Comanda de prova en cadascun dels estats previs a una transició invàlida |

El missatge del repartidor substitueix `{nom_repartidor(a)}` pel nom visible
del repartidor. Per a les dades d'aquesta taula, el text esperat és:
`En/Na Jordi ja porta la teva comanda. Està en camí!`

## Resum

| ID | Cas | Criteri / contracte | Prioritat | Tipus | Execució proposada |
|---|---|---|---|---|---|
| CP-US8-01 | Crear la notificació inicial en rebre una comanda | CA1, CA2, CA3 | Alta | Correcte | API i E2E |
| CP-US8-02 | Notificar el canvi de `rebuda` a `preparada` | CA1, CA2, CA4 | Alta | Correcte | API i E2E |
| CP-US8-03 | Notificar el canvi de `preparada` a `en camí` amb el nom del repartidor | CA1, CA2, CA5 | Alta | Correcte | API i E2E |
| CP-US8-04 | Notificar el canvi de `en camí` a `lliurada` | CA1, CA2, CA6 | Alta | Correcte | API i E2E |
| CP-US8-05 | Verificar el recorregut complet i una notificació per canvi | CA1, CA2 | Alta | Correcte | API |
| CP-US8-06 | Rebutjar transicions no permeses sense notificar-les | CA1, CA2, contracte T1 | Alta | Error | API |
| CP-US8-07 | No mostrar comandes ni notificacions d'un altre usuari | Contracte T3 | Alta | Error | API |
| CP-US8-08 | Rebutjar la consulta sense autenticació | Contracte T3 | Alta | Error | API |

## Casos de prova

### CP-US8-01 · Crear la notificació inicial en rebre una comanda

- **Criteris d'acceptació**: CA1, CA2 i CA3.
- **Precondicions**:
  - Les generals.
  - L'usuari A encara no té cap comanda de prova ni cap notificació associada.
- **Passos**:
  1. Confirmar una comanda amb l'usuari A.
  2. Consultar les comandes de l'usuari A.
  3. Consultar les notificacions de l'usuari A.
- **Resultat esperat**:
  - La comanda queda en estat `rebuda`.
  - Es crea una notificació associada a aquesta comanda i a l'usuari A.
  - El text de la notificació és exactament:
    `La teva comanda s'ha rebut correctament. La biblioteca ja l'està preparant`
  - La notificació apareix com a no llegida.
- **Tipus**: correcte.
- **Automatització**:
  - pytest-django: comprovar estat, text, comanda associada i estat de lectura.
  - Playwright: comprovar l'estat i el text visibles per a l'usuari.

### CP-US8-02 · Notificar el canvi de `rebuda` a `preparada`

- **Criteris d'acceptació**: CA1, CA2 i CA4.
- **Precondicions**:
  - Les generals.
  - L'usuari A té una comanda en estat `rebuda`.
- **Passos**:
  1. Fer que la biblioteca marqui la comanda com a preparada.
  2. Consultar les comandes i notificacions de l'usuari A.
- **Resultat esperat**:
  - La comanda passa a `preparada`.
  - Es crea exactament una notificació nova per a aquest canvi.
  - El text de la notificació nova és exactament:
    `La teva comanda ja està preparada i aviat sortirà cap a casa teva`
  - La notificació correspon a la comanda de prova i apareix com a no llegida.
- **Tipus**: correcte.
- **Automatització**:
  - pytest-django: comprovar transició i notificació.
  - Playwright: comprovar el text que veu l'usuari.

### CP-US8-03 · Notificar el canvi de `preparada` a `en camí` amb el nom del repartidor

- **Criteris d'acceptació**: CA1, CA2 i CA5.
- **Precondicions**:
  - Les generals.
  - L'usuari A té una comanda en estat `preparada`.
  - Hi ha un repartidor assignat amb el nom visible indicat a les dades de prova.
- **Passos**:
  1. Fer que el repartidor reculli la comanda i la marqui com a `en camí`.
  2. Consultar l'estat de la comanda i les notificacions de l'usuari A.
- **Resultat esperat**:
  - La comanda passa a `en_cami` a l'API (text visible: `en camí`).
  - Es crea exactament una notificació nova associada a aquesta comanda.
  - Per al repartidor de prova, el text és exactament:
    `En/Na Jordi ja porta la teva comanda. Està en camí!`
  - El nom visible del repartidor substitueix el marcador; no es mostra
    literalment `{nom_repartidor(a)}`.
- **Tipus**: correcte.
- **Automatització**:
  - pytest-django: comprovar estat, nom i text literal.
  - Playwright: comprovar el text visible per a l'usuari.

### CP-US8-04 · Notificar el canvi de `en camí` a `lliurada`

- **Criteris d'acceptació**: CA1, CA2 i CA6.
- **Precondicions**:
  - Les generals.
  - L'usuari A té una comanda en estat `en_cami`.
- **Passos**:
  1. Fer que el repartidor marqui la comanda com a lliurada.
  2. Consultar les comandes i notificacions de l'usuari A.
- **Resultat esperat**:
  - La comanda passa a `lliurada`.
  - Es crea exactament una notificació nova associada a aquesta comanda.
  - El text és exactament:
    `La teva comanda s'ha lliurat correctament. Gaudeix del teu llibre!`
  - La notificació apareix com a no llegida.
- **Tipus**: correcte.
- **Automatització**:
  - pytest-django: comprovar transició i notificació.
  - Playwright: comprovar l'estat i el text visibles.

### CP-US8-05 · Verificar el recorregut complet i una notificació per canvi

- **Criteris d'acceptació**: CA1 i CA2.
- **Precondicions**: les generals i una comanda de prova en estat inicial.
- **Passos**:
  1. Crear la comanda i verificar `rebuda`.
  2. Fer les transicions vàlides, en ordre: `rebuda` → `preparada` →
     `en_cami` → `lliurada`.
  3. Consultar l'estat final de la comanda i totes les notificacions associades.
- **Resultat esperat**:
  - La comanda segueix els quatre estats en l'ordre indicat i acaba en
    `lliurada`.
  - Hi ha exactament una notificació per a cadascun dels quatre esdeveniments:
    recepció (`rebuda`) i els tres canvis d'estat posteriors.
  - Els quatre textos coincideixen exactament amb CP-US8-01 a CP-US8-04,
    incloent-hi el nom del repartidor al missatge d'`en_cami`.
  - No es crea cap notificació duplicada per una mateixa transició.
- **Tipus**: correcte.
- **Automatització**: pytest-django; l'E2E pot comprovar el recorregut visible.

### CP-US8-06 · Rebutjar transicions no permeses sense notificar-les

- **Criteris d'acceptació**: CA1 i CA2; transicions permeses del contracte T1.
- **Precondicions**:
  - Les generals.
  - Comandes de prova en estats dels quals es pugui provar una transició no
    permesa, com ara `rebuda` → `lliurada` o `lliurada` → `preparada`.
- **Passos**:
  1. Intentar cada transició no permesa.
  2. Tornar a consultar l'estat de la comanda i les notificacions associades.
- **Resultat esperat**:
  - La transició és rebutjada i l'estat de la comanda no canvia.
  - No es crea cap notificació per a la transició rebutjada.
  - El codi i el missatge concrets de l'error es comproven segons el contracte
    de l'acció que ha intentat fer la transició; els criteris de la US8 no
    defineixen un missatge literal per a aquest error.
- **Tipus**: error.
- **Automatització**: pytest-django.

### CP-US8-07 · No mostrar comandes ni notificacions d'un altre usuari

- **Origen**: contracte T3 dels endpoints de les comandes i notificacions de
  l'usuari.
- **Precondicions**: els usuaris A i B tenen comandes i notificacions diferents.
- **Passos**:
  1. Autenticar-se com a usuari A i consultar les comandes i notificacions.
  2. Repetir les consultes com a usuari B.
- **Resultat esperat**:
  - Cada usuari només veu les seves pròpies comandes i notificacions.
  - Cap notificació no revela el text, l'estat ni l'identificador de la comanda
    d'un altre usuari.
- **Tipus**: error / permisos.
- **Automatització**: pytest-django.

### CP-US8-08 · Rebutjar la consulta sense autenticació

- **Origen**: contractes T3 i `docs/api-auth.md`.
- **Passos**:
  1. Consultar `GET /api/prestecs/comandes/` sense capçalera
     `Authorization`.
  2. Repetir-ho amb `GET /api/prestecs/notificacions/`.
  3. Repetir amb un token invàlid o caducat.
- **Resultat esperat**:
  - Cada petició retorna `401 Unauthorized`.
  - El cos segueix el format d'error definit a `docs/api-auth.md`.
  - No es retorna cap comanda ni notificació.
- **Tipus**: error.
- **Automatització**: pytest-django.

## Matriu de traçabilitat

| Criteri d'acceptació | Casos que el cobreixen | Cobertura |
|---|---|---|
| CA1: estats de la comanda | CP-US8-01 a CP-US8-06 | Cobert |
| CA2: cada canvi d'estat genera una notificació | CP-US8-01 a CP-US8-05 | Cobert |
| CA3: missatge en rebre la comanda | CP-US8-01, CP-US8-05 | Cobert |
| CA4: missatge de `rebuda` a `preparada` | CP-US8-02, CP-US8-05 | Cobert |
| CA5: missatge de `preparada` a `en camí`, amb el nom del repartidor | CP-US8-03, CP-US8-05 | Cobert |
| CA6: missatge de `en camí` a `lliurada` | CP-US8-04, CP-US8-05 | Cobert |

## Decisions i abast

- Els missatges d'aquest document són literals dels criteris d'acceptació.
  S'han de comprovar exactament, sense canviar accents, apòstrofs, puntuació ni
  espais.
- El marcador `{nom_repartidor(a)}` s'ha de substituir pel nom visible del
  repartidor; per a la dada de prova d'aquest document, el text comença
  `En/Na Jordi`.
- La comanda cancel·lada és fora dels quatre estats d'aquesta història i es
  tracta a US20.
- El Product Owner encara ha de confirmar si la notificació és dins de
  l'aplicació, per correu o totes dues, i si cal adaptar el missatge quan la
  comanda és per recollir a la biblioteca. Fins que es confirmi, els casos
  comproven els missatges literals indicats als criteris de la US8.
