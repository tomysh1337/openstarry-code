---
name: mixed-content-hardening
description: >-
  Find and fix HTTPS mixed content (active and passive), insecure third-party
  assets, missing upgrade-insecure-requests / HSTS, and CSP report endpoints for
  residual HTTP subresources. Use when hardening org-owned or authorized HTTPS
  sites that still load http:// scripts, styles, images, iframes, XHR/fetch, or
  media — not for attacking third-party properties without permission.
---

# Mixed Content Hardening (HTTPS)

Assess and remediate **mixed content** on HTTPS pages: blocked/degraded
`http://` subresources, weak transport policy, third-party HTTP dependencies — authorized hardening only.

## Scope And Authorization

- **In scope:** apps/static sites/CDNs/edges you own or are written to test;
  staging/prod under engagement; labs and CTF web challenges.
- **Out of scope:** mass unauthorized crawling; coercing unrelated vendor HTTP;
  production DoS. Prefer inventory + DevTools + controlled `curl`. Redact
  cookies/tokens. No HSTS `preload` or live-asset removal without rollback.

## When To Use

- Browser mixed-content warnings/blocks on HTTPS pages.
- Review asks for **upgrade-insecure-requests**, HSTS, or full HTTPS migration.
- Third-party widgets, analytics, fonts, ads, or APIs still on `http://`.
- After `nginx-security-headers` when residual risk is **page-level HTTP
  subresources**, not TLS ciphers/`server_tokens` alone.

Do **not** use as primary for CSP bypass (`content-security-policy-bypass`), XSS
(`xss-cross-site-scripting`), cookie flags alone (`cookie-security-flags`), or
edge TLS laundry lists without mixed-content evidence (`nginx-security-headers`).

## Core Model

| Class | Examples | Typical modern browser |
| --- | --- | --- |
| **Active** | `script`, XHR/fetch, `ws:`, workers | **Blocked** on HTTPS documents |
| **Passive** | `img`, audio/video (limited) | Warning or restricted by policy |
| **Upgradable** | Same host with working HTTPS | Fix via `https://` or UIR |

**Good proof:** URL + request type + blocked/allowed + fix.  
**Bad proof:** “not fully HTTPS” with no subresource list.

## Workflow

### 1. Document context

Confirm HTTPS (or intended), redirects, `Secure` cookies. Capture HSTS, CSP /
CSP-Report-Only, reporting headers. Note browser version.

```bash
# Authorized host only
curl -sI https://app.example/
curl -sI http://app.example/   # expect redirect to HTTPS when required
```

### 2. Inventory insecure subresources

DevTools → Network (filter `http://`) plus source: HTML `src`/`href`/`action`/
`poster`/`data`; CSS `url()`/`@import`/fonts; JS dynamic scripts, fetch/XHR,
WebSockets; service-worker precaches; iframes and tag-manager embeds.

Classify each hit: **active/passive**, **first/third party**, same site vs vendor.

### 3. Active mixed content (priority)

Scripts, XHR/fetch to `http://`, `ws://`, insecure plugins — **high**: often
blocked (broken features) or dangerous if allowed. Prefer permanent `https://`
URLs, first-party CDN copies, or removal. Migrate `ws://` → `wss://`
(`websocket-security` when auth/origin matters).

### 4. Passive mixed content

HTTP images/media enable MITM of content and referrer leak. Prefer HTTPS or
same-origin static. No vendor HTTPS: replace, reverse-proxy via **allowlisted**
HTTPS origin only, or drop. Document temporary residuals; enable CSP reporting.

### 5. UIR, HSTS, CSP reporting

| Control | Role | Caveat |
| --- | --- | --- |
| CSP `upgrade-insecure-requests` | Rewrite `http://` subresources to `https://` | Fails if host has no HTTPS |
| HSTS | Force HTTPS **navigation** to host (± subdomains) | Does not rewrite third-party HTTP includes |
| CSP Report-Only / Reporting API | Discover residual mixed / failed upgrades | Collectors must be **owned** |

```http
Content-Security-Policy: upgrade-insecure-requests; default-src https: 'self'; object-src 'none'
Strict-Transport-Security: max-age=15552000; includeSubDomains
```

Emit HSTS only on successful HTTPS; raise `max-age` gradually;
`includeSubDomains`/`preload` only when org-ready. **UIR is a bridge**, not a
substitute for correct HTTPS URLs.

### 6. Third-party HTTP assets

Vendor table: domain, purpose, HTTPS status, owner. Prefer SRI for mirrored
scripts once on HTTPS. Retest after consent/tag-manager loads. Escalate vendors
with evidence; do not hammer unrelated sites.

### 7. Verify and remediate

1. Stage Report-Only CSP; sample and redact reports.
2. Recheck login/checkout/admin/home — Network clean of document `http://`/`ws://`.
3. Templates: no same-site `http://`; root-relative or `https://`.
4. Edge `:80` → HTTPS; optional CSP/HSTS (`nginx-security-headers`).
5. Trust `X-Forwarded-Proto` only from known LBs; CI checks for `http://` in
   templates. Pair changes with `code-quality-standards`.

## Routing

| Need | Skill |
| --- | --- |
| nginx/edge headers, TLS termination | `nginx-security-headers` |
| CSP bypass research | `content-security-policy-bypass` |
| XSS via injected script/URL | `xss-cross-site-scripting` |
| Cookie `Secure` / cleartext sessions | `cookie-security-flags` |
| WebSocket auth/origin | `websocket-security` |
| Safe config/template changes | `code-quality-standards` |
| Secrets during HTTPS migration | `secrets-management-hygiene` |

## Output Checklist

- [ ] Scope/authorization and browser(s)
- [ ] Document HTTPS + redirect/HSTS/CSP evidence
- [ ] Inventory: URL, type, active/passive, first/third party
- [ ] Block / allow / upgrade behavior observed
- [ ] Vendor status and owners; staged UIR / HSTS / reports
- [ ] Fixes or accepted residuals with risk notes
- [ ] Post-change verification; redaction of tokens/PII

## Rules

- Authorized hardening only; no mass unauthorized scans or vendor DoS.
- Fix **active** mixed content first; HSTS ≠ third-party inventory done;
  UIR ≠ broken vendor HTTPS fixed. Prefer URL + type + browser result over
  header checklists alone. Keep captures immutable; redacted ticket notes.
