---
name: pwa-security-checklist
description: >
  Authorized PWA security review: service worker scope, Cache API / precache
  poisoning, HTTPS-only installability, Web Push permissions, and offline auth
  tokens. Use when assessing service workers, Workbox caches, manifest install
  flows, push handlers, or offline session handling on apps you own or are
  scoped to test — not third-party PWAs without permission.
---

# PWA Security Checklist

Assess PWAs for **service worker trust boundaries**, **cache integrity**,
**HTTPS**, **push**, and **offline credentials**. Authorized assessment only.

## Scope And Authorization

- **In scope:** PWAs you own, org staging/prod under written engagement, labs,
  CTFs, and local builds with controlled test accounts.
- **Out of scope:** Unauthorized subscription hijack, mass push spam, or
  weaponizing service workers against third-party users outside test accounts.
- Prefer DevTools Application panel, local HTTPS/localhost, and staged SW
  versions over production force-update without a rollback path.
- Treat Cache Storage, IndexedDB, and push endpoints as sensitive — redact
  tokens, subscription keys, and device IDs (`secrets-management-hygiene`).
- Keep originals of manifests/SW scripts immutable; store redacted notes separately.

## When To Use

- App registers a **service worker**, uses Workbox, or claims installability
  via `manifest.webmanifest` / `display` modes.
- Review asks for SW **scope**, update strategy, or navigation preload risk.
- Suspect **cache poisoning** (user-controlled URL precached, opaque responses,
  untrusted CDN shells) or stale privileged assets after logout.
- HTTPS / mixed-content / insecure SW registration failures or HTTP installs.
- **Push** permission UX, VAPID keys, notification click handlers opening URLs.
- **Offline auth**: tokens in Cache Storage, IndexedDB, or SW-mediated fetches.
- Not primary for pure website XSS without SW impact → `xss-cross-site-scripting`.
- Not primary for edge TLS laundry lists alone → `nginx-security-headers` /
  `mixed-content-hardening`. Cookie flag-only issues → `cookie-security-flags`.

## Workflow

### 1. Inventory PWA surface

1. Record origin, HTTPS status, manifest URL, SW script URL, `scope`, `updateViaCache`.
2. List caches (`caches.keys()`), IndexedDB DBs, and auth storage (cookies, localStorage).
3. Note install criteria (manifest, icons, SW controlling clients) and browsers tested.

### 2. Service worker scope and control

| Check | Why it matters |
| --- | --- |
| SW path vs `scope` | `/sw.js` defaults to `/`; nested path limits control — over-broad scope expands blast radius |
| `Service-Worker-Allowed` header | Can widen scope beyond script path; treat as high-trust config |
| `clients.claim()` / `skipWaiting()` | Instant control of open tabs; pair with careful cache busting |
| Import scripts / remote modules | Supply-chain risk if SW loads unpinned third-party code |
| Registration only on trusted pages | Avoid injecting SW from XSS gadgets (`xss-cross-site-scripting`) |

Confirm only first-party, integrity-reviewed scripts register the worker. Reject
unexpected scopes on sibling paths (admin vs marketing).

### 3. Cache poisoning and offline shells

1. Map strategies: precache, runtime cache, stale-while-revalidate, network-first.
2. Flag caches of **authenticated** HTML/JSON or user-specific API responses under
   shared cache keys.
3. User- or query-influenced URLs must not enter precache without allowlists.
4. Prefer **opaque** third-party responses only when necessary; document MITM limits.
5. On logout: delete sensitive cache entries and broadcast client clear; do not leave
   private shells offline for the next browser user on a shared device.
6. Host/header cache confusion on CDN + SW dual cache → `host-header-cache-poison`
   / `http-host-header-attacks` when edge is involved.

### 4. HTTPS only and install trust

1. SW registration requires secure context (HTTPS or localhost) — document any HTTP
   training/staging exceptions.
2. Inventory mixed `http://` subresources and insecure APIs (`mixed-content-hardening`).
3. Manifest `start_url` / `scope` must stay same-origin and not open open-redirect chains.
4. Prefer HSTS on install origins after HTTPS is stable (`nginx-security-headers`).

### 5. Push permissions and handlers

1. Request notification permission only on **user gesture** with clear purpose.
2. Protect VAPID application keys; never ship private VAPID keys in the client.
3. Validate push payload integrity/auth at the server; treat payload as untrusted
   input into notification title/body/URL (XSS / open redirect).
4. `notificationclick` must not navigate to attacker-controlled URLs from forged payloads.
5. Unsubscribe and drop server-side endpoints on logout/account disable.

### 6. Offline auth tokens

1. Prefer short-lived access tokens; refresh with rotation and revocation.
2. Avoid long-lived bearer tokens in Cache Storage or world-readable IndexedDB without
   threat model notes; HttpOnly cookie sessions still need CSRF and Secure flags
   (`cookie-security-flags`, `api-auth-and-jwt-abuse`).
3. SW fetch handlers must not attach tokens to **cross-origin** or unexpected URLs.
4. Clear tokens and auth caches on logout; test multi-account and shared-device reuse.
5. Secrets lifecycle → `secrets-management-hygiene`.

### 7. Remediate and verify

1. Tighten scope; pin SW and precache hashes; version caches.
2. Add logout cache/token wipe; retest offline after sign-out.
3. Stage SW updates; confirm no sticky poisoned entries.
4. Pair code changes with `code-quality-standards`.

## Routing

| Need | Skill |
| --- | --- |
| PWA / service worker / push / offline token review | **This skill** |
| DOM XSS into pages that can register SW | `xss-cross-site-scripting` |
| Mixed content / HTTP subresources | `mixed-content-hardening` |
| Edge HSTS / TLS headers | `nginx-security-headers` |
| Cookie Secure/HttpOnly/SameSite | `cookie-security-flags` |
| JWT / API bearer misuse | `api-auth-and-jwt-abuse` |
| Host / web cache poison at CDN | `host-header-cache-poison`, `http-host-header-attacks` |
| Keys in client, VAPID private material | `secrets-management-hygiene` |
| Implementation fixes and tests | `code-quality-standards` |

## Output Checklist

- [ ] Scope/authorization, origin, browsers, SW URL and effective scope
- [ ] Manifest `start_url` / scope and install notes
- [ ] Cache inventory: names, strategies, auth-sensitive entries
- [ ] Poisoning / stale-after-logout findings with evidence
- [ ] HTTPS-only registration and mixed-content residuals
- [ ] Push permission UX, VAPID handling, click navigation safety
- [ ] Offline token storage location, lifetime, wipe-on-logout
- [ ] Remediation and retest notes; redaction of tokens/subscriptions

## Rules

- Authorized PWAs and test accounts only — no unsolicited push abuse.
- Raise severity only with a reachable abuse or data-leak path.
- XSS that installs a malicious SW is high impact; document SW privilege honestly.
- Prefer reproducible DevTools steps; redact tokens, subscriptions, and PII.
