# Casos de prova: inici de sessió (US2)

Casos de prova de la US2 (tasca US2-T14), elaborats a partir dels criteris d'acceptació de la història d'inici de sessió.
Qualsevol canvi d'aquest document passa per pull request.

## Història i criteris d'acceptació

> **COM A** usuari registrat  
> **VULL** poder iniciar sessió al meu compte amb les meves credencials  
> **PER AIXÍ** poder fer les gestions pertinents al meu rol.

- **CA1**: l'usuari pot iniciar sessió introduint credencials vàlides: correu electrònic o nom d'usuari i contrasenya.
- **CA2**: si el correu, nom d'usuari o contrasenya són incorrectes, es mostra un missatge d'error clar sense indicar quin camp ha fallat.
- **CA3**: els camps de credencials són obligatoris i no es pot enviar el formulari si algun és buit.
- **CA4**: la contrasenya es mostra emmascarada per defecte i es pot mostrar o ocultar.
- **CA5**: si l'inici de sessió és correcte, es genera un JWT vàlid i s'emmagatzema de manera segura per autenticar peticions posteriors.
- **CA6**: si l'usuari clica fora de la capsa d'inici de sessió o a la creu, aquesta es tanca.

## Qüestions pendents

- El model actual d'usuari utilitza el correu electrònic i no té un nom d'usuari separat. Cal confirmar si l'inici de sessió es farà només amb el correu.
- No s'ha definit la ruta o el resultat de navegació després de l'inici de sessió.
- No s'ha especificat el mecanisme concret d'emmagatzematge segur del JWT.
- No s'ha especificat el missatge concret per a comptes pendents de validació o no verificats.

## Entorn i precondicions generals

- Aplicació disponible en l'entorn de proves.
- Base de dades migrada.
- Usuari registrat amb credencials vàlides.
- Navegador sense una sessió iniciada.
- Mida d'escriptori: 1280 × 720.
- Per comprovar el JWT i les peticions posteriors, obrir les eines de desenvolupador abans d'iniciar sessió.
- La ruta i els textos exactes de la capsa depenen de la implementació de la US2.

## Dades de prova

| Dada | Valor |
|---|---|
| Correu electrònic vàlid | `anna.puig@example.com` |
| Contrasenya vàlida | `Llibres-de-tardor-24` |
| Correu electrònic inexistent | `inexistent@example.com` |
| Contrasenya incorrecta | `Contrasenya-incorrecta-99` |

## Resum

| ID | Cas | Criteri | Prioritat | Execució proposada |
|---|---|---|---|---|
| CP-US2-01 | Inici de sessió amb credencials vàlides | CA1 | Alta | E2E i manual |
| CP-US2-02 | Inici de sessió amb correu o usuari inexistent | CA2 | Alta | E2E i manual |
| CP-US2-03 | Inici de sessió amb contrasenya incorrecta | CA2 | Alta | E2E i manual |
| CP-US2-04 | Correu o nom d'usuari buit | CA3 | Alta | E2E i manual |
| CP-US2-05 | Contrasenya buida | CA3 | Alta | E2E i manual |
| CP-US2-06 | Tots els camps buits | CA3 | Mitjana | E2E |
| CP-US2-07 | Contrasenya emmascarada per defecte | CA4 | Alta | E2E i manual |
| CP-US2-08 | Mostrar i ocultar la contrasenya | CA4 | Alta | E2E i manual |
| CP-US2-09 | Generació i emmagatzematge del JWT | CA5 | Alta | E2E i inspecció controlada |
| CP-US2-10 | Tancar clicant fora de la capsa | CA6 | Alta | E2E i manual |
| CP-US2-11 | Tancar amb la creu | CA6 | Alta | E2E i manual |

## Casos de prova

### CP-US2-01 · Inici de sessió amb credencials vàlides

- **Origen**: CA1.
- **Precondicions**: existeix un usuari registrat i autoritzat.
- **Dades**:
  - Correu electrònic: `anna.puig@example.com`.
  - Contrasenya: `Llibres-de-tardor-24`.
