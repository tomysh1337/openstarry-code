---
name: api-documentation-writing
description: >
  Write high-quality OpenAPI/Swagger operation descriptions, parameter and
  schema docs, error contracts, and request/response examples. Use when API
  docs, OpenAPI description writing, Swagger annotations, 写接口文档,
  endpoint documentation, operation summary/description, or improving
  example quality for REST/HTTP APIs. Not for offensive API recon.
---

# API Documentation Writing

Produce OpenAPI/Swagger (and equivalent) documentation that developers can
implement against without reverse-engineering the server. Prefer the repo’s
existing spec style, codegen pipeline, and portal over inventing a second
house format.

## Use When

- Authoring or rewriting OpenAPI 3.x / Swagger 2.x `summary`, `description`,
  parameters, request bodies, responses, and examples
- Improving endpoint docs quality: auth, pagination, idempotency, error codes
- Adding copy-pasteable request/response samples that match real schemas
- Annotating code-first APIs (Springdoc, NestJS `@Api*`, FastAPI, tsoa, etc.)
- User mentions: API docs, OpenAPI description writing, Swagger, 写接口文档,
  接口说明, operation docs, example payloads

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Discovering hidden/live APIs in assessments | `api-recon-and-docs` |
| Markdown prose form only | `markdown-docs-style` |
| Code docstrings / TSDoc | `docstring-and-typedoc` |
| Project README / CONTRIBUTING | `readme-and-contributing-docs` |

## Repo Config First

Repo config and neighboring operations **outrank** this skill’s defaults.

1. **Spec location:** `openapi.yaml` / `openapi.json`, `swagger.*`, `docs/api/`,
   `api/openapi/`, monorepo package that owns the public contract
2. **Generation pipeline:** code-first (annotations → build) vs design-first
   (YAML → codegen). Never invent fields the generator will overwrite without
   updating the source of truth
3. **Tooling:** Spectral (`.spectral.yaml`), Redocly, Stoplight, Swagger UI /
   Redoc / Scalar portal config, Postman collection export rules
4. **Conventions:** `operationId` naming, tag taxonomy, error envelope schema,
   pagination shape, auth scheme names (`bearerAuth`, `apiKey`, OAuth scopes)
5. **Neighboring ops:** copy 2–3 well-documented endpoints in the same API for
   summary length, description structure, example style, and `$ref` patterns
6. **Product language:** EN vs 中文 for public descriptions; keep wire field
   names and HTTP tokens in their canonical (usually English) form

**Precedence:** If repo rules conflict with defaults below, follow the repo.
Surface conflicts that leave auth, status codes, or examples wrong relative
to the live contract.

## Workflow

1. **Identify source of truth.** Design-first YAML/JSON, code annotations, or
   a portal that merges both. Edit only the authoritative layer; regenerate
   derived artifacts.
2. **Inventory the operation.** Method, path, auth, path/query/header/cookie
   params, body content types, success and error statuses, side effects
   (create, charge, send email), idempotency keys, rate limits if published.
3. **Write `summary` then `description`.**
   - `summary`: short (≈5–15 words), imperative or noun phrase, unique among
     siblings on the same tag
   - `description`: audience-facing contract — when to call, preconditions,
     ownership/tenant rules, pagination, eventual consistency, deprecation
4. **Document every input.** Required vs optional; defaults; formats
   (`uuid`, `date-time`, `email`); units; allowed enums with meanings; max
   length/range when enforced. Prefer schema `description` over burying
   meaning only in prose.
5. **Document every response class.** At least: success (and 201/202/204 when
   used), validation failure (400/422), authn (401), authz (403), not found
   (404 if applicable), conflict (409), rate limit (429) when real. Reference
   a shared error schema when the API has one.
6. **Add examples that compile against the schema.** Prefer `examples` (named)
   over a single misleading `example`. Cover happy path + one realistic
   error. Use placeholders (`"tok_live_…"` → `"sk_test_xxx"`) — never live
   secrets, real PII, or production host-only paths unless redacted.
7. **Cross-link.** Tags, related operations (`See also: createOrder`), shared
   components (`#/components/schemas/Order`). Mark `deprecated: true` with
   replacement operation and sunset notes.
8. **Verify.** Spectral/Redocly lint; portal render; optional contract tests
   or mock server. Diff descriptions against handlers/tests so docs do not
   invent behavior.

## Description Quality Bar

A finished operation doc answers without reading source:

- Who may call it (roles, scopes, API keys) and on which resources
- What must already exist (order paid, user verified)
- What changes as a side effect
- What success looks like (status + body shape)
- How failures are distinguished (status + error `code` / field errors)
- Whether retries are safe (idempotency key header name if any)

## Style Rules (defaults when repo is silent)

### Operation metadata

