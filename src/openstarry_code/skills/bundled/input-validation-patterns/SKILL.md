---
name: input-validation-patterns
description: >
  Secure input validation at trust boundaries: allowlists, schemas, type and
  range checks, normalization, and fail-closed parsing. Use when input
  validation, 输入校验, request validation, allowlist, schema validation,
  boundary checks, sanitize vs validate, or hardening untrusted parameters,
  headers, files, and event payloads. Complements code-quality-standards and
  json-schema-design; not a substitute for injection-class testing skills.
---

# Input Validation Patterns

Validate **untrusted data at trust boundaries** before it drives control flow,
queries, storage, or downstream calls. Prefer **allowlists and schemas** over
ad-hoc reject lists. Repository validators, OpenAPI/JSON Schema contracts, and
framework middleware **outrank** generic defaults in this skill.

This skill is **defensive secure coding** for systems you own or are authorized
to harden. It does not teach bypassing third-party validation or weaponizing
injection against systems outside scope.

## Use When

- Designing or reviewing **request/query/path/header/cookie/body** validation
- Choosing **allowlist vs denylist**, enums, formats, and size/depth caps
- Placing validation at **API gateways, controllers, workers, CLI, or file parsers**
- Aligning runtime checks with **OpenAPI / JSON Schema / Protobuf / form DTOs**
- Hardening **file upload metadata**, multiparts, webhooks, or queue/event payloads
- Fixing bugs where invalid or hostile input caused crashes, logic flaws, or injection
- User mentions: input validation, **输入校验**, request validation, allowlist,
  白名单校验, schema validation, boundary validation, “sanitize input”,
  Pydantic/Zod/Joi/class-validator, Bean Validation, `additionalProperties`

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Designing JSON Schema / OpenAPI model shapes | `json-schema-design` |
| Context-specific **output** encoding (HTML/SQL/URL) | `output-encoding-patterns` |
| General reliability, errors, tests, security baseline | `code-quality-standards` |
| Unknown injection class in an assessment | `injection-checking` |
| SQLi / XSS / SSRF / CMDi / path traversal testing | matching class skill |
| Secrets in env/config (not request body validation) | `secrets-management-hygiene` |
| Mass assignment / over-posting as authz issue | `mass-assignment` |

## Repo Config First

Repo contracts, middleware, and neighboring validators **outrank** this skill.

1. **Source of truth:** OpenAPI/JSON Schema, Protobuf, GraphQL schema, or
   code-first DTOs — edit the authoritative layer; do not invent a parallel rule set
2. **Validator stack:** Zod, AJV, Joi, Yup, Pydantic, class-validator, Bean
   Validation, FluentValidation, serde with deny-unknown — match project options
   (strict objects, coerce on/off, format assertion)
3. **Framework middleware:** Nest pipes, Django/DRF serializers, Spring
   `@Valid`, ASP.NET model binding + data annotations, Express/Fastify schema
   plugins, API gateway request validators — extend existing pipeline order
4. **Error envelope:** existing 400/422 shape, field-path conventions, i18n of
   validation messages — reuse, do not invent a second client contract
5. **Size limits:** reverse-proxy body limits, framework max body, multipart
   caps, and gateway policies already deployed
6. **Authn/authz placement:** validation does **not** replace authorization;
   follow how the repo orders parse → authenticate → authorize → handler
7. **Neighboring handlers:** copy 2–3 mature endpoints’ parse, reject, and
   log patterns before adding a one-off style
8. **Shared libs:** monorepo validation packages, branded ID types, common
   pagination/filter schemas — reuse them

**Precedence:** If repo rules conflict with defaults below, follow the repo.
Surface conflicts that accept unbounded input, skip validation on some routes,
or document stricter rules than runtime enforces.

## Core Principles