- **Passos**:
  1. Obrir la capsa d'inici de sessió.
  2. Introduir el correu electrònic o nom d'usuari vàlid.
  3. Introduir la contrasenya vàlida.
  4. Enviar el formulari.
- **Resultat esperat**:
  - L'inici de sessió es completa correctament.
  - No es mostra cap missatge d'error.
  - Es genera un JWT vàlid.
  - El token queda emmagatzemat segons el mecanisme definit pel projecte.
  - Les peticions posteriors que requereixen autenticació poden utilitzar la sessió iniciada.

### CP-US2-02 · Inici de sessió amb correu o nom d'usuari inexistent

- **Origen**: CA2.
- **Precondicions**: no existeix cap compte amb la credencial introduïda.
- **Dades**:
  - Correu o nom d'usuari: `inexistent@example.com`.
  - Contrasenya: `Llibres-de-tardor-24`.
- **Passos**:
  1. Obrir la capsa d'inici de sessió.
  2. Introduir el correu o nom d'usuari inexistent.
  3. Introduir una contrasenya.
  4. Enviar el formulari.
- **Resultat esperat**:
  - L'inici de sessió falla.
  - Es mostra un missatge d'error clar.
  - El missatge no indica si ha fallat el correu, el nom d'usuari o la contrasenya.
  - No es genera ni s'emmagatzema cap JWT.
  - La capsa continua oberta.

### CP-US2-03 · Inici de sessió amb contrasenya incorrecta

- **Origen**: CA2.
- **Precondicions**: existeix el compte amb el correu o nom d'usuari introduït.
- **Dades**:
  - Correu electrònic: `anna.puig@example.com`.
  - Contrasenya: `Contrasenya-incorrecta-99`.
- **Passos**:
  1. Obrir la capsa d'inici de sessió.
  2. Introduir el correu o nom d'usuari vàlid.
  3. Introduir la contrasenya incorrecta.
  4. Enviar el formulari.
- **Resultat esperat**:
  - L'inici de sessió falla.
  - Es mostra un missatge d'error clar.
  - El missatge no indica que ha fallat la contrasenya.
  - El missatge és equivalent al del cas CP-US2-02.
  - No es genera ni s'emmagatzema cap JWT.
  - La capsa continua oberta.

### CP-US2-04 · Correu o nom d'usuari buit

- **Origen**: CA3.
- **Passos**:
  1. Obrir la capsa d'inici de sessió.
  2. Deixar buit el camp del correu o nom d'usuari.
  3. Introduir una contrasenya.
  4. Intentar enviar el formulari.
- **Resultat esperat**:
  - El formulari no s'envia.
  - Es mostra un missatge que indica que el camp és obligatori.
  - No es fa cap petició d'inici de sessió.
  - No es genera cap JWT.
  - La capsa continua oberta.

### CP-US2-05 · Contrasenya buida

- **Origen**: CA3.
- **Passos**:
  1. Obrir la capsa d'inici de sessió.
  2. Introduir un correu o nom d'usuari.
  3. Deixar buida la contrasenya.
  4. Intentar enviar el formulari.
- **Resultat esperat**:
  - El formulari no s'envia.
  - Es mostra un missatge que indica que la contrasenya és obligatòria.
  - No es fa cap petició d'inici de sessió.
  - No es genera cap JWT.
  - La capsa continua oberta.

### CP-US2-06 · Tots els camps buits

- **Origen**: CA3.
- **Passos**:
  1. Obrir la capsa d'inici de sessió.
  2. Deixar buits tots els camps de credencials.
  3. Intentar enviar el formulari.
- **Resultat esperat**:
  - El formulari no s'envia.
  - Es mostra un missatge d'obligatorietat per a cada camp.
  - No es fa cap petició d'inici de sessió.
  - No es genera cap JWT.
  - La capsa continua oberta.

### CP-US2-07 · Contrasenya emmascarada per defecte

