---
name: websocket-rate-limit-design
description: >
  Design WebSocket rate limits: connection/upgrade budgets, concurrent sockets,
  per-message and byte/frame caps, subscription fan-out, close/backpressure
  signals, and abuse-resistant keying. Use when WebSocket rate limit design,
  WS throttle, socket quota, message RPS, concurrent connection limit, upgrade
  flood, subscription cost, or realtime abuse protection for owned systems.
---

# WebSocket Rate Limit Design

Design **fair, abuse-resistant WebSocket throttling**: upgrade rate, concurrent
sockets, inbound/outbound message and byte budgets, subscription fan-out cost,
and clear client signals. Prefer the repo’s gateway, mesh, or WS framework
limiters over a second ad-hoc counter layer. Pure HTTP REST quotas →
`api-rate-limit-design`. In-process queue pressure → `backpressure-patterns`.

## Scope And Authorization

- Design/implement on systems you **own** or are contracted to change — not to
  exhaust third-party realtime endpoints.
- Adversarial keying (header trust, multi-egress, path aliases) →
  `rate-limit-bypass-testing` under explicit authorization only.
- Prefer staging/synthetic clients for soak tests; avoid volumes that degrade
  shared production fan-out. Redact tokens and user ids in samples.
- Auth-sensitive actions over WS (login, OTP) need **dual keys** and progressive
  delay — never pure per-IP soft limits only.

## When To Use

- Limits for **upgrade rate**, **concurrent connections**, **message RPS**,
  **frame/message size**, and **subscribe/publish cost**
- Multi-tier realtime quotas (anonymous / free / paid / partner)
- Close codes, app error frames, and client retry after throttle
- Enforcement placement (edge L7, proxy, accept loop, room fan-out)
- Mentions: WebSocket rate limit, WS throttle, socket quota, message flood,
  connection storm, subscription limit, realtime abuse, concurrent WS

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| HTTP REST / API `429` product design | `api-rate-limit-design` |
| Auth/origin/CSWSH and WS security testing | `websocket-security` |
| Binary codecs / schema recovery | `websocket-binary-reverse-engineering` |
| Bounded buffers, slow consumer, overflow | `backpressure-patterns` |
| Authorized bypass / key-split testing | `rate-limit-bypass-testing` |
| Account hard lock after auth fails | `account-lockout-design` |
| Implementation quality baseline | `code-quality-standards` |

## Repo Config First

Repo gateways, proxies, and existing WS stacks **outrank** defaults below.

1. **Existing enforcers:** nginx/Envoy connection limits, gateway WS policies,
   framework middleware, Redis counters, max room subscribers — configure first
2. **Identity after upgrade:** user, org, API key, device bound to the socket
3. **Trusted client IP:** LB/edge hop only; never sole key on client `X-Forwarded-For`
4. **Protocol surface:** text vs binary, subprotocols, existing max frame size
5. **Auth on upgrade:** cookie/JWT/query ticket ADRs — align quotas with threat model
6. **Observability:** connect/reject, messages/s, close codes, fan-out lag metrics
7. **Config/flags:** dynamic per-plan concurrent and message budgets

**Precedence:** Follow the repo. Flag IP-only limits on authenticated sockets,
unlimited inbound frames, silent drops of critical events, or duplicate limiters
without one documented budget.

## Workflow

1. **Inventory surfaces and abuse cases.**

   | Surface | Abuse if unlimited | Suggested keying (start) |
   | --- | --- | --- |
   | HTTP upgrade | Connection storm / FD exhaustion | Trusted IP + user/API key |
   | Concurrent sockets | Resource hog / multi-tab abuse | User or device (+ IP ceiling) |
   | Inbound app messages | Parse/CPU flood, command spam | Socket + user + message type |
   | Large frames / blobs | Memory DoS | Global max frame + per-user bytes/s |
   | Subscribe / join room | Fan-out amplification | User + room count + members |
   | Server push / broadcast | Cost / noisy neighbor | Publisher + tenant + cost units |
   | Auth actions over WS | Stuffing / OTP grind | Normalized account **and** IP |

2. **Layer limits (compose; none alone is enough).**
   - **L1 Admit:** upgrades/min per IP and identity; max handshake size
   - **L2 Concurrency:** max sockets per user/device/org; optional process cap
   - **L3 Message rate:** token bucket per socket and user; separate ping vs costly ops
   - **L4 Payload:** max message bytes, frames/s, decompression bomb caps
   - **L5 Business cost:** subscribe count, broadcast weight, stream tokens as units

3. **Algorithm and store.** Token bucket for message rate; lease on open / release on
   close for concurrency; cost weights for variable fan-out. Atomic distributed
   counters; document fail-open vs fail-closed if the store is down.

4. **Signal clients (no silent blackhole for first-party APIs).**
   - App error frame: stable `code` (e.g. `rate_limit_exceeded`), `retry_after_seconds`
   - Or documented close (e.g. **1008** / custom app code); reason without secrets
   - After limit: **pause reads** or reject messages; queue pressure → `backpressure-patterns`
   - Clients honor backoff (`retry-backoff-patterns`); reconnect storms need L1+L2

5. **Place enforcement.** Edge: coarse IP connect rate and concurrent source caps.
   Accept loop: identity-aware concurrent and message limits after auth. Fan-out:
   membership and publish cost. One authoritative budget per class; normalize path
   aliases so `/ws` and `/ws/` share keys.

6. **Observe and review.** Metrics: upgrade rejects, active sockets, msg/s, limit
   hits (hashed keys), close-code histogram. Tests: burst messages, multi-tab cap,
   reconnect storm, large-frame reject. Adversarial keying →
   `rate-limit-bypass-testing`; WS security → `websocket-security`; code →
   `code-quality-standards`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| WS connect, concurrent, message, byte, fan-out budgets | **This skill** | — |
| HTTP REST quotas, `429` headers, plan tiers | `api-rate-limit-design` | this for sockets |
| Origin/auth/CSWSH, ticket leakage, WS security tests | `websocket-security` | this for quotas |
| Bounded buffers, slow consumer, overflow | `backpressure-patterns` | this for admit caps |
| Authorized bypass / multi-egress / header trust | `rate-limit-bypass-testing` | this for policy |
| Auth hard lockout (not soft WS QPS) | `account-lockout-design` | this for msg caps |
| Binary schema / codec RE | `websocket-binary-reverse-engineering` | — |
| Implement limiters, counters, tests, logs | `code-quality-standards` | **always** |

Keep **this skill primary** for WS-specific budgets. Use **`api-rate-limit-design`**
for pure HTTP; **`backpressure-patterns`** for internal queue depth;
**`rate-limit-bypass-testing`** when proving keys expand — feed findings back here.

## Output Checklist

- [ ] Surfaces inventoried: upgrade, concurrent, inbound msg, size, subscribe, publish, auth-over-WS
- [ ] Repo gateway/proxy/framework limiters and trusted-IP path inventoried
- [ ] Keys defined (IP / user / device / org / socket / message class) with composites
- [ ] L1–L5 covered; burst vs sustained and cost units documented
- [ ] Max frame/message size and decompression bounds set
- [ ] Client signals: error frame and/or close code + retry guidance documented
- [ ] Enforcement placement clear; path aliases share one bucket
- [ ] Fan-out/membership caps prevent amplification
- [ ] Metrics + cardinality-safe labels; store-outage fail-open/closed decided
- [ ] Reconnect storm controlled by upgrade-rate + concurrent leases
- [ ] Adversarial review via `rate-limit-bypass-testing` when in scope
- [ ] `code-quality-standards` applied for implementation, tests, logging hygiene
