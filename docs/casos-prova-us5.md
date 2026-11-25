# Casos de prova: biblioteques amb un llibre en estoc (US5)

Casos de prova de la US5, elaborats a partir dels criteris d'acceptació de la
història. El contracte de l'API (US5-T7) encara no està disponible; els casos
no pressuposen camps, endpoints ni missatges que no estiguin especificats.
Serveixen de base per als tests de l'API i E2E. Qualsevol canvi d'aquest
document passa per pull request.

## Història i criteris d'acceptació

> **COM A** usuari
> **VULL** saber quines biblioteques tenen el llibre en estoc
> **PER AIXÍ** saber si me'l podran portar aviat.

- **CA1**: es mostra la llista de biblioteques que tenen el llibre disponible.
- **CA2**: si l'usuari està registrat, les biblioteques apareixen ordenades per
  distància a l'adreça predeterminada de l'usuari.
- **CA3**: si cap biblioteca té el llibre en estoc, es mostra exactament:
  `Cap biblioteca te aquest llibre en estoc`.
- **CA4**: si l'usuari no té cap adreça predeterminada, se li demana que n'afegeixi
  una amb el missatge exacte `Afegeix una adreça per continuar`.
- **CA5**: si l'usuari no està registrat, les biblioteques no s'ordenen per
  distància i es mostra exactament:
  `Registrat per ordenar les biblioteques per distància`.
- **CA6**: si el llibre no té estoc a cap biblioteca o una biblioteca és fora
  de la zona de repartiment, s'ofereix l'opció d'apuntar-se a la llista
  d'espera del llibre.

## Entorn i precondicions generals

- Aplicació disponible en un entorn de proves.
- Hi ha dades de prova de llibres i biblioteques amb estoc controlable.
- Per provar distàncies, les dades de prova proporcionen una adreça
  predeterminada i ubicacions de biblioteques amb distàncies conegudes segons
  el mecanisme que defineixi el contracte.
- L'adreça, les ubicacions, els llibres i els comptes són dades sintètiques;
  no s'utilitzen dades personals reals.
- L'usuari registrat està autenticat quan el cas ho requereix; els casos de
  convidat s'executen sense sessió.
- La zona de repartiment i la manera de calcular les distàncies han d'estar
  definides per l'entorn de prova. No s'assumeix geocodificació, distància per
  carretera ni distància en línia recta mentre no ho decideixi el Product
  Owner.
- El contracte de l'API de la US5 encara està pendent; els casos descriuen els
  resultats visibles i deixen per al contracte els detalls de petició,
  resposta i persistència de la llista d'espera.

## Dades de prova

| Dada | Valor |
|---|---|
| Usuari registrat A | Usuari actiu amb adreça predeterminada de prova |
| Usuari registrat B | Usuari actiu sense adreça predeterminada |
| Convidat | Navegador sense sessió iniciada |
| Llibre amb estoc | Llibre de prova amb exemplars disponibles en més d'una biblioteca |
| Biblioteca propera | Biblioteca amb estoc i distància menor a l'adreça d'A |
| Biblioteca llunyana | Biblioteca amb estoc i distància major a l'adreça d'A |
| Biblioteca sense estoc | Biblioteca que té el llibre al catàleg però cap exemplar disponible |
| Llibre sense estoc | Llibre sense exemplars disponibles a cap biblioteca |
| Biblioteca fora de zona | Biblioteca amb el llibre disponible, però fora de la zona de repartiment de l'adreça provada |

Els valors exactes s'han de fixar a la preparació de l'entorn segons el
contracte de l'API i la decisió del Product Owner sobre distàncies i zona de
servei. No s'especifiquen valors d'estoc, camps de resposta ni textos de botons
que no apareguin als criteris.

## Resum

| ID | Cas | Criteri d'acceptació | Prioritat | Tipus | Execució proposada |
|---|---|---|---|---|---|
| CP-US5-01 | Mostrar les biblioteques que tenen el llibre disponible | CA1 | Alta | Correcte | E2E i API |
| CP-US5-02 | Ordenar les biblioteques per distància de l'adreça predeterminada | CA2 | Alta | Correcte | E2E i API |
| CP-US5-03 | Mostrar el missatge i la llista d'espera quan cap biblioteca té estoc | CA3, CA6 | Alta | Correcte / sense estoc | E2E i API |
| CP-US5-04 | Demanar una adreça predeterminada si l'usuari no en té | CA4 | Alta | Correcte | E2E |
| CP-US5-05 | Mostrar les biblioteques sense ordre per distància a un convidat | CA5 | Alta | Correcte | E2E |
| CP-US5-06 | Oferir la llista d'espera per a una biblioteca fora de la zona | CA6 | Alta | Correcte / fora de zona | E2E i API |

