---
name: api-rate-limit-design
description: >
  Design API rate limits and quotas: limit keys (IP, user, API key, route),
  budgets and windows, multi-tier policies, headers/UX, and abuse-resistant
  enforcement. Use when rate limit design, API quota, 限流设计, 429 policy,
  Retry-After, or throttle UX. Pair with bypass testing for adversarial review.
---

# API Rate Limit Design

Engineering design for **fair, abuse-resistant API throttling**: what to key on,
how large budgets should be, how windows work, what clients see on `429`, and
how enforcement stays consistent under proxies and multi-tenant load. Prefer the
repo’s existing gateway, mesh, or middleware rate-limit stack over a second
ad-hoc counter layer.

## Scope And Authorization

- This skill is for **designing and implementing** limits on systems you own or
  are contracted to change — not for denying service to third parties.
- When validating limits adversarially (header trust, key splits, rotation),
  hand off to `rate-limit-bypass-testing` under explicit authorization only.
- Do not recommend traffic volumes that degrade shared production infra.
  Prefer load/staging environments and synthetic users for soak tests.
- Redact API keys, tokens, and customer identifiers in design docs and samples.
- Auth-sensitive surfaces (login, OTP, password reset) need **stricter** dual
  keys and progressive delay; never design those as pure per-IP soft limits only.

## Use When

- Choosing limit keys, windows (fixed/sliding), and per-route or global budgets
- Designing multi-tier quotas (anonymous / free / paid / partner API keys)
- Defining `429` bodies, `Retry-After`, and `X-RateLimit-*` (or equivalent) UX
- Placing enforcement (edge gateway vs app middleware vs service mesh)
- Protecting expensive endpoints (search, export, AI, SMS/email) with cost-aware limits
- User mentions: rate limit design, API quota, throttle, 限流, 配额, budget,
  token bucket, leaky bucket, `429`, `Retry-After`, per-tenant QPS

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Authorized bypass / keying-gap testing | `rate-limit-bypass-testing` |
| CAPTCHA / bot-challenge control research | `captcha-bypass-research` |
| Client retry/backoff after 429 | `retry-backoff-patterns` |
| MFA/OTP logic beyond attempt budgets | `mfa-bypass-methodology` |
| General implementation quality | `code-quality-standards` |

## Repo Config First

Repo gateways, mesh policies, and existing middleware **outrank** this skill’s defaults.

1. **Existing enforcers:** API gateway rate policies, nginx `limit_req`, Envoy
   local rate limit, Redis/cluster counters, framework middleware, WAF bot rules —
   **extend or configure these** before inventing a parallel limiter
2. **Identity and tenancy:** how the app already knows user id, org id, API key,
   and trusted client IP (LB hop, `CF-Connecting-IP` only when edge overwrites)
3. **Auth and sensitive routes:** login, OTP, reset, signup policies already in
   security ADRs — align quotas with those threat models
4. **Partner / plan catalogs:** billed QPS tiers, burst vs sustained, SLA language
5. **Observability:** existing metrics for 429 rate, limit key cardinality, and
   top throttled routes — reuse dashboards rather than silent new counters only
6. **Neighboring services:** copy mature public or internal APIs in the same org
   for header names, window sizes, and error envelope shape
7. **Feature flags / config store:** dynamic limit tables vs hard-coded constants

**Precedence:** If repo rules conflict with defaults below, follow the repo.
Surface conflicts that trust raw client `X-Forwarded-For`, key only on IP for
auth endpoints, or stack duplicate limiters without a single documented budget.

## Workflow

1. **Inventory surfaces and abuse cases.**

   | Surface | Abuse if unlimited | Suggested keying (start) |
   | --- | --- | --- |
   | Password login / token | Credential stuffing | Normalized account **and** IP (stricter of both) |
   | MFA / OTP verify | Online code guess | Account + IP; progressive delay / lockout |
   | Reset / resend | Email/SMS flood | Account + IP; expensive sink budgets |
   | Public read API | Scraping / cost | IP + optional API key |
   | Authenticated API | Quota theft / noisy neighbor | User or API key (+ optional IP ceiling) |
   | Expensive jobs | Cost explosion | User/org + concurrent job cap + cost units |

