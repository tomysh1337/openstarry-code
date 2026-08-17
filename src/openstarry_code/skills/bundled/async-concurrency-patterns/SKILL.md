---
name: async-concurrency-patterns
description: >
  Design and implement safe async/await and concurrency in application code:
  cancellation, timeouts, structured task lifetimes, shared-state races, and
  shutdown. Use when async, await, concurrency, 并发, race condition in code,
  CancellationToken/Context, Promise.all, goroutines, tokio tasks, or concurrent
  workers. Not for HTTP TOCTOU / business limit-overrun testing (see race-condition).
---

# Async And Concurrency Patterns

Engineering design for **in-process** concurrency: who owns work, how it stops,
how shared state stays correct, and how failures surface. Language-agnostic
principles with concrete patterns for common runtimes. Prefer the repo’s
existing async style over inventing a second model.

## Use When

- Designing or fixing `async`/`await`, futures, coroutines, or callback chains
- Cancellation, timeouts, cooperative abort, or request-scoped lifetime
- Structured concurrency: parent tasks own children; no orphaned fire-and-forget
- In-memory / multi-task races: double-init, stale reads, lost updates, shutdown races
- Worker pools, fan-out/fan-in, pipelines, backpressure, and graceful shutdown
- User mentions: async, concurrency, 并发, race condition (in **code**), deadlock,
  CancellationToken, `asyncio.TaskGroup`, `Promise.allSettled`, goroutine leak

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| HTTP TOCTOU, coupon/limit overrun, parallel redeem testing | `race-condition` |
| General reliability, errors, tests, security hygiene | `code-quality-standards` |
| Language formatting / naming only | matching `*-style-*` skill |
| Distributed locking / multi-node consensus deep design | domain + ops docs; this skill stays process-local |

**Note:** HTTP race *vulnerability testing* is `race-condition`. Application
concurrency *design* (this skill) still applies when **implementing** atomic
fixes, idempotency, or transactional check-then-act in code.

## Repo Config First

Repo config and neighboring async code **outrank** this skill’s defaults.

1. **Runtime model:** single-threaded event loop (JS, asyncio default), M:N
   green threads (Go, Tokio), OS threads (Java, .NET ThreadPool), actor systems
2. **Cancellation primitives already used:** `CancellationToken`,
   `AbortController`, `context.Context`, `asyncio.CancelledError`,
   `tokio::select!` / `JoinHandle::abort`, Kotlin `CoroutineScope`
3. **Library conventions:** `Async` suffix, mandatory token on public I/O APIs,
   structured scopes (`TaskGroup`, `errgroup`, `nursery`, supervisor trees)
4. **Shared-state tools already in tree:** mutexes, channels, atomics, STM,
   actor mailboxes, DB transactions as the real source of truth
5. **Timeout policy:** global HTTP client timeouts, per-RPC deadlines, linkerd/
   mesh timeouts — do not stack silent conflicting budgets without documenting
6. **Tests:** concurrency tests, stress harnesses, fake clocks, sanitizers
   (TSan, Go race detector, `asyncio` debug mode)
7. **Neighboring code:** copy 2–3 mature services’ patterns for spawn, cancel,
   and error aggregation before inventing new helpers

**Precedence:** If repo rules conflict with defaults below, follow the repo.
Surface conflicts that leave orphaned tasks, swallowed cancellation, or
unbounded fan-out.

## Workflow

1. **State the concurrency contract.**
   - Inputs that may arrive concurrently
   - Ordering guarantees (if any): FIFO, happens-before, eventual
   - Failure modes: cancel, timeout, partial fan-out failure, poison message
   - Shutdown: drain vs cancel-in-flight vs abandon
2. **Choose structure first, primitives second.**
   - Prefer **structured concurrency**: a scope/parent that waits for children
   - Prefer **message passing / channels** over shared mutable state when
     ownership would otherwise be unclear
   - Prefer **single-writer** or **immutable snapshots** over multi-writer locks
3. **Thread cancellation and deadlines through every I/O boundary.**
   - Request/handler entry creates a cancel scope + deadline
   - Downstream calls inherit the same token/context (never invent a sibling
     root cancel for “background” work without ownership)
