---
name: chaos-engineering-basics
description: >
  Plan authorized chaos and fault-injection experiments in lab or owned
  non-prod: hypothesis, blast radius, steady state, inject/observe/stop.
  Use when chaos engineering, 混沌工程, fault injection, GameDay, Litmus,
  Chaos Mesh, Gremlin, toxiproxy, or resilience drills. Lab/owned only—not
  production without explicit approval. Complements observability and CQS.
---

# Chaos Engineering Basics (Authorized Lab Only)

Chaos engineering runs **controlled fault experiments** to learn whether the
system keeps a defined **steady state** under failure. Prefer **repo/platform**
chaos tools and lab/staging over ad-hoc kills. **Authorization and blast-radius
limits are mandatory.** Default target = lab / local compose / dedicated staging.

## Use When

- Designing **chaos / fault-injection** experiments (lab, staging, or approved
  prod GameDays only)
- Defining **hypothesis**, **steady-state metrics**, injectors, and **abort**
- High-level tools: Chaos Mesh, Litmus, Gremlin, AWS FIS, toxiproxy, Pumba,
  lab `tc`/iptables, kill-pod drills
- Triggers: chaos engineering, 混沌工程, fault injection, GameDay, network
  delay/partition in lab, dependency-down drill, resilience experiment

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Unit/example test design | `unit-testing-style` |
| Source mutants for test strength | `mutation-testing-basics` |
| Load without fault injection | `performance-testing-basics` |
| Always-on metrics/traces design | `observability-metrics-tracing` |
| Production hardening after findings | `code-quality-standards` |
| Malware/exploit detonation lab | `security-sandbox` |

**Hard gate:** No chaos on systems you do not own or lack written permission to
disrupt. Production only with named approver, window, and abort authority.

## Repo Config First

Platform and repo chaos policy **outrank** this skill’s defaults.

1. **Existing tooling:** Chaos Mesh/Litmus, Gremlin, FIS, toxiproxy, `chaos/`,
   GameDay docs—**extend these**
2. **Env allow-list:** namespaces/projects allowed; prod blocked by default
3. **Injector RBAC:** least privilege (no cluster-admin by habit)
4. **Steady-state SLIs** already on-call (`observability-metrics-tracing`)
5. **Abort/rollback:** flags, traffic shift, snapshot restore, bridge procedure
6. **Data/tenancy:** synthetic tenants; copy duration/scope from mature drills

**Precedence:** Honor org “no prod chaos” / change windows. Surface experiments
with unbounded blast radius or no hypothesis.

## Building Blocks

| Element | Meaning |
| --- | --- |
| **Steady state** | Measurable normal (success ≥ X%, p95 < budget) |
| **Hypothesis** | “If we inject X, steady state holds because Y” |
| **Fault** | Latency, errors, pod/process kill, CPU/disk stress, partition, dependency block |
| **Blast radius** | Traffic/users/namespaces that can be hurt |
| **Abort** | Metric or human stop before a real incident |

Lab examples: kill 1 replica; +200ms to dependency; stub HTTP 500; block one
host DNS; disk-full on a worker; compose partition A↔B.

## Workflow

1. **Authorize** — owner, env, window, contacts. Stop if unclear. Prefer lab;
   use `security-sandbox` for high-risk local injectors on a workstation.
2. **Hypothesis + steady state** with **metrics** (not “should be fine”).
3. **Open observability** — RED, dependency errors, restarts, synthetics
   (`observability-metrics-tracing`) before inject.
4. **Minimize blast** — one service/namespace, canary %, synthetic load;
   time-box (e.g. 5–15m). Define abort (error rate / SLO burn / manual).
5. **Dry-run** script/manifest; verify rollback.
6. **Inject once** — single primary fault; record start time and config SHA.
7. **Observe** steady state during run—not only “tool completed.”
8. **Stop + restore** — remove toxics/policies; confirm recovery.
9. **Document learning** — pass/fail vs hypothesis; tickets for gaps.
10. **Fix + pin** — resilience via `code-quality-standards`; logic via
    `unit-testing-style`; re-run the same hypothesis when possible.

## Good / Bad Examples

**Good — card:** env `payments-lab` (approved); hypothesis kill 1/3 api pods →
success ≥ 99.5%, p95 < 300ms for 10m; steady = success ratio + p95 + ready;
blast = that ns + synthetic only; abort success < 99% for 2m or manual.

**Bad:** “chaos monkey on prod Friday,” no metrics/abort, all namespaces.

**Good — lab toxic:** edge → toxiproxy → fake-payment; +200ms for 5m; observe
timeouts, retries, idempotency (no double charge). **Bad:** iptables DROP on
shared staging DB for all teams, no announcement.

**Good — after:** hypothesis FALSE → worker deadline + unit test; re-run with
Grafana/trace/manifest evidence. **Bad:** “tool OK,” NetworkPolicy left on.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Chaos design, GameDay, authorized fault injection, 混沌工程 | **This skill** | — |
| Steady-state SLIs, RED/USE, traces during run | `observability-metrics-tracing` | **required** |
| Timeouts, bulkheads, fallbacks, safe errors | `code-quality-standards` | **always on fixes** |
| Pin logic bugs from drill | `unit-testing-style` | this frames experiment |
| Dangerous local tooling isolation | `security-sandbox` | host-level faults |
| Pure load without faults | `performance-testing-basics` | optional combine |
| Source-level mutant killing | `mutation-testing-basics` | different layer |

**This skill** = experiment design/safety. **`observability-metrics-tracing`** =
steady state (without metrics, chaos is breakage). **`code-quality-standards`** =
product resilience fixes. **`unit-testing-style`** = pin pure regressions.
**`security-sandbox`** = isolate untrusted/host-destructive injectors; cluster
GameDays still need platform auth, not only a local VM.

## Checklist

- [ ] Authorization + env allow-list (lab default); no unowned/prod without approval
- [ ] Hypothesis + steady-state metrics; blast minimized; abort defined
- [ ] Dashboards ready (`observability-metrics-tracing`); dry-run/rollback OK
- [ ] Single primary fault; config/time recorded; recovery + cleanup verified
- [ ] Learning documented; fixes via `code-quality-standards`; tests via `unit-testing-style`
- [ ] High-risk local tools isolated (`security-sandbox`) when needed

## Rules

- **Permission before cleverness.** Unauthorized chaos is an outage.
- Hypothesis + steady state mandatory; tool-green is not learning. Small blast,
  short windows, strong abort. Repo policy wins; chaos finds gaps—tests/CQS close them.
