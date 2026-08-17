---
name: json-schema-design
description: >
  Design and evolve JSON Schema (and OpenAPI-aligned schemas): types, required
  fields, formats, composition, versioning, and validation at boundaries. Use
  when JSON Schema, schema design, OpenAPI components/schemas, AJV/Zod/Pydantic
  contract alignment, request/response validation, or reviewing JSON contracts
  for APIs, events, and config. Data-layer focus; not prose-only API docs.
---

# JSON Schema Design

Design **machine-enforceable JSON contracts** for APIs, events, config files,
and storage interchange. Prefer one source of truth, explicit nullability and
requiredness, and validators that match what producers and consumers actually
send. Repository schema layout, dialect, and codegen pipeline outrank generic
preferences.

## Use When

- Authoring or reviewing JSON Schema drafts (Draft-07, 2019-09, 2020-12) or
  OpenAPI 3.x `components/schemas` / request-response bodies
- Defining validation rules: `type`, `required`, `enum`, `format`, `pattern`,
  `minimum`/`maximum`, `minLength`/`maxLength`, `additionalProperties`
- Aligning runtime validators (AJV, Zod, Joi, Pydantic, class-validator,
  serde + schemars, etc.) with published schemas
- Evolving contracts without breaking clients: additive fields, deprecations,
  discriminators for polymorphism
- Designing event/payload schemas, config schemas, or shared DTO packages
- User mentions: JSON Schema, schema design, OpenAPI schema, request validation,
  `$ref` components, `additionalProperties`, nullable vs optional

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| OpenAPI operation prose, examples, error narrative | `api-documentation-writing` |
| API version path/header/deprecation strategy | `api-versioning-design` |
| SQL table/column naming and migration SQL style | `sql-style-conventions` |
| Safe expand/contract DB migrations / zero-downtime | `database-migration-safety` |
| Live API discovery in assessments | `api-recon-and-docs` |
| Application reliability/security/tests around validators | `code-quality-standards` |

## Repo Config First

Repo config, existing schemas, and tooling **outrank** this skill’s defaults.

1. **Source of truth:** design-first OpenAPI/JSON Schema packages vs code-first
   models that generate schemas — edit only the authoritative layer
2. **Dialect and tooling:** JSON Schema draft version; OpenAPI 3.0 vs 3.1
   (3.1 aligns more closely with JSON Schema); Spectral/Redocly/AJV config;
   `components/schemas` layout and `$id` / `$ref` conventions
3. **Validator stack:** AJV strict mode, Zod, Pydantic v2, Bean Validation,
   etc. — match options the repo already enables (`additionalProperties`,
   format assertion, coerce types on/off)
4. **Naming and packaging:** `PascalCase` vs `snake_case` schema titles;
   file layout (`schemas/`, `openapi/components/`, monorepo package);
   shared vs service-local components
5. **Nullability policy:** OpenAPI 3.0 `nullable: true` vs 3.1 `type: ["string","null"]`;
   optional (omit) vs null (present null) — copy dominant local pattern
6. **Error envelope and pagination:** reuse existing shared schemas rather than
   inventing parallel `Error` / `Page` shapes
7. **Neighboring contracts:** copy 2–3 mature schemas in the same API for
   `required`, `readOnly`/`writeOnly`, money/time encoding, and ID formats

**Precedence:** If repo rules conflict with defaults below, follow the repo.
Surface conflicts that would accept invalid data in production, diverge
validator vs docs, or break published clients.

## Workflow

1. **Identify the boundary and audience.**
   - Request body, response body, event payload, config file, or internal DTO
   - Who validates (edge API, worker, CLI) and who generates (client SDK, mocks)
2. **Inventory real samples.**
   - Happy paths, empty collections, partial updates, error bodies
   - Existing OpenAPI, fixtures, or producer code — do not invent fields
3. **Choose composition style.**
   - Flat objects + `$ref` for reuse; `allOf` for mixins when the repo uses them
   - `oneOf` / `anyOf` + `discriminator` for polymorphism when needed
   - Prefer explicit properties over open maps unless the domain is a bag of keys
4. **Define types and constraints.**
   - Wire types: string/number/integer/boolean/array/object/null (per dialect)
   - Formats: `date-time`, `uuid`, `email`, `uri` only when enforced
   - Bounds: lengths, ranges, array `maxItems`, string patterns for true invariants
   - Money: integer minor units **or** decimal strings — never silent float money
   - Time: timezone policy (`date-time` with offset vs epoch ms) documented
