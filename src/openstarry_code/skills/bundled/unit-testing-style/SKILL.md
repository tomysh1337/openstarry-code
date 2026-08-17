---
name: unit-testing-style
description: >
  Design and review unit tests: what to test, naming, AAA structure, isolation,
  and focused assertions. Use when unit tests, 单元测试, test naming, Arrange-Act-Assert,
  table-driven tests, test design, or reviewing flaky/brittle unit suites. Complements
  code-quality-standards; for mocks/fakes/stubs see mocking-and-test-doubles.
---

# Unit Testing Style

Unit tests prove a **small unit’s public behavior** under controlled inputs. Prefer
readable names, one clear behavior per test, and deterministic setup. Repository
test layout and runners outrank generic preferences.

## When To Use

- Writing or reviewing unit tests for functions, classes, pure modules, or domain services.
- Fixing brittle, flaky, or unreadable tests; choosing unit vs integration scope.
- Standardizing names, AAA layout, fixtures, and table-driven / parameterized cases.
- Triggers: unit tests, 单元测试, test naming, AAA, Arrange-Act-Assert, table tests.
- **Not** mock/stub/fake selection as main problem → `mocking-and-test-doubles`.
- **Not** full product quality gates alone → `code-quality-standards`.

## Repo Config First

1. Read tooling: pytest/unittest, Jest/Vitest, Go `testing`, JUnit/xUnit/NUnit, Rust `#[test]`, plus package scripts, `pyproject`/`tox`, CI test jobs.
2. Honor layout: `test_*.py` vs `*_test.py`, `*.test.ts` vs `*.spec.ts`, `Test` suffix, `tests/` mirror, fixtures/`conftest`.
3. Match nearby tests: assertion library, factories, clock/random injection, coverage gates, markers (`@pytest.mark.unit`).
4. Prefer the repo runner over inventing a second suite layout.
5. Repo rules outrank this skill unless they force private-only tests, disabled asserts, or sleep-until-pass flakiness — surface that conflict.

## What To Test

| Prefer | Avoid as unit scope |
| --- | --- |
| Public contract: inputs → outputs / errors / side effects | Private helpers (prefer via public API) |
| Domain rules, branching, invariants | Full HTTP stack / real DB (integration/e2e) |
| Boundaries: empty, null, zero, max, invalid enum | Unranked combinatorial explosion |
| Failure paths the unit owns | Private call-order trivia |
| Regression for a fixed bug | Huge snapshots of irrelevant fields |

Scale depth with **blast radius** (money, authz, parsing, concurrency > thin mappers).

## Naming And AAA

**Names:** unit + scenario + expected outcome (case per language/repo).

```text
methodOrBehavior_whenCondition_shouldExpected
handles empty input / rejects expired token / computes tax for NY
```

Behavior over ticket-only names (`handles empty JWKS` > `test1`). Bug id may suffix. Avoid `works` / `success` with no condition.

**AAA (Given-When-Then):**

1. **Arrange** — inputs, doubles, state; no asserts yet.
2. **Act** — one primary action.
3. **Assert** — few strong outcome checks.

Optional `// Arrange` labels only if the repo already uses them.

## Workflow

1. **State the contract** — success, key boundaries, owned failures.
2. **Pick the layer** — unit = in-process, fast; inject fakes for clock/I/O; push real I/O to integration.
3. **Design cases** — happy + meaningful edges + regression when fixing a bug; table-driven for pure matrices.
4. **Name and structure** — behavior name; AAA; one conceptual behavior per test.
5. **Control non-determinism** — inject clock/UUID/RNG; no real sleep/network/FS when a seam exists.
6. **Assert outcomes** — return/state/error over private call graphs unless interaction *is* the contract (`mocking-and-test-doubles`).
7. **Run** focused unit tests, then the package suite CI would run.
8. **TDD when driving design** — Red → Green → Refactor; small cycles; do not batch many reds.

## Good Vs Bad Examples

```python
# good — behavior name, AAA, strong assert
def test_apply_discount_rejects_negative_percent():
    order = Order(total_cents=1000)
    with pytest.raises(ValueError, match="percent"):
        apply_discount(order, percent=-1)

# bad — vague name, weak assert
def test_discount():
    apply_discount(Order(total_cents=1000), percent=10)
    assert True
```

```go
// good — table-driven boundaries
func TestClamp(t *testing.T) {
    cases := []struct{ in, want int }{{-1, 0}, {0, 0}, {5, 5}, {99, 10}}
    for _, tc := range cases {
        if got := Clamp(tc.in, 0, 10); got != tc.want {
            t.Fatalf("Clamp(%d)=%d want %d", tc.in, got, tc.want)
        }
    }
}
```

```typescript
// good — deterministic time
expect(isExpired(token, { now: () => FIXED_TS })).toBe(true);

// bad — private call order / sleep
// expect(svc["repo"].save).toHaveBeenCalledBefore(svc["bus"].publish);
// await sleep(2000); expect(eventuallyDone()).toBe(true);
```

## Anti-Patterns

- One giant test covering five behaviors; shared mutable fixtures without reset.
- Asserting volatile logs/JSON dumps/timestamps; catching-and-ignoring failures.
- Deleting or weakening tests to land a change; calling full-stack suites “unit.”

## Routing

| Need | Skill |
| --- | --- |
| Unit design, naming, AAA, what to test, 单元测试 | **This skill** (primary) |
| Mocks, fakes, stubs, spies, over-mocking | `mocking-and-test-doubles` |
| Reliability, security, errors, broader verification | `code-quality-standards` |
| TDD / red-green-refactor delivery mode | **This skill** + `code-quality-standards` |
| Test identifier naming only | `naming-conventions-general` |
| Language style of test code | Matching `*-style-*` skill |

Primary here for unit design; apply **`code-quality-standards`** on production changes; doubles → **`mocking-and-test-doubles`**.

## Output Checklist

- [ ] Repo test layout, runner, and local patterns followed
- [ ] Public behavior/invariants tested; not private trivia
- [ ] Names state scenario + outcome; package style consistent
- [ ] AAA clear; one primary act per test
- [ ] Boundaries and owned failures covered at risk-appropriate depth
- [ ] Deterministic (no real network/DB/sleep/random/clock without injection)
- [ ] Strong assertions; no empty/always-true tests
- [ ] Bug fix includes regression when reproducible
- [ ] Doubles correct and sparse (`mocking-and-test-doubles`)
- [ ] Focused suite run (or gap noted); `code-quality-standards` on prod changes

## Rules

- Green without encoding the contract is not success.
- Fast, isolated, deterministic units beat “unit” tests that hit the world.
- Rewrite brittle tests; never weaken asserts to silence real failures.
- Prefer runner evidence over coverage-% opinions alone.
