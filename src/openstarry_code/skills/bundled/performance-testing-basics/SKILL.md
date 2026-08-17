---
name: performance-testing-basics
description: >
  Plan and review basic performance and load tests: goals, SLIs, scenarios,
  workloads, and high-level tools. Use when performance testing, 性能测试,
  load test, stress test, soak test, latency percentiles, k6, JMeter, Gatling,
  Locust, or capacity checks. Complements observability SLIs and
  code-quality-standards; not a substitute for unit or property tests.
---

# Performance Testing Basics

Performance tests answer **whether the system meets timed and capacity goals
under a defined load**—not whether business logic is correct. Prefer **repo and
platform** load-tool configs, environments, and SLOs over inventing a one-off
script against production. Keep goals quantitative (latency, error rate,
throughput) and evidence reproducible.

## Use When

- Planning or reviewing **load**, **stress**, **soak**, **spike**, or
  **capacity** tests
- Defining **performance SLIs/SLOs** (latency percentiles, error ratio, RPS)
  for a test pass
- Choosing a **high-level tool** approach (k6, JMeter, Gatling, Locust,
  vegeta, NBomber, cloud load services)
- Interpreting p50/p95/p99, saturation, and “pass/fail” against a budget
- User mentions: performance testing, 性能测试, load test, 压力测试, stress
  test, soak test, spike test, benchmark, latency, throughput, RPS, p95, p99,
  k6, JMeter, Gatling, Locust, Artillery, capacity test

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Correctness unit tests, AAA, naming | `unit-testing-style` |
| Property / generative functional tests | `property-based-testing` |
| Production metrics/traces design (always-on) | `observability-metrics-tracing` |
| App reliability, retries, bounds in code | `code-quality-standards` |
| CI pipeline wiring only | `ci-cd-pipeline-patterns` |
| Micro-benchmark only (language `testing.B`, Criterion) | this skill lightly + language style; still set goals |

## Repo Config First

Repo, env, and platform performance config **outrank** this skill’s defaults.

1. **Existing load tools & folders:** `k6/`, `load-tests/`, JMeter `.jmx`,
   Gatling sims, Locust `locustfile`, CI workflow names—**extend these**
2. **Target environment policy:** dedicated perf env vs scaled staging; **never
   assume** production load tests are allowed—require explicit ownership
3. **SLOs and budgets:** product/SRE latency error budgets, partner API limits,
   published non-functional requirements (NFRs)
4. **Auth and test data:** service accounts, synthetic users, seed datasets,
   anonymization rules—match how neighboring perf scripts authenticate
5. **Observability during tests:** dashboards, RED metrics, APM, log volume
   limits (`observability-metrics-tracing`)
6. **CI gates:** which suites are PR smoke (tiny load) vs nightly/pre-release
   full load; artifact retention for HTML/JSON reports
7. **Isolation & cost:** max RPS caps, cloud spend alerts, shared-tenant rules
8. **Neighboring scenarios:** copy think time, ramp, and pass criteria from a
   mature suite before inventing new shapes

**Precedence:** Follow repo/env policy when it conflicts with examples below.
Surface conflicts that load-test production without approval, skip baseline
comparison, or “pass” on average latency while p99 burns the SLO.

## Test Types (high level)

| Type | Question | Typical shape |
| --- | --- | --- |
| **Smoke / sanity load** | Does the script work? Can the env take a trickle? | Few VUs, short |
| **Load** | Meet SLO under expected peak? | Ramp to target RPS/VUs, hold |
| **Stress** | Where does it break? | Beyond peak until errors/latency cliff |
| **Spike** | Survive sudden surge? | Steep ramp up/down |
| **Soak / endurance** | Leak, bloat, or degradation over time? | Moderate load, hours |
| **Capacity / breakpoint** | Max sustainable throughput with SLO held? | Step-up until fail |
| **Scalability** | Does adding instances buy linear capacity? | Repeat under N replicas |
| **Benchmark (micro)** | Is this function/path faster after a change? | Tight loop; isolate CPU |

Use **load** for release confidence; **stress/soak** for risk discovery; do not
call a 30-second local hit “performance sign-off.”

## SLIs, SLOs, And Pass Criteria

Define **Service Level Indicators** for the test before running traffic:

| SLI family | Examples | Notes |
| --- | --- | --- |
| **Latency** | p50, p95, p99, max of request duration | Prefer percentiles over averages |
| **Availability / errors** | HTTP 5xx rate, timeout rate, business error ratio | Separate client (4xx) from server faults when relevant |
| **Throughput** | RPS, transactions/min completed **successfully** | Open vs closed workload models differ |
| **Saturation** | CPU, memory, queue depth, pool wait, GC | USE signals explain *why* SLIs fail |
| **Correctness under load** | checksum samples, idempotent create counts | Load without validation can hide data loss |

**Pass criteria sketch (document per scenario):**

