# Casos de prova: comandes pendents de la biblioteca (US10)

Casos de prova de la US10, elaborats a partir dels criteris d'acceptació de la
història i del contracte de `docs/api-comandes.md` (US10-T1). Serveixen de base
per als tests unitaris i E2E. Qualsevol canvi d'aquest document passa per pull
request.

## Història i criteris d'acceptació

> **COM A** bibliotecari
> **VULL** veure les comandes pendents de la meva biblioteca
> **PER AIXÍ** preparar-les.

- **CA1**: les comandes apareixen ordenades per data de lliurament.

## Entorn i precondicions generals

- Aplicació disponible en un entorn de proves amb la base de dades migrada.
- Biblioteca activa de prova amb un usuari de rol `biblioteca` autenticat.
- Hi ha dades de prova de comandes per a la biblioteca i per a una altra
  biblioteca.
- Les dates de lliurament i de creació de les dades de prova es poden controlar.
- Les dades de cada cas són independents, tret que s'indiqui el contrari.
- L'endpoint és `GET /api/prestecs/biblioteca/comandes/`; no té cos ni
  paginació.

## Dades de prova

| Dada | Valor |
|---|---|
| Biblioteca autenticada | Biblioteca activa A |
| Altra biblioteca | Biblioteca activa B |
| Usuari | Usuari actiu de prova amb rol `usuari` |
| Repartidor | Compte actiu de prova amb rol `repartidor` |
| Dates de lliurament | Dues dates diferents i una comanda sense data (`null`) |
| Empat de data | Dues comandes amb la mateixa data i hores de creació diferents |
| Estats pendents del contracte | `rebuda`, `preparada`, `cancellada` |
| Estats que no es llisten | `en_cami`, `lliurada` |

## Resum

| ID | Cas | Criteri / contracte | Prioritat | Tipus | Execució proposada |
|---|---|---|---|---|---|
| CP-US10-01 | Ordenar les comandes per data de lliurament | CA1 | Alta | Correcte | API i E2E |
| CP-US10-02 | Aplicar l'ordre d'estats del contracte | Contracte T1 | Alta | Correcte | API |
| CP-US10-03 | Llistar només les comandes de la biblioteca autenticada | Contracte T1 | Alta | Correcte | API i E2E |
| CP-US10-04 | Retornar una llista buida si no hi ha comandes | Contracte T1 | Mitjana | Correcte | API |
| CP-US10-05 | Incloure les dades necessàries per identificar la comanda | Contracte T1 | Mitjana | Correcte | API |
| CP-US10-06 | Rebutjar la petició sense autenticació | Contracte T1 | Alta | Error | API |
| CP-US10-07 | Rebutjar rols no autoritzats i biblioteques inactives | Contracte T1 | Alta | Error | API |

## Casos de prova

### CP-US10-01 · Ordenar les comandes per data de lliurament

- **Origen**: CA1 i regles d'ordre de T1.
- **Precondicions**: la biblioteca autenticada té comandes en estat llistable
  amb dates de lliurament diferents, dues comandes amb la mateixa data i una
  comanda sense data.
- **Passos**: enviar `GET /api/prestecs/biblioteca/comandes/` amb la biblioteca
  autenticada.
- **Resultat esperat**:
  - La resposta és `200 OK` i les comandes surten de la data de lliurament més
    propera a la més llunyana.
  - Les comandes sense data (`data_lliurament: null`) apareixen al final.
  - Si dues comandes tenen la mateixa data, apareix primer la més antiga segons
    la data de creació.
  - La resposta és una llista sense paginació.
- **Tipus**: correcte.
- **Automatització**: pytest-django per verificar l'ordre de la resposta;
  Playwright per verificar l'ordre visible a la pàgina.

### CP-US10-02 · Aplicar l'ordre d'estats del contracte

- **Origen**: contracte de T1.
- **Precondicions**: la biblioteca té comandes en cadascun dels estats indicats.
- **Passos**: consultar l'endpoint de comandes pendents.
- **Resultat esperat**:
  - Apareixen les comandes en estat `rebuda`, `preparada` i `cancellada`.
  - No apareixen les comandes en estat `en_cami` ni `lliurada`.
- **Tipus**: correcte.
- **Automatització**: API.
- **Abast**: segueix la decisió provisional P7 de T1; cal actualitzar el cas si
  el Product Owner decideix excloure les comandes preparades o cancel·lades.

### CP-US10-03 · Llistar només les comandes de la biblioteca autenticada

- **Origen**: contracte de T1.
- **Precondicions**: hi ha comandes llistables a la biblioteca A i a la
  biblioteca B.
- **Passos**: autenticar-se com a biblioteca A i consultar l'endpoint.
- **Resultat esperat**:
  - La resposta conté les comandes de la biblioteca A.
  - No conté cap comanda de la biblioteca B, encara que sigui pendent.
- **Tipus**: correcte.
- **Automatització**: API i Playwright.

### CP-US10-04 · Retornar una llista buida si no hi ha comandes

- **Origen**: contracte de T1.
- **Precondicions**: la biblioteca autenticada no té cap comanda en els estats
  llistables.
- **Passos**: consultar l'endpoint.
- **Resultat esperat**:
  - La resposta és `200 OK`.
  - El cos és exactament una llista buida: `[]`.
  - La resposta no inclou cap estructura de paginació.
- **Tipus**: correcte.
- **Automatització**: API.

### CP-US10-05 · Incloure les dades necessàries per identificar la comanda

- **Origen**: contracte de T1.
- **Precondicions**: la biblioteca té almenys una comanda llistable.
- **Passos**: consultar l'endpoint i inspeccionar una comanda de la resposta.
- **Resultat esperat**:
  - Cada element conté el format de comanda definit al contracte.
  - Inclou `usuari` amb `id` i `nom`, a més de `biblioteca`, `llibres`,
    `estat`, `data_lliurament` i `creada`.
  - La informació de biblioteca i usuari correspon a la comanda retornada.
- **Tipus**: correcte.
- **Automatització**: API.

### CP-US10-06 · Rebutjar la petició sense autenticació

- **Origen**: contracte de T1 i `docs/api-auth.md`.
- **Passos**: consultar l'endpoint sense capçalera `Authorization` i repetir la
  petició amb un token invàlid o caducat.
- **Resultat esperat**:
  - La resposta és `401 Unauthorized`.
  - El cos segueix el format d'error definit a `docs/api-auth.md`.
  - No s'exposen dades de cap biblioteca.
- **Tipus**: error.
- **Automatització**: API.

### CP-US10-07 · Rebutjar rols no autoritzats i biblioteques inactives

- **Origen**: contracte de T1.
- **Passos**:
  1. Consultar l'endpoint amb un usuari autenticat amb rol `usuari`.
  2. Repetir-ho amb un usuari autenticat amb rol `repartidor`.
  3. Repetir-ho amb un compte de biblioteca inactiu, si el model permet aquest
     estat.
- **Resultat esperat**:
  - Cada petició no autoritzada retorna `403 Forbidden`.
  - El cos és exactament `{"detail": "No té permisos per realitzar aquesta acció."}`.
  - No es retorna cap comanda.
- **Tipus**: error.
- **Automatització**: API.

## Decisions i abast

- El contracte de T1 inclou provisionalment els estats `rebuda`, `preparada` i
  `cancellada`. El Product Owner encara ha de confirmar si les preparades han de
  continuar apareixent.
- El criteri d'acceptació només exigeix l'ordre per data de lliurament. Les
  regles de dates nul·les i desempat per data de creació provenen del contracte
  T1 i queden cobertes com a comportament complementari.