4. **Bound all fan-out.**
   - Max concurrency (semaphore / worker pool)
   - Max queue depth and explicit backpressure (block, drop, or shed load)
   - Aggregate errors deliberately (`all` fail-fast vs `allSettled` vs first-success)
5. **Protect or eliminate shared mutable state.**
   - Critical sections minimal; no I/O under locks unless designed for it
   - Check-then-act → atomic update, compare-and-swap, or DB constraint
6. **Make lifecycle explicit.**
   - No detached `spawn` / `Promise` without join, error sink, and cancel path
   - On shutdown: stop accepting → cancel or drain with timeout → release resources
7. **Observe and test.**
   - Metrics: in-flight tasks, queue depth, cancel rate, timeout rate
   - Tests: cancel mid-flight, double-complete, duplicate delivery, slow consumer,
     partial failure, graceful shutdown under load

## Design Principles

| Principle | Practice |
| --- | --- |
| Structured lifetimes | Parent waits for children; children do not outlive the scope that owns them |
| Cooperative cancel | Propagate token/context; treat cancel as success path for cleanup, not silent drop |
| Deadlines over infinite wait | Prefer absolute deadlines; remaining budget flows to children |
| Explicit ownership | One owner for each mutable resource; others get handles or messages |
| Fail visibly | Surface child errors; never empty `catch` on background tasks |
| Bound concurrency | Always cap fan-out and buffers |
| Idempotent side effects | Retries and duplicate wakes must not double-charge or double-write |
| Shutdown is a feature | Define drain/cancel policy; test it |

### Cancellation semantics (high-level)

| Runtime sketch | Pattern |
| --- | --- |
| .NET | Pass `CancellationToken` on public async APIs; honor `ThrowIfCancellationRequested`; map to `OperationCanceledException` |
| TypeScript/Node | `AbortSignal` on fetch/timers; abort → reject; clear handles in `finally` |
| Python asyncio | Cancel scope / `TaskGroup`; on cancel run cleanup; do not blanket-suppress `CancelledError` |
| Go | `context.WithCancel` / `WithTimeout`; all blocking calls take `ctx`; `errgroup` for structured wait |
| Rust async | `select!` with cancel future; drop = cancel for many futures; careful with `spawn` + `JoinHandle` |
| Java | `Future.cancel`, structured concurrency APIs (where adopted), interrupt-aware blocking |

### Race classes in application code (not HTTP vuln tests)

| Class | Symptom | Fix direction |
| --- | --- | --- |
| Lost update | Concurrent read-modify-write | Atomic RMW, version column, row lock |
| Double init | Two tasks create the same singleton | `once` / double-checked under lock / lazy init API |
| Stale callback | Response applied after newer request | Generation counter, abort previous, ignore stale |
| TOCTOU local | Check then act without sync | Single critical section or transactional predicate |
| Shutdown race | Work after dispose | Phase flag + cancel; reject new work after stop |
| Join race | Dropped task errors | Always await/join or attach supervised error handler |

## Good / Bad Examples

### Structured concurrency vs fire-and-forget

**Good** — parent owns children and aggregates errors:

```ts
// TypeScript sketch: bounded fan-out with AbortSignal
async function loadAll(ids: string[], signal: AbortSignal): Promise<Item[]> {
  const limit = pLimit(8);
  return Promise.all(
    ids.map((id) => limit(() => fetchItem(id, { signal }))),
  );
}
```

```go
// Go: errgroup cancels siblings on first error
g, ctx := errgroup.WithContext(ctx)
g.SetLimit(8)
for _, id := range ids {
  id := id
  g.Go(func() error { return fetchItem(ctx, id) })
}
return g.Wait()
```

**Bad** — orphaned work, no cancel, unbounded spawn:

```ts
// Bad: detached promises; errors become unhandled rejections
for (const id of ids) {
  fetchItem(id); // no await, no signal, no limit
}
```

```go
// Bad: leaked goroutines; no context
for _, id := range ids {
  go fetchItem(context.Background(), id)
}
```

### Cancellation propagation

**Good**

```csharp
public async Task<Order> GetOrderAsync(string id, CancellationToken ct)
{
    ct.ThrowIfCancellationRequested();
    return await _db.Orders.AsNoTracking()
        .FirstAsync(o => o.Id == id, ct);
}
```