- Unique `operationId` in stable camelCase or the repo’s generator style
- Tags map to product domains (`Orders`, `Billing`), not HTTP verbs
- Prefer one resource concern per operation; document bulk variants explicitly

### Prose

- Lead with the outcome, then constraints
- Use “returns”, “creates”, “marks as canceled” — not “this endpoint is used to”
- Document **observable** behavior only; no implementation tours (“hits Redis then…”) unless operators need it in a separate runbook
- Keep Chinese/English consistent with portal language policy; do not machine-translate field semantics without a human pass

### Schemas

- Every non-obvious property has `description`; units in the description or name
- `readOnly` / `writeOnly` set when applicable; discriminators documented
- Nullable vs optional: match server truth; do not mark required fields optional to “simplify”
- Arrays: item constraints and max items when enforced

### Examples

- Valid against the schema (types, required fields, enums)
- Minimal but complete enough to copy into curl/Postman
- Show auth header pattern once in portal intro or securitySchemes; per-op examples may omit secrets and say “requires `Authorization: Bearer`”
- Error examples include the standard envelope (`code`, `message`, `details[]`)

## Good / Bad Examples

### Summary and description

**Good**

```yaml
summary: Cancel an open order
description: |
  Cancels an order in `open` or `pending_payment` status for the caller’s tenant.
  Idempotent: repeating the call on an already-canceled order returns `200` with
  the current order. Orders in `shipped` or `completed` return `409`.
  Requires scope `orders:write`.
```

**Bad**

```yaml
summary: Order API
description: This endpoint is used to cancel orders and stuff. Internal only maybe.
```

### Parameter documentation

**Good**

```yaml
parameters:
  - name: idempotency-key
    in: header
    required: false
    description: >
      Client-generated key (UUID recommended). Retries with the same key and
      body return the original result for 24 hours.
    schema:
      type: string
      format: uuid
  - name: limit
    in: query
    description: Page size (1–100). Default 20.
    schema:
      type: integer
      minimum: 1
      maximum: 100
      default: 20
```

**Bad**

```yaml
parameters:
  - name: limit
    in: query
    description: limit
    schema:
      type: string   # wrong type; no bounds; no default
```

### Response and error contract

**Good**

```yaml
responses:
  "200":
    description: Order canceled (or already canceled).
    content:
      application/json:
        schema:
          $ref: "#/components/schemas/Order"
        examples:
          canceled:
            value:
              id: "ord_01HZX…"
              status: canceled
  "409":
    description: Order is not cancelable in its current status.
    content:
      application/json:
        schema:
          $ref: "#/components/schemas/Error"
        example:
          code: order_not_cancelable
          message: Shipped orders cannot be canceled.
          details: []
```

**Bad**

```yaml
responses:
  "200":
    description: OK
  "500":
    description: Error
# Missing 401/403/404/409; no schema; no example
```

### Annotation (code-first sketch)

**Good** — documents contract, not implementation:

```ts
/**
 * Cancel an open order for the current tenant.
 * @remarks Idempotent on already-canceled orders. Scope: `orders:write`.
 */
@ApiOperation({ summary: "Cancel an open order" })
@ApiResponse({ status: 409, description: "Order not cancelable", type: ErrorDto })
```

**Bad** — vague and secret-leaky examples:

```ts
@ApiOperation({ summary: "do order" })
// example Authorization: Bearer eyJhbGciOiJIUzI1NiIs…real token…
```

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| OpenAPI/Swagger descriptions, examples, endpoint doc quality | **This skill** | — |
| Markdown rendering / fences / tables in docs site | `markdown-docs-style` | this skill for API content |
| README quickstart that *links* to API portal | `readme-and-contributing-docs` | this skill for OpenAPI body |
| Code docstrings on handlers (not HTTP contract) | `docstring-and-typedoc` | — |
| Security assessment / shadow API discovery | `api-recon-and-docs` | not a writing skill |
| Auth scheme correctness in product code | domain + `code-quality-standards` | keep docs aligned |
| GraphQL schema descriptions | this skill’s principles | adapt to SDL/`@doc`; not OpenAPI-only |

## Checklist

- [ ] Repo OpenAPI source of truth, lint config, and portal conventions identified
- [ ] Neighboring operations’ style matched (tags, summary length, error envelope)
- [ ] `summary` + `description` state purpose, preconditions, side effects, auth
- [ ] All parameters documented: required/optional, defaults, formats, bounds
- [ ] Success and realistic error responses documented with schemas
- [ ] Examples validate against schemas; placeholders only (no live secrets/PII)
- [ ] `operationId`, tags, deprecation/replacement noted where needed
- [ ] Shared components reused via `$ref` instead of copy-paste drift
- [ ] Descriptions match handlers/tests (no invented status codes or fields)
- [ ] Spectral/Redocly/portal build run when available
- [ ] Language policy respected (EN/中文); wire names stay canonical
