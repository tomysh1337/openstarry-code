---
name: integration-test-strategy
description: >
  Decide when to write integration tests vs unit or e2e, and how to draw
  reliable boundaries. Use when integration tests, 集成测试, test pyramid,
  unit vs integration vs e2e, test boundaries, contract tests, or when suites
  are slow/flaky from wrong layer choice. Pairs with code-quality-standards and
  unit-testing-style; frontend UI seams pair with react-component-patterns.
---

# Integration Test Strategy

Choose the **right test layer** and draw **stable boundaries**. Integration tests
prove that **multiple real pieces work together** (modules, process + DB, API +
auth middleware, component + router) without necessarily driving a full browser
product tour. Prefer the repo’s test layout, markers, and CI jobs over a generic
pyramid slogan.

## Use When

- Deciding unit vs integration vs e2e for a change or new feature
- Designing integration suite scope, fixtures, and seams (DB, HTTP, queue, UI)
- Fixing slow or flaky suites caused by testing at the wrong layer
- Splitting “everything is e2e” or “everything is mocked unit” extremes
- Planning contract tests between frontend and backend or between services
- User mentions: integration tests, 集成测试, test pyramid, unit vs e2e,
  测试边界, contract test, 契约测试, component integration, test layers

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Unit design, naming, AAA, pure isolation | `unit-testing-style` |
| Mock/fake/stub selection and over-mocking | `mocking-and-test-doubles` |
| React component structure (not test layer) | `react-component-patterns` |
| Vue component structure | `vue-component-patterns` |
| Reliability/security implementation baseline | `code-quality-standards` |
| CI pipeline wiring only | `ci-cd-pipeline-patterns` |

## Repo Config First

Repo config and neighboring tests **outrank** this skill’s defaults.

1. **Runners and jobs:** Jest/Vitest, pytest, Go test, JUnit, Playwright/Cypress,
   package scripts, CI stages (`unit`, `integration`, `e2e`)
2. **Markers and tags:** `@pytest.mark.integration`, `describe` file suffixes
   (`*.integration.test.ts`), CI path filters — match existing taxonomy
3. **Real dependencies already available:** Testcontainers, docker-compose,
   embedded DB, localstack, in-memory bus, MSW, mock service worker, WireMock
4. **Data fixtures:** factories, seed scripts, migration-on-boot for test DB —
   reuse; do not invent a parallel fixture world mid-PR
5. **Frontend harness:** React Testing Library + MSW, Vue Test Utils / VTU +
   testing-library, Storybook interaction tests, Playwright component tests
6. **Environment policy:** what may hit network in CI; secrets; parallelization
   and DB isolation rules
7. **Neighboring suites:** copy 2–3 mature integration tests for boundary style
   (what is real vs doubled) before adding a new layer of mocks

**Precedence:** If repo rules conflict with defaults below, follow the repo.
Surface conflicts that force full production network calls in unit jobs, skip
migrations, or share mutable global DB state across parallel tests without isolation.

## Layer Definitions

| Layer | Proves | Typical doubles | Speed / stability target |
| --- | --- | --- | --- |
| **Unit** | One unit’s public behavior in-process | Clock, I/O, network fully injected/faked | Milliseconds; deterministic |
| **Integration** | Several real collaborators cooperate across a boundary | Fewer doubles; real DB/HTTP adapter/router where that *is* the risk | Seconds; controlled env |
| **E2E / end-to-end** | Full user-visible journey through real UI + backend stack | Minimal; staging-like deps | Tens of seconds+; more hermetic cost |
| **Contract** | Producer/consumer agree on schema and status semantics | Often isolated per side with shared contract artifact | Fast if schema-level; can be CI gate |

**Integration is not “unit test plus more mocks.”** If every dependency is mocked,
it is still a unit (or a brittle collaboration test). If a browser drives the
whole product through UI only, it is e2e even if someone labeled the file
`integration`.

## When To Prefer Which Layer

### Prefer **unit** when

- Logic is pure or easily isolated (parsing, pricing, policy, reducers)
- Failures should pinpoint one module in milliseconds
- Combinatorial matrices of inputs/edges
- Collaborators are trivial or already proven at another layer

### Prefer **integration** when

- Risk lives **at the seam**: ORM mapping, SQL, migrations, HTTP middleware,
  authn/z wiring, serialization, message handler + schema, cache invalidation
- Mocks would re-implement the dependency’s real contract (false confidence)
- You need proof that DI/composition roots wire correctly
- Frontend: component + router + real store/query client + MSW handlers (not a
  full browser product tour)

