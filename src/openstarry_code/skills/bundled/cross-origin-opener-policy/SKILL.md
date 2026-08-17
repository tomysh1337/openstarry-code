---
name: cross-origin-opener-policy
description: >
  Assess and implement Cross-Origin-Opener-Policy (COOP) for browsing-context
  isolation: same-origin, same-origin-allow-popups, unsafe-none, pairing with
  COEP for crossOriginIsolated / SharedArrayBuffer, and popup/OAuth breakage.
  Use when hardening window.opener isolation, reverse-tabnabbing residual risk,
  Spectre-era cross-origin isolation, missing COOP on auth shells, or verifying
  COOP+COEP delivery on owned apps and authorized assessments — hand framing
  controls to clickjacking-frame-busting, credentialed CORS to
  cors-credentialed-requests, and edge header lists to nginx-security-headers.
---

# Cross-Origin-Opener-Policy (COOP)

Use **Cross-Origin-Opener-Policy** so documents get a dedicated top-level
browsing context group, cutting cross-origin `window.opener` / `window.open`
access and enabling **cross-origin isolation** when paired with COEP. Own COOP
value choice, delivery consistency, popup compatibility, and isolation proofs.
Not a substitute for CSP framing or CORS.

## When To Use

- Missing, weak (`unsafe-none`), or path-inconsistent `Cross-Origin-Opener-Policy`.
- Enabling `crossOriginIsolated`, `SharedArrayBuffer`, high-res timers (needs
  COOP + COEP in supporting browsers).
- Reverse tabnabbing / hostile `window.opener` after OAuth or help-center popups
  (COOP complements `rel=noopener` / `noopener` features).
- Auth, account, or payment HTML shells sharing a context group with untrusted
  openers or opened cross-origin pages.
- Popups, SSO, payment widgets, or `postMessage` partners break after COOP rollout.
- Keywords: COOP, COEP, COOP+COEP, `same-origin-allow-popups`, browsing context
  group, `crossOriginIsolated`, reverse tabnabbing, opener nullification.

Do **not** use as primary for iframe embedding (`clickjacking-frame-busting`),
CORS theft (`cors-credentialed-requests`), CSP script policy
(`content-security-policy-bypass` / `csp-report-only-rollout`), or edge header
dumps alone (`nginx-security-headers`).

## Scope And Authorization

- **In scope:** owned web apps, staging/prod under engagement, labs/CTFs where
  header and popup behavior may be changed or measured.
- **Out of scope:** drive-by isolation of third-party sites; breaking real-user
  OAuth/payment without approval; claiming Spectre immunity from COOP alone.
- Prefer test accounts and controlled popup pairs. Redact cookies, tokens, PII.
- Keep original headers and isolation checks under derived paths. Evidence over
  header presence alone.

## Workflow

### 1. Map COOP values and effects

| Value | Effect (summary) | Typical use |
| --- | --- | --- |
| `unsafe-none` (default) | May share context group; opener preserved | Legacy / max compatibility |
| `same-origin` | Isolate unless other side matches origin **and** COOP | Sensitive apps; isolation |
| `same-origin-allow-popups` | Isolate self; friendlier popup UX | OAuth/payment popups |

COOP is a **document response header**. Cross-origin openers lose script access;
`window.opener` often becomes `null`. Isolation is per browsing context group —
not a framing ban (XFO / `frame-ancestors`).

### 2. Inventory documents and opener graph

1. List top-level HTML/SPA shells: login, session, settings, checkout, admin,
   OAuth callback, and any page that may be `window.open`’d or open others.
2. Map intentional popups: who opens whom, origins, `postMessage` contracts,
   return-to-opener assumptions (`opener.location`, `opener.postMessage`).
3. Capture COOP (and COEP/CORP if present) on critical document paths: CDN vs
   origin, 3xx landings, error documents.

### 3. Choose policy for product needs

1. **Default harden:** `Cross-Origin-Opener-Policy: same-origin` on sensitive
   first-party documents when no cross-origin popup partnership is required.
2. **Popup-heavy SSO/pay:** try `same-origin-allow-popups` on the opener; force
   partners to use `postMessage` + explicit `targetOrigin`.
3. **Isolation APIs:** need COOP `same-origin` **and** COEP (`require-corp` or
   `credentialless`) so `self.crossOriginIsolated === true`. Plan CORP/CORS on
   subresources. COOP on JSON-only APIs does not protect navigable HTML shells.

```http
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
```

### 4. Authorized verification

| Check | How | Pass signal |
| --- | --- | --- |
| Header on UI document | DevTools / proxy on final HTML | Expected COOP value |
| Opener cut | Cross-origin `window.open(app)`; read opener | No script access / null as designed |
| Popup UX | OAuth/pay under test accounts | Completes via postMessage/redirect |
| Isolation | `self.crossOriginIsolated` when required | `true` only if COOP+COEP OK |
| Consistency | www vs apex, mobile host, CDN | No silent `unsafe-none` gaps |

Use an **approved** opener origin. Record browser + version.

### 5. Breakage triage, remediate, retest

1. Broken SSO: prefer redirect or `postMessage`; trial `same-origin-allow-popups`
   on opener — do not drop COOP site-wide without a risk note.
2. Do not leave auth shells at `unsafe-none` solely for analytics popups.
3. Keep `rel="noopener noreferrer"` on untrusted outbound links; COOP is not
   clickjacking control → `clickjacking-frame-busting`.
4. Edge delivery → `nginx-security-headers`; code/config → `code-quality-standards`.
5. Ship COOP on all sensitive document routes; add COEP+CORP only when isolation
   APIs demand it. Retest popups, opener cut, and `crossOriginIsolated`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| COOP values, opener isolation, COOP+COEP | **This skill** | — |
| Iframe / XFO / frame-ancestors | `clickjacking-frame-busting` | this if opener vs embed confused |
| Credentialed CORS / ACAO | `cors-credentialed-requests` | not a COOP substitute |
| CSP RO / script-src rollout | `csp-report-only-rollout` | this for isolation headers only |
| Edge/nginx security header bundle | `nginx-security-headers` | this for COOP semantics |
| postMessage / XSS via opener pages | `xss-cross-site-scripting` | this for context-group cut |
| Cookie flags (SameSite etc.) | `cookie-security-flags` | layered session hardening |
| Implementing headers/tests | `code-quality-standards` | **always** on code |

**This skill** owns COOP semantics, popup compatibility, and COOP+COEP isolation
proofs. Hand framing to `clickjacking-frame-busting` and CORS to
`cors-credentialed-requests`.

## Output Checklist

- [ ] Scope/authorization; hosts/paths and test browsers recorded
- [ ] Opener/popup graph (who opens whom; origins; postMessage needs)
- [ ] COOP values quoted on critical **documents** (gaps/host variants)
- [ ] Chosen policy: `same-origin` vs `same-origin-allow-popups` + rationale
- [ ] If isolation APIs: COEP (+ CORP/CORS) plan; `crossOriginIsolated` evidence
- [ ] Authorized opener/popup tests: access cut vs UX still works
- [ ] Breakage list (SSO/pay/widgets) and mitigations; residual weaker COOP
- [ ] Layering: noopener links; framing skill if embed risk; no Spectre overclaim
- [ ] Remediation + retest; CQS if code/config changed; PII redacted
