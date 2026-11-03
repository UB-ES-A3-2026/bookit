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

El compte es crea amb el rol `biblioteca` i `is_active=false`. El backend envia
un correu de verificació a l'adreça indicada. La contrasenya no forma part
d'aquest registre.

### Errors

**400 Bad Request**. Els errors s'agrupen per camp.

| Cas | Camp | Missatge |
|---|---|---|
| Camp `nom` absent o buit | `nom` | `Algún dels camps no és vàlid o no s'ha introduït, torna a intentar-ho` |
| Camp `correu` absent o buit | `correu` | `Algún dels camps no és vàlid o no s'ha introduït, torna a intentar-ho` |
| Correu amb format incorrecte | `correu` | `Algún dels camps no és vàlid o no s'ha introduït, torna a intentar-ho` |
| Correu ja registrat | `correu` | `Aquest correu correspon a un compte existent, torna a probar amb un altre correu` |

## Verificar el correu

`GET /api/auth/verify/biblioteca/<uidb64>/<token>/`

El `uidb64` i el `token` són els valors inclosos en l'enllaç del correu de
verificació. El token és de Django i caduca al cap de 24 hores.

### Resposta correcta

**200 OK**

```json
{
  "detail": "El compte de biblioteca s'ha verificat correctament."
}
```

En verificar correctament l'enllaç, el compte passa a `is_active=true` i ja pot
autenticar-se.

### Enllaç invàlid o caducat

**400 Bad Request**

```json
{
  "detail": "L'enllaç de verificació no és vàlid o ha caducat."
}
```

Un compte que encara no ha verificat el correu no pot autenticar-se.