- **Origen**: CA4.
- **Passos**:
  1. Obrir la capsa d'inici de sessió.
  2. Localitzar el camp de contrasenya.
  3. Introduir una contrasenya.
- **Resultat esperat**:
  - El camp de contrasenya està emmascarat per defecte.
  - El valor introduït no es mostra en text pla.
  - Existeix una opció per mostrar la contrasenya, si està implementada.

### CP-US2-08 · Mostrar i ocultar la contrasenya

- **Origen**: CA4.
- **Passos**:
  1. Obrir la capsa d'inici de sessió.
  2. Introduir una contrasenya.
  3. Activar l'opció per mostrar-la.
  4. Tornar a activar l'opció per ocultar-la.
- **Resultat esperat**:
  - En mostrar-la, la contrasenya es veu en text pla.
  - En ocultar-la, torna a estar emmascarada.
  - El valor de la contrasenya no canvia.
  - L'opció permet saber si la contrasenya està visible o oculta.

### CP-US2-09 · Generació i emmagatzematge del JWT

- **Origen**: CA5.
- **Precondicions**: existeix un usuari registrat i autoritzat.
- **Dades**:
  - Correu electrònic: `anna.puig@example.com`.
  - Contrasenya: `Llibres-de-tardor-24`.
- **Passos**:
  1. Obrir la capsa d'inici de sessió.
  2. Introduir credencials vàlides.
  3. Enviar el formulari.
  4. Comprovar la resposta de l'operació d'inici de sessió.
  5. Fer una petició posterior que requereixi autenticació.
- **Resultat esperat**:
  - Es genera un JWT vàlid.
  - El token s'emmagatzema segons el mecanisme segur definit pel projecte.
  - La petició posterior inclou el token correctament.
  - La petició autenticada és acceptada.
  - El token no es mostra en textos visibles de la interfície ni en logs.

### CP-US2-10 · Tancar clicant fora de la capsa

- **Origen**: CA6.
- **Passos**:
  1. Obrir la capsa d'inici de sessió.
  2. Fer clic en una zona buida de dins de la capsa.
  3. Comprovar que la capsa continua oberta.
  4. Fer clic al fons, fora de la capsa.
- **Resultat esperat**:
  - El clic dins de la capsa no la tanca.
  - El clic fora de la capsa la tanca.
  - No es fa cap petició d'inici de sessió.
  - No es genera ni s'emmagatzema cap JWT.

### CP-US2-11 · Tancar amb la creu

- **Origen**: CA6.
- **Passos**:
  1. Obrir la capsa d'inici de sessió.
  2. Fer clic a la creu o botó de tancament.
- **Resultat esperat**:
  - La capsa es tanca.
  - No es fa cap petició d'inici de sessió.
  - No es genera ni s'emmagatzema cap JWT.

## Traçabilitat

| Criteri d'acceptació | Casos coberts |
|---|---|
| CA1 | CP-US2-01 |
| CA2 | CP-US2-02, CP-US2-03 |
| CA3 | CP-US2-04, CP-US2-05, CP-US2-06 |
| CA4 | CP-US2-07, CP-US2-08 |
| CA5 | CP-US2-01, CP-US2-09 |
| CA6 | CP-US2-10, CP-US2-11 |

## Casos pendents d'aclaració

Els casos següents no es poden concretar més sense decisions addicionals:

- Identificador d'accés: correu electrònic, nom d'usuari o tots dos.
- Ruta o pantalla posterior a l'inici de sessió.
- Mecanisme concret d'emmagatzematge segur del JWT.
- Missatges i permisos per a comptes pendents de validació o no verificats.

## Validació del document

- Els sis criteris d'acceptació tenen almenys un cas associat.
- Els identificadors `CP-US2-01` a `CP-US2-11` són únics.
- Els casos inclouen escenaris positius, negatius i de validació.
- No s'han modificat criteris d'acceptació.
- No s'ha modificat cap fitxer de codi.