2. **Choose limit keys (identity of the bucket).**
   - **IP:** always secondary or anonymous; never sole key for auth if IP rotation is realistic
   - **User / subject:** after authentication; normalize identifiers (case, phone E.164)
   - **API key / OAuth client:** partner and machine clients
   - **Route / operation class:** separate buckets for cheap vs expensive ops
   - **Tenant / org:** multi-tenant fairness
   - Prefer **composite** policies: e.g. per-key QPS **and** global/IP ceiling
   - Document trusted client-IP extraction (one LB hop); strip spoofable hop headers at edge

3. **Choose algorithm and window.**

   | Model | Behavior | Typical use |
   | --- | --- | --- |
   | Fixed window | Simple; edge bursts at window boundary | Coarse quotas |
   | Sliding window / rolling log | Smoother fairness | User-facing APIs |
   | Token bucket | Sustained rate + burst | Public HTTP APIs |
   | Leaky bucket | Smooth outflow | Protecting fragile backends |
   | Cost / weight units | Batch, GraphQL, AI tokens | Variable-cost ops |

   Define: capacity, refill/sustained rate, burst, and whether limits are
   distributed (Redis/`INCR`+TTL, gateway cluster) with **atomic** updates.

4. **Set budgets from product and capacity — not guesswork alone.**
   - Start from p95 legitimate traffic × safety factor; load-test the origin
   - Separate **soft** (429 + Retry-After) from **hard** lockout (auth abuse)
   - Tier by plan; document free-tier scrape resistance vs paid burst
   - GraphQL/batch: cost-based limits, not only one HTTP request = one unit

5. **Place enforcement.**
   - Edge/gateway: coarse IP and global; early drop of obvious floods
   - App: identity-aware and business-cost limits after authz
   - One **authoritative** decision per class of traffic; avoid contradictory dual 429s
   - Normalize path/method before keying so aliases share one bucket

6. **Design client UX and signals.**

   ```http
   HTTP/1.1 429 Too Many Requests
   Retry-After: 12
   X-RateLimit-Limit: 100
   X-RateLimit-Remaining: 0
   X-RateLimit-Reset: 1710000012
   Content-Type: application/json

   {
     "error": {
       "code": "rate_limit_exceeded",
       "message": "Rate limit exceeded. Retry after the time in Retry-After.",
       "retry_after_seconds": 12
     }
   }
   ```

   - Prefer stable machine `code`; human `message` without leaking whether a user exists
   - Document headers in OpenAPI; keep names consistent across versions
   - Optional: different messages for quota vs transient edge throttle
   - Pair clients with `retry-backoff-patterns` (honor `Retry-After`, jitter, budget)

7. **Auth and high-risk special cases.**
   - Login/OTP: progressive delay, captcha step-up, hard lockout — not only soft QPS
   - Never reset auth failure counters on partial success races (atomic counters)
   - SMS/email: strict per-destination and per-account budgets
   - Admin/export: lower concurrency; audit log throttle hits on sensitive routes

8. **Observe, test, and review adversarially.**
   - Metrics: 429 ratio, top keys (hashed/cardinality-safe), latency of limiter
   - Contract tests for headers and status; chaos: Redis blip fail-open vs fail-closed policy (document choice)
   - Authorized keying review → `rate-limit-bypass-testing`
   - Implementation hygiene → `code-quality-standards`

## Limit Key Design Notes

