---
name: mutation-testing-basics
description: >
  Plan and review mutation testing: mutants, kill/survive scores, equivalent
  mutants, and CI budgets. Use when mutation testing, 变异测试, PIT, Stryker,
  mutmut, infection, mutant survival, or test strength beyond coverage %.
  Complements unit-testing-style and code-quality-standards; not load/chaos.
---

# Mutation Testing Basics

Mutation testing injects small **faults (mutants)** into production code and
checks whether the **test suite fails** (kills the mutant). Prefer
**repo-configured** PIT / Stryker / mutmut / Infection / cargo-mutants over a
one-off script. Coverage shows what ran; mutation score shows whether tests
would **notice** a change.

## Use When

- Assessing **test suite strength** beyond line/branch coverage
- Introducing or tuning **mutation tools** (PIT, Stryker, mutmut, Infection,
  cargo-mutants, Mull)
- Triaging **survived mutants** (weak tests vs equivalent/uninteresting)
- Setting **CI budgets** (scoped packages, incremental PR, nightly full)
- Triggers: mutation testing, 变异测试, mutant, mutation score, killed /
  survived, PIT, Stryker, mutmut, Infection, equivalent mutant

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Unit design, AAA, naming, what-to-test | `unit-testing-style` |
| Property / generative invariants | `property-based-testing` |
| Load / capacity | `performance-testing-basics` |
| Runtime fault injection (lab) | `chaos-engineering-basics` |
| Production reliability/security of product code | `code-quality-standards` |

## Repo Config First

Repo mutation and test config **outranks** this skill’s defaults.

1. **Tool present:** `stryker.conf.*`, PIT Maven/Gradle, mutmut/`pyproject`,
   Infection `infection.json*`, CI job names—**extend these**
2. **Runner integration:** which suite mutates; timeouts; workers
3. **Scope policy:** include/exclude (skip generated/DTOs); risk packages first
4. **Thresholds / baseline** mutation score gates and HTML report artifacts
5. **Unit style nearby** (`unit-testing-style`): AAA, factories, markers
6. **CI cost:** PR incremental vs nightly full; suppressions only with reasons

**Precedence:** Follow repo thresholds/excludes when they conflict. Surface
excludes that hide business logic, or coverage-only gates with no mutation on
critical packages.

## Core Ideas

| Term | Meaning |
| --- | --- |
| **Mutant** | Small auto-edit (`>`→`>=`, flip bool, delete call, change literal) |
| **Killed** | ≥1 test fails after mutation |
| **Survived** | All tests still pass — suite missed the fault |
| **Equivalent** | Semantically identical change; not usefully killable |
| **Score** | killed / (killed + survived) per tool policy |

Prefer the tool **default operators** first; expand only with time budget.

## Workflow

1. **Goal** — e.g. raise kill rate on `billing/` rules, not “100% everywhere.”
2. **Inventory** — tool, excludes, CI, unit runner, baseline report.
3. **Scope** — domain/validation/money/authz first; exclude noise deliberately.
4. **Green unit suite first** (`unit-testing-style`); no mutation on flaky red.
5. **Run slice** — record score, survivors, duration.
6. **Triage survivors** — add focused test, or document equivalent/out-of-scope.
   Never weaken production code to silence mutants.
7. **Pin gaps** as clear example tests; re-run same scope; track score trend.
8. **CI** — PR: changed/critical modules; nightly: broader; cap wall time.

## Good / Bad Examples

**Good — triage:** mutant `percent > 0` → `>= 0` survived → add
`test_apply_discount_zero_percent_…` per product rule.

**Bad — triage:** ignore all math mutants globally; or delete the production
check so the mutant vanishes.

**Good — scope:** mutate `src/billing/**` only; ignore specs/generated;
`thresholds.break: 60`. **Bad:** mutate `src/**` + `dist/**` with break `0`.

**Good — kill boundary**

```python
def test_clamp_rejects_above_max():
    with pytest.raises(ValueError, match="max"):
        clamp(11, lo=0, hi=10)
```

**Bad:** only `assert clamp(5, 0, 10) == 5` (happy path; boundary mutants live).

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Mutation score, PIT/Stryker/mutmut, survivors, 变异测试 | **This skill** | — |
| Tests that kill mutants (AAA, cases) | `unit-testing-style` | this for priority |
| Production fix after a finding | `code-quality-standards` | **always** |
| CI job duration / suite health metrics | `observability-metrics-tracing` | optional |
| Untrusted tool binary isolation | `security-sandbox` | rare |
| Runtime pod/network fault injection | `chaos-engineering-basics` | not mutation |

**This skill** for mutation goals/triage; **`unit-testing-style`** for tests that
kill mutants; **`code-quality-standards`** on prod changes (never remove
validation to “pass”); **`observability-metrics-tracing`** for pipeline metrics
only if needed; **`security-sandbox`** only for untrusted tooling.

## Checklist

- [ ] Repo tool, excludes, thresholds, CI job identified
- [ ] Unit suite green/non-flaky; scope risk-aligned (noise excluded on purpose)
- [ ] Survivors triaged (test gap vs equivalent vs ignore-with-reason)
- [ ] New tests match `unit-testing-style`; no prod weakening to dismiss mutants
- [ ] CI PR incremental vs nightly full stated; artifacts retained
- [ ] Prod changes reviewed with `code-quality-standards`
- [ ] Not confused with chaos/load testing

## Rules

- Survived mutants on critical logic are **test debt** until triaged.
- Coverage without mutation can be false confidence; mutation without solid
  units is expensive noise. Repo budgets win; kill with clear behavioral tests.
