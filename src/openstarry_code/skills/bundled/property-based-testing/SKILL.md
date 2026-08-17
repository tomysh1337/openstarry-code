---
name: property-based-testing
description: >
  Design and review property-based and fuzz-style property tests: invariants,
  generators, shrinking, and when properties beat examples. Use when
  property-based testing, 属性测试, hypothesis, fast-check, jqwik, proptest,
  generators, shrinking, or invariant testing. Complements unit-testing-style
  and code-quality-standards; not a substitute for example unit tests.
---

# Property-Based Testing

Property-based tests (PBT) check that a **general property** holds for many
generated inputs—not only hand-picked examples. Prefer **repo Hypothesis /
fast-check / jqwik / proptest / FsCheck** setup over inventing a second
generator stack. Use PBT where **invariants and round-trips** matter; keep
focused example tests for named regressions and documentation.

## Use When

- Writing or reviewing **property-based** / **fuzz-style property** tests
- Encoding **invariants**, **round-trips**, **idempotence**, or **metamorphic**
  relations over large input spaces
- Choosing or tuning **generators**, **filters**, and **shrinking**
- Debugging a counterexample: minimize, fix, pin as regression
- User mentions: property-based testing, 属性测试, property test, Hypothesis,
  `@given`, fast-check, `fc.assert`, jqwik, proptest, FsCheck, QuickCheck,
  generators, shrinking, invariant testing, generative testing

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Example unit design, AAA, naming, what-to-test | `unit-testing-style` |
| Mocks / fakes / stubs | `mocking-and-test-doubles` |
| Production reliability, security, error design | `code-quality-standards` |
| Load / latency / capacity tests | `performance-testing-basics` |
| Security fuzzing of unowned network targets | authorized security skills only |

## Repo Config First

Repo test layout, libraries, and CI **outrank** this skill’s defaults.

