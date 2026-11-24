# Casos de prova: adreces de lliurament (US3)

Casos de prova de la US3, elaborats a partir dels criteris d'acceptació de la
història. El contracte de l'API d'adreces encara no està disponible; els casos
no pressuposen camps, endpoints ni codis d'error que el Product Owner no hagi
confirmat. Serveixen de base per als tests de l'API i E2E. Qualsevol canvi
d'aquest document passa per pull request.

## Història i criteris d'acceptació

> **COM A** usuari registrat
> **VULL** poder gestionar les meves adreces de lliurament
> **PER AIXÍ** rebre els llibres on em vagi bé.

- **CA1**: l'usuari pot afegir una nova adreça de lliurament.
- **CA2**: l'usuari pot editar una adreça existent.
- **CA3**: l'usuari pot suprimir una adreça.
- **CA4**: l'usuari pot marcar una adreça com a predeterminada i només n'hi pot
  haver una alhora.
- **CA5**: si l'adreça introduïda és fora de la zona de servei, es mostra
  exactament l'avís `Aquesta adreça està fora de la zona de servei, introdueix
  una adreça vàlida`.

## Entorn i precondicions generals

- Aplicació disponible en un entorn de proves.
- Usuari registrat i autenticat a la pantalla "Les meves adreces".
- Les dades d'adreces de prova són sintètiques; no s'utilitzen domicilis reals.
- Abans d'executar els casos, el Product Owner ha de definir una adreça de
  prova dins de la zona de servei i una fora de la zona.
- Els camps de l'adreça, la manera de representar la zona de servei i els
  missatges diferents de l'avís de zona no estan especificats encara. No s'han
  d'inferir ni afegir expectatives fins que s'acordi el contracte.

## Dades de prova

| Dada | Valor |
|---|---|
| Usuari | Usuari registrat de prova |
| Adreça dins de servei A | Adreça sintètica que el Product Owner confirma dins de la zona |
| Adreça dins de servei B | Una altra adreça sintètica dins de la zona |
| Adreça fora de servei | Adreça sintètica que el Product Owner confirma fora de la zona |
| Camps i valors | Els acordats amb el Product Owner; pendents de concretar a la història |
| Adreça predeterminada inicial | Adreça A, quan el cas parteix d'una adreça ja desada |

Els valors concrets s'han de fixar abans de l'execució. No s'ha de deduir la
zona de servei a partir de codis postals, municipis o distàncies fins que el
Product Owner decideixi quin criteri s'aplica.

## Resum

| ID | Cas | Criteri d'acceptació | Prioritat | Tipus | Execució proposada |
|---|---|---|---|---|---|
| CP-US3-01 | Afegir una adreça dins de la zona de servei | CA1 | Alta | Correcte | E2E i API |
| CP-US3-02 | Editar una adreça existent | CA2 | Alta | Correcte | E2E i API |
| CP-US3-03 | Suprimir una adreça | CA3 | Alta | Correcte | E2E i API |
| CP-US3-04 | Marcar una adreça com a predeterminada | CA4 | Alta | Correcte | E2E i API |
| CP-US3-05 | En canviar la predeterminada, deixar-ne només una | CA4 | Alta | Correcte | API |
| CP-US3-06 | Mostrar l'avís per una adreça fora de la zona de servei | CA5 | Alta | Error | E2E i API |

## Casos de prova

### CP-US3-01 · Afegir una adreça dins de la zona de servei

- **Criteri d'acceptació**: CA1.
- **Precondicions**:
  - Les generals.
  - L'adreça de prova està confirmada com a dins de la zona de servei.
- **Passos**:
  1. Obrir "Les meves adreces".
  2. Seleccionar l'acció per afegir una adreça.
  3. Introduir els camps i valors acordats per a l'adreça de prova.
  4. Desar l'adreça.
- **Resultat esperat**:
  - L'adreça es desa i apareix a la llista de l'usuari.
  - Els valors mostrats coincideixen amb els introduïts, segons el format
    acordat.
  - No es mostra l'avís d'adreça fora de la zona de servei.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: comprovar el formulari i l'adreça desada visible.
  - pytest-django: comprovar la creació de l'adreça un cop definit el contracte
    de l'API.

### CP-US3-02 · Editar una adreça existent

- **Criteri d'acceptació**: CA2.
- **Precondicions**:
  - Les generals.
  - L'usuari té una adreça de prova desada.
- **Passos**:
  1. Obrir l'acció d'edició de l'adreça.
  2. Canviar un o més camps amb valors vàlids acordats.
  3. Desar els canvis.
- **Resultat esperat**:
  - L'adreça existent s'actualitza amb els valors nous.
  - No es crea una adreça duplicada.
  - La resta d'adreces de l'usuari es mantenen sense canvis.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: comprovar l'edició i la llista actualitzada.
  - pytest-django: comprovar l'actualització quan es defineixi el contracte.

### CP-US3-03 · Suprimir una adreça

- **Criteri d'acceptació**: CA3.
- **Precondicions**:
  - Les generals.
  - L'usuari té una adreça de prova desada.
- **Passos**:
  1. Seleccionar l'acció per suprimir l'adreça.
  2. Confirmar l'acció si la interfície demana confirmació.
- **Resultat esperat**:
  - L'adreça seleccionada deixa d'aparèixer a la llista de l'usuari.
  - Les altres adreces es mantenen sense canvis.
  - El comportament en suprimir l'adreça predeterminada s'ha de validar segons
    la decisió pendent del Product Owner; no se n'assumeix la permissió ni la
    substitució automàtica.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: comprovar que desapareix l'adreça seleccionada.
  - pytest-django: comprovar la supressió un cop definit el contracte de l'API.

### CP-US3-04 · Marcar una adreça com a predeterminada

- **Criteri d'acceptació**: CA4.
- **Precondicions**:
  - Les generals.
  - L'usuari té més d'una adreça desada i cap canvi concurrent durant la prova.
- **Passos**:
  1. Seleccionar una adreça no predeterminada.
  2. Marcar-la com a predeterminada.
  3. Tornar a consultar o actualitzar la llista.
- **Resultat esperat**:
  - L'adreça seleccionada queda marcada com a predeterminada.
  - La selecció es manté després de tornar a consultar la llista.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: comprovar la selecció a la llista.
  - pytest-django: comprovar la dada desada un cop definit el contracte.

### CP-US3-05 · En canviar la predeterminada, deixar-ne només una

- **Criteri d'acceptació**: CA4.
- **Precondicions**:
  - Les generals.
  - L'adreça A és la predeterminada i l'adreça B no ho és.
- **Passos**:
  1. Marcar l'adreça B com a predeterminada.
  2. Tornar a consultar totes les adreces.
- **Resultat esperat**:
  - L'adreça B és l'única marcada com a predeterminada.
  - L'adreça A deixa d'estar marcada com a predeterminada.
  - Cap altra adreça de l'usuari queda marcada com a predeterminada.
- **Tipus**: correcte.
- **Automatització**:
  - Playwright: comprovar l'indicador visible.
  - pytest-django: comprovar que hi ha exactament una adreça predeterminada per
    a l'usuari un cop definit el contracte de l'API.

### CP-US3-06 · Mostrar l'avís per una adreça fora de la zona de servei

- **Criteri d'acceptació**: CA5.
- **Precondicions**:
  - Les generals.
  - El Product Owner ha confirmat que l'adreça de prova és fora de la zona de
    servei.
- **Passos**:
  1. Afegir o editar una adreça introduint els valors de prova fora de zona.
  2. Intentar desar-la o validar-la segons el flux de la interfície.
- **Resultat esperat**:
  - Es mostra exactament l'avís:
    `Aquesta adreça està fora de la zona de servei, introdueix una adreça vàlida`
  - L'avís correspon a l'adreça introduïda.
  - El criteri no especifica si l'adreça fora de zona s'ha de desar o rebutjar;
    no s'ha d'assumir aquest resultat fins que el Product Owner el confirmi.
- **Tipus**: error.
- **Automatització**:
  - Playwright: comprovar el text exacte de l'avís.
  - pytest-django: comprovar la resposta i la persistència quan el contracte
    defineixi si la validació és a l'API i si la petició s'ha de rebutjar.

## Matriu de traçabilitat

| Criteri d'acceptació | Casos que el cobreixen | Cobertura |
|---|---|---|
| CA1: afegir una adreça | CP-US3-01 | Cobert |
| CA2: editar una adreça existent | CP-US3-02 | Cobert |
| CA3: suprimir una adreça | CP-US3-03 | Cobert; pendent la regla per a la predeterminada |
| CA4: marcar la predeterminada i mantenir-ne només una | CP-US3-04, CP-US3-05 | Cobert |
| CA5: avisar si és fora de la zona de servei | CP-US3-06 | Cobert; pendent la definició de zona i persistència |

## Decisions i abast

- Els camps de l'adreça encara s'han d'acordar amb el Product Owner. Els casos
  fan servir valors vàlids acordats en lloc d'inventar camps obligatoris o
  formats.
- La zona de servei encara no està definida; el Product Owner ha de decidir si
  depèn de codis postals, municipis o distància a les biblioteques.
- Encara cal confirmar si es pot suprimir l'adreça predeterminada i si, en fer-ho,
  cal triar-ne una altra.
- L'issue no defineix el comportament de persistència per a una adreça fora de
  la zona ni cap missatge d'error addicional. Aquest document només exigeix
  l'avís literal especificat.
- Els codis d'estat, endpoints, errors de camps i requisits d'autenticació de
  l'API es concretaran a US3-T6 abans d'afegir expectatives específiques de
  l'API.