**Bad**

```csharp
// Bad: drops caller's token; cannot cancel slow DB
public async Task<Order> GetOrderAsync(string id, CancellationToken ct)
{
    return await _db.Orders.FirstAsync(o => o.Id == id); // no ct
}
```

### Stale async UI / request race

**Good** — ignore stale responses:

```ts
let seq = 0;
async function search(q: string, signal: AbortSignal) {
  const my = ++seq;
  const res = await api.search(q, { signal });
  if (my !== seq) return; // superseded
  render(res);
}
```

**Bad** — last write wins even if older request finishes last:

```ts
async function search(q: string) {
  const res = await api.search(q); // no abort, no generation
  render(res); // stale query can overwrite newer results
}
```

### Shared mutable state

**Good** — serialize mutations or use atomic update:

```python
# Bad pattern avoided: check-then-act without lock
async with self._lock:
    if self._balance >= amount:
        self._balance -= amount
        return True
    return False
```

**Bad**

```python
# Race: two coroutines both pass the check
if self._balance >= amount:
    await asyncio.sleep(0)  # yield — window
    self._balance -= amount
```

### Shutdown

**Good** — stop intake, cancel or drain with timeout, then close resources.

**Bad** — process exit while tasks still write to closing connections; or
`while True: await work()` with no cancel/stop channel.

## Anti-Patterns

- Fire-and-forget without supervision, join, or error metrics
- Swallowing cancellation (`except: pass`, empty `.catch(() => {})`) so cleanup never runs
- Creating a new root timeout that **extends** past the caller’s deadline
- Unbounded `Promise.all` / goroutine spawn on user-controlled batch size
- Holding locks/mutexes across network I/O without a deliberate design
- Using “sleep and hope” instead of events/conditions for coordination
- Treating HTTP race exploit methodology as a substitute for application locking
  (use `race-condition` for authorized vuln tests; fix with atomic design here)
- Thread-unsafe lazy singletons and static mutable caches

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Async/await design, cancel, structured concurrency, in-code races | **This skill** | — |
| Production correctness, errors, resources, tests, security | `code-quality-standards` | **always apply** on implementation |
| Language style (Async suffix, naming) only | matching `*-style-*` | this skill for lifetime/cancel design |
| HTTP TOCTOU / limit overrun **assessment** | `race-condition` | this skill when writing the **fix** |
| API idempotency / versioned contract wording | `api-versioning-design` / `api-documentation-writing` | this for concurrent handlers |
| User-visible timeout/cancel errors | `error-message-ux-writing` | this for when to cancel |
| Logging cancel/timeout fields | `logging-message-style` | — |

### Routing to `code-quality-standards`

Keep **this skill primary** for concurrency structure. Always apply
**`code-quality-standards`** as the implementation baseline when code changes:

- Error context across task boundaries; do not swallow failures
- Resource cleanup on every exit path (including cancel)
- Retries: bounded, idempotent, cancellable, observable
- Tests for cancel, partial failure, and shutdown when risk warrants
- No secrets in concurrent logs; validate untrusted batch sizes at the boundary

This skill specializes **task lifetimes, cancellation, races, and structured
concurrency**. It does not replace general quality, security, or test policy.

## Checklist

- [ ] Repo async model, cancel primitive, and neighboring patterns identified
- [ ] Concurrency contract written: ordering, failure, shutdown, bounds
- [ ] Work is structured (parent/scope owns children) — no unsupervised detach
- [ ] Cancellation/deadline propagated through all I/O and wait points
- [ ] Fan-out and queues are bounded; backpressure policy explicit
- [ ] Shared mutable state eliminated or protected; check-then-act is atomic
- [ ] Stale callbacks / superseded requests ignored or aborted
- [ ] Shutdown: stop intake → drain or cancel with timeout → release resources
- [ ] Errors from background/child work are observed (metrics or await)
- [ ] Side effects are safe under retry and duplicate wake-ups
- [ ] Tests cover cancel mid-flight, partial fan-out failure, and shutdown where risk is high
- [ ] `code-quality-standards` applied for errors, cleanup, security, and verification
- [ ] Not confused with HTTP `race-condition` vuln testing unless implementing the fix
