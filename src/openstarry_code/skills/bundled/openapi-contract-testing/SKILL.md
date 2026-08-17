---
name: openapi-contract-testing
description: >
  Verify OpenAPI (and similar) contracts against real producers/consumers:
  request/response conformance, CI gates, consumer-driven checks, and drift
  detection. Use when OpenAPI contract tests, schema conformance, Pact/OpenAPI
  validation, Specmatic/Dredd/Schemathesis, or API contract CI—not prose-only docs.
---

# OpenAPI Contract Testing

Prove **published OpenAPI matches runtime** and **consumers/producers stay
compatible**. Prefer the repo’s spec path, harness, and CI jobs over a parallel suite.

## Use When

- Tests that validate HTTP traffic against OpenAPI 3.x / Swagger
- Preventing doc/runtime drift; consumer-driven or bidirectional checks
- CI gates: lint + example validation + live/stub conformance
- Tools: Schemathesis, Dredd, Spectral+tests, Specmatic, Pact+OpenAPI, Prism
- Triggers: OpenAPI contract testing, schema conformance, CDC, OpenAPI drift, 契约测试

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Operation descriptions and example narrative | `api-documentation-writing` |
| Designing JSON Schema / component model shapes | `json-schema-design` |
| GraphQL schema design (not OpenAPI) | `graphql-schema-design-style` |
| Authorized GraphQL/API recon and abuse testing | `graphql-and-hidden-parameters` |
| Implementation reliability/security baseline | `code-quality-standards` |

## Repo Config First

Repo tooling and source of truth **outrank** defaults below.

1. **Spec location:** `openapi.yaml`/`.json`, split files, monorepo package, or
   code-first generation (Springdoc, Nest, FastAPI, tsoa)
2. **Authority:** design-first vs code-first — validate the **published** client artifact
3. **Tools:** Spectral/Redocly, Schemathesis, Dredd, Pact, Specmatic, Prism — extend them
4. **CI:** stage, required vs optional, ephemeral env (compose/Testcontainers)
5. **Auth fixtures:** token/key acquisition via secret store — no hardcoded secrets
6. **Versions:** cover each still-supported OpenAPI / `/v1`|`/v2` surface
7. **Neighbors:** copy mature tests for base URL, fixtures, additionalProperties policy

**Precedence:** Follow the repo. Surface suites that skip authz ops, only happy-path
GETs, or green-check a dead generated file never served.

## Workflow

1. **Pin the artifact** consumers get (release tag, portal package)—not a stale branch copy.
2. **Lint first** (Spectral/Redocly) so invalid OpenAPI cannot false-green.
3. **Choose mode(s):**

   | Mode | Proves | Typical tools |
   | --- | --- | --- |
   | **Producer conformance** | API traffic matches OpenAPI | Schemathesis, Dredd, middleware asserts |
   | **Consumer conformance** | Client uses only legal ops/fields | Generated clients, Pact consumer, MSW |
   | **Bidirectional / CDC** | Provider meets consumer expectations | Pact provider verify, Specmatic |
   | **Example validation** | Documented examples match schemas | AJV / OpenAPI parser unit tests |

4. **SUT** — in-process app + test DB or ephemeral stack for PR gates (not shared staging).
5. **Cover critical ops** — success, 400/422, 401/403 when real, error envelope.
   Scale with blast radius (pay/identity > pure reads).
6. **Assert both sides** — request path/query/header/body; response status set,
   content-type, body schema.
7. **Openness policy** — strict vs tolerant extra properties; match product rules
   (`json-schema-design`).
8. **Wire CI** — fail PR on break; JUnit/HTML reports; no mandatory production URL.
9. **Triage** — spec vs code vs fixture; fix source of truth; never weaken asserts to ship.
10. **Docs** — after green: prose → `api-documentation-writing`; models → `json-schema-design`.

## Design Rules (defaults when repo is silent)

- One OpenAPI document (or versioned set) feeds mocks, tests, and portal
- Generate clients/mocks from the **same** artifact tests validate
- Negative cases required: undocumented statuses and missing required fields must fail
- Happy-path-only GET suites are not “full contract coverage”
- Redact secrets in recordings and failure dumps
- GraphQL-only APIs: do not fake coverage with empty OpenAPI — use
  `graphql-schema-design-style` (+ `graphql-and-hidden-parameters` when assessing)

## Good / Bad Examples

**Good — producer at HTTP boundary**

```ts
it("POST /orders conforms to OpenAPI", async () => {
  const res = await request(app)
    .post("/orders")
    .set("Authorization", `Bearer ${token}`)
    .send({ customerId: FIXTURE.customerId, items: [{ sku: "sku_1", qty: 1 }] });
  expect(res.status).toBe(201);
  assertResponseConforms(openapi, "post", "/orders", res);
});
```

**Bad** — mock-only with no schema: `expect(handler).toHaveBeenCalled()`.

**Good:** each OpenAPI example validates against its schema; optional ephemeral send.  
**Bad:** portal examples with invalid enums; suite never loads them.

**Good:** generated consumer types + provider verification on PR.  
**Bad:** manual Postman only; frontend calls renamed fields under the same version.

**Good:** CI fails when annotations and committed OpenAPI diverge.  
**Bad:** hand-edited `/docs/openapi.json` never regenerated; suite greens on stale file.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| OpenAPI conformance, CDC, contract CI gates | **This skill** | — |
| Operation prose, example narrative | `api-documentation-writing` | this so examples stay executable |
| Schema types, required, additionalProperties design | `json-schema-design` | this to enforce schemas in tests |
| GraphQL type graph design | `graphql-schema-design-style` | — |
| Live GraphQL/API security assessment | `graphql-and-hidden-parameters` | not a substitute for contract CI |
| Handlers, errors, security hygiene | `code-quality-standards` | **always** on production changes |

- **`api-documentation-writing`:** human-readable summaries; this skill owns machine-checkable truth.
- **`json-schema-design`:** how to shape components; this skill checks they hold at runtime.
- **`graphql-and-hidden-parameters`:** authorized recon/abuse — not OpenAPI green builds.
- **`code-quality-standards`:** boundary validation, stable error codes, secret-safe fixtures,
  tests that encode the real contract.

## Checklist

- [ ] Published OpenAPI artifact and version under test identified; lint clean first
- [ ] Producer and/or consumer mode chosen; SUT hermetic for PR CI
- [ ] Critical ops: success + validation + auth errors as applicable
- [ ] Request and response (status, content-type, body) asserted to the spec
- [ ] Examples/fixtures schema-valid; no live secrets in recordings
- [ ] Additional-properties policy matches product compatibility
- [ ] Each supported API version covered or explicitly waived
- [ ] CI fails on drift; readable reports; no mandatory prod URL
- [ ] Failures triaged to spec vs code vs fixture — asserts not weakened
- [ ] Schema design → `json-schema-design`; prose → `api-documentation-writing`
- [ ] GraphQL-only surfaces not falsely covered by empty OpenAPI
- [ ] `code-quality-standards` applied for implementation and verification depth
