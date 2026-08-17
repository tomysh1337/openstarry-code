---
name: cdn-cache-key-design
description: >
  Design CDN/edge HTTP cache keys: scheme/host/path, Vary, cookie inclusion,
  query-string allowlists, unkeyed header poison defenses, and purge strategy.
  Use when configuring CloudFront/Fastly/Cloudflare/Akamai cache keys, Vary
  headers, qs whitelist, cookie keying, cache poison hardening, or edge purge
  APIs. Hand app L1/L2 Redis TTL and stampede policy to caching-strategies.
---

# CDN Cache Key Design

Design **shared HTTP cache keys at the CDN/edge**: what enters the key, how
`Vary` and product rules interact, and how to purge safely. Prefer the org’s
CDN product, IaC modules, and origin `Cache-Control` over a second key scheme.

## When To Use

- Defining/reviewing **CDN cache keys** (host, path, query, headers, cookies)
- Setting **`Vary`** for negotiation without over-fragmenting the keyspace
- **Query allowlists** (keep filters; ignore tracking params)
- **Cookies** in key vs force private/`no-store`
- Hardening **cache poisoning** via unkeyed headers (Host/XFH, Accept-*, auth, CORS)
- **Purge** models: URL, tag/surrogate-key, soft purge, generation bump
- Mentions: CDN cache key, Vary, qs whitelist, cookie in key, Surrogate-Key,
  CF-Cache-Status, Fastly VCL, CloudFront cache policy

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| App/Redis L1–L2 keys, TTL, stampede, cache-aside | `caching-strategies` |
| Authorized Host/XFH poison assessment | `host-header-cache-poison` |
| Path-confusion private body on “static” URL | `web-cache-deception` |
| Generic Host/vhost without cache focus | `http-host-header-attacks` |
| CORS preflight Max-Age / ACAO shared-cache | `cors-preflight-cache` |
| Implementation quality baseline | `code-quality-standards` |

## Repo Config First

Repo CDN IaC, origin headers, and edge modules **outrank** defaults below.

1. **CDN product:** CloudFront policies, Fastly VCL/Compute, Cloudflare Cache Rules/Workers, Akamai — extend first
2. **Origin contract:** `Cache-Control`, `Surrogate-Control`, `Vary`, `Surrogate-Key` / CDN-Cache-Tag
3. **Shared strip/allow lists:** query allow/deny, cookie strip, host canonicalizers
4. **Purge tooling:** CI jobs, tag APIs, soft-purge, deploy generation bumps
5. **Auth/privacy paths:** private / `no-store` / cache-bypass already marked
6. **Neighbor services:** copy mature static/API edge policies in the org
7. **Observability:** HIT/MISS, purge latency, poison canary dashboards

**Precedence:** Follow the repo. Flag public cache of personalized bodies, unbounded
query keys, or missing purge when users observe their own writes.

## Workflow

1. **Classify responses before keying.**

   | Class | Cacheability | Key posture |
   | --- | --- | --- |
   | Public immutable asset | Long TTL, public | Path (+ version in path); ignore most query |
   | Public HTML/API (same for all) | Short/medium public | Path + allowlisted query; tight Vary |
   | Negotiated (lang, encoding, format) | Public if safe | Negotiation inputs in key or `Vary` |
   | Personalized / authz-sensitive | `private` or `no-store` | **Bypass** shared cache; never cookie-blind public key |
   | Error / challenge | Short or no-store | Do not sticky-cache 5xx/auth as long public HITs |

2. **Define canonical key components.**
   - **Scheme + host + path** (normalized: slash, case, default port). Document edge vs origin so keys cannot be forked.
   - **Method:** usually GET/HEAD only; do not cache arbitrary POST as GET.
   - **Query — allowlist** meaningful params (id, page, sort); strip `utm_*`, `fbclid`, analytics busters. Prefer allowlist over denylist. Normalize order/encoding so equivalent sets share one key.
   - **Headers / `Vary`:** only inputs that change body or security headers (`Accept-Encoding` or edge-normalized compression; `Accept` / `Accept-Language` only when body differs and cardinality is bounded).
   - **Cookies:** include a **named** session/segment cookie only if body varies and cardinality is OK; else strip cookies on public routes or use `private`. Whole-`Cookie` in key shatters HIT rate and does not fix other unkeyed inputs.

