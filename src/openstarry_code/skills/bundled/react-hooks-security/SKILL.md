---
name: react-hooks-security
description: >
  Harden React hooks against security pitfalls: dangerouslySetInnerHTML sinks,
  effect cleanup that leaks tokens/subscriptions, stale auth/closure state, and
  useMemo/useCallback values that land secrets in logs or client bundles.
  Use when reviewing or fixing React hooks (useEffect, useMemo, useState, custom
  use*) for XSS sinks, token lifetime, auth race, or secret leakage; keywords
  React hooks security, dangerous HTML, effect cleanup, stale auth.
---

# React Hooks Security

Security-focused review of **React hooks** as data and privilege carriers—not
component structure. Prefer repo sanitizers, auth providers, and secret policies.
Structure/composition → `react-component-patterns`. XSS methodology →
`xss-cross-site-scripting`. Always apply `code-quality-standards` on code changes.

## When To Use

- `dangerouslySetInnerHTML`, raw HTML in effects/refs, or URL/user content rendered
  through hooks without a typed sanitize boundary
- `useEffect` / `useLayoutEffect` holding tokens, refreshers, WebSockets, or
  timers without cleanup that clears secrets and aborts work
- Auth/session state in hooks that goes **stale** after logout, role change, or
  token refresh (closed-over user id, bearer, permissions)
- `useMemo` / `useCallback` / debug logs capturing tokens, PII, or session objects
- Custom `useAuth`, `useSession`, `useApi`, or data hooks that cache privileged
  responses across identity changes

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Props, composition, colocation, hooks *structure* | `react-component-patterns` |
| Authorized XSS mapping / general PoC | `xss-cross-site-scripting` |
| HTML sanitizer library + allowlist choice | `html-sanitizer-selection` |
| Client vs server state library choice | `state-management-guidelines` |
| Abort/stale-response concurrency design | `async-concurrency-patterns` |
| General reliability, errors, tests | `code-quality-standards` |

## Repo Config First

Repo auth, sanitizer, and React mode **outrank** defaults below.

1. **Auth stack:** existing `AuthProvider`, cookie vs Bearer, refresh flow, logout
2. **Sanitize path:** DOMPurify / shared `sanitizeHtml` — do not invent a second policy
3. **React mode:** Next RSC/`"use client"`, SPA, RN — secrets must not cross to client
4. **Lint:** `eslint-plugin-react-hooks`; do not disable exhaustive-deps for auth
5. **Logging:** redaction helpers, env gates for verbose debug
6. **Neighbors:** copy 2–3 mature feature hooks for token storage and cleanup

**Precedence:** Follow the repo. Surface client-bundled secrets, unsanitized HTML
sinks, and effects that keep tokens after unmount/logout.

## Workflow

1. **Inventory privileged hooks** — list `use*` that touch auth, HTML, tokens,
   storage, or privileged fetch. Note where identity lives (context, cookie, memory).

2. **Dangerous HTML sinks**
   - Flag `dangerouslySetInnerHTML`, `innerHTML` via ref, or third-party widgets fed
     from hook state/props derived from user or URL content.
   - Require: sanitize at boundary → typed fragment → single sink; or plain text only.
   - Prefer no HTML; if required, use repo sanitizer (`html-sanitizer-selection`).
   - Assessment depth / PoC → `xss-cross-site-scripting`.

3. **Effect cleanup and token lifetime**
   - Every effect that starts fetch, interval, WS, or holds a token must return
     cleanup: `abort`, `clearTimeout`/`clearInterval`, `close` socket, drop refs.
   - On unmount **and** logout: clear in-memory tokens from hook/module state;
     cancel in-flight work so responses cannot re-hydrate state after sign-out.
   - Do not leave bearer strings in closure-held variables, module caches, or
     `setTimeout` callbacks scheduled before logout.

4. **Stale auth state**
   - Closures must not keep pre-logout `userId` / roles for privileged calls.
   - Re-bind identity: put auth version/user id in deps, or read from a store that
     updates synchronously on logout; reset query caches and local `useState`.
   - After token refresh, avoid dual-token races (old refresh still writing session).
   - Treat “fetch completed after unmount/logout then `setState`” as a security
     bug when it re-applies another user’s data.

5. **useMemo / useCallback / logs and secrets**
   - Never memoize raw tokens, cookies, or full session objects “for convenience”
     if that value is logged, stringified into metrics, or passed to third-party SDK.
   - Ban `console.log` / analytics of hook return values that include secrets.
   - `useMemo` does not protect secrets—it retains them in memory longer; minimize
     privileged surface; prefer short-lived reads from secure storage/httpOnly cookie.
   - Client bundles: no API keys or privileged secrets in hook modules or env
     prefixes that ship to the browser.

6. **Verify**
   - Logout mid-flight: no privileged UI/data restore; network aborted or ignored.
   - Identity switch (user A → B) without full reload: no A data flash or A token use.
   - HTML fixtures: script/img handlers neutralized at hook-fed sinks.
   - Lint clean; tests for cleanup and auth reset (`code-quality-standards`).

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Hook security: HTML sinks, token cleanup, stale auth, secret memo/logs | **This skill** | — |
| Component structure, props, colocation, non-security hooks style | `react-component-patterns` | this when security risk found |
| Authorized XSS proof / sink methodology | `xss-cross-site-scripting` | this for React hook wiring |
| Sanitizer library/allowlist | `html-sanitizer-selection` | this for hook→sink placement |
| Abort, races, structured cancel | `async-concurrency-patterns` | this for auth/token effects |
| Implementation hygiene, errors, tests | `code-quality-standards` | **always** on code changes |

Keep **this skill primary** for hooks security pitfalls. Hand structure to
**`react-component-patterns`**. Hand general XSS assessment to
**`xss-cross-site-scripting`**. Always apply **`code-quality-standards`**.

## Output Checklist

- [ ] Privileged hooks inventoried (auth, HTML, tokens, storage, fetch)
- [ ] No unsanitized `dangerouslySetInnerHTML` / raw HTML from hook state
- [ ] Effects clean up: abort, timers, sockets; tokens cleared on unmount/logout
- [ ] No stale auth closures; identity switch and mid-flight logout verified
- [ ] No tokens/secrets in `useMemo`/`useCallback` surfaces that log or ship client-side
- [ ] Logs/metrics redacted; no privileged dump of hook returns
- [ ] Client/server boundary: no secrets in client hook modules
- [ ] Handoff: structure → `react-component-patterns`; XSS depth → `xss-cross-site-scripting`
- [ ] `code-quality-standards` + tests for cleanup and auth reset
- [ ] Repo auth/sanitizer/lint conventions followed

## Rules

- Hooks are privilege boundaries: treat return values and closures as sensitive.
- Cleanup is security control, not only a memory nicety.
- Sanitize or encode before any HTML sink; framework escape is not enough for raw HTML APIs.
- Stale auth after logout or user switch is a finding even without classic XSS.
- Authorized/owned apps and defensive review only; redact tokens in reports.
