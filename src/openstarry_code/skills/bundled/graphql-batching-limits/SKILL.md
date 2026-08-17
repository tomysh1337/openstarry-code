---
name: graphql-batching-limits
description: >
  GraphQL batching and alias multiplication: JSON-array multi-ops, field-alias
  fan-out, rate-limit/cost gaps, and Apollo/server batch configuration. Use when
  assessing or hardening GraphQL against array batching, alias brute force,
  per-HTTP vs per-operation throttles, or missing batch/cost limits on owned or
  authorized targets. Hand complexity scoring and broad GraphQL security to
  specialized skills.
---

# GraphQL Batching Limits

## Scope And Authorization

- Authorized assessments, labs, CTFs, and systems you own or are contracted to harden only.
- Batching and alias fan-out multiply resolver work and auth attempts. Cap probe size; stop before shared production latency or lockouts degrade for real users.
- Prefer staging or explicit capacity windows for large batches. Prove the **multiplier** with small N on **test** identities — no credential stuffing, OTP farms, or unbounded brute force.
- Redact tokens, cookies, emails, OTPs, and tenant IDs. Complexity scoring and full GraphQL surface mapping belong in handoff skills (see Routing).

## When To Use

- `POST /graphql` (or `/gql`, `/api/graphql`) accepts a **JSON array** of operations or many **aliases** in one document.
- Login, OTP, password-reset, coupon, or enumeration mutations may be **amortized** into one HTTP request past a per-request rate limit.
- Keywords: GraphQL batching, alias batching, array queries, batch HTTP, Apollo `allowBatchedHttpRequests`, batch cost, GraphQL rate-limit bypass.
- Hardening review: Apollo Server, Yoga, graphql-java, Absinthe, Hot Chocolate, or gateway config for batch size, alias limits, and cost accounting.
- After `graphql-and-hidden-parameters` notes batching but **limits/rate-keying** are unproven; after `rate-limit-bypass-testing` when the gap is GraphQL-specific multiplication.

**Not primary for:** deep nested cost algorithms (`graphql-query-complexity`); schema recon / BOLA / injection (`graphql-and-hidden-parameters`, `idor-graphql-nodes`, class skills); generic HTTP quotas without GraphQL (`api-rate-limit-design`).

## Workflow

### 1. Confirm transport and batch modes

1. Capture honest single-op traffic: `{"query","variables","operationName"}` (optional `extensions`).
2. Probe **JSON array batching** (in scope; tiny N first):

   ```http
   POST /graphql
   Content-Type: application/json

   [{"query":"query { __typename }"},{"query":"query { __typename }"}]
   ```

3. Record: HTTP 200 array of results, 400 “batch disabled”, single-object-only parse, or gateway rejection.
4. Probe **alias fan-out** in one document:

   ```graphql
   query {
     a1: user(id: "1") { id }
     a2: user(id: "2") { id }
   }
   ```

5. Note GET GraphQL, multipart, or persisted-query batch variants. Document server clues (error shape, `extensions`, headers).

### 2. Measure multiplication vs rate limits

| Probe | Change | Finding if budget multiplies |
| --- | --- | --- |
| Baseline single-op | Same cheap/failing op until `429` / lockout | Per-HTTP N |
| Array batch size K | K ops in one HTTP body | K attempts count as 1 if only HTTP-keyed |
| Alias set size K | K aliases, one query | K logical ops, one HTTP unit |
| Mixed ops | Auth-sensitive + cheap reads in one batch | Sensitive ops share cheap-request budget |

1. Baseline N for the sensitive action (failed login, OTP check, id probe) with single ops — low volume.
2. Repeat with batch/alias size **K** well below N (e.g. 5–20) on **test** accounts only.
3. Count logical attempts until throttle vs HTTP requests. Report **effective guess rate** = f(batch size, window).
4. Identify limit keys (IP, user, API key, `operationName`, document hash); one dimension at a time (`rate-limit-bypass-testing` for XFF/path).

### 3. Cost of a batch (practical accounting)

