---
name: host-header-cache-poison
description: >-
  Authorized Host header and cache-poisoning methodology: unkeyed Host /
  X-Forwarded-Host influence on cacheable responses, cache-key confusion,
  absolute URL injection into shared caches, and second-client proofs. Use when
  CDNs or reverse proxies may store attacker-influenced content for other users.
---

# Host Header + Cache Poisoning

## Scope And Authorization

- Authorized apps, labs, and owned infrastructure only. Shared CDN/proxy poison can affect **other users** — prefer staging, unique canary paths, and short TTL/purge when allowed.
- Do not mass-poison production caches or flood email/reset systems. One clean proof per poison class is enough.
- Use attacker domains **you control** (collaborator/OAST). Never poison or reset against third-party victims.
- Redact tokens, cookies, secret-bearing URLs, and PII from public write-ups; store raw evidence offline per policy.
- Distinguish **application** Host trust from **edge** rejection; document where authority is consumed and what enters the cache key.

## Use When

- Focus is **Host / X-Forwarded-* / authority + cache** (not only reflected Host in HTML).
- CDN or reverse proxy present (`Age`, `X-Cache`, `CF-Cache-Status`, `Via`, long `Cache-Control`).
- Apps build absolute links, script `src`, redirects, or canonicals from `Host`, `X-Forwarded-Host`, `Forwarded`, or `:authority`.
- Suspected unkeyed headers: response varies with XFH/Host override but cache key ignores them.
- Keywords: Host header cache poisoning, unkeyed header, web cache poisoning via Host, authority confusion on CDN.
- Primary when cache **poison** (attacker writes bad content for others) is the goal. Path-confusion private-body leaks → `web-cache-deception`. Generic Host without cache → `http-host-header-attacks`. Reset-email ATO → `password-reset-poisoning`.

## Workflow

1. **Separate poison from deception**

   | Class | Who primes cache | Harm |
   | --- | --- | --- |
   | **Poison (this)** | Attacker request with unkeyed input | Later visitors get attacker content |
   | **Deception** | Victim (auth) on static-looking URL | Attacker reads victim private body |
   | **Host-only** | N/A or single request | Reflected link / reset / vhost, no shared store |

2. **Map cache and authority consumers**  
   Baseline with `Host: target.example`. Note cache HIT/MISS/`Age`, product fingerprints, `Cache-Control`/status/`Set-Cookie`, suspected key (path, query, Host, `Vary`, cookies), and absolute URL builders (HTML links, `Location`, script/src, meta canonical). Reuse host-consumer inventory from `http-host-header-attacks`.

3. **Find unkeyed or weakly keyed inputs**  
   Goal: response **depends** on a header the cache **does not** key on. Keep edge-valid Host when required; inject:

   ```http
   GET / HTTP/1.1
   Host: target.example
   X-Forwarded-Host: attacker.tld
   X-Forwarded-Proto: https
   Forwarded: host=attacker.tld
   X-Host: attacker.tld
   ```

   Also probe: evil `Host` if edge still caches; Host+port; duplicate Host; `:authority` vs Host (HTTP/2); absolute-form URI. Success candidate: body/headers reflect attacker authority **and** response looks cacheable (200, public/static path, missing `private`/`no-store`).

4. **Poison then second-client verify**  
   1. Poison with canary authority you control (unique path to limit collateral).  
   2. Clean client (no special headers) requests the **same cache key** URL.  
   3. Confirmed when clean client gets attacker host in links, script URLs, redirects, or injected content — ideally HIT / rising `Age`.

   ```http
   GET /static/app-shell.js HTTP/1.1
   Host: target.example
   X-Forwarded-Host: canary.attacker.tld
   ```

   ```bash
   curl -sS -D- "https://target.example/static/app-shell.js" -o /tmp/poison_body
   ```

   If Host is fully keyed, classic cross-user Host poison may fail — focus unkeyed XFH and related headers.

5. **Impact classes and handoffs**

   | Impact | Evidence / handoff |
   | --- | --- |
   | XSS via cached absolute script/src | Second user executes attacker JS → `xss-cross-site-scripting` |
   | Open redirect / phishing links | Cached `Location` or href → `open-redirect` if param-led |
   | Mixed content / asset base flip | CSS/JS base points at attacker |
   | SEO/canonical only | Usually low without security decision |
   | Desync-based poison | `request-smuggling` |
   | Path-only private leak | `web-cache-deception` |

6. **Non-cache Host effects**  
   Record Host/XFH changes to `Location`, email links, or vhost routing when severity is single-user. Full reset methodology → `password-reset-poisoning`. Broad Host ladder → `http-host-header-attacks`.

7. **Normalization and edge vs origin**  
   If simple XFH fails: encoded hosts, trailing dots, ports, `X-Forwarded-Host` lists (`a, b`), proto mismatch, extra unkeyed stack headers. Record on-wire bytes. Note edge reject vs direct-origin accept when origin is in scope.

8. **Containment and retest**  
   Unique canaries; purge or wait TTL. After fix: unkeyed header no longer affects cacheable body; Host allowlist; key includes authority or strips client XFH. Code fixes → `code-quality-standards` (canonical `APP_URL`, trusted-proxy, `Vary`/key correctness, `private`/`no-store` on personalized pages).

## Routing

| Need | Skill |
| --- | --- |
| Broad Host/XFH/vhost without cache focus | `http-host-header-attacks` |
| Path confusion / victim private body on static URL | `web-cache-deception` |
| Password-reset / magic-link email ATO | `password-reset-poisoning` |
| Desync / smuggling cache poison | `request-smuggling` |
| XSS via poisoned cached page | `xss-cross-site-scripting` |
| SSRF if server fetches Host-derived URL | `ssrf-server-side-request-forgery` |
| Canonical base URL / proxy trust / cache headers in code | `code-quality-standards` |

## Checklist

- [ ] Authorization; canary domain; unique paths; purge/TTL plan
- [ ] CDN/proxy evidence; baseline vs poison headers
- [ ] Inputs that change response (`Host`, XFH, `Forwarded`, `:authority`)
- [ ] Cache key hypothesis (Host in key? unkeyed header?)
- [ ] Poison + **clean second client** proof (HIT/Age when available)
- [ ] Impact class labeled; poison vs deception vs Host-only
- [ ] Edge vs origin differences; collateral minimized; secrets redacted
- [ ] Remediation: configured base URL; trust XFH only from known proxies; key authority or strip unkeyed headers; Host allowlist; no public cache of personalized HTML

## Rules

- Always second-client (or equivalent) proof for cross-user cache claims — reflection alone is not poison.
- Never mass-poison popular production asset URLs; use unique canaries when possible.
- Do not reset or target accounts you do not own.
- Reflected Host without cache or security decision is usually low severity — escalate only with multi-user or ATO path.
- Separate write-ups: Host cache **poison** (this) vs **web cache deception** vs generic Host attacks.
- Rate-limit email and state-changing endpoints; authorized testing only.