| Principle | Practice |
| --- | --- |
| Boundary first | Validate at every trust boundary (HTTP edge, worker entry, admin import, webhook) |
| Allowlist over denylist | Accept known-good types, enums, patterns, and shapes; do not chase every bad string |
| Schema as contract | Types, requiredness, bounds, and openness match published API/events |
| Fail closed | Reject invalid input; never “best effort” into privileged paths |
| Normalize then validate | Canonicalize encoding/path/Unicode **before** checks when the domain requires it |
| Validate ≠ authorize | Schema-valid `resourceId` does not mean the caller may access it |
| Validate ≠ encode | Validation reduces bad shapes; **output encoding** and parameterized APIs stop injection |
| Bound resources | Cap length, count, depth, and upload size to resist DoS |
| Single parse | Parse once to a typed model; avoid re-parsing raw strings with different rules later |
| Preserve intent | Prefer structured fields over free-text when the domain is structured |

## Workflow

1. **Map trust boundaries and data sources.**
   - HTTP path/query/header/cookie/body, multipart files, gRPC metadata, WS messages
   - Queue/event payloads, cron args, CLI flags, admin CSV/JSON imports
   - Third-party webhooks and callbacks (verify signature **and** schema)
2. **Inventory fields and sensitivity.**
   - IDs, enums, money, dates, emails, URLs, free text, nested objects, files
   - Which fields affect control flow, queries, redirects, shell, or HTML
3. **Choose representation and schema.**
   - Prefer existing DTO/schema modules; align with `json-schema-design` for contracts
   - Closed objects by default on public write APIs (`additionalProperties: false` / `.strict()`)
   - Separate create/update/query schemas when required sets differ
4. **Define allowlists and constraints.**
   - Types and formats (UUID, enum status, integer ranges, date-time policy)
   - Length/min/max, array `maxItems`, object depth, regex only for true invariants
   - URL/redirect allowlists (scheme + host) for any open-redirect-sensitive field
5. **Place validation in the pipeline.**
   - Parse and validate **before** business logic and persistence
   - Keep gateway and app rules non-conflicting; prefer one SSOT where possible
   - After success, pass **typed** values only (no raw `any` / untyped maps downstream)
6. **Handle failure safely.**
   - Stable 400/422 (or framework equivalent); field paths clients can fix
   - Do not leak stack traces, SQL, or internal schema dumps
   - Log enough for ops (route, error codes) without full sensitive payloads
7. **Authorize after identity is known.**
   - Ownership/tenant checks on IDs (`idor-broken-object-authorization` mindset in product code)
8. **Verify.**
   - Positive and negative tests at the boundary (`code-quality-standards`)
   - Fuzz or property tests for parsers when risk warrants
   - Confirm body/proxy limits match application caps

## Validation Patterns

### Allowlists (preferred)

| Target | Allowlist approach |
| --- | --- |
| Enums / status | Closed set in schema; reject unknown values (or document “ignore unknown” only for **read** evolution) |
| IDs | Format + existence/authz checks; prefer opaque server IDs over user-controlled paths |
| Sort/filter fields | Explicit map of allowed column/API names → query builder; never splice raw query keys |
| Content types | Explicit MIME allowlist for uploads; verify content, not only extension |
| Redirects / callbacks | Scheme `https` (and approved customs) + host allowlist |
| Locales / currencies | ISO sets the product supports |
| Feature flags / ops actions | Enum of known actions; deny by default |

### Schemas and types

- Use declarative schemas (Zod/JSON Schema/Pydantic/etc.) as the first line
- Prefer **decoding to typed models** over manual `if` chains scattered in handlers
- Optional vs null: make PATCH semantics explicit (omit vs null clear)
- Coercion: disable silent type coercion on public APIs unless the repo standard requires it (e.g. query strings) and then coerce **once** at the edge
- Unknown keys: strip only when policy allows and clients never rely on them; otherwise reject

### Normalization (when needed)

Apply **before** equality or path checks:

| Domain | Normalize |
| --- | --- |
| Unicode | NFKC/NFC per policy; beware lookalike IDs in security-sensitive comparisons |
| Paths | Resolve/`pathlib` safe join; reject `..` and absolute escapes (`path-traversal-lfi` class) |
| Emails | Framework-proven parsers; do not invent partial RFC regexes for auth identity alone |
| Hostnames | Lowercase ASCII DNS labels; IDN policy explicit |
| JSON numbers | Integers for money minor units; reject NaN/Infinity if language allows |