```text
At 500 RPS for 10m after 5m ramp:
  - http_req_failed < 0.1%
  - p95(latency) < 300ms, p99 < 800ms
  - no error budget burn beyond X
  - no pod OOM / restart storm
```

Tie criteria to **product SLOs** when they exist; otherwise state an explicit
**NFR budget** for the change. Averages alone are not enough.

## Workload Model Basics

| Concept | Meaning |
| --- | --- |
| **VU / concurrent users** | Parallel sessions (closed model often) |
| **Arrival rate (open)** | RPS independent of response time (prefer for servers) |
| **Ramp / stages** | Warm-up → steady → cool-down |
| **Think time** | Pause between user actions (more realistic) |
| **Scenario mix** | Weighted paths (browse 70%, checkout 30%) |
| **Data cardinality** | Unique ids/tokens so caches and DB plans are realistic |

**Closed model pitfall:** slow responses reduce throughput automatically and
can hide saturation. Prefer **constant-arrival** styles when the tool supports
them and the goal is “RPS at SLO.”

## Tools (high level—prefer repo choice)

| Tool | Ecosystem | Notes |
| --- | --- | --- |
| **k6** | JS scripts, CLI, cloud option | Good DX, thresholds as code, CI-friendly |
| **JMeter** | GUI + XML plans, Java | Broad protocol plugins; plans can get heavy |
| **Gatling** | Scala/Java DSL | Strong reporting; code-centric |
| **Locust** | Python | Flexible scenarios; scale workers |
| **Artillery** | YAML/JS | API-focused, quick starts |
| **vegeta** | Go CLI | Simple HTTP attack reports |
| **NBomber** / **Bombardier** / cloud (Azure Load Testing, etc.) | varies | Match org platform |

This skill does **not** mandate a tool. Prefer what the repo already runs in CI
and what operators can re-run from docs.

## Workflow

1. **Name the goal and risk.** e.g. “p95 < 300ms at 2× current peak for
   checkout API after cache change,” not “make it faster.”
2. **Inventory repo perf assets.** Existing scripts, envs, auth, SLOs,
   dashboards, CI jobs, data seeders.
3. **Pick test type and environment.** Load vs soak vs stress; staging shape
   vs production (authorized only). Confirm isolation and blast radius.
4. **Define scenarios and data.** Critical user journeys; realistic mix;
   unique test data; cache-warm vs cold policy stated.
5. **Write SLIs and thresholds** as pass/fail (tool thresholds or report
   gates). Include error rate **and** latency percentiles.
6. **Establish baseline.** Run the same scenario on known-good revision or
   pre-change env; store reports as artifacts.
7. **Ramp safely.** Smoke → partial load → target. Abort on error storms or
   budget burn to protect shared envs.
8. **Observe while testing.** RED on entrypoints, USE on CPU/mem/pools,
   dependency latency (`observability-metrics-tracing`). Correlate load stages
   with deploys and autoscaling events.
9. **Interpret results.** Pass/fail vs thresholds; compare to baseline;
   explain failures with saturation or dependency evidence—not only “k6 red.”
10. **Act and re-test.** Fix or tune; re-run the **same** scenario; attach
    before/after. Add unit/regression tests if a logic bug appeared under load
    (`unit-testing-style`, `code-quality-standards`).
11. **Record limits.** Document max validated RPS, known bottlenecks, and
    follow-ups (index, pool size, cache, query).

## Good / Bad Examples

### Goal and thresholds

**Good**

```text
Scenario: POST /checkout, open model 300 RPS, 5m ramp, 15m hold
Pass: p95 < 250ms, p99 < 600ms, failed < 0.1%, checkout success business code
Baseline: main@abc123 report attached
Env: perf-staging (4 api + managed DB), same flags as prod
```

**Bad**

```text
"Run JMeter until it feels fine"
Pass if average latency < 1s   # hides p99 disasters
Hit production Black Friday week without approval
```

### k6-style threshold sketch

**Good**

```js
// Sketch — follow repo’s real k6 layout and auth helpers
export const options = {
  scenarios: {
    checkout: {
      executor: "constant-arrival-rate",
      rate: 300,
      timeUnit: "1s",
      duration: "15m",
      preAllocatedVUs: 50,
      maxVUs: 200,
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.001"],
    http_req_duration: ["p(95)<250", "p(99)<600"],
  },
};
```

**Bad**

```js
export const options = { vus: 10000, duration: "1h" }; // no thresholds, no ramp, shared env risk
export default function () {
  http.get("https://production.example/"); // unauthorized / uncontrolled blast radius
}
```

### Scenario mix

**Good**

```text
70% GET /catalog (cacheable)
20% GET /cart
10% POST /checkout
Think time 1–3s on browse; no think time on API capacity pure test (stated)
```

**Bad**

```text
100% heaviest report export endpoint only, then claim "site can take Black Friday"
```

