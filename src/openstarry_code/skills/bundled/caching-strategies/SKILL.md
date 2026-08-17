---
name: caching-strategies
description: >
  Design application and edge caches: key design, TTLs, invalidation, stampede
  protection, and consistency. Use when caching, cache invalidation, 缓存,
  Redis/Memcached, CDN cache keys, TTL, thundering herd, or cache-aside patterns.
  Not for web cache deception/poisoning assessment (see web-cache-deception).
---

# Caching Strategies

Engineering design for **correct, operable caches**: what is stored, under which
key, for how long, how it is invalidated, and how concurrent misses stay safe.
Covers in-process, distributed (Redis/Memcached), and HTTP/CDN layers when you
**own** the cache policy. Prefer the repo’s existing cache libraries and key
conventions over inventing a second scheme.

## Use When

- Adding or changing application caches (memory, Redis, Memcached, local L1/L2)
- Designing **cache keys**, namespaces, versioning, and multi-tenant isolation
- Choosing **TTLs**, soft/hard expiry, stale-while-revalidate, or refresh-ahead
- Implementing **invalidation** (delete, tag/version bump, write-through/write-around)
- Preventing **stampede / thundering herd** on hot keys after expiry or deploy
- Debugging stale data, cross-tenant leaks via keys, or cache inconsistency
- User mentions: caching, cache invalidation, 缓存, TTL, cache-aside, stampede,
  thundering herd, `Cache-Control`, Redis cache, CDN HIT/MISS (as **policy**, not attack)

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Web cache deception / private body on public URL (authorized test) | `web-cache-deception` |
| Cache poisoning via Host/smuggling (authorized test) | `http-host-header-attacks` / `request-smuggling` |
| Concurrent handler design, cancel, in-process races | `async-concurrency-patterns` |
| General reliability, errors, tests, security hygiene | `code-quality-standards` |
| Retrying failed origin loads that feed the cache | `retry-backoff-patterns` |

## Repo Config First

Repo config, infra, and neighboring cache helpers **outrank** this skill’s defaults.

1. **Cache stack already in tree:** Redis client, Caffeine/Guava, Spring Cache,
   `.NET IDistributedCache`, Next.js/HTTP cache middleware, CDN product (Cloudflare,
   Fastly, CloudFront) — match APIs and key helpers already used
2. **Key conventions:** prefix, service name, env, tenant id, schema version;
   shared “cache key builder” modules — **reuse them**
3. **TTL policy:** product SLAs, config tables, feature flags, or ops runbooks
   that define freshness per resource class
4. **Invalidation hooks:** domain events, outbox, pub/sub, admin purge APIs,
   deploy scripts that bump cache generations
5. **Multi-layer layout:** L1 process → L2 Redis → L3 CDN; who owns what and
   whether write paths touch every layer
6. **Auth and privacy:** never cache personalized or secret responses under
   public/shared keys; prefer `private` / `no-store` where required
7. **Observability:** existing metrics for hit rate, latency, eviction, errors;
   dashboards and alerts to extend rather than replace
8. **Neighboring code:** copy 2–3 mature services’ get-or-load, stampede, and
   invalidation patterns before inventing new abstractions

**Precedence:** If repo rules conflict with defaults below, follow the repo.
Surface conflicts that risk cross-tenant data, unbounded memory growth, or
indefinite stale reads after writes.

## Workflow

1. **State the freshness and correctness contract.**
   - What may be stale, and for how long (business max lag)
   - What must never be served stale (authz decisions, balances, one-time tokens)
   - Single-key vs multi-object consistency requirements
   - Failure mode when cache is down: fail open (hit origin) vs fail closed
2. **Choose a pattern that matches write/read ratio.**

   | Pattern | When | Notes |
   | --- | --- | --- |
   | **Cache-aside** (lazy load) | Read-heavy, origin is source of truth | App loads on miss; invalidate or short TTL on write |
   | **Read-through** | Library/proxy loads for you | Same correctness rules; centralize loader |
   | **Write-through** | Must keep cache warm on write | Higher write latency; simpler read path |
   | **Write-behind** | High write volume, can tolerate lag | Needs durability queue; careful crash semantics |
   | **Refresh-ahead / SWR** | Predictable hot keys | Serve stale briefly while one revalidation runs |

3. **Design keys deliberately (see Key Design).**
4. **Pick TTLs and hard bounds** (see TTL Design).
5. **Plan invalidation** for every write path that changes cached data.
6. **Stampede-protect hot keys** (singleflight, locking, probabilistic early expiry).
7. **Bound memory and cardinality** — no unbounded key growth from user input.
8. **Observe, test, and document** hit rates, stale windows, and purge procedures.

## Key Design

