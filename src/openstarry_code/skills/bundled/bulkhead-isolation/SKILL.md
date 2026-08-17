---
name: bulkhead-isolation
description: >
  Isolate failure domains with bulkheads: separate pools, semaphores, queues,
  and resource budgets so one dependency or tenant cannot exhaust the process.
  Use when bulkhead, isolation, noisy neighbor, pool per dependency, 舱壁,
  隔离舱, or cascading pool exhaustion. Complements circuit breakers, async
  bounds, and observability.
---

# Bulkhead Isolation

**Bulkheads** partition limited resources (threads, connections, concurrency
slots, queues) so overload or latency in one dependency, tenant, or workload
class cannot starve the rest. Prefer the repo’s existing pool and limit helpers
over a single shared unbounded executor.

## Use When

- One slow dependency, queue, or tenant is **starving** unrelated paths
- Designing **per-dependency** client pools, worker pools, or semaphores
- Separating **latency classes** (interactive vs batch) or priority work
- Preventing **cascading exhaustion** of threads, connections, or event-loop time
- User mentions: bulkhead, isolation, noisy neighbor, pool per host, 舱壁, 隔离

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Open/half-open fail-fast after errors | `circuit-breaker-patterns` |
| Cancel, structured tasks, general fan-out | `async-concurrency-patterns` |
| Streaming overflow / slow-consumer policy | `backpressure-patterns` |
| Pool saturation metrics/traces | `observability-metrics-tracing` |
| General reliability, errors, tests | `code-quality-standards` |

## Repo Config First

Repo libraries and platform limits **outrank** this skill’s defaults.

1. **Isolation primitives:** Resilience4j/Polly bulkheads, per-client HTTP pools,
   DB pool configs, named worker pools
2. **Mesh/gateway caps:** concurrency, connection, RPS at the edge—document
   stacked budgets
3. **Shared clients:** global vs per-dependency client patterns already in tree
4. **Multi-tenant quotas:** product fair-share and rate limits
5. **Timeouts:** pool wait must fit parent deadlines
6. **Telemetry:** existing utilization, wait, reject metrics
7. **Neighbors:** copy mature services’ per-dependency limits before inventing

**Precedence:** Follow the repo. Surface conflicts that share one unbounded pool
for all outbound I/O or let batch hold every slot.

## Workflow

1. **Map failure domains** — dependencies, tenants, workload classes that must
   not share fate.
2. **Inventory shared resources** — thread pools, DB/HTTP connections, queues.
3. **Choose isolation dimension** — per dependency (common), per class
   (interactive/batch), and/or per tenant fair-share.
4. **Pick mechanism** — semaphore, dedicated executor, connection pool, queue,
   or process/replica isolation.
5. **Set budgets** — max concurrent, max wait/queue, reject policy (prefer fail
   fast). Total slots ≤ real process capacity; optionally reserve minimums for
   critical paths.
6. **Compose** — pair with `circuit-breaker-patterns` (broken deps),
   `async-concurrency-patterns` (cancel/structure), `backpressure-patterns`
   (buffer overflow).
7. **Instrument** — in-use/max, wait, rejections per bulkhead name
   (`observability-metrics-tracing`).
8. **Test** — saturate domain A; domain B still meets SLO.

## Patterns

| Pattern | Partitions | Use |
| --- | --- | --- |
| Semaphore bulkhead | In-flight slots (+ optional wait) | Outbound RPC per dependency |
| Thread/executor bulkhead | Dedicated workers | Blocking I/O on mixed runtimes |
| Connection pool bulkhead | TCP/DB connections | One host must not drain shared pool |
| Queue bulkhead | Buffer per class | Interactive vs batch |
| Tenant fair-share | Weighted slots / tokens | Noisy-neighbor multi-tenancy |

## Good / Bad Examples

**Good** — separate limits:

```text
paymentsClient: maxConcurrent=20, maxWait=50ms, onFull=fail-fast
catalogClient:  maxConcurrent=50, maxWait=100ms
# dedicated pools or limiters; interactive not behind batch
```

**Bad** — one unbounded shared executor for HTTP + DB + email; one slow payment
host holds every worker → entire API 503s.

**Good** — batch on a smaller pool; checkout has its own semaphore and DB budget.

**Bad** — nightly export and checkout share DB pool size 10 with no acquire
timeout.

**Good** — per-tenant concurrency + global cap; excess 429; metrics by bulkhead
name (avoid raw tenant id as unbounded metric labels).

**Bad** — one tenant fans out 10k jobs and exhausts the process.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Pools, semaphores, per-dep/tenant resource budgets | **This skill** | — |
| Trip/open circuit; fail-fast when dep is down | `circuit-breaker-patterns` | this for caps |
| Cancel while waiting for a slot; structured fan-out | `async-concurrency-patterns` | this for partitions |
| Streaming/async buffer full policy | `backpressure-patterns` | this when partitions own buffers |
| Utilization, reject rate, wait histograms | `observability-metrics-tracing` | this for what to meter |
| Implementation hygiene, errors, tests | `code-quality-standards` | **always** |

Keep **this skill primary** for isolation. Always apply
**`code-quality-standards`**. Use **`circuit-breaker-patterns`** for trip state,
**`async-concurrency-patterns`** for cancel/structure,
**`observability-metrics-tracing`** for saturation signals.

## Checklist

- [ ] Failure domains listed (deps, tenants, classes)
- [ ] Shared pools/executors/queues inventoried
- [ ] Isolation dimension + mechanism chosen
- [ ] Max concurrent, max wait/queue, reject policy documented
- [ ] Total capacity coherent; critical paths reserved if needed
- [ ] Acquire waits honor parent deadlines/cancel
- [ ] Composed with circuit breaker / backpressure where appropriate
- [ ] Metrics: in-use, wait, rejections (`observability-metrics-tracing`)
- [ ] Test: saturating A does not collapse B
- [ ] `code-quality-standards` + `async-concurrency-patterns` applied as needed
