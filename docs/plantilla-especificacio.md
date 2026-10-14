# Plantilla d'especificació de tasca per a l'agent

L'estil de codi i les restriccions permanents ja són a `AGENTS.md`. El camp "Restriccions" només és per a
excepcions puntuals d'aquesta tasca.

```markdown
## Tasca: [nom curt]

**Context**: [què ha de saber l'agent que no és obvi llegint el codi: convencions, dependències,
decisions prèvies rellevants]

**Objectiu**: [què ha de fer, en una frase clara]

**Criteris d'acceptació**:
- [ ] Criteri 1
- [ ] Criteri 2
- [ ] Criteri 3

**Restriccions específiques d'aquesta tasca** (excepcions a AGENTS.md; en blanc si no n'hi ha):
- [...]

**Exemples** (si escau):
- Input → Output esperat
- Cas límit a tenir en compte

**Nivell de supervisió esperat**: [lleugera / exhaustiva / no delegable]
```

---

## Exemple: tasca trivial de cap a cap del Sprint 0

```markdown
## Tasca: endpoint de salut de l'API

**Context**: Backend Django + DRF a `backend/` (cal que el projecte Django ja estigui creat). Encara no hi ha
cap endpoint propi. Totes les rutes de l'API van sota `/api/`.

**Objectiu**: Afegir un endpoint `GET /api/health/` que retorni `{"status": "ok"}`.

**Criteris d'acceptació**:
- [ ] `GET /api/health/` respon 200 amb el cos `{"status": "ok"}`.
- [ ] És accessible sense autenticació.
- [ ] Hi ha un test amb pytest-django que verifica el codi 200 i el cos de la resposta.
- [ ] `ruff check .`, `ruff format --check .` i `pytest` passen.

**Restriccions específiques d'aquesta tasca**:
- No afegeixis dependències noves.

**Exemples**:
- `GET /api/health/` → `200 {"status": "ok"}`
- `POST /api/health/` → `405 Method Not Allowed`

**Nivell de supervisió esperat**: lleugera
```
