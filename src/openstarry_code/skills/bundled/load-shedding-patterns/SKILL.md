---
name: load-shedding-patterns
description: >
  Design load shedding under overload: admission control, priority queues,
  graceful degradation, and drop/reject policies that protect critical paths.
  Use when load shedding, overload, backpressure, 限流丢弃, 过载保护, 503
  shedding, queue full, admission control, or graceful degradation under
  capacity pressure. Complements retries and circuit breakers; not a substitute
  for capacity planning or unbounded concurrency fixes.
---

# Load Shedding Patterns

Survive **overload** by admitting less work deliberately so critical traffic
stays healthy. Prefer repo rate limiters, bulkheads, mesh/gateway policies, and
queue bounds over ad-hoc drops.

## Use When

- Protecting a service under **overload**, spikes, or dependency slowdown
- Designing **admission control**, queue caps, **priority** shedding
- Choosing **reject vs degrade vs drop** (503/429, lite mode, best-effort drop)
- Stopping retry storms from full queues or saturated pools
- User mentions: load shedding, overload, backpressure, admission control,
  graceful degradation, 过载, 限流, 丢弃, 降级

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Retry / backoff after transient failure | `retry-backoff-patterns` |
| Per-dependency fail-fast (open circuit) | `circuit-breaker-patterns` |
| Cancel, deadlines, worker pools | `async-concurrency-patterns` |
| Saturation metrics / RED alerts | `observability-metrics-tracing` |
| General reliability, tests, security | `code-quality-standards` |

## Repo Config First

Repo, mesh, and platform limits **outrank** this skill’s defaults.

1. **Admission tools:** gateway quotas, Envoy/local rate limits, token buckets,
   semaphores, queue max depth, HPA/limits
2. **Pool sizes:** server max concurrent, worker pools, DB pool, gRPC streams
3. **Priority policy:** SLA tiers, internal vs external, read vs write headers
4. **Degrade flags:** kill switches / lite-mode paths already used in incidents
5. **Client contracts:** 429/503, `Retry-After`, idempotency expectations
6. **Observability:** queue depth, reject rate, pool wait, overload alerts
7. **Neighbors:** copy 2–3 mature admit patterns before inventing drop policy

**Precedence:** Follow repo/gateway policy on conflict. Surface silent drops
without metrics, shedding health/auth, or clients retrying shed traffic unboundedly.

## Workflow

1. **Capacity and criticality** — safe concurrent/queue depth; must-serve
   (health, auth, payment commit) vs sheddable (analytics, non-critical reads).
2. **Control point (early)** — edge → server admit → handler semaphore →
   outbound bulkhead → queue producer.
3. **Shed signals** — in-flight/queue depth, latency/SLO burn, pool/CPU USE,
   token bucket.
4. **Action by class** — **reject fast** (preferred HTTP/RPC); **degrade**
   (skip optional work); **drop** only for accepted-loss telemetry.
5. **Protect control plane** — do not shed liveness incorrectly; keep kill-switch path.
6. **Client coordination** — `Retry-After` when useful; often **avoid** inviting
   immediate retries on pure overload.
7. **Instrument and test** — reject reason metrics; flood sheddable class and
   prove critical class still meets a floor SLO.

## Strategies

| Strategy | Prefer when |
| --- | --- |
| Hard concurrency limit (semaphore) | CPU-bound handlers, fixed pools |
| Bounded queue + reject | Async workers, message ingress |
| Token bucket / RPS cap | Multi-tenant edge fairness |
| Priority shedding | Mixed critical + best-effort |
| Latency-aware admit | Slow dependency cascade |
| Cooperative degradation | Partial UX better than outage |

**Rule:** Fail **cheap and early** with a **clear signal**. Unbounded queues are
delayed failure, not shedding.

## Good / Bad Examples

**Good** — bound in-flight; reject with 503 + `Retry-After` + stable code before
expensive work; metric `admit_rejected_total{reason=...}`.

```ts
if (inFlight >= MAX_IN_FLIGHT) {
  metrics.incr("admit_rejected_total", { reason: "in_flight" });
  return res.status(503).set("Retry-After", "2").json({
    code: "SERVICE_OVERLOADED",
    message: "Service is busy. Try again later.",
  });
}
```

**Bad** — unbounded `queue.push(req)`; multi-minute waits; no reject metric.

**Good** — under pressure, reject `priority=bulk` before interactive user API.

**Bad** — random drops including checkout and health checks.

**Good** — skip personalized ranking; serve cached top-N; mark degraded for metrics.

**Bad** — fan-out five non-critical deps with full retries while core is saturated.

**Good** — clients use **budgeted** backoff + jitter (`retry-backoff-patterns`).

**Bad** — 500 with no policy; clients hammer every 50 ms until OOM.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Overload admit/reject, priority shed, degrade | **This skill** | — |
| Client retry after 429/503; budgets; no storms | `retry-backoff-patterns` | this for shed signals |
| Failing **dependency** isolation | `circuit-breaker-patterns` | this if local capacity |
| Semaphores, workers, cancel, bounds | `async-concurrency-patterns` | this for admit policy |
| Reject/saturation metrics and alerts | `observability-metrics-tracing` | this for shed triggers |
| Implementation quality, tests, security | `code-quality-standards` | **always** |

Keep **this skill primary** for overload admission. Always apply
**`code-quality-standards`**. Pair **`async-concurrency-patterns`** for
in-process limits/cancel; **`retry-backoff-patterns`** so clients do not undo
shedding; **`observability-metrics-tracing`** for saturation signals;
**`circuit-breaker-patterns`** when the issue is a **broken peer**, not only
excess local demand.

## Checklist

- [ ] Gateway limits, pools, queue max, degrade flags inventoried
- [ ] Critical vs sheddable classified; health/admin protected
- [ ] Early control point chosen; capacity signals defined
- [ ] Action: reject / degrade / drop with stable codes (429/503)
- [ ] Priority/tenant fairness defined when multi-class traffic shares capacity
- [ ] Client retry budgeted; no nested retry storms encouraged
- [ ] Cancel/deadlines free resources for waiting or rejected work
- [ ] Metrics: admit, reject reason, depth, degraded rate; alerts on burn
- [ ] Load test: flood sheddable; critical still meets floor SLO
- [ ] `code-quality-standards` + helpers per Routing table applied
