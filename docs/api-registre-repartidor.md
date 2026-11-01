# Contracte de l'API: registre de repartidor (US1.1)

Acord entre backend i frontend sobre l'endpoint de registre de repartidors. El backend
l'implementa a US1.1-T3 (serializer), US1.1-T4 (endpoint) i US1.1-T6 (tests); el frontend
s'hi connecta a US1.1-T10 i QA en treu els casos de prova a US1.1-T14. Qualsevol canvi d'aquest
document passa per pull request i s'avisa les dues parts.

## Endpoint

`POST /api/auth/register/repartidor/`

- Públic: no requereix autenticació.
- Cos i resposta en JSON (`Content-Type: application/json`).

## Petició

Cos JSON (`Content-Type: application/json`):

| Camp | Tipus | Obligatori | Validació |
|---|---|---|---|
| `nom` | text | Sí | No pot ser buit. Màxim 150 caràcters. |
| `cognoms` | text | Sí | No pot ser buit. Màxim 150 caràcters. |
| `correu` | text | Sí | Format de correu electrònic vàlid. Únic (no distingeix majúscules de minúscules). |
| `dni` | text | Sí | DNI (8 xifres i lletra de control) o NIE (lletra inicial X, Y o Z, 7 xifres i lletra de control) vàlid segons l'algorisme estàndard de mòdul 23. Únic. Espais, guions i barres no compten. |
| `telefon` | text | Sí | Telèfon espanyol vàlid de 9 xifres començat per 6, 7, 8 o 9, amb prefix `+34` opcional. Espais, guions i barres no compten. |
| `vehicle` | text | Sí | Tipus de vehicle. Valors permesos: `"bici"`, `"moto"`, `"cotxe"`. |
| `matricula` | text | Condicional | Obligatori si `vehicle` és `"moto"` o `"cotxe"`. Format espanyol actual de 4 xifres i 3 consonants (sense vocals, Ñ ni Q). Espais, guions i barres no compten. Si `vehicle` és `"bici"`, s'omet o s'envia buit. |
| `num_seguretat_social` | text | Sí | Número d'afiliació a la Seguretat Social de 12 dígits. Espais, guions i barres no compten. |
| `contrasenya` | text | Sí | Validadors de contrasenya de Django. No es retorna mai. |

### Models interns i correspondència de camps

Els noms dels camps d'aquest contracte són els de l'API i es mantenen en català:
- El model intern `Usuari` emmagatzema `email` (correu en minúscules), `name` (nom) i `password` (hash de la contrasenya). El rol s'assigna automàticament com a `repartidor` (`role="repartidor"`).
- El model `PerfilRepartidor` (vinculat un a un amb `Usuari`) emmagatzema `cognoms`, `dni` (DNI/NIE normalitzat en majúscules i net de caràcters separadors), `telefon` (normalitzat, amb el `+34` si s'ha enviat), `vehicle`, `matricula` (normalitzada, o buida si el vehicle és bicicleta), `num_seguretat_social` (12 dígits normalitzats) i l'estat inicial `pendent` ("Pendent de validació").
- El camp de confirmació de contrasenya es comprova únicament al formulari del frontend abans de l'enviament; l'API no rep aquest camp duplicat.

### Exemples de petició

**Amb vehicle de motor (requereix matrícula):**

```json
{
  "nom": "Pol",
  "cognoms": "Ferrer Soler",
  "correu": "repartidor@example.com",
  "dni": "12345678Z",
  "telefon": "+34 612 345 678",
  "vehicle": "moto",
  "matricula": "1234 BCD",
  "num_seguretat_social": "28/12345678/90",
  "contrasenya": "Llibres-de-tardor-24"
}
```

**Amb bicicleta (sense matrícula):**

```json
{
  "nom": "Laia",
  "cognoms": "Martí Roca",
  "correu": "laia.marti@example.com",
  "dni": "X1234567L",
  "telefon": "612345678",
  "vehicle": "bici",
  "num_seguretat_social": "081234567890",
  "contrasenya": "Llibres-de-tardor-24"
}
```

## Resposta correcta

**201 Created**

Retorna les dades del repartidor registrat amb l'estat del perfil i el rol, sense incloure mai la contrasenya:

```json
{
  "id": 1,
  "nom": "Pol",
  "cognoms": "Ferrer Soler",
  "correu": "repartidor@example.com",
  "dni": "12345678Z",
  "telefon": "+34612345678",
  "vehicle": "moto",
  "matricula": "1234BCD",
  "num_seguretat_social": "281234567890",
  "rol": "repartidor",
  "estat": "pendent"
}
```

El compte queda creat en estat "pendent" (pendent de validació per part d'un administrador des de l'admin de Django, US1.1-T5). En rebre el 201, el frontend redirigeix a la pantalla de confirmació de la sol·licitud (US1.1-T11).

## Errors

**400 Bad Request**. Els errors s'agrupen per camp, amb una llista de missatges per a cada camp afectat (format per defecte de Django REST Framework). El frontend mostra cada missatge sota el camp corresponent (US1.1-T10).

Exemple:

```json
{
  "correu": ["DNI/correu ja registrat"],
  "dni": ["DNI/correu ja registrat"]
}
```

### Taula de missatges d'error

| Cas | Camp | Missatge d'error |
|---|---|---|
| Camp obligatori buit o absent | el camp afectat | `Aquest camp és obligatori.` |
| Correu ja registrat | `correu` | `DNI/correu ja registrat` |
| DNI/NIE ja registrat | `dni` | `DNI/correu ja registrat` |
| Correu amb format invàlid | `correu` | `Introduïu una adreça de correu electrònic vàlida.` |
| Format de DNI/NIE invàlid o lletra incorrecta | `dni` | `El DNI/NIE no és vàlid` |
| Format de telèfon incorrecte | `telefon` | `El telèfon ha de tenir 9 xifres` |
| Vehicle invàlid (no és bici, moto ni cotxe) | `vehicle` | `"bici", "moto" o "cotxe" no és una opció vàlida.` |
| Matrícula absent per a moto o cotxe | `matricula` | `Aquest camp és obligatori.` |
| Format de matrícula incorrecte | `matricula` | `La matrícula ha de tenir 4 xifres i 3 lletres` |
| Format de Seguretat Social incorrecte | `num_seguretat_social` | `El número de la Seguretat Social ha de tenir 12 xifres` |
| Contrasenya no vàlida | `contrasenya` | Missatges dels validadors de Django en català (p. ex. `Aquesta contrasenya és massa curta. Ha de tenir com a mínim 8 caràcters.`) |

Els missatges `"DNI/correu ja registrat"` són literals dels criteris d'acceptació de la US1.1.
Els missatges de format coincideixen exactament amb els validadors reutilitzables de `backend/usuaris/validacions.py` (US1.1-T2) i les comprovacions del client a `frontend/src/utils/validacions.js` (US1.1-T9).

Les peticions amb un mètode HTTP diferent de `POST` reben una resposta **405 Method Not Allowed**.
