---
name: retry-backoff-patterns
description: >
  Design safe retries: exponential backoff, jitter, budgets, idempotency, and
  when not to retry. Use when retry, backoff, 重试, transient failure, 429/503
  handling, dead-letter, or retry storms. Complements async cancel and cache
  loaders; not a substitute for fixing non-idempotent APIs.
---

# Retry And Backoff Patterns

Engineering design for **recovering from transient failures** without creating
outages: what is safe to retry, how long to wait, how to bound total work, and
how to stay idempotent under duplicate execution. Prefer the repo’s existing
retry helpers, HTTP clients, and queue middleware over ad-hoc sleep loops.

## Use When

- Implementing or reviewing retries on HTTP/RPC, DB, message consumers, or SDKs
- Choosing **exponential backoff**, caps, **jitter**, and attempt budgets
- Handling **429 / 503**, `Retry-After`, timeouts, and connection resets
- Ensuring **idempotency** for retried side effects (payments, emails, writes)
- Stopping **retry storms** that amplify origin or dependency outages
- User mentions: retry, backoff, 重试, exponential backoff, jitter, idempotent
  retry, at-least-once delivery, dead-letter queue (DLQ)

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Cancellation, deadlines, structured task lifetimes | `async-concurrency-patterns` |
| Cache miss loaders, stampede, TTL (except retrying the load) | `caching-strategies` |
| General reliability, errors, tests, security hygiene | `code-quality-standards` |
| HTTP race / limit-overrun **vulnerability testing** | `race-condition` |
| User-visible error copy only | `error-message-ux-writing` |

## Repo Config First

Repo config, client libraries, and mesh policies **outrank** this skill’s defaults.

1. **Existing retry utilities:** Polly, Resilience4j, Tenacity, aws-sdk retry,
   gRPC retry config, axios interceptors, custom `withRetry` helpers — **extend
   these** rather than nesting a second retry layer blindly
2. **Timeout and deadline policy:** HTTP client timeouts, mesh/route timeouts,
   per-RPC deadlines — retries must fit **inside** the caller’s remaining budget
3. **Idempotency infrastructure:** idempotency-key middleware, upsert keys,
   outbox patterns already in the codebase
4. **Queue / messaging:** built-in redelivery, max receive count, DLQ, visibility
   timeout — align application retries with broker redelivery to avoid double loops
5. **Rate limits and quotas:** service 429 policies, partner API rules, bulkhead
   settings
6. **Observability:** retry metrics, attempt traces, span events already emitted
   by neighboring services
7. **Neighboring code:** copy 2–3 mature clients’ max attempts, backoff base/cap,
   and non-retryable error lists before inventing new constants

**Precedence:** If repo rules conflict with defaults below, follow the repo.
Surface conflicts that retry non-idempotent writes, ignore `Retry-After`, or
stack retries across layers without a single budget.

## Workflow

1. **Classify the operation.**
   - **Read / pure:** usually safe to retry if result is not “exactly once” sensitive
   - **Idempotent write:** safe with same key/body (PUT upsert, DELETE, GET-like)
   - **Non-idempotent write:** do **not** blind-retry without idempotency key or
     dedupe store
2. **Classify the error.**
   - **Transient:** timeouts, connection reset, 408/425/429/500/502/503/504
     (tune to API; not all 500s are safe)
   - **Non-retryable:** 400/401/403/404/422 validation, permanent business rejection
   - **Ambiguous success:** timeout after request may have committed — requires
     idempotency or status probe, not naive re-POST
3. **Define a budget (not infinite loops).**
   - Max attempts **or** max wall-clock duration (prefer both)
   - Honor parent deadline/cancel; do not retry after abort
4. **Choose delay policy** (see Backoff And Jitter).
5. **Honor server signals:** `Retry-After`, rate-limit headers, gRPC retry info.
6. **Make side effects safe:** idempotency keys, dedupe tables, exactly-once
   business outcome with at-least-once transport.
7. **Observe:** attempt count, final outcome, delay histogram; alert on retry
   rate spikes (storm indicator).
8. **Test:** transient then success; permanent fail-fast; cancel mid-backoff;
   `Retry-After`; double-commit protection.

## When To Retry

| Retry | Do not retry (by default) |
| --- | --- |
| Connection failures before request bytes committed | Validation / schema errors |
| Explicit transient status (429, 503) with policy | 401/403 (fix auth first) |
| Idempotent reads and safe upserts | Non-idempotent POST without key |
| Consumer handler after visible transient dependency blip | Poison messages that always fail (→ DLQ) |
| After `Retry-After` wait when still in budget | Errors after local cancel/deadline exceeded |