## Casos de prova

### CP-US5-01 · Mostrar les biblioteques que tenen el llibre disponible

- **Criteri d'acceptació**: CA1.
- **Precondicions**:
  - Les generals.
  - El llibre està disponible en dues biblioteques i no té exemplars disponibles
    en una tercera.
- **Passos**:
  1. Obrir el detall del llibre.
  2. Consultar la llista de biblioteques que l'ofereixen.
- **Resultat esperat**:
  - Es mostren les biblioteques que tenen almenys un exemplar disponible del
    llibre.
  - No es mostra com a disponible la biblioteca que té zero exemplars.
  - Cada biblioteca mostrada correspon al llibre consultat.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: comprovar la llista visible.
  - pytest-django: comprovar les biblioteques retornades per l'API quan el
    contracte estigui disponible.

### CP-US5-02 · Ordenar les biblioteques per distància de l'adreça predeterminada

- **Criteri d'acceptació**: CA2.
- **Precondicions**:
  - Les generals.
  - L'usuari registrat A té una adreça predeterminada.
  - El llibre té estoc en dues o més biblioteques amb distàncies de prova
    diferents.
- **Passos**:
  1. Iniciar sessió com a usuari A.
  2. Obrir el detall del llibre.
  3. Comparar l'ordre de les biblioteques amb les distàncies conegudes a
     l'adreça predeterminada.
- **Resultat esperat**:
  - Les biblioteques apareixen de la més propera a la més llunyana respecte de
    l'adreça predeterminada.
  - Les biblioteques sense estoc no apareixen a la llista de disponibles.
- **Tipus**: correcte.
- **Automatització**:
  - pytest-django: comprovar l'ordre amb les ubicacions de prova un cop definit
    el contracte de distància.
  - Playwright: comprovar l'ordre visible.
- **Abast pendent**: no es fixa com es calcula la distància (en línia recta,
  per carretera o altra regla) fins que ho decideixi el Product Owner.

### CP-US5-03 · Mostrar el missatge i la llista d'espera quan cap biblioteca té estoc

- **Criteris d'acceptació**: CA3 i CA6.
- **Precondicions**:
  - Les generals.
  - El llibre no té cap exemplar disponible a cap biblioteca.
- **Passos**: obrir el detall del llibre.
- **Resultat esperat**:
  - La llista de biblioteques disponibles és buida.
  - Es mostra exactament el missatge:
    `Cap biblioteca te aquest llibre en estoc`
  - S'ofereix l'opció d'apuntar-se a la llista d'espera d'aquest llibre.
  - En activar l'opció amb un usuari registrat, s'inicia el flux per apuntar-se
    a la llista d'espera. El resultat de persistència i els errors es validaran
    segons el contracte de l'API US5-T7.
- **Tipus**: correcte / sense estoc.
- **Automatització**:
  - Playwright: comprovar el missatge exacte i l'opció visible.
  - pytest-django: comprovar el resultat de disponibilitat i el flux de llista
    d'espera quan el contracte estigui disponible.

### CP-US5-04 · Demanar una adreça predeterminada si l'usuari no en té

- **Criteri d'acceptació**: CA4.
- **Precondicions**:
  - Les generals.
  - L'usuari registrat B no té cap adreça predeterminada.
- **Passos**:
  1. Iniciar sessió com a usuari B.
  2. Obrir el detall d'un llibre disponible en una o més biblioteques.
- **Resultat esperat**:
  - Es mostra exactament el missatge:
    `Afegeix una adreça per continuar`
  - No es presenta l'ordre com si estigués calculat a partir d'una adreça
    predeterminada inexistent.
  - El cas no exigeix una ruta concreta per afegir l'adreça, perquè aquesta no
    està definida als criteris.
- **Tipus**: correcte.
- **Automatització**: Playwright.

