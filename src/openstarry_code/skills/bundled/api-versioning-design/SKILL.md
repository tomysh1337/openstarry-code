---
name: api-versioning-design
description: >
  Design and evolve HTTP/RPC API versions: URL path vs header vs media-type
  versioning, compatibility rules, deprecation, sunset, and client migration.
  Use when API versioning, 接口版本, v1/v2 paths, API-Version header, breaking
  change policy, or deprecation timelines. Not for offensive API recon alone.
---

# API Versioning Design

Engineering design for **public and partner API contracts** over time: how
clients select a version, what counts as a breaking change, how to deprecate
safely, and how docs/gateways stay honest. Prefer the repo’s existing versioning
scheme; do not introduce a second strategy without an explicit migration plan.

## Use When

- Choosing or changing version strategy (URL path, query, header, media type)
- Adding `v2` endpoints, dual-running versions, or compatibility shims
- Classifying changes as breaking vs additive; planning rollouts
- Deprecation, `Sunset` / `Deprecation` headers, changelog communication
- Gateway, OpenAPI `servers`/path versioning, or SDK generation alignment
- User mentions: API versioning, 接口版本, breaking change, deprecate API,
  `API-Version`, `/v1/`, content negotiation versioning

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| OpenAPI prose quality, examples, error narrative | `api-documentation-writing` |
| Discovering shadow/live APIs in assessments | `api-recon-and-docs` |
| JWT/auth scheme design flaws (testing) | `api-auth-and-jwt-abuse` |
| Async handler races / cancel design | `async-concurrency-patterns` |
| Release notes packaging only | `changelog-and-release-notes` |

## Repo Config First

Repo config, gateway rules, and published contracts **outrank** this skill’s defaults.

1. **Existing strategy:** path (`/v1/...`), header (`API-Version`, `Accept-Version`),
   media type (`application/vnd.example.v2+json`), query (`?version=`), or
   date-based (Stripe-style) — **match it** unless the task is an explicit redesign
2. **Source of truth:** design-first OpenAPI vs code-first annotations; monorepo
   package that owns the public contract
3. **Gateway / edge:** API gateway route maps, ingress path rewrites, service mesh
   canaries, feature flags for version traffic split
4. **Compatibility docs:** ADR, `CONTRIBUTING`, partner API policy, SLA for
   deprecation windows
5. **SDK / clients:** generated clients, mobile app min versions, internal
   service stubs — who must move when a version is cut
6. **Auth and tenancy:** version-specific scopes, OAuth audience, or key
   product entitlements tied to a version
7. **Neighboring APIs:** copy mature public APIs in the same org for header
   names, error envelopes, and deprecation header style

**Precedence:** If repo rules conflict with defaults below, follow the repo.
Surface conflicts that would strand external clients or fork two incompatible
“current” contracts without a sunset plan.

## Workflow

1. **Inventory the contract surface.**
   - Resources, operations, auth, error envelope, pagination, idempotency keys
   - Current version identifier and how clients send it
   - Known consumers (1st party apps, partners, scripts) and their update cadence
2. **Classify the change.**
   - **Additive (usually non-breaking):** new optional field, new endpoint,
     new enum value only if clients ignore unknown values by policy
   - **Breaking:** removed/renamed field, type change, new required field,
     stricter validation, auth change, status/code meaning change, default change
     that alters behavior
   - When unsure, treat as breaking for external APIs
3. **Choose strategy only if greenfield or explicitly redesigning.**

   | Strategy | Pros | Cons | Typical use |
   | --- | --- | --- | --- |
   | URL path `/v1` | Very visible; easy routing/cache | URL sprawl; hard to version partial resources | Public REST |
   | Header `API-Version: 2024-01-15` | Clean URLs; fine-grained dates | Less cache-key obvious; harder to try in browser | Large public APIs |
   | Media type / `Accept` | True content negotiation | Client and CDN complexity | Hypermedia / strict REST |
   | Query `?api-version=` | Simple for some gateways | Caching and logging noise; easy to omit | Azure-style / internal |

   Prefer **one primary** selection mechanism. Document defaults when the version
   is omitted (pin to oldest supported vs latest — pick explicitly).

