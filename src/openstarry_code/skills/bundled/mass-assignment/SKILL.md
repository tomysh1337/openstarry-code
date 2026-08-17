---
name: mass-assignment
description: >
  Find and safely prove mass assignment / over-posting when APIs or frameworks
  bind client JSON or form fields onto domain objects, including hidden role,
  ownership, price, and flag fields. Use when create/update endpoints accept
  broad DTOs, Rails/Laravel/Spring/ASP.NET model binding, or GraphQL input
  types during authorized assessments.
---

# Mass Assignment / Over-Posting

## Scope And Authorization

- Authorized targets only: owned apps, labs, CTFs, or written engagement scope.
- Prefer non-destructive proofs: toggle a **lab-safe** flag, role on a throwaway account, or ownership of objects you control.
- Do not promote yourself to production admin, alter live pricing catalogs, or reassign other tenants’ data without explicit SOW.
- Keep request/response evidence redacted (tokens, PII, payment fields).
- Pair privilege changes with dual-account checks so impact is reproducible and reversible.

## When To Use

- Create/update/register/profile/checkout endpoints that accept large JSON bodies or form posts.
- Client sends fields never shown in UI: `role`, `isAdmin`, `verified`, `balance`, `price`, `userId`, `orgId`, `permissions`, `status`.
- Stack clues: Rails strong params gaps, Laravel `$fillable`/`$guarded`, Spring `@ModelAttribute` / Jackson on entities, ASP.NET model binding, Django `ModelForm` with extra fields, Nest/TypeORM entities exposed directly.
- After `api-recon-and-docs` maps schemas and request samples show server entities echoing extra properties.
- Overlaps with IDOR when client supplies `ownerId`/`userId` — still use this skill for **bindable field** methodology; use `idor-broken-object-authorization` for pure ID swap without extra fields.

## Workflow

### 1. Build a bindable-field inventory

1. Capture legitimate create/update requests (UI + raw API).
2. Diff **UI fields** vs **API fields** vs **response/schema fields** (OpenAPI, GraphQL input types, mobile clients often send more).
3. List sensitive server-side properties from responses, admin UIs, or code: roles, flags, balances, limits, tenant keys, workflow state, audit fields (`createdBy`).
4. Note framework binding mode: whole-entity JSON deserialize vs explicit DTO vs allowlist params.

### 2. Baseline dual-session fixtures

1. Account A (low privilege) and Account B (peer); optional admin only if provided in lab.
2. Record baseline object after clean create/update (status, role, owner, price).
3. Hold separate tokens/sessions; do not mix cookies when comparing (`api-auth-and-jwt-abuse` if token issues appear).

### 3. Over-post probes (one field family at a time)

Replay create/update with **extra** properties. Common high-yield families:

| Family | Example keys | Expected safe behavior |
| --- | --- | --- |
| Privilege | `role`, `roles[]`, `isAdmin`, `is_staff`, `permission`, `authorities` | Ignored; remains user |
| Ownership | `userId`, `ownerId`, `accountId`, `orgId`, `tenantId` | Bound to authenticated principal |
| Commerce | `price`, `total`, `discount`, `currency`, `paid`, `tax` | Server recomputes |
| Workflow | `status`, `state`, `approved`, `verified`, `emailConfirmed` | Server-side transitions only |
| Quotas | `credits`, `balance`, `quota`, `plan`, `tier` | Server assigns |
| Nested | `user.role`, `profile.permissions`, `meta.isAdmin` | Nested allowlist |

Techniques:

1. **JSON add:** copy body, append `"isAdmin": true` / `"role":"admin"`.
2. **Form/query twin:** `role=admin` if only JSON was tested (or reverse).
3. **Array/object variants:** `"roles":["admin"]`, `"roles":"admin"`, nested maps.
4. **Alias casing:** `IsAdmin`, `is_admin`, `ROLE` if binder is case-insensitive.
5. **Update vs create:** mass assignment often fixed on register but open on `PATCH /users/me`.
6. **Partial update:** send only the sensitive field on PATCH/MERGE endpoints.
7. **GraphQL:** extra fields on input objects; mutations that take whole `UserInput`.
8. **Multipart:** hidden form fields plus file upload metadata.

