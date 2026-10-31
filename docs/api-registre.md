# Contracte de l'API: registre d'usuari (US1)

Acord entre backend i frontend sobre l'endpoint de registre. El backend l'implementa a US1-T3 (serializer),
US1-T4 (endpoint) i US1-T6 (tests); el frontend s'hi connecta a US1-T9 i QA en treu els casos de prova a US1-T12.
Qualsevol canvi d'aquest document passa per pull request i s'avisa les dues parts.

**Estat**: esborrany. Les decisions pendents són al final del document.

## Endpoint

`POST /api/auth/register/`

- Públic: no requereix autenticació.
- Cos i resposta en JSON (`Content-Type: application/json`).

## Petició

| Camp | Tipus | Obligatori | Validació |
|---|---|---|---|
| `nom` | text | Sí | No pot ser buit. |
| `correu` | text | Sí | Format de correu electrònic vàlid. Únic. |
| `adreca` | text | Sí | No pot ser buit. |
| `num_carnet` | text | Sí | Exactament 10 dígits. Únic. |
| `contrasenya` | text | Sí | Validadors de contrasenya de Django. No es retorna mai. |

Els noms dels camps d'aquest contracte són els de l'API i es mantenen en català. El model intern `Usuari`
fa servir `email`, `name`, `address`, `library_card_number`, `role` i `password`; el serializer tradueix
els noms públics `correu`, `nom`, `adreca`, `num_carnet` i `contrasenya` quan crea l'usuari. La contrasenya
es desa amb el mecanisme de hash de Django i no s'inclou mai a la resposta.

El tipus de compte no s'envia: el registre sempre crea un compte amb rol `usuari`. Les opcions "Repartidor" i
"Biblioteca" del formulari mostren "Funcionalitat no implementada" al frontend (US1-T11) i no criden l'endpoint.

```json
{
  "nom": "Anna Puig",
  "correu": "anna@example.com",
  "adreca": "C/ Major 1, 08001 Barcelona",
  "num_carnet": "1234567890",
  "contrasenya": "una-contrasenya-segura"
}
```

## Resposta correcta

**201 Created**

```json
{
  "id": 1,
  "nom": "Anna Puig",
  "correu": "anna@example.com",
  "adreca": "C/ Major 1, 08001 Barcelona",
  "num_carnet": "12345678",
  "rol": "usuari"
}
```

Si l'equip decideix fer inici de sessió automàtic (US1-T5, vegeu P3), la resposta inclourà també:

```json
{
  "access": "<token JWT d'accés>",
  "refresh": "<token JWT de refresc>"
}
```

## Errors

**400 Bad Request**. Els errors s'agrupen per camp, amb una llista de missatges per a cada camp (format per
defecte de Django REST Framework). El frontend mostra cada missatge sota el camp corresponent (US1-T9).

```json
{
  "correu": ["Aquest correu electrònic ja està registrat"],
  "num_carnet": ["Aquest usuari ja està registrat"]
}
```

| Cas | Camp | Missatge |
|---|---|---|
| Correu ja registrat | `correu` | `Aquest correu electrònic ja està registrat` |
| Carnet ja registrat | `num_carnet` | `Aquest usuari ja està registrat` |
| Format de carnet incorrecte | `num_carnet` | `El format d’aquest carnet no és vàlid` |
| Camp obligatori buit o absent | el camp | `Aquest camp és obligatori.` |
| Correu amb format incorrecte | `correu` | `Introduïu una adreça de correu electrònic vàlida.` |
| Contrasenya no vàlida | `contrasenya` | Missatges dels validadors de Django |

Els tres primers missatges són literals dels criteris d'acceptació de la US1 i els tests els comproven
exactament.

## Decisions pendents

- **P3. Inici de sessió automàtic.** Cal decidir si el registre retorna els tokens JWT (US1-T5). Si és així,
  falta una tasca per configurar `djangorestframework-simplejwt`.
