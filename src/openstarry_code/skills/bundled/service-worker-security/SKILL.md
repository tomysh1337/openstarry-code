---
name: service-worker-security
description: >
  Service Worker security: scope, registration source, fetch hijacking, cache
  isolation, updates, push/notifications, and CSP interaction. Use when adding
  or reviewing service workers, Workbox, PWA offline shells, or SW fetch
  interception. Authorized hardening/review only — not third-party SW abuse.
---

# Service Worker Security

Engineering and **authorized** review for **Service Workers (SW)**: scope,
registration trust, `fetch`/cache risk, updates, and push. Prefer the repo’s
existing PWA/Workbox setup over a second uncontrolled `register` call.

## Use When

- Adding, changing, or reviewing `service-worker.js` / Workbox / PWA offline
- Debugging hijacked `fetch`, stale shells, or cross-user cache surprises
- Assessing registration URL, scope, update behavior, or push handlers
- Relating SW to CSP, XSS persistence, or mixed-content interception
- Mentions: service worker security, SW scope, Cache Storage, skipWaiting,
  clients.claim, push SW, Workbox hardening

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| XSS sink discovery | `xss-cross-site-scripting` |
| CSP parse / bypass research | `content-security-policy-bypass` |
| WebSocket client lifecycle | `websocket-client-patterns` |
| Authorized WS Origin/CSWSH testing | `websocket-security` |
| Implementation reliability baseline | `code-quality-standards` |

## Repo Config First

Hosting and PWA config **outrank** defaults below.

1. **Registration:** call site, `scope`, which HTML entrypoints load it
2. **Build:** Workbox mode, hashed precache manifest, SW asset path
3. **Headers:** `Service-Worker-Allowed`, CSP, `Clear-Site-Data`, SW `Cache-Control`
4. **Caches:** precache vs runtime names; deploy purge strategy
5. **Push:** VAPID keys, permission UX, server endpoints
6. **Auth:** cookie vs bearer; whether SW sets credentials on fetch
7. **Neighbors:** match existing offline allowlists before widening intercept

**Precedence:** Surface untrusted registration URLs, over-broad scope, or caching
personalized API bodies under shared keys.

## Workflow

1. **Trust map:** SW script origin (HTTPS/localhost same-origin); max scope;
   paths visible to SW; any `Service-Worker-Allowed` expansion.
2. **Registration:** first-party pages only; fixed `sw.js` path (not user input);
   narrowest scope that still serves the PWA.
3. **`fetch` audit:** allowlist offline routes; **network-only** for sensitive/auth
   APIs; never rewrite security-critical responses from untrusted cache.
4. **Cache Storage:** versioned names; delete old on activate; no tokens or full
   account HTML in shared caches; bound runtime cardinality.
5. **Updates:** `skipWaiting` + `clients.claim` blast radius; SW script `no-cache`;
   unregister / `Clear-Site-Data` kill-switch.
6. **Push/sync:** least data in notification bodies; validate push source/payload.
7. **CSP/XSS:** SW does not replace CSP; XSS that registers SW is high impact;
   align `worker-src` / `script-src` / `connect-src`.
8. **Test:** register, update, offline miss, API not cache-first, unregister.

## Threat Themes

| Theme | Risk | Mitigation sketch |
| --- | --- | --- |
| Malicious registration | Persistent same-origin MitM | XSS hygiene; fixed first-party SW URL |
| Over-broad scope | Intercepts extra paths | Narrow scope; justify header expansion |
| Cache poisoning | Hostile/stale shell or API replay | Network-first auth APIs; version precache |
| Sticky insecure SW | Bug remains after “fix” | Short cache on SW file; kill-switch |
| Push abuse | Phishing notifications | Permission UX; payload checks; revoke |

## Good / Bad Examples

**Good — narrow register + updatable SW script**

```js
await navigator.serviceWorker.register("/app/sw.js", { scope: "/app/" });
// SW response: Cache-Control: no-cache
```

**Bad:** `register(userControlledUrl)`; scope `/` when only `/docs/` needs offline;
year-long immutable cache on `sw.js` without fingerprint.

**Good — network for APIs**

```js
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(fetch(event.request));
    return;
  }
  if (event.request.mode === "navigate") {
    event.respondWith(networkFirstShell(event.request));
  }
});
```

**Bad:** cache-first for `/api/me` or credentialed responses in a shared cache;
never delete old caches; claim every deploy with no unregister runbook.

## Anti-Patterns

- SW from third-party or XSS-injected markup (persistence)
- Using SW to “bypass” CSP by design (fix CSP/XSS instead)
- Caching authenticated APIs without isolation; default cache-first for all paths
- Mutable CDN `importScripts` without pin/review; logging URLs that contain tokens

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| SW scope, registration, fetch/cache/push | **This skill** | — |
| CSP `worker-src` / `script-src` / `connect-src` | `content-security-policy-bypass` | this for SW under policy |
| XSS → install/poison SW | `xss-cross-site-scripting` | this for persistence impact |
| WebSocket client design | `websocket-client-patterns` | this if SW hosts related assets |
| Authorized WS security testing | `websocket-security` | this only if SW touches WS assets |
| Production quality of SW code | `code-quality-standards` | **always** on implementation |

Keep **this skill primary** for SW security. Always apply
**`code-quality-standards`**. Use **`content-security-policy-bypass`** for CSP
posture of workers/scripts/connect. Use **`websocket-security`** /
**`websocket-client-patterns`** for realtime endpoints and clients, not SW scope.

## Checklist

- [ ] Registration fixed, first-party, HTTPS; scope minimized
- [ ] SW script headers allow updates; kill-switch documented
- [ ] `fetch`: network for auth APIs; safe offline for static only
- [ ] Caches versioned/cleaned; no secrets in caches/notifications
- [ ] `skipWaiting` / `clients.claim` understood; push payloads validated
- [ ] Supply chain (`importScripts`/bundle) reviewed
- [ ] CSP aligned (`content-security-policy-bypass`); XSS persistence considered
- [ ] Tests: offline shell, no cross-user API cache, update, unregister
- [ ] `code-quality-standards` applied; realtime → `websocket-client-patterns` / `websocket-security`