- **Naive:** 1 HTTP request = 1 rate unit regardless of op or field count.
- **Better:** cost = Σ (per-op base + alias count + weighted fields), or reject batch size > B.
- Measure wall time and partial errors for modest K; stop at proof of expensive acceptance — no shared-prod stress.
- Persisted queries: ensure clients cannot switch to full-query batch mode that skips allowlists.
- Hand scoring formulas, depth/width, and static cost plugins to **`graphql-query-complexity`**.

### 4. Apollo and common server configuration

Review code/config (not live DoS):

| Stack | Batch / limit knobs (examples) |
| --- | --- |
| Apollo Server 4 | Prefer disabling HTTP batching; pair with limit plugins |
| Armor / similar | Max aliases, max directives, max depth, cost |
| Yoga / envelop | Batching plugins; reject oversized arrays |
| graphql-java | Complexity/depth instrumentation; max tokens |
| Gateways | Operation count, payload size, timeout, concurrency |

Remediation (implement with `code-quality-standards`):

1. **Disable** JSON-array batching on public APIs unless required; else cap **max ops per body** (small fixed B).
2. Cap **max aliases** (and duplicate field fan-out) per document.
3. Charge abuse budgets in **cost units per operation/alias**, not per HTTP request — especially login, OTP, reset, search.
4. Apply authZ and lockout counters **per logical attempt** inside batches.
5. Timeouts, max payload bytes, concurrent resolver limits; log batch size/cost; alert on alias/batch spikes.
6. Prefer persisted queries / allowlists for untrusted clients.

### 5. Abuse patterns (authorized, minimal PoC)

- **Credential / OTP window expansion:** K aliases of `login` / `verifyOtp` with different secrets in one request.
- **ID enumeration:** aliased `user(id:)` / `node(id:)` past per-request throttles (ACL proof → `idor-graphql-nodes`).
- **Missing caps:** large alias/batch acceptance as evidence only — no production crash demos without approval.
- **Policy split:** REST login limited, GraphQL twin unlimited or batchable.

Leave broader GraphQL work to handoffs: schema/recon → `graphql-and-hidden-parameters`; complexity engines → `graphql-query-complexity`; multi-class GraphQL review → `graphql-security`; rate-key quirks → `rate-limit-bypass-testing`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Array batch / alias limits, batch cost vs rate limit, Apollo batch config | **This skill** | — |
| Schema recon, introspection, hidden fields | `graphql-and-hidden-parameters` | this for batch depth |
| Query complexity, depth, field weights, cost plugins | `graphql-query-complexity` | this for batch/alias units |
| Broader GraphQL security (authZ, injections, hardening set) | `graphql-security` | this when batching is one control |
| GraphQL node/edge IDOR | `idor-graphql-nodes` | this if batch multiplies ID reads |
| HTTP quota design without GraphQL detail | `api-rate-limit-design` | this for GraphQL cost units |
| Limit-key / XFF / path bypass | `rate-limit-bypass-testing` | this for GraphQL multiplier |
| Implement limiters and plugins | `code-quality-standards` | always on code changes |

## Output Checklist

- [ ] Endpoint, auth mode, server/gateway family (if known)
- [ ] Array batching: enabled/disabled; max K; over-cap error
- [ ] Alias fan-out: max aliases; partial-error behavior
- [ ] Baseline single-op N vs effective N with batch/alias K
- [ ] Limit keying (IP / user / operation / cost unit)
- [ ] Sensitive ops (login/OTP/reset/enum) on test accounts only
- [ ] Config notes (Apollo/Yoga/gateway batch and alias caps)
- [ ] Cost model: per-HTTP vs per-op vs weighted; gaps
- [ ] Impact: multiplied guess/enum/cost window (not volumetric DoS)
- [ ] Remediation: disable/cap batch, alias caps, per-op cost limits
- [ ] Handoffs: `graphql-query-complexity`, `graphql-security`, IDOR/rate-limit
- [ ] Artifacts redacted; originals immutable