5. **Mark required, optional, read/write, deprecated.**
   - `required` = must be present on that operation’s schema
   - Optional omit ≠ null unless both are allowed and documented
   - `readOnly` response fields; `writeOnly` secrets/passwords on requests
   - `deprecated: true` with replacement field notes when evolving
6. **Control openness.**
   - Default closed objects: `additionalProperties: false` when the API is strict
     and clients should not rely on unknown fields — **unless** the repo’s
     compatibility policy requires ignoring unknowns (document either choice)
   - Maps: `additionalProperties` with a value schema, plus key constraints if any
7. **Align OpenAPI and runtime.**
   - Same names, types, enums, and required sets in handlers and schemas
   - Generate or hand-sync clients; fail CI on drift when tools exist
8. **Evolve safely.**
   - Additive: new optional fields, new enum values only if consumers tolerate unknowns
   - Breaking: remove/rename, type change, new required field, stricter pattern —
     pair with `api-versioning-design` for public APIs
9. **Verify.**
   - Validate fixtures against schema (positive + negative cases)
   - Lint OpenAPI/JSON Schema (Spectral, etc.)
   - Contract or unit tests at the parse boundary (`code-quality-standards`)

## Design Rules (defaults when repo is silent)

### Types and requiredness

- Prefer `integer` over `number` for whole counts and minor currency units
- Prefer string enums with stable machine values (`"canceled"`) over free text
- Never use `type: string` for structured data that should be an object/array
- Document units in `description` or field name (`durationMs`, `sizeBytes`)
- Empty string vs null: pick one invalid/absent story; do not allow both without reason

### Composition

- `$ref` shared components; avoid copy-paste schema drift
- Avoid deep `allOf` stacks that obscure `required` after merge
- For polymorphism, set `discriminator.propertyName` and map values to schemas
- Prefer separate request/response schemas when write and read shapes differ
  (`OrderCreate` vs `Order`) over one overloaded model with many conditionals

### OpenAPI alignment

- Put reusable models under `components/schemas`; reference with `$ref`
- Keep operation-level bodies thin: `$ref` + minimal overrides
- Match status-specific response schemas (200 vs 201 vs 404 error)
- Schema `description` holds field meaning; operation `description` holds
  behavior — hand narrative polish to `api-documentation-writing`

### Validation placement

- Validate **untrusted input at the boundary**; trust internal types after parse
- Do not double-parse with conflicting rules (gateway schema ≠ app schema)
- Reject with stable error codes and field paths; do not leak stack traces

### Security and abuse resistance

- Cap string lengths, array sizes, and nesting depth on public inputs
- Avoid catastrophic regexes (`pattern` with nested quantifiers)
- Do not put secrets in example values; use placeholders
- Treat free-form HTML/Markdown fields as untrusted even when schema-valid

## Good / Bad Examples

### Clear object contract

**Good**

```yaml
# components/schemas/CreateOrderRequest.yaml
type: object
additionalProperties: false
required: [customerId, items]
properties:
  customerId:
    type: string
    format: uuid
    description: Customer that owns the order.
  items:
    type: array
    minItems: 1
    maxItems: 100
    items:
      $ref: "#/components/schemas/OrderItemInput"
  note:
    type: string
    maxLength: 500
    description: Optional buyer note. Omitted if unused; empty string allowed.
```

**Bad**

```yaml
type: object
# no required, no additionalProperties, no bounds
properties:
  customerId: true
  items: {}
  total: { type: number }  # float money; ambiguous
```

### Optional vs null

**Good** — explicit nullability (OpenAPI 3.1 / JSON Schema style):

```yaml
middleName:
  type: ["string", "null"]
  maxLength: 100
  description: >
    Present null clears a stored middle name on PATCH; omit leaves unchanged.
```

**Bad** — ambiguous:

```yaml
middleName:
  type: string
  # Is omit OK? Is null OK? Does null mean delete or "unknown"?
```

### Enums and evolution

**Good**

```yaml
status:
  type: string
  enum: [draft, open, paid, canceled]
  description: Lifecycle status. Clients must ignore unknown future values.
```

**Bad**

```yaml
status:
  type: string  # unrestricted; typos become production data
```

### Discriminated union

**Good**