3. **Align `Vary` with product cache-key rules.**
   - Every input that changes a **shared** response must be in the **CDN key** or listed in `Vary` *and* honored by the product.
   - Avoid lazy `Vary: Cookie` / `Vary: *` for personalization — uncache or whitelist named cookies.
   - Origin `Vary` and CDN “include header X” must not disagree on Host/XFH, `Origin` (CORS), or `Authorization`.

4. **Poison-resistant keying (defensive eng).**
   - Strip/overwrite client `X-Forwarded-Host`, `Forwarded`, `X-Original-URL` at trusted edge; block unkeyed authority from rewriting cacheable absolute URLs.
   - If body/`Location` reflects Host/XFH: put authority in the key **or** force a configured public base URL (stop reflecting).
   - Never `public`-cache responses with `Set-Cookie` or authz-specific bodies under a URL-only key.
   - Cache `OPTIONS`/CORS only if `Vary: Origin` (or Origin in key) is proven — see `cors-preflight-cache`.
   - Authorized second-client poison proofs → `host-header-cache-poison`.

5. **Purge strategy.**

   | Strategy | When | Notes |
   | --- | --- | --- |
   | URL purge | Few known paths | Misses query/header variants unless all listed |
   | Tag / Surrogate-Key | Entity graphs, CMS | Emit tags; purge by tag on write — default for HTML |
   | Soft purge / SWR | Instant unpublish | Stale while revalidate if product supports |
   | Path / generation version | Immutable assets | `/assets/v{build}/…` |
   | TTL-only | Low-risk static | Insufficient when users must see own writes |

   Document purge owner (write path, webhook, deploy), blast radius, purge API auth,
   and multi-layer order (CDN then app L2 — L2 detail → `caching-strategies`).

6. **Verify HIT identity.** Two clients, same intended key → same body; change
   allowlisted query or Vary input → MISS; stripped tracking query → same object.
   Log key components in staging only.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| CDN/edge key, Vary, query allowlist, cookie key, purge tags | **This skill** | — |
| App Redis/memory keys, TTL, stampede, cache-aside | `caching-strategies` | this for L3 HTTP key |
| Authorized Host/XFH shared-cache poison testing | `host-header-cache-poison` | this when **fixing** key |
| Web cache deception (path / extension tricks) | `web-cache-deception` | this for public vs private |
| CORS ACAO under shared cache / Max-Age | `cors-preflight-cache` | this for Origin in key/Vary |
| nginx edge headers / proxy Host | `nginx-security-headers` | this for CDN key |
| Implement policies, tests, header hygiene | `code-quality-standards` | **always** on code/IaC |

- **`caching-strategies`:** L1/L2 pattern, Redis namespaces, stampede, multi-layer TTL. Keep **this skill primary** for shared HTTP/CDN key composition, Vary, query/cookie rules, and edge purge.
- **`code-quality-standards`:** bound keyed-input cardinality; no secrets in keys/purge logs; tests for allowlist normalization and private-path bypass.

## Output Checklist

- [ ] Response classes: public vs private/no-store vs negotiated
- [ ] Repo CDN product, IaC policies, origin Cache-Control inventoried
- [ ] Key: scheme/host/path normalization, method scope documented
- [ ] Query allowlist; tracking params ignored; order normalized
- [ ] Cookies: named include or strip; no whole-Cookie public personalization
- [ ] `Vary` + CDN key cover every body-affecting input; no lazy `Vary: *`
- [ ] Unkeyed Host/XFH reflection reviewed; strip at edge or key authority
- [ ] Purge model (URL / tag / soft / generation) with owners and blast radius
- [ ] HIT identity verified (same key + fork cases)
- [ ] L1/L2 app policy paired with `caching-strategies` when both layers exist
- [ ] `code-quality-standards` applied for IaC/app header emission and tests