### Reading results

**Good**

```text
p95 OK until 450 RPS; at 500 RPS p99 cliffs + DB pool wait spikes
Conclusion: pool max / query plan bottleneck; not "need bigger CI runner"
Evidence: APM DB span + pool USE metrics during stage 3
```

**Bad**

```text
"Latency high" with no percentile, no RPS, no baseline, no dependency view
Tuning GC based on one 60s run with cold caches
```

### Micro-benchmark vs load test

**Good** — use language benchmark for a pure parser hot path; use load test for
the HTTP + DB checkout path. Do not equate ns/op with user SLO.

**Bad** — ship only a micro-benchmark of JSON serialization as “performance QA”
for a multi-service release.

## Anti-Patterns

- Load testing production without explicit authorization and guardrails
- No baseline → cannot tell regression from noise
- Pass on **average** latency only; ignore error rate and p99
- Unrealistic data (same user id, tiny tables) that overstates cache hits
- Coordinated omission: closed workload looks healthy while queueing grows
- Skipping warm-up then declaring cold-start failure a release blocker (or the
  reverse: only warm paths measured when users hit cold)
- Changing code **and** test script between baseline and candidate
- Treating tool green as product green without checking business success codes
- Running soak for 5 minutes and claiming memory-leak freedom
- Ignoring client-side timeouts that mark failures the server never sees
- Coupling perf scripts to brittle UI selectors when an API scenario would do
- Using performance tests as the only functional test suite

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Load/perf plans, SLIs for tests, k6/JMeter/Locust scenarios, 性能测试 | **This skill** | — |
| Always-on metrics, traces, RED/USE instrumentation | `observability-metrics-tracing` | this for experiment design |
| Correctness unit/example tests | `unit-testing-style` | this only if load exposed a bug to pin |
| Property/invariant generative tests | `property-based-testing` | not load |
| Production code fixes from perf findings | `code-quality-standards` | **always apply** on implementation |
| CI job wiring for perf workflows | `ci-cd-pipeline-patterns` | this for what to measure |
| Caching as the fix under test | `caching-strategies` | this for measuring impact |
| Retries amplifying load | `retry-backoff-patterns` | this for storm symptoms |

### Routing to `unit-testing-style`

Keep **this skill primary** for load/perf experiments and SLI thresholds.
Use **`unit-testing-style`** when:

- Pinning a functional bug found under load as a fast unit/integration example
- Testing pure computational regressions with table-driven cases or benchmarks
  that do not need a fleet
- Keeping correctness suites healthy so perf tests are not misused as the only gate

Performance green never replaces behavior tests.

### Routing to `code-quality-standards`

Keep **this skill primary** for how to plan and judge performance tests. Always
apply **`code-quality-standards`** when implementing optimizations or fixes:

- Measure before and after; avoid speculative complexity
- Bounds, timeouts, and backpressure rather than unbounded queues
- No security or correctness regressions “for speed”
- Clear errors under overload (fail fast, load shed) with safe messages
- Verification: automated test or documented perf re-run attached to the change

### Routing to `observability-metrics-tracing`

Use **`observability-metrics-tracing`** so test runs are interpretable: RED on
the boundary under test, USE on pools/nodes, correlation ids for sample
failures. This skill decides **workload and pass/fail**; observability explains
**where time and errors go**.

## Checklist

- [ ] Goal stated as measurable SLI/SLO or NFR budget (percentiles + errors)
- [ ] Repo tools, scripts, auth, env policy, and CI perf jobs inventoried
- [ ] Environment authorized and isolated; blast radius acceptable
- [ ] Test type chosen (load/stress/soak/spike/capacity) with duration justified
- [ ] Scenarios and traffic mix reflect real critical paths (or deviation noted)
- [ ] Data realism: cardinality, cache policy, auth, seed strategy
- [ ] Workload model stated (open arrival vs closed VUs); ramp defined
- [ ] Thresholds encoded in tool or explicit report gate
- [ ] Baseline captured on comparable revision/env
- [ ] Observability dashboards watched (RED + key USE/dependencies)
- [ ] Results compared to baseline; bottleneck hypothesis evidence-backed
- [ ] Findings lead to fix or accepted risk; same scenario re-run after change
- [ ] Artifacts (report, seed, config, commit SHA) stored for repro
- [ ] Functional regressions pinned with `unit-testing-style` when applicable
- [ ] Production changes reviewed with `code-quality-standards`
- [ ] Not run as a substitute for unit/integration correctness suites

## Rules

- **Goals first, tools second.** A precise budget beats a fancy script.
- Percentiles and error rates beat averages; success RPS beats attempted RPS.
- Never load-test systems you do not own or lack permission to stress.
- Reproducibility (script + data + env + SHA + report) is part of the result.
- Repo and platform standards win; this skill is the planning and review bar.
- Performance work without observation is guesswork—instrument, then stress.