```yaml
PaymentMethod:
  oneOf:
    - $ref: "#/components/schemas/CardPayment"
    - $ref: "#/components/schemas/BankTransfer"
  discriminator:
    propertyName: type
    mapping:
      card: "#/components/schemas/CardPayment"
      bank_transfer: "#/components/schemas/BankTransfer"
```

**Bad**

```yaml
# Single object with every field optional and no discriminator —
# invalid combinations (card + iban) still validate
```

### Runtime alignment sketch

**Good**

```ts
// Schema and validator share the same required set and closed object
const CreateOrderSchema = z.object({
  customerId: z.string().uuid(),
  items: z.array(OrderItemSchema).min(1).max(100),
  note: z.string().max(500).optional(),
}).strict();
```

**Bad**

```ts
// Docs say customerId required; handler accepts anything
function createOrder(body: any) {
  return repo.save(body);
}
```

### Open map for free-form metadata (when intentional)

**Good**

```yaml
metadata:
  type: object
  description: Client key/value bag; keys max 40 chars; values strings max 500.
  maxProperties: 50
  additionalProperties:
    type: string
    maxLength: 500
```

**Bad**

```yaml
metadata:
  type: object  # unbounded depth/size; easy DoS and schema-less drift
```

## Anti-Patterns

- Publishing OpenAPI that does not match runtime validation (docs lie)
- `additionalProperties` left default/`true` on strict public APIs with no policy
- Breaking field renames under the same API version
- Using `number` for currency; timezone-naive timestamps without policy
- Giant god-schemas shared for create/update/response with contradictory `required`
- Copy-pasted schemas instead of `$ref` (silent drift)
- `format: email` (or similar) in docs only, never enforced — or enforced only
  in one layer with different rules in another
- Allowing unlimited arrays/strings on public endpoints
- Treating schema validity as authorization (`id` in body passes schema ≠ may access)

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| JSON Schema / OpenAPI model design, validation rules, `$ref` layout | **This skill** | — |
| Operation summaries, descriptions, example prose | `api-documentation-writing` | this for schema correctness |
| URL/header version strategy, sunset, breaking policy | `api-versioning-design` | this for per-version schemas |
| SQL naming, query format, migration file readability | `sql-style-conventions` | this if JSON columns/config schemas |
| Expand/contract, locking, zero-downtime DB changes | `database-migration-safety` | this if payload shape tracks columns |
| Implementing validators, handlers, tests | `code-quality-standards` | **always apply** on code changes |
| Security assessment of APIs | domain vuln skill / `api-recon-and-docs` | not schema design |

### Routing to shared skills

- **`api-documentation-writing`:** field/operation prose, examples, error narrative;
  keep this skill primary for types, constraints, and composition
- **`sql-style-conventions`:** relational naming and SQL style when schemas mirror
  tables; do not put SQL style rules in JSON Schema files
- **`code-quality-standards`:** always apply when implementing or reviewing code:
  - Validate untrusted JSON at the boundary; typed internals after parse
  - Stable error mapping; no swallowed validation failures
  - Caps on size/depth; no secret logging of raw bodies
  - Tests for accept/reject cases that encode the contract
  - Avoid `any`/unchecked maps where a schema exists

This skill specializes **data-contract shape and validation design**. It does not
replace SQL migration safety, API prose quality, or full implementation standards.

## Checklist

- [ ] Repo dialect (JSON Schema draft / OpenAPI 3.0|3.1), source of truth, and validator tooling identified
- [ ] Neighboring schemas’ naming, nullability, and openness policy matched
- [ ] Types, formats, enums, and bounds match real producer/consumer behavior
- [ ] `required` / optional / null semantics explicit and consistent (esp. PATCH)
- [ ] `additionalProperties` / maps intentional; public inputs size-capped
- [ ] Shared models via `$ref`; request vs response shapes split when needed
- [ ] Polymorphism uses discriminator (or documented alternative)
- [ ] Money, time, IDs, and units unambiguous
- [ ] OpenAPI components aligned with runtime validators (no known drift)
- [ ] Additive evolution preferred; breaking changes versioned or approved
- [ ] Positive and negative fixtures validate as expected
- [ ] Spectral/AJV/repo schema checks run when available
- [ ] Prose/examples handed to or checked against `api-documentation-writing` quality bar
- [ ] `code-quality-standards` applied for boundary validation, errors, tests, and security hygiene