| Rule | Practice |
| --- | --- |
| Stable identity | Key from canonical ids, not display names or unordered maps |
| Namespace | `svc:env:domain:…` or repo-standard prefix; avoid collisions across services |
| Version / generation | Include schema or generation token so deploy can wipe logical space |
| Tenant isolation | Always include tenant/org id when data is tenant-scoped |
| No secrets in keys | Tokens, passwords, raw PII must not appear in key strings or Redis KEYS scans |
| Normalize inputs | Sorted query parts, lowercased where case-insensitive, explicit defaults |
| Vary correctly (HTTP) | Everything that changes the body must be in the cache key or `Vary` |
| Avoid huge keys | Hash long natural keys; keep debug mapping out of hot path if needed |

**Good key sketch:** `orders:v2:t{tenantId}:order:{orderId}`  
**Bad key sketch:** `order-cache:` + raw user JSON dump or unvalidated path segments

## TTL Design

| Concern | Guidance |
| --- | --- |
| Upper bound | TTL ≤ business-acceptable staleness for that resource class |
| Negative caching | Cache “not found” briefly only; shorter TTL; never cache auth failures long |
| Jitter | Add small random jitter to aligned TTLs so many keys do not expire together |
| Soft vs hard | Soft-expire: serve stale + revalidate; hard-expire: must reload before serve |
| Zero / infinite | Avoid infinite TTL unless invalidation is proven complete for every write |
| Clock skew | Prefer relative TTL from cache server; document absolute-expiry edge cases |
| Config | Prefer configurable TTLs per resource type over magic numbers in deep call sites |

## Invalidation

1. **Prefer explicit delete or version bump** on write over “wait for TTL only”
   when users can observe their own writes.
2. **Invalidate the right set:** primary key + secondary indexes + list/aggregate
   keys that embed the entity (or use tags/generations to bulk-invalidate).
3. **Order of operations (cache-aside):**
   - Write origin **first**, then invalidate cache (not update-then-write-origin
     with stale fill race unaddressed).
   - On race (stale fill after write): short TTL, version checks, or
     compare-and-set with content version from origin.
4. **Multi-layer:** purge L3 CDN and L2 Redis when both can serve the path;
   document who triggers which purge.
5. **Never rely on `KEYS *` in production** for purge; use tracked sets, tags,
   or generation counters.
6. **Admin/emergency purge** runbook: key pattern, blast radius, auth on purge API.

## Stampede / Thundering Herd

When a hot key expires or is invalidated, many concurrent requests may hit origin.

| Technique | Mechanism |
| --- | --- |
| **Singleflight / request coalescing** | One in-flight load per key; others wait for the same future |
| **Distributed lock** | Short lock around reload; waiters read through or serve stale |
| **Probabilistic early recompute** | XFetch-style: revalidate before hard expiry with probability rising near TTL |
| **Stale-while-revalidate** | Serve last value while background refresh runs (if stale is allowed) |
| **TTL jitter** | Reduce synchronized expiry across the keyspace |

Always **bound waiters**, honor cancellation, and fall back if the loader fails
(see `async-concurrency-patterns` for structured wait and cancel).

## Consistency And Safety

- **Authz:** Cache **after** authorization, or include principal/role in the key
  when responses are principal-specific. Prefer not caching per-user secrets.
- **PII / secrets:** Encrypt at rest if required; restrict who can `GET` keys;
  never log full cache values with secrets.
- **Poisoning defense (defensive eng):** Do not key only on untrusted Host/path
  without normalization; set explicit `Cache-Control` on sensitive responses.
- **Null/poison values:** Do not cache thrown errors as immortal empty hits.
- **Partial failure:** If origin succeeds but cache set fails, prefer serving the
  fresh origin result and metric the set failure — do not fail the user unless
  policy requires cache durability.

## Good / Bad Examples

### Cache-aside with invalidation

**Good**

```ts
// Sketch: load from origin on miss; invalidate on write
async function getOrder(tenantId: string, orderId: string): Promise<Order> {
  const key = `orders:v2:t${tenantId}:order:${orderId}`;
  const hit = await cache.get(key);
  if (hit) return decode(hit);

  const order = await db.orders.find(tenantId, orderId);
  await cache.set(key, encode(order), { ttlSeconds: 60 + jitter(10) });
  return order;
}

async function updateOrder(tenantId: string, orderId: string, patch: Patch) {
  await db.orders.update(tenantId, orderId, patch); // origin first
  await cache.del(`orders:v2:t${tenantId}:order:${orderId}`);
  // also invalidate list/aggregate keys or bump generation
}
```

**Bad** — write cache then DB; or never invalidate:

```ts
await cache.set(key, newValue, { ttlSeconds: 86400 });
await db.orders.update(...); // if this fails, cache lies
// readers may see old DB on later miss after wrong ordering
```

### Key isolation

**Good**

```text
orders:v2:t42:order:ord_123
user:v1:t42:profile:u_9
```

**Bad**

```text
order:ord_123          # missing tenant → cross-tenant risk if ids collide or leak
profile:Alice          # display name, not stable id
```

### Stampede protection (singleflight)

**Good**

