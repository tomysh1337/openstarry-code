---
name: e2e-testing-playwright
description: >
  Playwright end-to-end testing strategy: critical journeys, stable selectors,
  fixtures, isolation, and CI discipline. Use when Playwright, e2e tests,
  end-to-end, browser tests, page object, web-first assertions, or flaky UI
  suites. Complements integration-test-strategy and unit-testing-style; not for
  pure unit matrices or Pact contracts alone.
---

# E2E Testing (Playwright)

Playwright e2e tests prove **critical user journeys** in a real browser against a
**deployed or locally composed** stack. Prefer the repo’s Playwright config,
fixtures, and CI projects. Keep e2e **few, deep, and stable**; push logic matrices
to unit tests and seams to integration or contracts.

## Use When

- Adding or reviewing **Playwright** e2e (or Cypress→Playwright migration)
- Choosing which flows deserve browser e2e vs component/integration/unit
- Fixing **flaky** UI tests (selectors, waits, shared state, network races)
- Designing **fixtures**, auth `storageState`, test data, parallel projects
- Splitting PR **smoke** e2e vs nightly full journeys
- Triggers: Playwright, e2e, 端到端, browser test, `getByRole`, trace, POM

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Unit design, AAA, pure isolation | `unit-testing-style` |
| API+DB seams, layer pyramid choice | `integration-test-strategy` |
| Consumer-driven API contracts (Pact) | `contract-testing-pact` |
| Production reliability/security baseline | `code-quality-standards` |

## Repo Config First

Repo Playwright layout and CI **outrank** this skill’s defaults.

1. **Setup:** `playwright.config.*`, `e2e/`/`tests/`, projects, `baseURL`, workers
2. **Scripts & CI:** `test:e2e`, PR smoke vs nightly; upload trace/video/HTML report
3. **Auth:** `storageState`, global setup, seeded users; no committed secrets
4. **Envs:** local compose, preview, staging—explicit; not prod credentials
5. **Data:** factories, API seeds, tenant isolation, cleanup policy
6. **Selectors/POM:** role/label first; shared `pages/` only if already used
7. **Network:** when to `route` third parties vs hit real app API
8. **Neighbors:** copy 2–3 mature journeys before new abstraction layers

**Precedence:** Follow repo config. Surface `waitForTimeout`-heavy suites, one
shared mutable user across workers, or full multi-browser matrices on every PR.

## Scope

| Prefer e2e | Prefer lower layers |
| --- | --- |
| Login → core happy path → visible result | Every validation / tax edge → unit |
| Cross-page wiring, cookies, redirects | Pure functions / reducers → unit |
| Release smoke on real composition | API shape only → `contract-testing-pact` |
| Critical failure UX (pay fail, auth deny) | ORM/middleware → integration |

If the bug needs browser + FE + API + data on one user path → e2e; single module
rule → unit; adapter/DB → integration; FE/BE field agreement → contract.

## Workflow

1. **Name journey and risk** (“paid checkout shows confirmation id”).
2. **Inventory** config, fixtures, auth state, seeds, CI, traces.
3. **Short path** — minimum UI steps; seed unrelated setup via API/fixtures.
4. **Resilient locators** — `getByRole` / `getByLabel`; `data-testid` only per repo rules.
5. **Web-first asserts** — `await expect(...).toBeVisible()`; URL/toast/row outcomes.
6. **Isolate data** — unique user/tenant per test or worker; parallel-safe.
7. **Cut flakes** — no fixed sleeps as primary sync; wait on nav/response/locator.
8. **Light structure** — fixtures for auth/page; POM only if repo already benefits.
9. **Run as CI would** — trace-on-retry; fix isolation/product, not “retry only.”
10. **Depth elsewhere** — `unit-testing-style`, `integration-test-strategy`;
    production fixes with `code-quality-standards`.

## Good / Bad Examples

**Good**

```ts
test("checkout shows confirmation", async ({ page }) => {
  await page.goto("/cart");
  await page.getByRole("button", { name: "Checkout" }).click();
  await page.getByLabel("Card number").fill("4242424242424242");
  await page.getByRole("button", { name: "Pay" }).click();
  await expect(page.getByRole("heading", { name: /confirmation/i })).toBeVisible();
});
```

**Bad:** `waitForTimeout(5000)` + brittle `#btn-3 > span` + no outcome expect.

| Topic | Good | Bad |
| --- | --- | --- |
| Seed | API creates cart; e2e pays → confirmation | Register + verify email every test |
| Isolation | `user-${worker}-${nonce}@…` | Shared `admin@` and one order row |
| Network | Real app API; route analytics noise | Mock entire backend, call it e2e |
| CI | PR chromium smoke + trace on retry | 200×3 browsers on every docs PR |

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Playwright e2e strategy, journeys, flakes, 端到端 | **This skill** | — |
| Unit naming, AAA, logic matrices | `unit-testing-style` | pin bugs found in UI |
| Integration vs e2e vs contract choice | `integration-test-strategy` | this when browser e2e chosen |
| Pact/CDC API compatibility | `contract-testing-pact` | this for full UI journeys |
| Production correctness, security, verification | `code-quality-standards` | **always apply** on implementation |

- **`unit-testing-style`:** extract pure rules and fast regressions so e2e stays thin.
- **`integration-test-strategy`:** decide API+DB / component+MSW vs full browser; do not promote every seam into Playwright.
- **`code-quality-standards`:** product fixes from e2e; accessible names; no secrets in tests/logs; do not delete asserts to hide failures.

## Checklist

- [ ] Playwright config, scripts, projects, CI jobs identified
- [ ] Journey risk stated; e2e justified over unit/integration/contract
- [ ] Path minimized; setup seeded when UI grind is unrelated
- [ ] User-centric locators; outcomes asserted with web-first expects
- [ ] No fixed sleeps as primary synchronization
- [ ] Parallel-safe unique data; no shared mutable fixtures
- [ ] Core stack real for the risk; third parties handled deliberately
- [ ] Auth via repo storageState/setup; secrets not committed
- [ ] PR smoke vs full suite split; traces/reports on failure
- [ ] Flakes fixed via isolation/waits/product—not retries alone
- [ ] Depth via `unit-testing-style` / `integration-test-strategy`
- [ ] Production changes reviewed with `code-quality-standards`

## Rules

- Few reliable journeys beat a brittle encyclopedia of clicks.
- E2E green with a fully mocked backend is not end-to-end confidence.
- Prefer role/label selectors—they reward accessible product UI.
- Repo Playwright config and CI policy win; this skill is the strategy bar.
