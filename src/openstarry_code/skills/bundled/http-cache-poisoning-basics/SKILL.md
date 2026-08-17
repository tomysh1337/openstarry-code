---
name: http-cache-poisoning-basics
description: >-
  High-level HTTP web cache poisoning methodology: unkeyed inputs, cache-key
  design, Host/X-Forwarded-* authority, fat GET, and second-client proofs. Use when
  shared caches (CDN, reverse proxy, gateway) may store attacker-influenced
  responses for other users during authorized assessments or defensive reviews.
---

# HTTP Cache Poisoning Basics

Entry-level methodology for **web cache poisoning**: an attacker primes a shared
cache with a response that later clients receive under a normal cache key.
Specialize Host/XFH proofs, edge key design, and app-layer caching via routing.

## When To Use

- Suspected **shared HTTP cache** (CDN, reverse proxy, API gateway) with HIT/MISS,
  `Age`, `CF-Cache-Status`, `X-Cache`, `Via`, or long public `Cache-Control`.
- Response **depends** on a header, method quirk, or body the cache may **not** key.
- Keywords: web cache poisoning, unkeyed header, fat GET, cache key confusion,
  Host/X-Forwarded-Host poison, reflected absolute URLs in cacheable pages.
- Defensive review of what enters the key vs what the origin trusts.

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Deep Host/XFH poison ladder + second-client Host proofs | `host-header-cache-poison` |
| Designing/hardening CDN keys, Vary, qs allowlist, purge | `cdn-cache-key-design` |
| App Redis/memory L1–L2, TTL, stampede, cache-aside | `caching-strategies` |
| Path-confusion private body on “static” URL | `web-cache-deception` |
| Desync / smuggling-based cache poison | `request-smuggling` |
| Password-reset / magic-link email Host ATO | `password-reset-poisoning` |

## Scope And Authorization

- **Authorized** targets only: owned apps, labs, CTFs, or written engagement scope.
- Shared-cache poison can harm **other users**. Prefer staging, unique canary paths,
  short TTL, and purge when allowed. **No unauthorized mass exploit** of popular
  production asset URLs or shared keys.
- One clean proof per poison class is enough. Use collaborator/OAST domains **you** control.
- Redact cookies, tokens, secret-bearing URLs, and PII from reports; keep raw captures offline per policy.
- Distinguish reflection (single request) from **cross-user poison** (second clean client).

## Workflow

1. **Confirm a shared cache exists**  
   Baseline a cacheable-looking URL (static asset, public HTML shell, long TTL).
   Note status, `Cache-Control`/`Surrogate-Control`, `Vary`, cache headers, body
   fingerprint. Record product hints (Cloudflare, Fastly, CloudFront, nginx, etc.).

2. **Hypothesize the cache key**  
   What likely enters the key: scheme, host, path, method, allowlisted query,
   selected headers/`Vary`, sometimes cookies. What is often **unkeyed**: most
   request headers (`X-Forwarded-*`, `X-Original-URL`, `Accept-*` if not in Vary),
   request body on GET, tracking query params if stripped. Document the hypothesis
   before mutating. For product key design and defenses → `cdn-cache-key-design`.

3. **Find unkeyed, response-shaping inputs**  
   Goal: change the **origin response** while keeping the **same cache key**.

   | Input class | Examples | Why it matters |
   | --- | --- | --- |
   | Authority / Host | `Host`, `X-Forwarded-Host`, `Forwarded`, `:authority` | Absolute script/link/`Location` may flip |
   | Path/routing overrides | `X-Original-URL`, `X-Rewrite-URL` | Different backend body, same keyed path |
   | Negotiation | `Accept`, `Accept-Language`, `Accept-Encoding` | Wrong variant cached if unkeyed |
   | Fat GET | Body or trailing data on GET | Origin uses body; cache keys method+URL only |
   | Header injection / CRLF | Rare on modern stacks | Extra response headers into store |

   Probe with edge-valid `Host` when required; inject unkeyed headers one class at a
   time. Candidate: response changes **and** remains cacheable (200, public path,
   missing `private`/`no-store`/`Set-Cookie` personalization).

4. **Host / X-Forwarded-* (high level)**  
   Keep `Host: target.example` if the edge rejects foreign hosts; set
   `X-Forwarded-Host` / `Forwarded` to a canary you control. Look for reflected
   authority in HTML, JS `src`, CSS, or `Location`. Full Host/XFH poison methodology
   and second-client Host ladder → `host-header-cache-poison`. Generic Host without
   cache → `http-host-header-attacks`.

5. **Fat GET and method quirks**  
   Some stacks parse a **request body on GET** (or nonstandard methods) while the
   cache keys only method + URL. Send a cacheable GET with a body that influences
   routing, template selection, or reflected content. Confirm the clean follow-up
   has **no body** yet receives the poisoned object. Do not spam high-traffic keys.

6. **Poison then second-client verify**  
   1. Poison request (unkeyed input + canary) against a **unique** path when possible.  
   2. Clean client (browser or curl, no special headers/body) hits the **same keyed URL**.  
   3. Confirm: clean client sees attacker-influenced content; prefer HIT / rising `Age`.  
   Reflection alone is **not** cross-user poison.

7. **Impact triage and containment**  
   Label impact: stored XSS via cached shell, open redirect phishing links, wrong
   CORS/security headers, SEO/canonical only, or desync-assisted store. Hand XSS to
   `xss-cross-site-scripting`, desync to `request-smuggling`, path deception to
   `web-cache-deception`. Purge canaries or wait TTL; retest after key/strip fixes.

8. **Defensive takeaways**  
   Strip or overwrite client-supplied authority headers at the trusted edge; put
   every body-affecting input in the key or `Vary`; never public-cache personalized
   or `Set-Cookie` responses under a URL-only key; configured `APP_URL` over Host
   reflection. Edge design → `cdn-cache-key-design`; app L1/L2 → `caching-strategies`;
   code hygiene → `code-quality-standards`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| General cache-poison triage / unkeyed input hunt | **This skill** | — |
| Host/XFH shared-cache poison assessment | `host-header-cache-poison` | this for framing |
| CDN key, Vary, query allowlist, purge hardening | `cdn-cache-key-design` | this for attack model |
| App Redis/memory cache, TTL, stampede | `caching-strategies` | this for HTTP/CDN layer |
| Web cache deception (not attacker-primed store) | `web-cache-deception` | — |
| Smuggling-enabled poison | `request-smuggling` | this for impact framing |
| Implementation / header emission tests | `code-quality-standards` | always on code/IaC |

## Output Checklist

- [ ] Authorization, canary domain, unique paths, purge/TTL plan stated
- [ ] Shared-cache evidence (product headers, Age/HIT, Cache-Control)
- [ ] Cache-key hypothesis (keyed vs unkeyed components)
- [ ] Unkeyed input class documented (Host/XFH, fat GET, Accept-*, routing headers)
- [ ] Poison + **clean second client** proof (or explicit “reflection only”)
- [ ] Impact class labeled; poison vs deception vs Host-only vs desync
- [ ] Collateral minimized; secrets redacted
- [ ] Remediation pointers: strip unkeyed headers, key/`Vary` completeness,
      private/no-store on personalized pages; handoffs to design skills as needed