```go
// One load per key; concurrent callers share the result
var group singleflight.Group

func GetUser(ctx context.Context, id string) (*User, error) {
  v, err, _ := group.Do("user:"+id, func() (interface{}, error) {
    return loadUserFromDB(ctx, id)
  })
  if err != nil {
    return nil, err
  }
  return v.(*User), nil
}
```

**Bad** — every concurrent miss hits DB:

```go
if val, ok := cache.Get(key); ok {
  return val, nil
}
return loadUserFromDB(ctx, id) // N parallel loads for one hot key
```

### HTTP / CDN cacheability

**Good**

```http
HTTP/1.1 200 OK
Cache-Control: public, max-age=60, stale-while-revalidate=30
Vary: Accept-Encoding
# Body is identical for all users; no Set-Cookie; no Authorization variance
```

**Bad**

```http
HTTP/1.1 200 OK
Cache-Control: public, max-age=3600
Set-Cookie: session=…
# Personalized body cached under a shared URL key
```

### Negative caching

**Good** — short TTL on 404 for known-stable missing ids; re-check soon.

**Bad** — cache “user not found” for 24h after a race where the user was just created.

## Anti-Patterns

- Unbounded keys from raw user input (path, query, body hash without limits)
- Omitting tenant or principal from keys for non-public data
- Infinite TTL with incomplete invalidation coverage
- Synchronized expiry of millions of keys at the same second (no jitter)
- Updating cache value on write without versioning while concurrent loaders
  can re-fill stale origin snapshots
- Caching errors, empty bodies, or auth challenges as long-lived hits
- Using production `FLUSHALL` / broad `KEYS` as the normal invalidation strategy
- Treating CDN “static rule by extension” as safe for HTML account pages
  (engineering: fix policy; assessment: `web-cache-deception`)
- L1 process cache without generation bump on deploy when shape changes
- Silent cache-aside that hides origin outages without metrics/alerts

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Cache keys, TTL, invalidation, stampede, cache-aside design | **This skill** | — |
| Concurrent load coalescing, cancel while waiting on singleflight | `async-concurrency-patterns` | this skill for key/TTL policy |
| Retry origin loader on transient failure | `retry-backoff-patterns` | this for whether to cache failures |
| Production correctness, bounds, tests, security hygiene | `code-quality-standards` | **always apply** on implementation |
| Web cache deception assessment | `web-cache-deception` | this when **fixing** cache policy |
| Logging cache miss/hit fields | `logging-message-style` | — |
| User-facing “stale data” / timeout errors | `error-message-ux-writing` | — |

### Routing to `code-quality-standards`

Keep **this skill primary** for cache policy and invalidation design. Always
apply **`code-quality-standards`** when implementing cache code:

- Validate and bound key material from untrusted input
- Failures: distinguish miss, origin error, and cache infrastructure error
- No secrets in keys, logs, or shared public cache entries
- Resource cleanup and client connection lifecycle for Redis/etc.
- Tests for invalidation, stampede coalescing, and tenant isolation when risk warrants
- Preserve documented behavior under cache-down modes

### Routing to `async-concurrency-patterns`

Use **`async-concurrency-patterns`** whenever cache loaders involve concurrent
waiters, background refresh, or cancellation:

- Singleflight waiters must honor abort/deadlines
- Background revalidation tasks need structured ownership (no orphan refresh)
- Bound fan-out when warming many keys
- Shutdown: stop accepting refresh work; do not write to closed clients

This skill specializes **what to cache, keys, TTL, invalidation, and stampede
policy**. It does not replace concurrency structure or general code quality.

## Checklist

- [ ] Repo cache stack, key helpers, TTL config, and purge hooks inventoried
- [ ] Freshness contract written: max staleness, never-stale set, cache-down mode
- [ ] Pattern chosen (aside / through / behind / SWR) with write-path implications
- [ ] Keys: namespace, version/generation, tenant, stable ids, no secrets
- [ ] HTTP `Vary` / CDN key includes every body-affecting input for shared caches
- [ ] TTLs bounded; jitter on aligned expiries; negative cache TTLs short
- [ ] Invalidation covers primary + derived keys (or generation/tag strategy)
- [ ] Origin write precedes invalidate (cache-aside); stale-fill race addressed
- [ ] Stampede protection on hot keys (singleflight, lock, early recompute, or SWR)
- [ ] Cardinality and memory bounded; no unbounded key explosion
- [ ] Authz/PII: not cached publicly; principal-specific data keyed or uncached
- [ ] Metrics: hit rate, latency, errors, invalidations; alert on origin storm risk
- [ ] Tests: miss/hit, invalidate-after-write, multi-tenant isolation, stampede coalesce
- [ ] `code-quality-standards` applied for bounds, errors, security, verification
- [ ] `async-concurrency-patterns` applied for coalesced loads, refresh tasks, cancel
- [ ] Not confused with `web-cache-deception` assessment unless implementing the fix
