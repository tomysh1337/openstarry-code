---
name: nosql-injection-defenses
description: >
  Defend applications against NoSQL operator injection and type confusion:
  block $gt/$ne/$where and other operator keys, force typed scalars, sanitize
  Mongo-style filters, and use query sanitization libraries. Use when hardening
  MongoDB/Mongoose/CouchDB-style APIs, login/filter/search against operator JSON,
  PHP array-style query expansion, or $where/server-side JS — authorized/org-owned
  systems only. Offensive proofs hand off to nosql-injection.
---

# NoSQL Injection Defenses

Design and verify **defenses** that stop untrusted input from becoming Mongo-style
**query operators**, **type-confused filter values**, or **server-side JS** (`$where`).
Defensive hardening only; not a penetration-testing catalog.

## Scope And Authorization

- **In scope:** Org-owned APIs/workers using MongoDB, Mongoose, or similar document
  stores; authorized secure code review; own-project labs.
- **Out of scope:** Unauthorized probing; destructive `$where`/regex DoS;
  full-collection dumps; production operator abuse against third parties.
- Prefer proving **controls reject operators** over extracting credentials or PII.
  Accidental exposure: stop, redact, rotate secrets if needed.
- Offensive find-and-prove → `nosql-injection`. This skill owns **defense design,
  sanitization, schemas, and verification**.

## When To Use

- Login, search, filter, export, or admin query-builder paths that merge user
  JSON/BSON into `find` / `update` / `aggregate` / `delete`
- JSON or form/query expansion (`password[$ne]=`) that can inject `$gt`, `$ne`,
  `$in`, `$regex`, `$where`, `$expr`, `$function`
- Type confusion: password/username sent as object/array/boolean where a scalar
  is required
- Mentions: NoSQL injection defense, operator sanitization, `mongo-sanitize`,
  `express-mongo-sanitize`, forbid `$` keys, disable `$where`

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Authorized NoSQL exploit / auth-bypass proofs | `nosql-injection` |
| Injection class unknown (assessment) | `injection-checking` |
| Classic SQL injection | `sqli-sql-injection` |
| General boundary allowlists / schemas | `input-validation-patterns` |
| Implementation quality baseline | `code-quality-standards` |

## Workflow

### 1. Map untrusted → query sinks

1. Inventory handlers that pass body/query into Mongo filters, updates,
   projections, sorts, or aggregation stages (including second-order stored JSON).
2. Note parsers: pure JSON, form-urlencoded, query arrays, GraphQL→filter maps.
3. List drivers and privileges (can the app user eval JS?).

### 2. Never pass raw user objects into queries

1. **Explicit field pick** and coerce types at the edge; load auth by scalar
   identity only; verify password hashes **in app code** (bcrypt/argon2) — never
   `find({ username, password: body.password })` with operator-capable values.
2. Allowlisted filter/sort keys via a server dictionary; server builds operators.
3. Forbid client-controlled **projection**, **pipeline stages**, and **update
   operator trees** on public APIs.
4. Reject nested objects where a **scalar** is required (type-confusion defense).

### 3. Operator and key sanitization

1. Recursively reject keys starting with `$` or containing `.` in untrusted objects.
2. Schema-first validation (Zod/Joi/JSON Schema/Mongoose strict) with **forbid
   unknown** and **no silent object coercion** on auth/filter fields.
3. Libraries (check version and placement — middleware alone fails if sinks rebuild
   filters later): Node `express-mongo-sanitize` / `mongo-sanitize`; Python
   Pydantic (never `**user_dict` into filters); equivalent `$`/`.` reject elsewhere.
4. Sanitization is **defense in depth**; primary control is typed field construction.

### 4. Engine constraints and auth/filter patterns

| Control | Intent |
| --- | --- |
| Disable `$where` / server JS if unused | Blocks expression injection and CPU bombs |
| No string-concat `$where` | Avoid `this.x == '` + input patterns |
| Least-privilege DB users | No arbitrary eval; minimal collection rights |
| Bound regex / body size / depth | Server-built patterns only; limit smuggling/DoS |

Login: identity scalar + app-side hash. Search: allowlisted fields + operators
**you** choose. PHP/legacy: neutralize `foo[bar]` expansion into operator maps.
Re-validate any stored filter JSON before reuse (second-order).

### 5. Verify defenses (authorized)

1. Staging: `$gt`/`$ne`/`$where` and form `[$ne]` → **400/validation**, not
   auth bypass or widened results.
2. Type confusion: object/array password rejected; no CastError→bypass path.
3. Regression tests for sanitizer + schema (`code-quality-standards`).
4. Residual offensive proofs → `nosql-injection` (in scope); redact PII.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Harden against NoSQL operators / type confusion | **This skill** | — |
| Authorized offensive NoSQL proof / bypass testing | `nosql-injection` | this for remediation |
| Injection class unknown | `injection-checking` | then this or `nosql-injection` |
| General boundary schemas / allowlists | `input-validation-patterns` | this for Mongo `$` |
| SQL engine issues | `sqli-sql-injection` | — |
| Implement validators, errors, tests | `code-quality-standards` | always on code changes |
| Mass assignment / extra field privilege | `mass-assignment` | closed schemas here |

- **`nosql-injection`:** find/prove operator abuse; remediate with **this skill**.
- **`input-validation-patterns`:** general allowlists; keep Mongo `$where` rules here.
- **`code-quality-standards`:** typed APIs, fail closed, tests on auth/query paths.

## Output Checklist

- [ ] Untrusted → Mongo filter/update/aggregate sinks inventoried
- [ ] No raw user objects in driver queries; fields picked and typed
- [ ] Auth: scalar identity + app-side hash verify (not password operators)
- [ ] `$` / `.` keys rejected recursively; schema forbid-unknown on filters
- [ ] Sanitization library/middleware before query construction (if used)
- [ ] Client projection, pipeline, and update-operator trees blocked
- [ ] `$where` / server JS disabled or unused; no string-concat `$where`
- [ ] DB least privilege; regex/body/depth bounds set
- [ ] Tests: `$gt`/`$ne`/`$where`/form `[$ne]`/type confusion fail closed
- [ ] Residual risk noted; offensive follow-up via `nosql-injection` if needed
- [ ] `code-quality-standards` on code changes; no secrets/PII in reports
- [ ] Authorized systems only

## Rules

- Defense in depth: typed construction + schema + `$` rejection + engine off +
  least privilege. Sanitizer middleware is not enough alone.
- Prefer reject-unknown over silent strip when clients must not send `$` keys.
- Authorized hardening only; no destructive or cluster-melting probes.
- Redact connection strings, tokens, and personal data from tickets and prompts.