**Rule of thumb:** Retry only when a **later identical attempt** can succeed
without corrupting state or double-charging.

## Backoff And Jitter

### Exponential backoff (default sketch)

```text
delay = min(cap, base * 2^attempt)   # attempt starting at 0
delay = delay * jitter_factor
sleep(delay)
```

| Parameter | Typical starting point (tune to repo) |
| --- | --- |
| `base` | 50–200 ms for in-DC RPC; higher for cold external APIs |
| `cap` | 1–30 s depending on SLA and user-facing vs background |
| `maxAttempts` | 2–5 for user-facing; more only for background with long budget |
| Total budget | Must remain under caller timeout / UX budget |

### Jitter modes

| Mode | Formula sketch | Use |
| --- | --- | --- |
| **Full jitter** | `random(0, exp_delay)` | Best default to desynchronize clients |
| **Equal jitter** | `exp/2 + random(0, exp/2)` | Smoother than full; still spreads load |
| **Decorrelated** | `random(base, prev * 3)` capped | Good under contention (AWS-style) |

**Avoid:** fixed sleep for all workers; pure exponential **without** jitter on
large fleets (synchronized retry storms).

### `Retry-After`

- If present, wait at least that long (HTTP-date or delta-seconds).
- Still enforce max budget; if `Retry-After` exceeds budget, fail fast with a
  clear error rather than partial wait then surprise retry.

## Idempotency

Retries create **at-least-once** execution. Protect outcomes:

| Mechanism | Practice |
| --- | --- |
| **Idempotency-Key** | Client sends unique key; server stores response for key+principal+route |
| **Natural keys** | Upsert on business id (`PUT /resources/{id}`) instead of blind insert |
| **Dedupe store** | Record processed `messageId` / `eventId` before side effects commit |
| **Outbox** | Durable intent then publisher retries without re-running business logic |
| **State machine** | Transitions accept only legal predecessors (ignore duplicate events) |

**Good:** payment create with `Idempotency-Key: uk_…` and server returns same
result on retry.  
**Bad:** retry `POST /charges` with no key after a timeout (double charge risk).

## Layering And Budgets

```text
User request deadline ─────────────────────────────────────┐
  Service A retry budget ──────────┐                       │
    Service B retry budget ────┐   │                       │
      Dependency timeout ──┐   │   │                       │
```

- Prefer **one primary retry layer** per hop; disable or sharply limit nested
  SDK retries when the outer layer already retries.
- Propagate **deadlines** so inner work does not outlive the user budget
  (`async-concurrency-patterns`).
- On fan-out, apply **bulkheads** and per-dependency concurrency limits so
  retries cannot exhaust the whole process.

## Messaging Consumers

- Visibility timeout ≥ max processing time (including retries **inside** the handler).
- Prefer broker redelivery **or** in-handler retry — not both unbounded.
- After max attempts → **DLQ** with poison reason; alert; do not infinite loop.
- Handlers must be idempotent under at-least-once delivery.

## Good / Bad Examples

### Exponential backoff with full jitter

**Good**

```ts
// Sketch — cancel-aware, bounded, full jitter
async function withRetry<T>(
  op: (signal: AbortSignal) => Promise<T>,
  opts: { baseMs: number; capMs: number; maxAttempts: number; signal: AbortSignal },
): Promise<T> {
  let lastErr: unknown;
  for (let attempt = 0; attempt < opts.maxAttempts; attempt++) {
    opts.signal.throwIfAborted();
    try {
      return await op(opts.signal);
    } catch (e) {
      lastErr = e;
      if (!isTransient(e) || attempt === opts.maxAttempts - 1) throw e;
      const exp = Math.min(opts.capMs, opts.baseMs * 2 ** attempt);
      const delay = Math.floor(Math.random() * exp); // full jitter
      await sleep(delay, opts.signal);
    }
  }
  throw lastErr;
}
```

**Bad**

```ts
for (;;) {
  try {
    return await op();
  } catch {
    await sleep(1000); // infinite, no jitter, no classify, no cancel
  }
}
```

### Honoring Retry-After

**Good**

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 5
```

```text
# Wait ≥ 5s (plus optional small jitter), then retry if budget remains
```

**Bad** — ignore header and hammer every 50 ms; or sleep 5 s **past** parent deadline.

### Idempotent write with key

**Good**

```http
POST /v1/transfers HTTP/1.1
Idempotency-Key: 8f3c2a6e-…
Content-Type: application/json

