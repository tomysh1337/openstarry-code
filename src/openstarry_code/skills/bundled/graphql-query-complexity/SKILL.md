---
name: graphql-query-complexity
description: >
  Authorized GraphQL query depth and complexity analysis: cost scoring models,
  maxDepth / maxComplexity limits, alias and list-multiplier abuse, nested-query
  DoS proofs, and persisted-query allowlists. Use when GraphQL resolvers risk
  expensive nested selection sets, depth/cost limits are missing or mis-keyed,
  or you must validate complexity middleware before production exposure.
---

# GraphQL Query Complexity (Authorized)

## Scope And Authorization

- Authorized apps, labs, CTFs, and program-scoped APIs **only**. Nested queries and alias floods can exhaust CPU, memory, and databases — treat as **capacity-sensitive** probes, not volumetric DoS.
- Prefer staging or dedicated tenants. On shared production: low concurrency, short selection sets that prove missing limits, stop at first clear acceptance of unbounded cost. No recursive “crash the server” demos without explicit load-test approval.
- Cap alias/batch count and nesting depth per probe class. Coordinate before hitting paid backends, fan-out resolvers, or third-party data sources.
- Redact tokens, cookies, operation bodies with PII, and internal type names when required. Keep original requests immutable; store trimmed PoCs separately.

## When To Use

- Endpoint accepts arbitrary GraphQL documents (`query` / `mutation`) without persisted-query-only mode.
- Keywords: query complexity, cost analysis, maxDepth, maxComplexity, nested query DoS, GraphQL alias flood, circular type nesting, Apollo cost plugin, graphql-query-complexity.
- Schema has recursive relations (`User.friends`, `Comment.replies`, Relay connections) or list fields without pagination hard caps.
- You must **measure or implement** depth/cost limits, not only discover schema/authz (that is `graphql-and-hidden-parameters` / `idor-graphql-nodes`).
- Not primary for: introspection-only recon, classic BOLA on node IDs, JWT issues, or HTTP rate-limit keying alone (`rate-limit-bypass-testing`).

## Workflow

### 1. Establish baseline and surface

1. Confirm GraphQL path, auth mode, batching (`[{query}]`), and whether **full queries** and/or **persisted query hashes** (`extensions.persistedQuery`) are accepted.
2. Obtain schema (introspection if allowed, else client operations). Map recursive edges and high-fan-out fields (lists, connections, nested joins).
3. Send a minimal authenticated query; record latency, status, error extensions, and any cost/depth headers or messages.

### 2. Depth analysis (maxDepth)

1. Build a **linear nested** selection along one recursive path, increasing depth by 1 each step:

   ```graphql
   query D3 {
     user(id: "TEST") {
       friends { friends { friends { id } } }
     }
   }
   ```

2. Record first rejected depth (4xx/200 with GraphQL error) vs last accepted. Note off-by-one: some stacks count root; others count only nested fields.
3. Test **breadth-at-depth**: shallow root with many nested branches — depth limit alone may miss wide trees.
4. Mutations/subscriptions: apply the same depth ladder if nested payloads or subscription selection sets exist.
5. Finding: unbounded or high maxDepth (e.g. ≥15–20 on recursive graphs) without cost limits → document accepted depth and estimated resolver fan-out.

### 3. Complexity / cost scoring

Depth is necessary but not sufficient. Prefer **field-cost** models:

| Signal | What to check |
| --- | --- |
| Static cost per field | Default 1 vs expensive fields weighted higher |
| List multipliers | `friends(first: N)` multiplies child cost by N (or schema default page size) |
| Connection args | Missing max on `first`/`last` inflates cost |
| Aliases | `a1: user … aN: user` multiplies root cost in one HTTP request |
| Fragments | Spreads must be included in cost; ensure no double-count bugs in middleware |
| Introspection | Often excluded or separately limited |

1. If the server exposes cost (errors like “query complexity exceeds X”, custom extensions), binary-search the threshold with controlled aliases/lists.
2. If no server cost: estimate client-side (sum field weights × parent multiplicity) and compare wall-clock/DB impact on **staging** only.
3. Prove **alias multiplication**: N identical cheap fields in one document when per-HTTP rate limits exist but per-operation cost does not.
4. Prove **list multiplier**: large `first` on a connection nested under another list (quadratic/cubic explosion).

### 4. Nested-query DoS class (authorized proof only)

Goal: show the API **accepts** a document whose theoretical work exceeds a safe budget — not to take down production.

1. Minimal PoC: recursive nesting **or** moderate aliases **or** nested lists with large `first` — pick the smallest that crosses a clear threshold (latency cliff, timeout, 5xx, or missing rejection).
2. One variable per series (depth **or** width **or** list size). Stop after reproducible evidence (≥2 runs).
3. Note interaction with DataLoader/caching (may hide N+1 until cold cache) and with batching HTTP arrays.
4. Never combine maximum depth × maximum aliases × maximum list size on shared prod.

### 5. Persisted queries and allowlists

1. Detect Automatic Persisted Queries (APQ) / trusted document lists: hash-only clients vs open query body.
2. If both modes work, try sending a full expensive query while the client normally uses hashes — **allowlist bypass**.
3. If hash-only: complexity still matters for **who can register** documents (CI vs runtime registration). Review registration auth; untrusted runtime persist = delayed DoS surface.
4. Recommend: production public clients on allowlisted operations; cost limits still enforced server-side as defense in depth.

### 6. Control validation and remediation

When implementing or reviewing defenses (pair with `code-quality-standards`):

- Enforce **maxDepth** and **maxComplexity** before execution; reject with generic errors (no schema hints).
- Score **aliases**, **fragments**, and **list args**; cap `first`/`last` independently of cost.
- Apply limits **per operation** inside JSON batches; optionally budget per HTTP request.
- Prefer persisted queries for first-party apps; keep introspection off or restricted in production.
- Add timeouts and resolver-level pagination hard caps; monitor p99 and GraphQL error codes for limit hits.
- Rate-limit by user/IP **and** cost units when possible (`rate-limit-bypass-testing` for keying).

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Depth / cost / nested-query DoS / persisted allowlist | **This skill** | — |
| Schema recon, introspection, hidden fields | `graphql-and-hidden-parameters` | then this skill for cost |
| Node/edge IDOR in GraphQL | `idor-graphql-nodes` / `idor-broken-object-authorization` | — |
| Per-HTTP rate limit / alias budget keying | `rate-limit-bypass-testing` | this skill for cost units |
| API map missing | `api-recon-and-docs` | — |
| Implement limits / middleware | `code-quality-standards` | this skill for test evidence |
| Schema style (not abuse testing) | `graphql-schema-design-style` | — |

## Output Checklist

- [ ] Authorization, environment, probe budget (depth/alias/list caps used)
- [ ] Endpoint, auth, batching, full-query vs persisted-query modes
- [ ] Recursive/list hotspots from schema or client ops
- [ ] maxDepth: last accepted vs first rejected; counting rule if known
- [ ] Complexity: model used, threshold, alias and list-multiplier results
- [ ] Minimal nested/alias/list PoC (redacted) and reproducible impact metric
- [ ] Persisted-query posture and allowlist bypass attempt result
- [ ] Remediation: depth + cost + list caps + per-batch accounting + APQ/allowlist
