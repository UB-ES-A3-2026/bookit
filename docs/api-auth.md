# Contracte de l'API: autenticació (US2)

Acord entre backend i frontend sobre l'inici de sessió, la renovació del token i les dades de l'usuari
autenticat. El backend l'implementa a US2-T1 (JWT), US2-T2 (inici de sessió i renovació), US2-T3 (estat del
compte), US2-T4 (`/me`) i US2-T5 (tests); el frontend s'hi connecta a US2-T10 i US2-T11 i QA en treu els casos de
prova a US2-T14. Qualsevol canvi d'aquest document passa per pull request i s'avisa les dues parts.

**Estat**: esborrany. Les decisions pendents són al final del document.

## Resum

| Mètode i ruta | Autenticació | Per a què serveix |
|---|---|---|
| `POST /api/auth/login/` | Pública | Canvia el correu i la contrasenya per dos tokens. |
| `POST /api/auth/refresh/` | Pública (cal el token de refresc al cos) | Obté un token d'accés nou. |
| `GET /api/auth/me/` | `Authorization: Bearer <access>` | Retorna les dades i el rol de l'usuari. |

Peticions i respostes en JSON (`Content-Type: application/json`). Les peticions amb un altre mètode HTTP reben
**405 Method Not Allowed**.

## Tokens

| Token | Durada | Ús |
|---|---|---|
| `access` | 15 minuts | Capçalera `Authorization: Bearer <access>` de les peticions autenticades. |
| `refresh` | 1 dia | Només al cos de `POST /api/auth/refresh/`. |

No hi ha rotació ni llista negra: renovar no canvia el token de refresc i, en acabar-se el dia, cal tornar a
iniciar sessió. El frontend els desa a `sessionStorage`. Tancar sessió és una acció del frontend, que esborra els
tokens; no hi ha cap endpoint per fer-ho.

## Inici de sessió

`POST /api/auth/login/`

### Petició

| Camp | Tipus | Obligatori | Validació |
|---|---|---|---|
| `correu` | text | Sí | No pot ser buit. No distingeix majúscules de minúscules i s'ignoren els espais del voltant. |
| `contrasenya` | text | Sí | No pot ser buida. No es retorna mai. |

No es valida el format del correu: un correu mal format és un correu inexistent i rep el missatge genèric.

```json
{
  "correu": "anna@example.com",
  "contrasenya": "una-contrasenya-segura"
}
```

### Resposta correcta

**200 OK**. Només retorna els tokens; les dades i el rol s'obtenen de `GET /api/auth/me/`.

```json
{
  "access": "<token JWT d'accés>",
  "refresh": "<token JWT de refresc>"
}
```

### Errors

**400 Bad Request**. Falta algun camp o és buit. Els errors s'agrupen per camp, com als contractes de registre.

```json
{
  "correu": ["Aquest camp és obligatori."],
  "contrasenya": ["Aquest camp és obligatori."]
}
```

**401 Unauthorized**. Les credencials no són correctes. El missatge és el mateix tant si el correu no existeix com
si la contrasenya és incorrecta, per no revelar quins correus estan registrats.

```json
{
  "detail": "El correu o la contrasenya no són correctes."
}
```

**403 Forbidden**. Les credencials són correctes, però l'estat del compte no permet entrar. No es retorna cap token.

```json
{
  "detail": "Pendent de validació"
}
```

| Cas | Estat | Missatge (`detail`) |
|---|---|---|
| Camp obligatori buit o absent | 400 | `Aquest camp és obligatori.` (al camp afectat) |
| Correu inexistent o contrasenya incorrecta | 401 | `El correu o la contrasenya no són correctes.` |
| Compte inactiu que no és de biblioteca | 401 | `El correu o la contrasenya no són correctes.` |
| Repartidor amb l'estat `pendent` | 403 | `Pendent de validació` |
| Repartidor amb l'estat `rebutjat` | 403 | `Validació incompleta` |
| Biblioteca amb el correu sense verificar (compte inactiu) | 403 | `Verifica el teu correu` |

Els casos de 403 només s'apliquen si la contrasenya és correcta. Amb una contrasenya incorrecta, un compte en
qualsevol d'aquests estats rep el 401 genèric, de manera que ningú pot esbrinar l'estat d'un compte aliè.

Els missatges de 401 i 403 són literals: els tests els comproven exactament (US2-T5) i el frontend mostra `detail`
tal com arriba (US2-T11).

## Renovació del token

`POST /api/auth/refresh/`

### Petició

```json
{
  "refresh": "<token JWT de refresc>"
}
```

