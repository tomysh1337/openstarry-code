---
name: circuit-breaker-patterns
description: >
  Design circuit breakers for dependency isolation: closed/open/half-open
  states, failure thresholds, probe recovery, and fallbacks. Use when circuit
  breaker, 熔断, bulkhead isolation, fail-fast dependency, open circuit, or
  cascading failure protection toward a slow or erroring peer. Complements
  retries and load shedding; not a substitute for fixing the dependency.
---

# Circuit Breaker Patterns

**Fail fast toward unhealthy dependencies** so local resources and callers are
not dragged into a cascade. Prefer repo resilience libraries (Resilience4j,
Polly, Istio outlier detection) over hand-rolled state machines.

## Use When

- Isolating a **slow or erroring dependency** (HTTP/RPC, DB, cache, third-party)
- Stopping **cascading failures**, pool exhaustion, or retry amplification
- Designing **closed / open / half-open**, thresholds, windows, and probes
- Providing **fallback** while a peer is isolated
- User mentions: circuit breaker, 熔断, open/half-open, fail-fast, cascading failure, outlier detection

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Transient retry, backoff, jitter, idempotency | `retry-backoff-patterns` |
| Inbound overload admit/reject | `load-shedding-patterns` |
| Cancel, deadlines, bulkheads only | `async-concurrency-patterns` |
| Breaker/dependency metrics and traces | `observability-metrics-tracing` |
| General reliability, tests, security | `code-quality-standards` |

## Repo Config First

Repo and mesh resilience config **outrank** this skill’s defaults.

1. **Existing breakers:** Resilience4j, Polly, `gobreaker`, Spring Cloud CB,
   Envoy/Istio outlier ejection — **extend these**
2. **Timeouts first** — breakers without client deadlines are ineffective
3. **Retry interaction** — disable or sharply reduce retries when open
4. **Bulkheads** — per-dependency pools/semaphores already isolating peers
5. **Fallbacks** — caches, defaults, feature-flag degraded modes
6. **Error taxonomy** — 5xx/timeout trip; most 4xx and client cancel do **not**
7. **Observability** — state metrics, transition events, peer RED dashboards
8. **Neighbors** — copy mature clients’ thresholds and breaker naming

**Precedence:** Follow repo/mesh policy on conflict. Surface open-on-4xx, retries
through open breakers, or one global breaker across unrelated hosts.

## Workflow

1. **Scope** — one breaker per dependency + operation class (or host group), not
   one process-wide switch.
2. **Baseline** — set **timeouts** and **concurrency caps**
   (`async-concurrency-patterns`) before tuning trip rates.
3. **Define failure** — timeouts, connect errors, selected 5xx; exclude most 4xx,
   caller cancel, intentional business rejection.
4. **Trip policy** — min volume in window; failure-rate or consecutive failures;
   optional slow-call rate for latency outages.
5. **Open + half-open** — open fails fast (or fallback); half-open allows limited
   probes; success → close; failure → open.
6. **Compose retries** — only inside a **closed** budget; open means **stop calling**.
7. **Fallback** — cache/default/queue-later or clear degraded error—never false success on money/auth.
8. **Observe and test** — transitions, rejects, probes; chaos: down, slow, flap.

## State Machine

```text
CLOSED --(failure threshold)--> OPEN --(wait)--> HALF-OPEN
  ^                                                    |
  +-------------------- probe success -----------------+
  OPEN <---------------- probe failure ----------------+
```

| State | Behavior |
| --- | --- |
| **Closed** | Normal calls; record results in sliding window |
| **Open** | Fail fast locally; do not call dependency |
| **Half-open** | Limited probes; re-evaluate health |

## Good / Bad Examples

**Good** — library breaker with timeout, volume threshold, fallback, state metrics:

```ts
const breaker = new CircuitBreaker(callPayment, {
  timeout: 2_000,
  errorThresholdPercentage: 50,
  resetTimeout: 10_000,
  volumeThreshold: 20,
});
breaker.fallback(() => ({ ok: false, code: "PAYMENTS_DEGRADED" }));
```

**Bad** — no timeout; blind retry on every error (amplifies outage).

**Good** — trip on peer timeout/503; do **not** trip on 400 invalid card.

**Bad** — any exception counts; validation bugs open the breaker for everyone.

**Good** — separate breakers/pools for `billing-api` vs `recommend-api`.

**Bad** — one global breaker; unbounded parallel calls to a dying peer.

**Good** — half-open allows 1–N probes; emit state metric on transitions.

**Bad** — open → full traffic instantly (recovery stampede).

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Breaker states, thresholds, fallbacks | **This skill** | — |
| Retry when closed; budgets; no retry while open | `retry-backoff-patterns` | this for open behavior |
| Inbound overload shed | `load-shedding-patterns` | this for outbound isolation |
| Timeouts, bulkheads, cancel, bounds | `async-concurrency-patterns` | this for trip machine |
| State metrics, peer RED, alerts | `observability-metrics-tracing` | this for transitions |
| Implementation quality, tests, security | `code-quality-standards` | **always** |

Keep **this skill primary** for dependency isolation. Always apply
**`code-quality-standards`**. Pair **`async-concurrency-patterns`** for
timeouts/bulkheads; **`retry-backoff-patterns`** so retries respect open state;
**`observability-metrics-tracing`** for state/peer SLIs; **`load-shedding-patterns`**
when **inbound** demand must be rejected due to local saturation.

## Checklist

- [ ] Resilience library / mesh outlier config reused
- [ ] Breaker scoped per dependency (or justified group)
- [ ] Timeouts + bulkheads set before threshold tuning
- [ ] Failure taxonomy: trip vs non-trip (4xx/cancel)
- [ ] Trip policy: min volume, rate/consecutive, window documented
- [ ] Open wait + half-open probe limit; no full-traffic slam
- [ ] Retries reduced/disabled when open; overall budget clear
- [ ] Fallback domain-safe (no false success on money/auth)
- [ ] Metrics: state, rejects, probe outcomes; alert if stuck open
- [ ] Tests: peer down → open; recovery → half-open → close; 4xx no trip
- [ ] `code-quality-standards` + helpers per Routing table applied