### CP-US5-05 · Mostrar les biblioteques sense ordre per distància a un convidat

- **Criteri d'acceptació**: CA5.
- **Precondicions**:
  - Les generals.
  - El llibre està disponible en dues o més biblioteques.
  - No hi ha cap usuari autenticat.
- **Passos**:
  1. Obrir el detall del llibre com a convidat.
  2. Revisar la llista de biblioteques i el missatge.
- **Resultat esperat**:
  - Es mostren les biblioteques que tenen el llibre disponible.
  - La llista no es presenta com a ordenada per distància de l'usuari.
  - Es mostra exactament el missatge:
    `Registrat per ordenar les biblioteques per distància`
- **Tipus**: correcte.
- **Automatització**: Playwright; API si el contracte defineix el comportament
  públic de la llista.

### CP-US5-06 · Oferir la llista d'espera per a una biblioteca fora de la zona

- **Criteri d'acceptació**: CA6.
- **Precondicions**:
  - Les generals.
  - El llibre té estoc a la biblioteca de prova, però aquesta biblioteca està
    confirmada com a fora de la zona de repartiment de l'usuari.
- **Passos**:
  1. Iniciar sessió amb un usuari registrat.
  2. Obrir el detall del llibre.
  3. Localitzar la biblioteca fora de zona i l'acció de llista d'espera que li
     correspon.
- **Resultat esperat**:
  - La biblioteca es reconeix com a fora de la zona de repartiment per a aquest
    usuari.
  - S'ofereix l'opció d'apuntar-se a la llista d'espera del llibre.
  - El fet que hi hagi estoc a aquesta biblioteca no elimina l'opció exigida
    per al cas de zona fora de servei.
  - El contracte de l'API ha de concretar si la biblioteca fora de zona es
    mostra en una llista separada o amb un altre indicador; aquest cas no
    pressuposa cap representació concreta.
- **Tipus**: correcte / fora de zona.
- **Automatització**:
  - Playwright: comprovar que s'ofereix l'acció de llista d'espera.
  - pytest-django: comprovar la resposta i la regla de zona quan el contracte
    estigui disponible.

## Matriu de traçabilitat

| Criteri d'acceptació | Casos que el cobreixen | Cobertura |
|---|---|---|
| CA1: llistar biblioteques amb el llibre disponible | CP-US5-01, CP-US5-05 | Cobert |
| CA2: ordenar per distància a l'adreça predeterminada | CP-US5-02 | Cobert |
| CA3: missatge quan cap biblioteca té estoc | CP-US5-03 | Cobert |
| CA4: demanar adreça predeterminada | CP-US5-04 | Cobert |
| CA5: convidat sense ordre per distància i missatge de registre | CP-US5-05 | Cobert |
| CA6: oferir llista d'espera sense estoc o fora de zona | CP-US5-03, CP-US5-06 | Parcial; CP-US5-06 pendent |

## Decisions i abast

- La manera de geocodificar les adreces i ubicacions de biblioteques, i si la
  distància és en línia recta o per carretera, encara són decisions pendents
  del Product Owner. Els casos exigeixen l'ordre correcte segons el mecanisme
  que s'acordi, però no n'inventen un.
- La definició concreta de zona de repartiment s'ha de confirmar i preparar a
  les dades de prova abans d'executar els casos de zona fora de servei.
- L'endpoint, el format de la resposta, els textos de l'acció d'espera, els
  errors i la persistència de la subscripció s'han de concretar a US5-T7.
- L'issue de l'endpoint de llista d'espera limita aquesta funció a usuaris
  registrats. Els criteris no especifiquen què ha de fer un convidat quan veu
  l'opció d'espera; cal confirmar si se li demana iniciar sessió o registrar-se.
- El criteri no defineix si una biblioteca fora de zona es treu de la llista
  d'estoc o s'hi mostra amb una indicació. El cas només exigeix que es pugui
  reconèixer com a fora de zona i que s'ofereixi la llista d'espera.
- A US5-T9 s'ha decidit mostrar l'opció de llista d'espera quan el llibre no té
  estoc. El cas de biblioteca fora de zona queda pendent fins que se'n defineixi
  la regla i l'API retorni aquesta informació; no s'ha d'inferir a partir de la
  distància ni del codi postal de l'usuari.