1. **PBT library already in use:** Hypothesis (Python), fast-check (JS/TS),
   jqwik / junit-quickcheck (Java), proptest / rapid (Go), FsCheck (F#/.NET),
   QuickCheck / Hedgehog (Haskell), proptest equivalents—**extend that stack**
2. **Runner integration:** pytest markers, Jest/Vitest scripts, Go test tags,
   JUnit engine config, CI time budgets and flaky-retry policy
3. **Seed and determinism:** how the repo records seeds (`--hypothesis-seed`,
   `fc.configureGlobal`, proptest seeds) for CI repro
4. **Example unit style nearby:** names, AAA, fixtures, factories
   (`unit-testing-style`)—property tests should **live next to** example tests,
   not invent a parallel suite tree unless the repo already does
5. **Domain generators:** shared strategies/arbitraries in `conftest`,
   `*Arbitrary*`, or test helpers—prefer reuse over one-off generators
6. **Coverage / gate policy:** whether PBT runs on every PR, nightly, or opt-in
   markers (`@pytest.mark.property`, slow suites)
7. **Neighboring code:** copy 2–3 mature properties (max examples, suppress
   health checks, size bounds) before inventing new defaults

**Precedence:** Follow repo conventions when they conflict with examples below.
Surface conflicts that disable shrinking forever, use unbounded generation in
PR CI without budgets, or replace all example tests with opaque properties.

## Core Ideas

| Concept | Meaning |
| --- | --- |
| **Property** | Predicate that should hold for *all* valid inputs in a class |
| **Generator / arbitrary** | Produces random (or structured-random) inputs |
| **Example count** | How many cases per run (trade confidence vs time) |
| **Shrinking** | Minimize a failing input to a simpler counterexample |
| **Seed** | Reproducibility handle for CI and bug reports |
| **Precondition / filter / assume** | Restrict to valid domain without testing the filter itself |

**Properties beat single examples when:** the rule is universal (round-trip,
sort order, parse/print, commutativity), the input space is large, or edge
cases are easy to miss by hand.

**Examples still win when:** documenting a product story, locking a past bug,
or the “property” is only restating the implementation (tautology).

## Strong Property Patterns

| Pattern | Sketch | Good for |
| --- | --- | --- |
| **Round-trip** | `decode(encode(x)) == x` | Codecs, serializers, parsers with printers |
| **Idempotence** | `f(f(x)) == f(x)` | Normalize, dedupe, set-like ops |
| **Invariant** | `len(sort(x)) == len(x)` and sorted | Collections, transforms |
| **Oracle / model** | `impl(x) == slow_or_simple(x)` | Optimized vs reference |
| **Metamorphic** | `f(x) ≤ f(x + positive)` | Pricing, ranking, metrics |
| **Inverse pair** | `add/remove`, `push/pop` balance | Stateful APIs (with care) |
| **Does not crash** | no throw on any valid input | Parsers, validators (weak alone) |

Prefer **oracle and invariant** properties over “does not throw” alone.

## Workflow

1. **State the contract as a property** (or a small set), not “test everything
   randomly.” Name the universal claim in one sentence.
2. **Inventory repo PBT tooling** — library, markers, seeds, CI budget, shared
   generators.
3. **Define the domain** — valid inputs; encode constraints in generators
   (preferred) rather than heavy `assume`/`filter` (which wastes trials).
4. **Write the property** with clear arrange of inputs → act → assert
   invariant (`unit-testing-style` structure still applies).
5. **Bound generation** — max size, max examples, timeouts; keep PR runs fast;
   push expensive campaigns to nightly if the repo does that.
6. **Run until green or counterexample** — on fail, **keep the shrunk
   example**, understand it, fix production (or correct the property).
7. **Pin the bug** — add a focused example unit test for the shrunk case
   (`unit-testing-style`) so the regression is obvious without re-searching.
8. **Stabilize CI** — record seed on failure; avoid non-determinism from real
   time/IO (inject clocks; use doubles via `mocking-and-test-doubles` only at
   true boundaries).
9. **Review for tautologies** — if the property reimplements the code under
   test, replace with an independent oracle or drop PBT for that claim.

## Generators And Shrinking

| Practice | Why |
| --- | --- |
| Build complex values from small strategies | Better shrinking and readability |
| Prefer `maps`/`flatMap` composition over rejection sampling | Higher valid rate |
| Cap collection sizes in unit/PR tests | Avoid CI timeouts and OOM |
| Include interesting constants (0, 1, empty, unicode, max int) | Libraries often bias these; ensure domain coverage |
| Keep shrinking enabled | Unminified failures are hard to debug |
| Log seed + shrunk input on failure | Repro without “works on my machine” |

**Stateful / model-based testing** (Hypothesis rule-based state machines,
fast-check commands): use when the system is a **state machine** and sequential
ops have model-checkable invariants. Start with pure functions first.

## Good / Bad Examples

### Round-trip (codec)

**Good**

```python
from hypothesis import given, strategies as st

@given(st.binary())
def test_b64_roundtrip(data: bytes) -> None:
    assert decode_b64(encode_b64(data)) == data
```

**Bad**

```python
@given(st.binary())
def test_b64_roundtrip(data: bytes) -> None:
    encode_b64(data)  # no assert — only "does not throw"
    assert True
```

### Invariant (sort)

**Good**

```typescript
import fc from "fast-check";

fc.assert(
  fc.property(fc.array(fc.integer()), (xs) => {
    const sorted = sortNums(xs);
    // same multiset
    expect([...sorted].sort((a, b) => a - b)).toEqual(
      [...xs].sort((a, b) => a - b),
    );
    // nondecreasing
    for (let i = 1; i < sorted.length; i++) {
      expect(sorted[i]! >= sorted[i - 1]!).toBe(true);
    }
  }),
);
```

**Bad**

```typescript
fc.assert(
  fc.property(fc.array(fc.integer()), (xs) => {
    expect(sortNums(xs)).toEqual(sortNums(xs)); // tautology / same impl twice
  }),
);
```

### Domain constraints in the generator

**Good**

```python
# emails or ids built as structured strategies, not "any text then assume"
safe_name = st.text(alphabet=st.characters(whitelist_categories=("L", "N")), min_size=1, max_size=32)

@given(safe_name)
def test_slugify_idempotent(name: str) -> None:
    s = slugify(name)
    assert slugify(s) == s
```

**Bad**

```python
@given(st.text())
def test_slugify_idempotent(name: str) -> None:
    hypothesis.assume("@" not in name and len(name) > 0)  # rejects most trials
    ...
```

### Pin shrunk counterexample

**Good**

```python
def test_parse_rejects_lone_surrogate_regression() -> None:
    # Shrunk from property run; keep as permanent example
    with pytest.raises(ParseError):
        parse("\ud800")
```

**Bad** — fix prod only under a flaky seed with no example pin; failure returns
months later as “random CI red.”

### Oracle vs optimized path

**Good**

```go
// property: optimized sum matches simple loop for small slices
func TestSumEqNaive(t *testing.T) {
    // use repo’s rapid/proptest style; sketch:
    // for many random []int with len <= N: Sum(x) == naiveSum(x)
}
```

**Bad** — property only checks `Sum(x) >= 0` when negatives are allowed
(wrong property / false confidence).

## Anti-Patterns

- Properties that restate the implementation (same algorithm in the assert)
- Only “never throws” with no semantic invariant
- Unbounded collections/strings on every PR commit
- Disabling shrinking or ignoring seeds so failures cannot be reproduced
- Heavy `assume`/`filter` instead of modeling the valid domain
- Using PBT as a substitute for understanding the spec
- Mocking the unit under test so the property never exercises real code
- Flaky properties that depend on wall clock, real network, or unordered maps
  without canonicalization
- Asserting exact float equality without tolerance or integerization
- Generating invalid security-sensitive payloads against production systems
  (keep generative tests local and authorized)

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Property-based / generative invariants, Hypothesis, fast-check, 属性测试 | **This skill** | — |
| Example unit structure, AAA, naming, table-driven cases | `unit-testing-style` | this for universal properties |
| Mocks/fakes at I/O boundaries inside property setup | `mocking-and-test-doubles` | this for generators/properties |
| Production correctness, errors, security, verification depth | `code-quality-standards` | **always apply** on implementation fixes |
| Load / SLI / soak tests | `performance-testing-basics` | not PBT |
| Language style of test code | matching `*-style-*` skill | — |

### Routing to `unit-testing-style`

Keep **this skill primary** for property design, generators, and shrinking.
Use **`unit-testing-style`** when:

- Naming tests, AAA layout, and suite placement
- Adding **example** regressions for shrunk counterexamples
- Deciding unit vs integration scope for the harness around properties
- Table-driven fixed cases that document business rules alongside properties

PBT **extends** example tests; it does not replace readable unit examples.

### Routing to `code-quality-standards`

Keep **this skill primary** for how to express and run properties. Always apply
**`code-quality-standards`** when fixing code found by PBT or adding production
guards:

- Validate untrusted inputs at boundaries; properties often find gaps
- Fail clearly on contract violations; no silent clamp unless specified
- Deterministic seams for time/rng in both prod design and tests
- Do not “fix” a property by weakening production checks or assertions
- Treat counterexamples as defects until the property is proven wrong

### Routing to `mocking-and-test-doubles`

Use doubles only for **true external boundaries** (clock, entropy, HTTP) so
generation stays pure and fast. Prefer pure functions and fakes; do not mock
away the algorithm under property test.

## Checklist

- [ ] Repo PBT library, markers, seeds, and CI budget identified
- [ ] Property stated as a clear universal claim (not “randomly poke code”)
- [ ] Domain modeled in generators; minimal rejection sampling
- [ ] Strong pattern chosen (round-trip, oracle, invariant, metamorphic, …)
- [ ] Generation bounded for PR; expensive runs marked/nightly if needed
- [ ] Shrinking enabled; seed + shrunk input captured on failure
- [ ] Shrunk counterexample pinned as example unit test when it was a real bug
- [ ] No tautological properties; oracle independent of production code
- [ ] Deterministic (no real network/clock/rng without injection)
- [ ] Floats/collections/maps compared with appropriate equality rules
- [ ] Suite placement and naming consistent with `unit-testing-style`
- [ ] Doubles only at real boundaries (`mocking-and-test-doubles`)
- [ ] Production fix reviewed with `code-quality-standards`
- [ ] Focused property suite run (or gap noted) with reproducible seed

## Rules

- A green property with a wrong claim is false confidence—challenge the
  property as hard as the code.
- Prefer small pure units for PBT; push I/O to fakes or integration layers.
- Always keep a human-readable example for critical regressions.
- Repo libraries and time budgets win; this skill fills design and review gaps.
- Generative tests explore the space; specifications and example tests still
  teach the reader what the product guarantees.