### Prefer **e2e** when

- Critical user journeys must work across UI + API + data (login, checkout, pay)
- Cross-team confidence before release; smoke on staging
- Few high-value paths, not exhaustive business-rule matrices

### Prefer **contract** when

- Frontend and backend (or two services) evolve independently
- Schema/status/error shape is the shared risk; full e2e is too slow for every PR

### Decision sketch

```text
What failure would hurt, and which seam hides it?
  Pure logic / branching matrix     → unit
  Adapter, DB, middleware, wiring   → integration
  Multi-hop user journey in UI      → few e2e smokes
  Cross-team API shape              → contract (+ targeted integration)
  “I mocked the thing that breaks”  → move up to integration
  “Suite is slow/flaky for one rule”→ move down to unit; keep one seam test
```

## Boundaries (how to draw them)

1. **Name the system under test (SUT).** One feature slice or vertical path, not
   “the whole monolith.”
2. **List real collaborators** required to make the risk real (e.g. Postgres +
   repository + HTTP handler).
3. **Double only irrelevancies** for this risk (third-party email, payment sandbox
   if not under test, clock if not time-sensitive).
4. **Isolate data.** Unique keys per test, transactions/rollback, or ephemeral
   containers — no order-dependent shared rows.
5. **Control time and randomness** at the boundary you own (inject clock even in
   integration when flakes appear).
6. **Assert observable outcomes** at the boundary: HTTP status/body, DB row,
   published message, UI text/role — not private call graphs.
7. **Keep e2e paths thin.** Happy path + 1–2 critical failures; push matrices down.

## Workflow

1. **State the risk.** What bug would ship if this seam broke?
2. **Pick the lowest layer that can catch that risk** (table above).
3. **Inventory repo harnesses.** Reuse fixtures, containers, MSW, markers, CI job.
4. **Draw the boundary.** Real vs doubled; data isolation; env vars.
5. **Write few deep tests at the seam**, not a second copy of every unit case.
6. **Name by behavior and layer** so CI filters stay honest
   (`creates order with valid payment method` in integration suite).
7. **Run the layer’s job** as CI would; note flakes and tighten isolation.
8. **Apply `code-quality-standards`** to production code under test; apply
   `unit-testing-style` for structure/naming habits that still apply.

## Frontend-focused integration

Frontend “integration” often means:

| Scope | Real | Usually doubled |
| --- | --- | --- |
| Component + Testing Library | Component tree, user events | Network via MSW; sometimes router memory history |
| Page + router + store/query | Navigation, cache keys, forms | Backend via MSW or test API |
| Playwright/Cypress component | Browser layout engine | Network stubs as needed |
| Full e2e | Browser + real or staged API | External SaaS when policy requires |

Structure UI under test with clear props/state ownership so tests hit stable
roles and labels — use **`react-component-patterns`** (React) or
**`vue-component-patterns`** (Vue) when the component API itself is the problem.

## Good / Bad Examples

### Choosing layer for pricing rules

**Good** — unit for matrix; integration for persistence mapping:

```text
unit: computeLineTotal(cases…) many edges
integration: POST /orders persists line totals and tax fields correctly
e2e: one checkout smoke that paid order appears in history
```

**Bad** — 40 Playwright tests for every tax edge case; suite takes 40 minutes and
flakes on animation timing.

### Integration at the HTTP + DB seam

**Good**

```ts
// integration: real app router + test DB; no mocked repository
it("rejects create order when SKU is unknown", async () => {
  const res = await request(app)
    .post("/orders")
    .send({ sku: "nope", qty: 1 })
    .expect(400);

  expect(res.body.code).toBe("UNKNOWN_SKU");
  expect(await countOrders(db)).toBe(0);
});
```

**Bad** — “integration” that mocks the repository and the validator:

```ts
// Still a unit test with extra ceremony — seam never exercised
repo.create.mockResolvedValue({});
validator.assert.mockReturnValue(true);
await handler(req, res);
expect(repo.create).toHaveBeenCalled();
```

### Frontend: MSW integration vs pure unit

**Good** — component integration with real query client + MSW:

```tsx
// handlers return real-shaped JSON; assert UI outcomes
server.use(
  http.get("/api/orders", () => HttpResponse.json([{ id: "1", total: 500 }])),
);
render(<OrdersPage />, { wrapper: AppProviders });
expect(await screen.findByRole("row", { name: /500/i })).toBeInTheDocument();
```

**Bad** — mock the custom hook that is the entire page:

```tsx
jest.mock("./useOrders", () => ({
  useOrders: () => ({ data: [{ id: "1" }], isLoading: false }),
}));
// Page wiring + query keys + error paths never tested
```

### E2E scope discipline

**Good** — one critical path e2e:

```text
login → add item → checkout → confirmation id visible
```

**Bad** — e2e for every form validation message already covered by unit/component
tests.

### Contract vs full stack

**Good** — OpenAPI/consumer contract gate on PR; integration tests use the same
schema fixtures.

**Bad** — only manual Postman checks; frontend assumes fields that backend renamed.

### Boundary isolation

**Good** — unique tenant/user per test; migrations applied once per suite; cleanup
in `afterEach` or transaction rollback.

**Bad** — all tests share `userId = 1` and depend on run order.

## Anti-Patterns

- Calling fully mocked tests “integration” (false confidence)
- Duplicating the entire unit matrix at e2e speed
- Shared mutable DB/global state across parallel workers
- Real third-party network calls in PR CI without policy/sandbox
- Asserting implementation details (private methods, Redux action type strings)
  instead of boundary outcomes
- Sleeping for “eventual” UI without condition waits
- One mega-suite that mixes unit and browser e2e so failures are un-triagable
- New Testcontainers stack per tiny PR when the repo already has a harness
- Skipping integration for ORM/SQL because “unit coverage % is high”
- Testing only happy paths at the seam where failures matter (authz, payments)

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Integration vs unit/e2e choice, boundaries, pyramid | **This skill** | — |
| Unit naming, AAA, pure isolation | `unit-testing-style` | this for layer choice |
| Mocks/fakes/stubs, over-mocking | `mocking-and-test-doubles` | this for when not to mock |
| React UI structure for testable components | `react-component-patterns` | this for UI integration scope |
| Vue UI structure | `vue-component-patterns` | this for UI integration scope |
| Production correctness, errors, security, verification policy | `code-quality-standards` | **always apply** on implementation |
| CI job design | `ci-cd-pipeline-patterns` | this for what each job should run |
| State ownership affecting test doubles | `state-management-guidelines` | this for seam choice |

### Routing to `code-quality-standards`

Keep **this skill primary** for layer choice and boundaries. Always apply
**`code-quality-standards`** when implementing features or fixing tests that guard
production code:

- Prefer tests that encode real contracts, not implementation trivia
- Error and failure paths at risky seams deserve coverage
- Resource cleanup in tests and production (connections, servers, workers)
- No secrets in fixtures/logs; redact tokens in failure output
- Do not delete or weaken integration assertions to silence real regressions
- Verification depth scales with blast radius (authz, money, data loss)

### Routing to `react-component-patterns`

When integration tests exercise **React UI**, keep this skill primary for *what
layer* to use, and use **`react-component-patterns`** so the SUT is structured for
stable testing:

- Clear props/state ownership → fewer brittle setup trees
- Composition and roles/labels → assert on accessible queries, not DOM soup
- Avoid god components that force full-app mounts for one button
- Colocate component tests when the repo’s convention is feature-local

For Vue SFCs, use **`vue-component-patterns`** the same way. Do not treat the
React skill as a substitute for Vue component design.

This skill specializes **test layer selection and integration boundaries**. It does
not replace unit style details, mock catalog design, or general production quality.

## Checklist

- [ ] Repo runners, markers, CI jobs, and fixture harnesses identified
- [ ] Risk/seam stated; lowest adequate layer chosen (unit / integration / e2e / contract)
- [ ] Integration tests use **real** collaborators for the risk under test
- [ ] Doubles limited to irrelevant externals; not a fully mocked “integration”
- [ ] Data isolation: unique keys, cleanup, or ephemeral containers; parallel-safe
- [ ] Assertions on boundary outcomes (HTTP/DB/UI/message), not private call graphs
- [ ] Unit matrices kept in unit suite; e2e limited to critical journeys
- [ ] Contract/schema alignment considered for cross-team APIs
- [ ] Frontend: MSW/providers/router chosen deliberately; hooks not mocked away when wiring is the risk
- [ ] Time/randomness controlled if flakes appear
- [ ] Names and file layout match repo layer taxonomy
- [ ] Focused layer job run as CI would; flakes triaged via isolation not sleeps
- [ ] `unit-testing-style` / `mocking-and-test-doubles` applied where those concerns dominate
- [ ] `code-quality-standards` applied for production code and verification depth
- [ ] UI SUT structure guided by `react-component-patterns` or `vue-component-patterns` as appropriate