4. **Plan coexistence.**
   - Same service with versioned serializers/handlers, or separate deployables
   - Shared domain core; version adapters at the edge (anti-corruption)
   - Data model: additive columns + translation layers beat incompatible dual writes
5. **Define compatibility rules in writing.**
   - What clients may rely on (unknown JSON properties ignored? enum open/closed?)
   - Idempotency and error `code` stability across versions
   - Header and pagination invariants that never silently change
6. **Deprecation and sunset.**
   - Announce: docs, changelog, email/partner portal if contractual
   - Signal in-band: `Deprecation: true`, `Sunset: <http-date>`, `Link` to successor
   - Metrics: traffic per version; block sunset until under threshold or waiver
   - Keep behavior stable during deprecation — no “soft breaks” mid-window
7. **Ship docs and tests together.**
   - OpenAPI per version or tagged version; migration guide with field mapping
   - Contract tests for each supported version; consumer-driven checks where used
8. **Operate.**
   - Dashboards by version; alerts on deprecated version traffic spikes
   - Gateway rejects unknown versions with a clear, stable error code

## Compatibility Rules (defaults when repo is silent)

### Usually non-breaking

- Add optional request fields with safe defaults
- Add response fields (if clients ignore unknowns — document this requirement)
- Add new endpoints, new resources, new success/error **codes** that old clients never see
- Relax constraints (accept more input) without changing meaning of existing input
- Bug fixes that restore documented behavior

### Usually breaking

- Remove or rename fields, endpoints, or enum members clients use
- Change field type, units, timezone, or identifier format
- Make an optional field required; change default that affects results
- Change auth scheme, required scopes, or error envelope shape
- Reuse the same status/`code` for a different meaning
- Pagination cursor format change without dual support

### Version identity hygiene

- Prefer explicit, stable tokens: `v1`, `v2` or dates `2024-06-01`, not “latest” as the only pin
- Avoid **mutable** “current” without a pinned alias for serious integrators
- Do not mint a new major version for purely additive changes (version inflation)
- Do not overload one major version with incompatible silent behavior flags

## Deprecation Playbook

1. **Publish successor** (docs + sandbox) before marking old as deprecated.
2. **Mark deprecated** in OpenAPI (`deprecated: true`) and release notes.
3. **Emit deprecation headers** on old version responses when HTTP.
4. **Set a sunset date** aligned to policy (e.g. 6–12 months for public; shorter for internal with known clients).
5. **Monitor** usage; contact top remaining callers.
6. **Reject** after sunset with `410 Gone` or `400` + stable `code: api_version_retired` (match org standard).
7. **Remove** code paths only after traffic is gone and retention policy allows.

## Good / Bad Examples

### Path versioning (clear routing)

**Good**

```http
GET /v1/orders/ord_123 HTTP/1.1
Host: api.example.com
Authorization: Bearer …

GET /v2/orders/ord_123 HTTP/1.1
Host: api.example.com
Authorization: Bearer …
```

```yaml
# OpenAPI: separate path or server base for major versions
paths:
  /v1/orders/{id}:
    get:
      operationId: getOrderV1
  /v2/orders/{id}:
    get:
      operationId: getOrderV2
      description: >
        Successor to getOrderV1. Money fields are strings of decimal amounts;
        see migration guide.
```

**Bad** — ambiguous dual meaning on one URL without negotiation:

```http
GET /orders/ord_123 HTTP/1.1
# Sometimes returns v1 shape, sometimes v2 based on opaque feature flag
# Clients cannot pin or test reliably
```

### Header / date versioning

**Good**

```http
GET /orders/ord_123 HTTP/1.1
Host: api.example.com
API-Version: 2024-06-01
```

```text
# Document: omitted API-Version → 2023-01-15 (minimum supported), not "whatever is newest"
# Unknown version → 400 code: unsupported_api_version with list of supported versions
```

**Bad**

```http
# Silent upgrade: same header value, response shape changed in place last Tuesday
API-Version: 1
```