Do **not** “normalize away” characters as a substitute for parameterized queries or HTML encoding.

### What validation does **not** replace

| Control | Still required |
| --- | --- |
| SQL / NoSQL safety | Parameterized queries / safe builders (`output-encoding-patterns`, `sqli-sql-injection` mindset) |
| HTML / JS safety | Context encoding / safe templates (`output-encoding-patterns`, XSS skill for tests) |
| Command execution | Avoid shell; argv arrays; allowlisted binaries |
| SSRF | URL allowlists + block private ranges at request time |
| Authz | Server-side checks on every object reference |
| Business rules | “Quantity ≥ 0” ≠ “user may buy this SKU at this price” |

## Good / Bad Examples

### Schema at the HTTP boundary

**Good**

```ts
// Strict body; allowlisted fields only; bounds on free text
const CreateComment = z.object({
  postId: z.string().uuid(),
  body: z.string().trim().min(1).max(2000),
  visibility: z.enum(["public", "private"]),
}).strict();

app.post("/comments", async (req, res) => {
  const parsed = CreateComment.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ error: "validation_failed", details: parsed.error.flatten() });
  }
  // use parsed.data only
});
```

**Bad**

```ts
app.post("/comments", async (req, res) => {
  const { postId, body } = req.body; // any shape, any size
  await db.query(`INSERT INTO comments … '${body}'`); // validation missing + injection
});
```

### Allowlisted sort field

**Good**

```ts
const SORT_COLUMNS = { createdAt: "created_at", title: "title" } as const;

function listPosts(sort: string) {
  const column = SORT_COLUMNS[sort as keyof typeof SORT_COLUMNS];
  if (!column) throw new ValidationError("invalid_sort");
  return db.posts.orderBy(column); // identifier from map, not user string
}
```

**Bad**

```ts
// User-controlled identifier → SQLi / unexpected column access
return db.raw(`SELECT * FROM posts ORDER BY ${req.query.sort}`);
```

### Path / file parameter

**Good**

```python
from pathlib import PurePosixPath

ALLOWED_ROOT = Path("/var/app/exports").resolve()

def export_path(name: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", name):
        raise ValidationError("invalid_name")
    candidate = (ALLOWED_ROOT / name).resolve()
    if not candidate.is_relative_to(ALLOWED_ROOT):
        raise ValidationError("invalid_name")
    return candidate
```

**Bad**

```python
def export_path(name: str) -> Path:
    return Path("/var/app/exports") / name  # ../../etc/passwd
```

### Webhook: verify then validate

**Good**

```text
1) Verify signature/timestamp (authn of sender)
2) Parse JSON with size limit
3) Schema-validate event type + payload
4) Idempotency key allowlisted format
5) Business handler
```

**Bad**

```text
Parse body → business handler → optional signature check later
```

### Query string enums and caps

**Good**

```ts
const ListQuery = z.object({
  page: z.coerce.number().int().min(1).max(10_000).default(1),
  pageSize: z.coerce.number().int().min(1).max(100).default(20),
  status: z.enum(["open", "closed"]).optional(),
});
```

**Bad**

```ts
const pageSize = Number(req.query.pageSize); // NaN, 1e9, negative
```

### Free text vs structured input

**Good** — structured filters:

```json
{ "status": "open", "assigneeId": "uuid…", "q": "optional free text ≤ 200" }
```

**Bad** — single blob that encodes logic:

```json
{ "filter": "status=open; DROP TABLE …" }
```

## Anti-Patterns