### Resposta correcta

**200 OK**. Només retorna el token d'accés nou; el de refresc continua sent el mateix.

```json
{
  "access": "<token JWT d'accés>"
}
```

### Errors

| Cas | Estat | Resposta |
|---|---|---|
| `refresh` absent | 400 | `{"refresh": ["Aquest camp és obligatori."]}` |
| `refresh` buit | 400 | `{"refresh": ["Aquest camp no pot estar en blanc."]}` |
| Token invàlid | 401 | `{"detail": "Token is invalid", "code": "token_not_valid"}` |
| Token caducat | 401 | `{"detail": "Token is expired", "code": "token_not_valid"}` |
| Compte desactivat | 401 | `{"detail": "No active account found for the given token.", "code": "no_active_account"}` |

Els textos dels 401 són de `simplejwt`, que no té traducció al català, i no es mostren mai a l'usuari. El frontend
només mira l'estat: si la renovació falla amb un 401, tanca la sessió (US2-T10).

## Usuari autenticat

`GET /api/auth/me/`

Requereix la capçalera `Authorization: Bearer <access>`. No té cos.

### Resposta correcta

**200 OK**. Els mateixos camps per als tres rols.

| Camp | Tipus | Descripció |
|---|---|---|
| `id` | enter | Identificador de l'usuari. |
| `nom` | text | Nom de l'usuari. |
| `correu` | text | Correu electrònic, en minúscules. |
| `rol` | text | `usuari`, `repartidor` o `biblioteca`. |

```json
{
  "id": 1,
  "nom": "Anna Puig",
  "correu": "anna@example.com",
  "rol": "usuari"
}
```

`adreca` i `num_carnet` no s'hi inclouen perquè només tenen sentit per al rol `usuari`: els repartidors i les
biblioteques tenen l'adreça buida i un carnet generat internament que no s'ha d'exposar. La contrasenya no
s'inclou mai.

### Errors

**401 Unauthorized**.

| Cas | Resposta |
|---|---|
| Sense la capçalera `Authorization` | `{"detail": "Credencials d'autenticació no disponibles."}` |
| Token invàlid o caducat | `{"detail": "Given token not valid for any token type", "code": "token_not_valid", "messages": [...]}` |
| Compte desactivat | `{"detail": "User is inactive", "code": "user_inactive"}` |

Tampoc aquests textos es mostren a l'usuari. Davant d'un 401, el client HTTP intenta renovar el token i, si no pot,
tanca la sessió (US2-T10).

## Flux del frontend

1. `POST /api/auth/login/`. Si falla, es mostra `detail` (401 i 403) o el missatge de cada camp (400).
2. `GET /api/auth/me/` amb el token d'accés acabat de rebre, per saber el nom i el rol. Per això US2-T11 també
   depèn de US2-T4.
3. `iniciarSessio` de l'store amb els tokens, `usuari` (la resposta de `/me`) i `rol`.
4. Redirecció segons el rol: `usuari` a l'inici, `repartidor` a la vista de repartidor i `biblioteca` al seu catàleg.

## Canvis pendents al codi existent

- **Ruta de renovació al frontend.** `frontend/src/services/api.js` crida `/auth/token/refresh/`, però la ruta
  d'aquest contracte és `/auth/refresh/`. Cal canviar-la; si no, la sessió es tancarà quan caduqui el primer token
  d'accés.
- **Compte de biblioteca sense verificar (US2-T3).** Django no autentica els comptes inactius, de manera que
  `simplejwt` hi retorna el missatge genèric. Cal comprovar la contrasenya d'aquests comptes a part per poder
  respondre `Verifica el teu correu`.
- **Compte esborrat (US2-T2).** `simplejwt` no gestiona que l'usuari d'un token de refresc vàlid ja no existeixi i
  la petició acaba en un error 500. Ha de respondre 401, com un compte desactivat.

## Decisions pendents

- **P1. Missatges de l'estat del compte.** Els missatges de la taula d'inici de sessió surten de US2-T3 i de la
  US1.1, però el Product Owner encara ha de respondre el dubte obert a la US2.
- **P2. Inici de sessió amb nom d'usuari.** La US2 parla de "correu electrònic/nom d'usuari", però els usuaris no
  en tenen. Aquest contracte només accepta el correu, a l'espera que el Product Owner ho confirmi.
- **P3. Canvis d'estat amb la sessió oberta.** L'estat del repartidor només es comprova en iniciar sessió: si un
  repartidor validat passa a rebutjat, conserva l'accés fins que caduquin els seus tokens (màxim 1 dia).
