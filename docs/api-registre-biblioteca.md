# Contracte de l'API: registre de biblioteca (US1.2)

Acord entre backend i frontend sobre els endpoints de registre i verificació de
biblioteques. Les rutes són públiques i no requereixen una sessió iniciada.

## Registrar una biblioteca

`POST /api/auth/register/biblioteca/`

### Petició

Cos JSON:

| Camp | Tipus | Obligatori | Validació |
|---|---|---|---|
| `nom` | text | Sí | No pot ser buit. Màxim 150 caràcters. |
| `correu` | text | Sí | Ha de tenir un format de correu vàlid i no estar registrat. |

Exemple:

```json
{
  "nom": "Biblioteca Central",
  "correu": "biblioteca@example.com"
}
```

### Resposta correcta

**201 Created**

```json
{
  "nom": "Biblioteca Central",
  "correu": "biblioteca@example.com"
}
```

El compte es crea amb el rol `biblioteca`, `is_active=false` i sense contrasenya.
El backend envia un correu de verificació a l'adreça indicada amb un enllaç a la
pàgina de verificació del frontend (`<FRONTEND_URL>/verificacio/biblioteca/<uidb64>/<token>`).
La biblioteca tria la contrasenya en aquesta pàgina, i en desar-la el compte s'activa.

### Errors

**400 Bad Request**. Els errors s'agrupen per camp.

| Cas | Camp | Missatge |
|---|---|---|
| Camp `nom` absent o buit | `nom` | `Algún dels camps no és vàlid o no s'ha introduït, torna a intentar-ho` |
| Camp `correu` absent o buit | `correu` | `Algún dels camps no és vàlid o no s'ha introduït, torna a intentar-ho` |
| Correu amb format incorrecte | `correu` | `Algún dels camps no és vàlid o no s'ha introduït, torna a intentar-ho` |
| Correu ja registrat | `correu` | `Aquest correu correspon a un compte existent, torna a probar amb un altre correu` |

## Verificar el correu i triar la contrasenya

El `uidb64` i el `token` són els valors inclosos en l'enllaç del correu de
verificació. El token és de Django, caduca al cap de 24 hores (`PASSWORD_RESET_TIMEOUT`)
i deixa de ser vàlid quan es desa la contrasenya, així que l'enllaç només es pot fer
servir una vegada.

### Comprovar l'enllaç

`GET /api/auth/verify/biblioteca/<uidb64>/<token>/`

Comprova que l'enllaç sigui vàlid sense activar el compte. El frontend el crida en
obrir la pàgina per saber si ha de demanar la contrasenya.

**200 OK**

```json
{
  "correu": "biblioteca@example.com"
}
```

### Desar la contrasenya i activar el compte

`POST /api/auth/verify/biblioteca/<uidb64>/<token>/`

| Camp | Tipus | Obligatori | Validació |
|---|---|---|---|
| `contrasenya` | text | Sí | Les mateixes regles que la resta de comptes (validadors de Django). |

```json
{
  "contrasenya": "Llibres-de-tardor-24"
}
```

**200 OK**. El compte passa a `is_active=true`, la contrasenya queda desada i la
biblioteca ja pot iniciar sessió (`docs/api-auth.md`).

```json
{
  "detail": "El compte de biblioteca s'ha verificat correctament."
}
```

**400 Bad Request** si la contrasenya no és vàlida. L'enllaç continua sent vàlid i
es pot tornar a provar.

| Cas | Camp | Missatge |
|---|---|---|
| `contrasenya` absent, buida o `null` | `contrasenya` | `Aquest camp és obligatori.` |
| Contrasenya massa curta, massa comuna, només numèrica o semblant al correu | `contrasenya` | Els missatges dels validadors de Django, en català |

La confirmació de la contrasenya només la comprova el frontend.

### Enllaç invàlid o caducat

Tant el `GET` com el `POST` responen **400 Bad Request** si l'enllaç no és vàlid,
ha caducat, ja s'ha fet servir o no és d'un compte de biblioteca.

```json
{
  "detail": "L'enllaç de verificació no és vàlid o ha caducat."
}
```

Un compte que encara no ha verificat el correu no pot autenticar-se.