- Denylist-only filters (`remove <script>`, strip `../`) as the main control
- Validating only in the UI or client SDK
- Trusting `Content-Type` or file extension without size/type policy
- Accepting unbounded JSON depth/arrays/strings on public endpoints
- Using regexes that are catastrophic (nested quantifiers) or incomplete RFC clones for security decisions
- Coercing types differently in gateway vs app (docs say string, app casts quietly)
- Treating schema validation as authorization or multi-tenant isolation
- Logging full bodies that may contain passwords, tokens, or PII
- “Sanitizing” HTML input with regex instead of a vetted policy + encode on output
- Catch-and-ignore validation errors; defaulting invalid enums to a privileged value
- Building SQL/HTML/shell with validated-but-still-concatenated strings

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Input validation design, allowlists, boundary schemas, 输入校验 | **This skill** | — |
| JSON Schema / OpenAPI field types, `$ref`, openness | `json-schema-design` | this for placement and allowlist policy |
| HTML/JS/SQL/URL **output** encoding | `output-encoding-patterns` | this for inbound shape checks |
| Implementing validators, errors, tests | `code-quality-standards` | **always apply** on code changes |
| Injection class unknown (assessment) | `injection-checking` | this when **fixing** validation |
| Specific injection testing (SQLi, XSS, …) | matching vuln skill | this for defensive patterns |
| Mass assignment / extra fields privilege | `mass-assignment` | this for closed schemas |
| Upload content policy | `upload-insecure-files` (assess) / this (validate metadata & bounds) | |
| Error message wording for users | `error-message-ux-writing` | this for which failures exist |

### Routing to `code-quality-standards`

Keep **this skill primary** for *what* and *where* to validate. Always apply
**`code-quality-standards`** when implementing or reviewing validation code:

- Clear APIs: parse functions return typed results or Result/Either; avoid `any`
- Fail closed; no swallowed validation errors on security-sensitive paths
- Resource limits (body size, allocations) and timeouts around parsers
- Stable error mapping; no secret or stack leakage in responses or logs
- Tests: accept fixtures, reject cases (unknown keys, oversize, bad enums, path escape)
- Do not disable schema strictness or linters to “ship faster” without tracked exception
- Keep validation pure and side-effect free when possible (authz stays separate)

### Routing to `json-schema-design`

Use **`json-schema-design`** when the work is primarily **contract shape**
(OpenAPI components, `$ref`, nullability, evolution). Use **this skill** for
**boundary placement**, allowlists for control-plane fields (sort, redirect,
file names), normalization order, and how validation interacts with authz and
encoding.

### Routing to `output-encoding-patterns`

Validation reduces unexpected shapes; it does **not** make string concatenation
into SQL or HTML safe. Pair both skills on features that accept text and render
or query with it.

## Checklist

- [ ] Repo validator stack, schema SSOT, error envelope, and body size limits identified
- [ ] All trust boundaries listed (HTTP, workers, webhooks, imports, CLI)
- [ ] Schemas/DTOs cover each public input; strict/closed objects where policy requires
- [ ] Allowlists for enums, sort/filter keys, redirects, content types, ops actions
- [ ] Length, count, depth, and upload size caps set and aligned with proxy limits
- [ ] Normalization defined where needed (path, Unicode, host) **before** security checks
- [ ] Fail closed with stable 400/422 (or equivalent); no stack/SQL leakage
- [ ] Typed models only past the boundary; no raw maps driving queries/templates
- [ ] Authz checks on object IDs after authentication (not assumed from schema validity)
- [ ] Webhooks: signature verified and payload schema-validated
- [ ] Positive + negative boundary tests; oversize and unknown-field cases included
- [ ] No denylist-only “sanitizer” as the primary control for injection classes
- [ ] Output encoding / parameterized APIs planned for sinks (`output-encoding-patterns`)
- [ ] `json-schema-design` used when publishing or evolving formal contracts
- [ ] `code-quality-standards` applied for implementation quality, errors, and tests

## Rules

- Untrusted input is hostile until validated; trusted internal types stay internal.
- Allowlist what you accept; bound what you cannot fully enumerate (free text).
- One parse, one schema, one typed value — then business logic.
- Validation is necessary and not sufficient: encode on output, parameterize queries, authorize always.
- Repo contracts and middleware win; this skill fills gaps and review discipline.
- Defensive engineering and authorized hardening only.
---

# Note

This skill owns **inbound validation and allowlist discipline** at trust
boundaries. Pair with `json-schema-design` for formal contracts,
`output-encoding-patterns` for sink-safe rendering and query construction, and
`code-quality-standards` on every implementation change.