{"from":"a","to":"b","amount":"10.00"}
```

Server: same key + same body → same `transferId` and status; conflict if body differs.

**Bad**

```http
POST /v1/transfers HTTP/1.1
# timeout → client retries → two transfers created
```

### Nested retries

**Good** — outer orchestrator retries once; HTTP client retries disabled or
attempts=1 for that call path; total attempts documented.

**Bad** — client 5 attempts × service 5 × SDK 3 ≈ 75 calls on one blip.

### Non-retryable errors

**Good**

```python
if status in (400, 401, 403, 404, 422):
    raise  # no retry
if status in (429, 503) or is_timeout(err):
    retry_with_backoff(...)
```

**Bad** — retry 400 “invalid email” five times with exponential delay.

## Anti-Patterns

- Infinite retries without wall-clock or attempt budget
- Retrying non-idempotent side effects without dedupe/idempotency keys
- No jitter on large fleets → synchronized stampede after outage recovery
- Stacking retries at every layer without a global budget
- Sleeping without listening to cancellation/deadlines
- Treating all `5xx` and all timeouts as safe when the request may have committed
- Swallowing final errors after retries (`catch empty`) so callers see success
- Using retries as a substitute for fixing permanent bugs or missing capacity
- Retry storms on shared dependencies without bulkheads or circuit breaking
- Ignoring `Retry-After` and partner rate-limit contracts

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Retry policy, backoff, jitter, idempotent retries, retry storms | **This skill** | — |
| Cancel mid-backoff, deadline propagation, concurrent waiters | `async-concurrency-patterns` | this for delay/attempt policy |
| Retrying cache origin load; not caching failed attempts forever | `caching-strategies` | this for transient load errors |
| Production correctness, bounds, tests, security | `code-quality-standards` | **always apply** on implementation |
| Circuit breaker / bulkhead deep design with concurrency limits | this + `async-concurrency-patterns` | — |
| Logging attempt/backoff fields | `logging-message-style` | — |
| User-facing “try again later” copy | `error-message-ux-writing` | this for when retry is exhausted |

### Routing to `code-quality-standards`

Keep **this skill primary** for retry/backoff policy. Always apply
**`code-quality-standards`** when implementing retries:

- Bounded attempts and timeouts; no infinite loops
- Errors preserve context (attempt, last status, whether idempotent)
- No secrets in retry logs or idempotency key storage dumps
- Tests for transient success, permanent fail-fast, and cancel during sleep
- Validate untrusted inputs once; do not re-validate as a substitute for
  classifying retryability incorrectly

From `code-quality-standards`: *Make retries bounded, idempotency-aware,
cancellable, and observable* — this skill is the detailed playbook for that rule.

### Routing to `async-concurrency-patterns`

Use **`async-concurrency-patterns`** together with this skill when:

- Backoff sleeps must be abortable and deadline-aware
- Many concurrent requests retry the same dependency (bulkhead, coalescing)
- Background workers retry under structured supervision and shutdown drains
- Fan-out partial failure uses `allSettled`-style aggregation rather than
  unbounded per-child infinite retry

This skill specializes **whether and how to re-attempt work**. It does not
replace structured concurrency or general code quality.

## Checklist

- [ ] Repo retry helpers, client timeouts, queue redelivery, and idempotency tools inventoried
- [ ] Operation classified: read / idempotent write / non-idempotent write
- [ ] Error taxonomy: transient vs non-retryable vs ambiguous commit
- [ ] Budget: max attempts and/or max duration; fits parent deadline
- [ ] Backoff: exponential (or documented alternative) with **jitter**
- [ ] Cap on delay; no unbounded sleep
- [ ] `Retry-After` / rate-limit headers honored when present
- [ ] Nested retries inventoried; total amplification acceptable
- [ ] Side effects protected: Idempotency-Key, natural key, dedupe, or outbox
- [ ] Messaging: visibility timeout, max receive, DLQ path defined
- [ ] Cancel/deadline aborts further attempts and sleeps
- [ ] Metrics and logs: attempts, outcomes, delays (no secrets)
- [ ] Tests: transient→success, permanent fail-fast, cancel mid-wait, double-submit safety
- [ ] `code-quality-standards` applied for bounds, errors, security, verification
- [ ] `async-concurrency-patterns` applied for cancel, bulkheads, and supervised workers
