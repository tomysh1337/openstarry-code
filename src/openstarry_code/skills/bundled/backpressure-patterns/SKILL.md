---
name: backpressure-patterns
description: >
  Backpressure for async/streaming: bounded buffers, pull flow control,
  drop/sample/shed, slow consumers. Use when backpressure, bounded channel,
  overflow, 背压, 反压, or producer outruns consumer. Complements bulkheads,
  circuit breakers, async concurrency, and observability.
---

# Backpressure Patterns

**Backpressure** signals that consumers cannot keep up so producers slow down,
buffer **within bounds**, or shed load—else memory/latency collapse. Prefer
repo stream/channel/queue libraries over unbounded push into memory.

## Use When

- Producers can outrun consumers (ingest, websockets, logs, pipelines)
- Designing **bounded queues/channels**, reactive streams, or stage buffers
- Choosing **block / drop / sample / conflate / shed** when buffers fill
- Handling **slow consumers**, bursts, or fan-in aggregation
- User mentions: backpressure, slow consumer, overflow, 背压, 反压, 有界队列,
  Reactive Streams, `highWaterMark`, bounded channel

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Per-dependency partitions / noisy neighbor | `bulkhead-isolation` |
| Cancel, structured tasks, general fan-out | `async-concurrency-patterns` |
| Fail-fast after repeated dependency errors | `circuit-breaker-patterns` |
| Queue depth / lag / drop metrics | `observability-metrics-tracing` |
| General reliability, errors, tests | `code-quality-standards` |

## Repo Config First

Repo and platform flow-control config **outrank** this skill’s defaults.

1. **Stream/queue APIs:** Reactive Streams, Rx, Kotlin Flow, channels,
   Node `highWaterMark`, Kafka max poll, HTTP/2 windows
2. **Broker/proxy limits:** max queue length, lag alerts, ingress RPS, body size
3. **Protocol windows:** TCP/HTTP/2/gRPC flow control—avoid huge app buffers
   that hide pressure
4. **Deadlines:** blocking producers must still honor cancel
5. **Tenant quotas:** product RPS and fair queues already defined
6. **Telemetry:** depth, lag, drop/reject names already in use
7. **Neighbors:** copy mature stages’ sizes and overflow modes

**Precedence:** Follow the repo. Surface unbounded “temporary” queues or silent
drops of critical business events.

## Workflow

1. **Name the path** — who pushes, who pulls, where memory can accumulate.
2. **Correctness contract** — lossless (orders): block, durable queue, or
   reject/retry; lossy OK (metrics/UI): sample, conflate, or drop-old.
3. **Bound every buffer** — max length and/or bytes; no open-ended pending lists
   for untrusted rates.
4. **Choose overflow policy** per stage; document it (table below).
5. **Prefer pull/credit/demand** when supported (`request(n)`, channel recv).
6. **Propagate pressure upstream** — full buffer → slow/reject source (429/503,
   pause read), not only a warning log.
7. **Partition if needed** — `bulkhead-isolation` so one stream cannot fill a
   shared void.
8. **Instrument** — depth, lag, block time, drops (`observability-metrics-tracing`).
9. **Test** — fast producer + slow consumer; cancel mid-block; recovery; flat memory.

## Strategies

| Strategy | When full | Use when |
| --- | --- | --- |
| Block / await | Producer waits | In-process; loss bad; still enforce deadlines |
| Reject / fail fast | Error to caller (429/503) | Request/response; client may retry |
| Drop newest / oldest | Discard | Lossy signals; keep latest when gauges/positions |
| Conflate / sample | Merge or keep last | High-frequency optional intermediates |
| Throttle / shed | Cap admit; drop low priority | Smooth bursts; protect critical classes |
| Spill durable | Disk/broker absorbs | Need durability + decoupled consumers |

**Rule:** telemetry may drop; **business truth** must reject or persist—never
silent memory growth.

## Good / Bad Examples

**Good** — bounded send with deadline:

```go
ch := make(chan Event, 1024)
select {
case ch <- ev:
case <-ctx.Done():
  return ctx.Err()
case <-time.After(waitCap):
  return errQueueSaturated
}
```

**Bad** — unbounded channel/list; sender blocks forever with no `ctx`.

**Good**

```text
metrics_pipeline: buffer=10_000, overflow=drop_oldest + drop_total metric
order_ingest:     buffer=1_000,  overflow=reject_429 (client retries / durable)
```

**Bad** — drop-oldest on order ingest with no durable recovery (lost orders).

**Good** — handler returns 503 / pauses websocket read when worker queue is full.

**Bad** — accept all requests into an unbounded in-memory list “for the worker.”

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Bounded buffers, overflow, slow consumer, streaming pressure | **This skill** | — |
| Separate pools so one stream cannot exhaust resources | `bulkhead-isolation` | this for buffer policy |
| Cancel while blocked on send/recv; structured pipelines | `async-concurrency-patterns` | this for overflow |
| Fail-fast when dependency is broken (not just a full queue) | `circuit-breaker-patterns` | this when queues hide failures |
| Depth, lag, drop/reject metrics and traces | `observability-metrics-tracing` | this for signals |
| Implementation hygiene, errors, tests | `code-quality-standards` | **always** |

Keep **this skill primary** for flow control. Always apply
**`code-quality-standards`**. Use **`async-concurrency-patterns`** for
cancel/structure, **`bulkhead-isolation`** for partitions,
**`circuit-breaker-patterns`** for trip state,
**`observability-metrics-tracing`** for depth/lag/drops.

## Checklist

- [ ] Producer/consumer path and accumulation points identified
- [ ] Lossless vs lossy contract documented per stage
- [ ] Every buffer bounded; overflow policy explicit
- [ ] Pull/credit used where supported; pressure propagates upstream
- [ ] Deadlines/cancel honored while waiting for space
- [ ] Critical vs lossy paths not sharing one unsafe policy
- [ ] Bulkheads when multiple classes share a process
- [ ] Metrics: depth, lag, drops (`observability-metrics-tracing`)
- [ ] Tests: slow consumer, overflow, recovery, cancel mid-wait
- [ ] `code-quality-standards` + `async-concurrency-patterns` applied as needed
