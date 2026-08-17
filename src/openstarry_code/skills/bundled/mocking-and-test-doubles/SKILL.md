---
name: mocking-and-test-doubles
description: >
  Choose and review mocks, stubs, fakes, spies, and dummies: when each is
  appropriate, how to avoid over-mocking, and how to keep tests honest. Use when
  mock, test doubles, 单元测试 mock, stub, fake, spy, mockito, unittest.mock,
  jest.fn, or reviews flag brittle interaction tests. Complements unit-testing-style
  and code-quality-standards.
---

# Mocking And Test Doubles

Test doubles replace a **collaborator** so the unit stays fast and deterministic.
Use the **simplest double that preserves the behavior under test**. Over-mocking
couples tests to implementation and hides integration bugs.

## When To Use

- Isolating from I/O: HTTP clients, DB repos, buses, clocks, entropy, filesystem.
- Designing seams (interfaces, ports, injectable functions) without mock-library churn.
- Reviewing suites heavy on `mock` / `jest.fn` / `MagicMock` / Mockito that only assert call counts.
- Triggers: mock, test doubles, 单元测试 mock, stub, fake, spy, over-mocking.
- **Not** AAA/naming/what-to-test alone → `unit-testing-style`.
- **Not** full quality gates → `code-quality-standards`.

## Repo Config First

1. Note double style: classicist (fakes/in-memory) vs mockist (interaction); testcontainers vs pure unit.
2. Match libraries: `unittest.mock`/`pytest-mock`, Jest/Vitest, Go hand fakes, Mockito/MockK, NSubstitute, `mockall`, Sinon.
3. Prefer repo helpers/in-memory fakes over introducing a second mocking framework.
4. Mock only **replaceable boundaries** (ports/adapters); never concrete internals of the same unit.
5. Repo rules outrank this skill unless they require mocking pure functions/value objects — surface that conflict.

## Double Types

| Double | Role | Typical use |
| --- | --- | --- |
| **Dummy** | Unused required arg | Ctor filler |
| **Stub** | Canned return/error | Repo → None; API → 503 |
| **Fake** | Lightweight working impl | In-memory repo, fake clock |
| **Spy** | Records calls | “email sent once to X” |
| **Mock** | Expectations + verify | Strict interaction (sparingly) |

Casual “mock” often means any double — prefer the precise term in design discussion.

## When To Double

**Do:** slow/flaky/expensive collaborators; hard-to-trigger failures (timeout, 429); already-abstracted process boundaries.

**Don’t:** pure functions, DTOs, value objects, trivial helpers; when a **fake** proves more with less brittleness; “skip fixtures” (fix factories, not mocks). Prefer **fakes over mocks** for repos/caches/clocks when cheap.

## Anti Over-Mocking

| Smell | Prefer |
| --- | --- |
| Mocking the class under test | Split seams; test the real unit |
| Mocking every pure dependency | Call real pure deps |
| Full call graphs / private order | Assert return state / visible side effects |
| Incomplete stubs; partial mock of huge class | Fake + realistic builders; interface + fake |
| Re-implementing production in the mock | Contract/integration test for the adapter |

**Default:** classicist (state + fakes). **Narrow mockist:** only when the **interaction is the product** and state is not observable.

## Workflow

1. **Name unit and ports** that cross I/O or non-determinism.
2. **Choose depth** — dummy → stub → fake → spy/mock; stop at weakest sufficient.
3. **Arrange behavior** (port returns), not private walk order; **act** via public API (`unit-testing-style` AAA).
4. **Assert outcomes first** — return, error, fake state, or one spy fact; interaction asserts only if contract-critical.
5. **Keep doubles local**; note residual risk when adapters lack contract/integration tests.
6. **TDD** — failing behavior first; add a seam only when a real collaborator blocks green.

## Good Vs Bad Examples

```python
# good — stub port for owned failure
def test_checkout_maps_payment_timeout():
    payments = Mock()
    payments.charge.side_effect = TimeoutError()
    with pytest.raises(CheckoutError, match="payment"):
        CheckoutService(payments=payments).checkout(order_id="o1")

# bad — mock pure logic; never proved add/tax
def test_total(mocker):
    mocker.patch("app.pricing.add", return_value=10)
    mocker.patch("app.pricing.tax", return_value=1)
    assert cart.total() == 11
```

```typescript
// good — in-memory fake
const repo = new InMemoryOrderRepository();
await repo.save(order);
await new CancelOrderService(repo).cancel(order.id);
expect(await repo.find(order.id)).toMatchObject({ status: "cancelled" });

// bad — mock pure path APIs
// jest.mock("node:path");
```

```java
// bad — over-specified interactions for a cancel use case
// verifyNoMoreInteractions(repo, bus, clock, metrics, tracer);
```

```go
// good — spy only the visible side effect
var sent []Mail
mailer := MailFunc(func(m Mail) error { sent = append(sent, m); return nil })
_ = Notify(mailer, user)
if len(sent) != 1 || sent[0].To != user.Email {
    t.Fatalf("want one mail to user")
}
```

## Anti-Patterns

- Shared mocks without reset (order dependence); `MagicMock` attribute soup hiding API drift.
- Mocks to silence type/import errors; production logic re-coded in `side_effect`.
- Replacing integration coverage for auth/migrations/serializers with unit mocks “to go faster.”

## Routing

| Need | Skill |
| --- | --- |
| Mocks / fakes / stubs / spies / over-mock, 单元测试 mock | **This skill** (primary) |
| Unit naming, AAA, what to test | `unit-testing-style` |
| Production design, errors, security, verification | `code-quality-standards` |
| TDD with seams/doubles | `unit-testing-style` + **this skill** + `code-quality-standards` |
| Naming ports/interfaces | `naming-conventions-general` |

Primary here for double strategy; structure/cases → **`unit-testing-style`**; prod changes → **`code-quality-standards`**.

## Output Checklist

- [ ] Doubles only at real boundaries (I/O, time, entropy, third party)
- [ ] Weakest sufficient double (dummy/stub/fake before strict mock)
- [ ] Fake/in-memory preferred when cheap and realistic
- [ ] Outcomes asserted first; interaction only if contract-critical
- [ ] Unit under test and pure helpers not mocked
- [ ] Realistic stub shapes; no global mock pollution
- [ ] Residual risk noted if adapters lack contract/integration tests
- [ ] Deterministic/fast (`unit-testing-style`); seams minimal (`code-quality-standards`)

## Rules

- Every mock expectation is a coupling point — keep few and intentional.
- Port-implementing fakes beat partial mocks of infrastructure.
- Never greenwash an unknown/wrong real contract with doubles.
- If the test is harder to read than the code, simplify or promote to a fake.
- Interaction tests do not replace state-based proof of business rules.