| Pattern | Good | Bad |
| --- | --- | --- |
| Auth login | `hash(normalized_user) + trusted_ip` | IP-only with open registration of new “users” ignored |
| API key | Key id + route class | Same bucket for health check and export |
| Anonymous | Trusted IP + route; captcha on burn | Trust client-supplied `X-Forwarded-For` from public internet |
| Multi-tenant | Per-org cap + per-user subcap | One global counter starving all tenants |

**Cardinality:** Do not create unbounded Redis keys from raw untrusted input
(e.g. every random `X-Forwarded-For`). Use trusted IP only; cap key TTL.

## UX And Product Rules

- Communicate quotas in developer docs and plan pages before hard enforcement surprises
- Sandbox keys: lower budgets, clear `code` for upgrade path
- Idempotent reads may share higher budgets than expensive writes
- Avoid silent drops (no body) for first-party APIs unless edge L7 DDoS mode
- Support contacts: how to request limit increases without disabling safety on auth routes

## Anti-Patterns

- IP-only limits on login/OTP as the sole control
- Trusting client-controlled forwarding headers for the limit key
- Separate buckets for `/login` vs `/Login` vs `/api/v1/login` (alias split)
- Non-atomic counters under concurrent requests (TOCTOU over-admit)
- Stacking gateway + app + SDK limits with no single documented budget
- Omitting `Retry-After` so clients stampede
- Same budget for “list 10 items” and “export 10M rows”
- Fail-open under limiter outage on auth without compensating controls
- Logging full API keys or session tokens when recording 429s

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Design keys, budgets, windows, 429 UX, placement | **This skill** | — |
| Authorized testing of bypass, header trust, key splits | `rate-limit-bypass-testing` | this for intended policy |
| CAPTCHA / bot step-up design research | `captcha-bypass-research` | this for attempt budgets |
| Client retries after 429 | `retry-backoff-patterns` | this for server signals |
| MFA/OTP beyond rate budgets | `mfa-bypass-methodology` | this for verify/resend caps |
| API discovery of limit headers in assessments | `api-recon-and-docs` | note policies found |
| Implement middleware, counters, tests, IP trust | `code-quality-standards` | **always apply** on code changes |

### Routing to `rate-limit-bypass-testing`

Keep **this skill primary** for policy and product design. Switch to
**`rate-limit-bypass-testing`** when:

- Proving whether keys can be expanded (XFF, path aliases, method quirks)
- Measuring effective N under authorized multi-egress or dual-stack
- Validating auth-window effectiveness (login/OTP/reset)

Feed findings back into this skill’s keying and enforcement placement.

### Routing to `code-quality-standards`

Always apply **`code-quality-standards`** when implementing limiters:

- Atomic counters; bounded key cardinality; explicit fail-open/closed
- Validate and normalize identity at the boundary before keying
- No secrets in rate-limit logs or metric labels
- Tests for window edge, concurrent admit, and trusted-IP extraction
- Clear errors without user-enumeration side channels on auth routes

## Checklist

- [ ] Surfaces and abuse cases inventoried (auth, public, paid, expensive)
- [ ] Repo gateway/middleware/mesh limiters and IP-trust path inventoried
- [ ] Limit keys defined (IP / user / API key / org / route) with composites where needed
- [ ] Trusted client-IP source documented; spoofable headers not used as sole key
- [ ] Algorithm and window chosen; burst vs sustained documented
- [ ] Budgets tiered; cost-weighted ops (batch/GraphQL/AI) handled
- [ ] Enforcement placement clear; path normalization before keying
- [ ] `429` + `Retry-After` (+ optional rate-limit headers) and stable error `code`
- [ ] Auth routes: dual key, progressive controls, atomic counters
- [ ] Metrics and cardinality-safe dashboards
- [ ] Fail-open vs fail-closed under store outage decided and documented
- [ ] Docs/OpenAPI describe quotas and headers
- [ ] Authorized adversarial review planned via `rate-limit-bypass-testing` when in scope
- [ ] `code-quality-standards` applied for implementation, tests, and logging hygiene