### Additive vs breaking change

**Good** — additive in v1; breaking change only in v2:

```json
// v1 response (old clients keep working)
{ "id": "ord_123", "totalCents": 1999 }

// v1 later (additive)
{ "id": "ord_123", "totalCents": 1999, "currency": "USD" }

// v2 breaking: intentional redesign
{ "id": "ord_123", "total": { "amount": "19.99", "currency": "USD" } }
```

**Bad** — breaking change in place:

```json
// Deployed to /v1 without new version: totalCents removed, total string added
{ "id": "ord_123", "total": "19.99" }
```

### Deprecation headers

**Good**

```http
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 01 Mar 2027 00:00:00 GMT
Link: <https://api.example.com/v2/orders/ord_123>; rel="successor-version"
Link: <https://docs.example.com/migrations/orders-v2>; rel="deprecation"
```

**Bad**

```http
HTTP/1.1 200 OK
X-Warning: this api dies soon maybe
# No date, no successor, no metrics-driven sunset
```

### Adapter at the edge

**Good** — domain core stable; version mappers at HTTP boundary:

```ts
// Sketch
if (apiVersion === "v1") return toOrderV1Dto(domainOrder);
if (apiVersion === "v2") return toOrderV2Dto(domainOrder);
```

**Bad** — fork entire domain and databases per version with divergent business rules
and no translation, so the same order id means different totals in v1 vs v2.

## Anti-Patterns

- Shipping breaking JSON changes under the same version identifier
- Defaulting omitted version to **latest** without documenting sticky client risk
- Supporting infinite versions forever with no sunset policy
- Mixing path **and** header as mandatory dual selectors without a clear winner
- Using “v1.1” path spam for every additive tweak (prefer additive evolution)
- Undocumented behavior flags that act as hidden versions
- Deprecating without a working successor or migration guide
- Changing error `code` strings that clients branch on without a major version
- Forgetting caches/CDNs: version must be part of cache key when responses differ

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Version strategy, breaking-change policy, deprecation/sunset | **This skill** | — |
| OpenAPI descriptions, examples, operation prose | `api-documentation-writing` | this for version/deprecation metadata |
| Changelog / release announcement packaging | `changelog-and-release-notes` | this for sunset dates and migration notes |
| README “which base URL / version” quickstart | `readme-and-contributing-docs` | this for policy |
| Live API discovery in assessments | `api-recon-and-docs` | note versions found; not design |
| Implementing handlers, validation, tests | `code-quality-standards` | **always apply** on code changes |
| Concurrent/idempotent handlers under dual versions | `async-concurrency-patterns` | this for contract split |

### Routing to `code-quality-standards`

Keep **this skill primary** for version strategy and deprecation design. Always
apply **`code-quality-standards`** when implementing version switches or adapters:

- Validate version tokens at the boundary; reject unknown versions explicitly
- Preserve public behavior for each still-supported version
- Avoid hidden global “current version” mutable state across requests
- Test each supported version’s contract; add regression tests for migrations
- Do not log secrets from versioned payloads; treat auth the same across versions
  unless the version change is explicitly about auth

This skill specializes **contract evolution and client-safe versioning**. It does
not replace implementation quality, security, or test policy.

## Checklist

- [ ] Existing version strategy, consumers, and gateway routes inventoried
- [ ] Change classified (additive vs breaking) with explicit rationale
- [ ] Single primary version selection mechanism documented (path/header/media/query)
- [ ] Default when version omitted is defined and tested
- [ ] Unknown version returns a stable, documented error
- [ ] Breaking changes only on a new version (or documented exception with approvals)
- [ ] Coexistence plan: adapters, shared domain, data compatibility
- [ ] OpenAPI/docs/SDK updated for every supported version
- [ ] Migration guide maps fields/status/auth differences
- [ ] Deprecation: successor live, headers/docs/changelog, sunset date, usage metrics
- [ ] Cache keys and CDNs include version where responses differ
- [ ] Contract tests cover each supported version
- [ ] `code-quality-standards` applied for boundary validation, behavior freeze, and tests
