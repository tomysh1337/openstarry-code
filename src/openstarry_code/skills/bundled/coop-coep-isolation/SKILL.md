---
name: coop-coep-isolation
description: >
  Design, audit, and remediate Cross-Origin-Opener-Policy (COOP) and
  Cross-Origin-Embedder-Policy (COEP) for browser cross-origin isolation
  (crossOriginIsolated, SharedArrayBuffer, Spectre mitigations). Use when
  enabling or debugging COOP/COEP/CORP, SAB availability, opener nulling,
  require-corp vs credentialless, or process isolation on owned apps and
  authorized header reviews.
---

# COOP / COEP Cross-Origin Isolation

Ship and verify **cross-origin isolation**: COOP severs opener/window
relationships; COEP (with CORP or CORS) blocks unopted-in cross-origin
subresources. Together they set `crossOriginIsolated === true` and unlock
SAB / precise timers. Owns **response isolation headers and embed graph**.
Framing → clickjack skills; Sec-Fetch → `fetch-metadata-sec-headers`.

## When To Use

- Enabling SharedArrayBuffer, high-res timers, or WASM threads needing
  `crossOriginIsolated`.
- Auditing COOP, COEP, and companion CORP on documents and assets.
- Debugging broken embeds, popups, OAuth windows, or CDNs after COEP
  (`net::ERR_BLOCKED_BY_RESPONSE`, CORP/CORS failures).
- Hardening against XS-Leaks / Spectre-class channels via context-group
  separation (`same-origin` COOP).
- Keywords: COOP, COEP, CORP, `require-corp`, `credentialless`,
  `same-origin-allow-popups`, `crossOriginIsolated`, SAB.

**Not primary:** CSP → `content-security-policy-bypass` /
`csp-report-only-rollout`; framing → `clickjacking-frame-busting`;
credentialed CORS → `cors-credentialed-requests`; Sec-Fetch →
`fetch-metadata-sec-headers`.

## Workflow

### 1. Clarify isolation goal

| Goal | Typical header set |
| --- | --- |
| Full isolation + SAB | Doc: `COOP: same-origin` + `COEP: require-corp` (or `credentialless`); assets: CORP or CORS |
| Opener cut only (no SAB) | `COOP: same-origin` or `same-origin-allow-popups`; COEP optional |
| Popup-friendly opener cut | `COOP: same-origin-allow-popups` (weaker isolation) |
| Soft rollout | Stage paths; fix COEP breakages before enforce |

### 2. Inventory document and embed graph

1. Top-level documents that must isolate (app shell, admin, WASM).
2. Every subresource: scripts, styles, images, fonts, media, workers, iframes,
   fetch/XHR, modules, third-party widgets.
3. Per host: same-origin / same-site / CDN; existing ACAO and CORP.
4. Map `window.open` / OAuth / payment popups that need opener or postMessage.

### 3. Header semantics

| Header | Common values | Effect |
| --- | --- | --- |
| COOP | `unsafe-none`, `same-origin`, `same-origin-allow-popups` | Browsing context group; severs cross-origin opener |
| COEP | `unsafe-none`, `require-corp`, `credentialless` | Embeds must opt in (CORP/CORS) or load credentialless |
| CORP | `same-origin`, `same-site`, `cross-origin` | Who may load this resource under COEP |

**Isolation (Chromium-class):** COOP `same-origin` **and** COEP
`require-corp` or `credentialless` for `crossOriginIsolated === true`.
Measure in a real browser; headers alone are insufficient.

### 4. CORP / CORS under `require-corp`

1. Same-origin assets: CORP optional; `same-origin` is fine.
2. Cross-origin without CORS: send `CORP: cross-origin` (or tighter if only
   same-site consumers).
3. Cross-origin with CORS: ACAO must allow the document origin →
   `cors-credentialed-requests` if embeds need cookies.
4. Prefer **`credentialless` COEP** when partners cannot set CORP and anonymous
   loads are acceptable.
5. Workers and nested iframes need compatible COEP/COOP when they stay isolated
   or load further embeds.

### 5. Opener, popups, postMessage

1. `COOP: same-origin` nulls cross-origin opener handles; redesign OAuth via
   `postMessage` + origin checks → `postmessage-security` if listeners weak.
2. `same-origin-allow-popups` keeps some popup links; note residual XS-Leak
   risk if SAB is not required. COOP is not a CSRF substitute.

### 6. Authorized verification

```text
1. Isolated doc → crossOriginIsolated === true (if claimed)
2. SharedArrayBuffer / atomics path matches product need
3. Omit CORP on a test asset → expect COEP block
4. Cross-origin window.open → opener null/closed as designed
5. OAuth/popup path still works under chosen COOP
6. CDN: headers on HTML and on static hosts serving embeds
```

Record URL, full headers, browser/version. Edge plumbing →
`nginx-security-headers`. Set COOP/COEP on the **document that needs
isolation**, not only APIs. Fix embed graph before enforce; stage
`credentialless` if partners lag. Retest flag, widgets, popup auth. Code →
`code-quality-standards`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| COOP/COEP/CORP, SAB, crossOriginIsolated | **This skill** | — |
| Edge header inventory (nginx) | `nginx-security-headers` | this for isolation semantics |
| CORS credentialed / ACAO | `cors-credentialed-requests` | this if COEP forces CORP/CORS |
| postMessage after opener cut | `postmessage-security` | this for COOP choice |
| Framing / frame-ancestors | `clickjacking-frame-busting` | not a COEP substitute |
| Sec-Fetch request isolation | `fetch-metadata-sec-headers` | complementary |
| CSP script / report-only | CSP skills | orthogonal |
| Middleware / tests | `code-quality-standards` | **always** on code |

## Output Checklist

- [ ] Scope/authorization; browser/versions
- [ ] Goal: SAB vs opener-only vs staged
- [ ] Document COOP + COEP values; `crossOriginIsolated` result
- [ ] Embed inventory: CORP and/or CORS per critical asset
- [ ] Workers/iframes checked if applicable
- [ ] Popup/OAuth/opener behavior under chosen COOP
- [ ] Evidence: block without CORP; allow with CORP/CORS/credentialless
- [ ] Edge/CDN consistency (HTML vs static origin)
- [ ] Residual risk if `allow-popups` or missing COEP
- [ ] Handoffs (CORS, postMessage, nginx, CQS); redacted evidence; retest

## Scope And Authorization

- **In scope:** Owned apps, labs, CTFs, written header/isolation reviews;
  self-account popup and embed tests; staging COEP break/fix cycles.
- **Out of scope:** Forcing isolation on third-party sites without permission;
  drive-by Spectre research on real users; claiming SAB without measuring
  `crossOriginIsolated` in a supporting browser.
- Prefer non-destructive checks (flags, console, blocked resources). Do not
  exfiltrate production PII. Headers differ by path/CDN/status — record
  **effective** responses. Redact cookies, tokens, and PII from reports.