### 4. Confirm impact (status + body + side effect)

Require proof beyond “request accepted”:

1. **Read-back:** GET the resource or `/me` — did `role`/`flags` stick?
2. **Capability check:** call an admin-only or owner-only endpoint with the same session.
3. **Horizontal ownership:** set `userId`/`ownerId` to B; as A, confirm access or listing changes → document with `idor-broken-object-authorization` evidence pattern.
4. **Commerce:** if price accepted client-side, verify order total in payment/summary **on lab data only**.
5. Negative control: unknown field `"zzMassAssign":1` — if echoed into storage, binder is wide open even when sensitive names are blocked.

### 5. Framework-specific notes (review hints)

| Stack | Risk pattern | Hardening direction |
| --- | --- | --- |
| Rails | `params.permit!` or missing strong params | Explicit `permit(:name, :email)` only |
| Laravel | `$guarded = []` or broad `$fillable` | Narrow fillable; separate admin FormRequests |
| Spring | Controller binds `@RequestBody Entity` | DTO + MapStruct; never expose JPA entity |
| ASP.NET | Entity in action args / over-posting | ViewModel/DTO; `[Bind]` include lists |
| Django | `ModelForm` without field limit | Declare `fields = (...)` explicitly |
| Node | `Object.assign(user, req.body)` / spread | Pick allowlisted keys (Zod/JOI strip unknown) |
| GraphQL | Input type mirrors DB model | Separate input types; server sets owner/role |

White-box: search for bulk assign, `permit!`, `$fillable`, `@JsonIgnore` gaps, `UpdateModel` without property deny-lists.

### 6. Filters, denylists, and weak defenses

- Denylist of `role` only — try `roles`, nested paths, `_role`, `RoleId`.
- Client-side form removal without server allowlist — always retest raw API.
- “Read-only” response fields still bindable on write — trust write path, not GET shape.
- Admin UI and user UI sharing one update handler — different authZ still needs field-level policy.

### 7. Remediation verification

- Server allowlists writable fields per endpoint and role; default deny.
- Sensitive transitions (role, verify, price, owner) only via privileged services with explicit authZ.
- Use dedicated request DTOs, not persistence entities, at the HTTP boundary.
- Add tests: over-post `isAdmin`/`ownerId` must not persist for normal users (`code-quality-standards`).
- Retest original payloads after fix; confirm IDOR ownership still enforced.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Extra bindable fields / over-posting | `mass-assignment` (this) | — |
| Object ID swap without extra fields | `idor-broken-object-authorization` | this if ownership fields posted |
| Injection in a bound field value | `injection-checking` → class skill | this for binder surface |
| JWT/session privilege in token claims only | `api-auth-and-jwt-abuse` | this if DB role also client-set |
| API map / schema inventory | `api-recon-and-docs` | this for update bodies |
| Secure binding implementation | `code-quality-standards` | this |

## Output Checklist

- [ ] Endpoint, method, content-type, account role
- [ ] Field inventory: UI vs sent vs sensitive candidates
- [ ] Payload that assigned forbidden field (redacted)
- [ ] Read-back and capability proof (before/after)
- [ ] Ownership/price/role impact class
- [ ] Framework hypothesis and root cause (wide bind)
- [ ] Fix guidance (allowlist DTO) and retest result

## Rules

- Never self-elevate on production without explicit authorization and a rollback plan.
- One sensitive field family per proof for clean evidence; then expand coverage.
- Authentication ≠ field-level authorization: valid user tokens still fail closed on privileged attributes.
- Do not automate mass reassignment of other customers’ records.
- Prefer reversible lab accounts; document restore steps when state changes.
- Do not call mass assignment “IDOR only” or “JWT only” when the root cause is unrestricted model binding — cite both skills if chained.
