---
name: contract-testing-pact
description: >
  Consumer-driven contract testing (Pact-style): consumer expectations, provider
  verification, broker publish, and CI compatibility gates. Use when Pact, CDC,
  consumer-driven contracts, provider verification, pact broker, can-i-deploy,
  or API shape drift between services/frontends. Complements
  integration-test-strategy and unit-testing-style; not a substitute for e2e.
---

# Contract Testing (Pact-Style)

Consumer-driven contracts (CDC) prove a **consumer’s expected requests/responses**
match what a **provider** serves—without a full shared env on every PR. Prefer
the repo’s **Pact / Pactflow / Spring Cloud Contract / Specmatic** stack and
broker. Contracts catch **shape and status** drift; they do not replace unit
logic tests, DB/middleware integration, or thin critical-path e2e.

## Use When

- Adding or reviewing **consumer-driven contracts** (FE↔BE or service↔service)
- Choosing **Pact** (or equivalent) vs OpenAPI-only vs full integration/e2e
- Writing **consumer tests** that generate pacts; **provider verification**
- Wiring **Pact Broker / Pactflow**, publish, and **can-i-deploy** gates
- Debugging “works with my mock, breaks in staging” due to body/status drift
- Triggers: Pact, CDC, contract test, 契约测试, provider verification, broker

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Unit design, AAA, pure logic matrices | `unit-testing-style` |
| DB/HTTP seam integration, layer pyramid | `integration-test-strategy` |
| Browser journeys / Playwright e2e | `e2e-testing-playwright` |
| Production reliability/security baseline | `code-quality-standards` |

## Repo Config First

Repo tooling and broker policy **outrank** this skill’s defaults.

1. **Contract stack:** `@pact-foundation/pact`, Pact JVM/Python/Go/.NET, SCC,
   Specmatic—**extend that stack**
2. **Layout:** `pacts/`, language markers, consumer/provider package names
3. **Broker / Pactflow:** URL, secrets, versioning (git SHA), branch/tags
4. **CI:** consumer publish on green; provider verify on PR; can-i-deploy before promote
5. **Provider states & auth fixtures:** seed hooks, tokens, multi-tenant setup
6. **Transport:** HTTP first; message pacts only if repo already uses them
7. **Neighbors:** copy 2–3 mature interactions (matchers + states) before new DSL style
8. **OpenAPI:** align names if dual gates exist; do not invent a second source of truth mid-PR

**Precedence:** Follow repo/broker rules. Surface skips of provider verification,
secrets in pacts, or “200 only” checks with no body matchers.

## Workflow

1. **Name consumer, provider, and risk** (e.g. `GET /orders/{id}` → `totalCents` int).
2. **Inventory** library, pact dir, broker, CI jobs, state handlers, naming.
3. **Consumer tests (CDC first)** — exercise real client/adapter against Pact mock;
   assert **consumer-side** outcome; generate pact on green.
4. **Publish** pact with version = commit (or repo convention).
5. **Provider states** — implement each named state used in interactions.
6. **Provider verify** against broker or local files; fail on route/status/body mismatch.
7. **Matchers** — `like`/type/regex for ids/timestamps; exact on stable business fields.
8. **Gate deploy** with can-i-deploy (or equivalent); do not ship unverified breaks.
9. **On break** — fix provider or renegotiate deliberately; pin domain bug with
   `unit-testing-style` / seam with `integration-test-strategy`; apply
   `code-quality-standards` to production changes.
10. **Keep thin** — one interaction per meaningful scenario; logic matrices stay unit.

## Good / Bad Examples

**Good — consumer interaction (sketch):**

```ts
await provider.addInteraction({
  states: [{ description: "order 42 exists" }],
  uponReceiving: "a request for order 42",
  withRequest: { method: "GET", path: "/orders/42" },
  willRespondWith: {
    status: 200,
    body: like({ id: "42", totalCents: 500, status: "paid" }),
  },
});
expect((await orderClient.get("42")).totalCents).toBe(500);
```

**Bad:** ad-hoc `nock`/MSW only, never published or verified; field names diverge
from production (`total` string vs `totalCents` int).

**Good — provider:** CI verifier + state seeds; results published to broker.

**Bad:** “we have OpenAPI” with no consumer-generated expectations.

**Good — matchers:** exact money/status; flexible ids/timestamps.

**Bad:** exact `generatedAt` every ms (flake) **or** status-only empty body (false green).

**Good — scope:** contracts for shared shapes; units for tax matrix; one e2e checkout.

**Bad:** dozens of pacts cloning every unit branch; no provider states.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Pact/CDC, provider verify, broker, 契约测试 | **This skill** | — |
| Unit naming, AAA, example regressions | `unit-testing-style` | this for cross-service shape |
| Unit vs integration vs e2e vs contract | `integration-test-strategy` | this when contract is chosen |
| Browser e2e journeys | `e2e-testing-playwright` | this for FE/BE API shape |
| Production correctness, errors, security | `code-quality-standards` | **always apply** on implementation |

- **`unit-testing-style`:** structure/name consumer tests; pin shrunk/domain bugs as examples; keep pure logic out of pacts.
- **`integration-test-strategy`:** decide contract vs real DB/middleware integration vs e2e; contracts do not prove SQL or DI wiring.
- **`code-quality-standards`:** production fixes; validate inputs; no secrets in fixtures/logs; do not weaken matchers to silence real breaks.

## Checklist

- [ ] Repo Pact (or equivalent), paths, broker, and CI jobs identified
- [ ] Stable consumer/provider names match broker conventions
- [ ] Consumer tests generate interactions from real client behavior
- [ ] Matchers fit volatility (exact stable fields; like/type for noise)
- [ ] Provider states implemented for each named state
- [ ] Provider verification in CI; results published when broker is used
- [ ] Versioning supports can-i-deploy or repo-equivalent gate
- [ ] No secrets in pacts/states/logs
- [ ] Thin scope: contracts for shape; units for matrices; few e2e journeys
- [ ] Breaks fixed deliberately—not by skipping verify jobs
- [ ] `unit-testing-style` + `integration-test-strategy` used for layer/depth
- [ ] Production changes reviewed with `code-quality-standards`

## Rules

- Expectations come from **consumer tests**, not wiki guesses.
- Green mocks without **provider verification** are false confidence.
- Contracts prove **compatibility**, not full business correctness or UX.
- Repo broker and CI policy win; this skill is the CDC design/review bar.
