---
name: vue-router-auth-guards
description: >
  Design Vue Router navigation guards and route meta for auth UX: requiresAuth,
  role/permission meta, guest-only routes, redirect loops, and token refresh on
  navigation. Use when building or reviewing Vue 3 router beforeEach/afterEach,
  meta.requiresAuth, login redirects, silent refresh on route change, or SPA
  route protection. Complements jwt-refresh-token-patterns; client guards are
  UX only—server remains authoritative.
---

# Vue Router Auth Guards

**Navigation guards** improve SPA UX (unauthenticated → login; privileged
screens off the default path). They are **not** access control—every API and
SSR handler must re-check authz. Prefer the repo’s router, auth store, and meta
conventions over ad-hoc per-page checks.

## When To Use

- Implementing or reviewing Vue Router **`beforeEach` / `beforeResolve` /
  `afterEach`**, per-route `beforeEnter`, or `onBeforeRouteUpdate`
- Defining **`meta.requiresAuth`**, `meta.roles` / `permissions`, `meta.guestOnly`
- Fixing **redirect loops** (login ↔ app), lost return path, or open-redirect via
  post-login `redirect` / `next` / `returnUrl`
- Wiring **token refresh / session restore** during navigation (boot, 401 recovery)
- Mentions: Vue Router guard, `requiresAuth`, navigation guard, route meta auth,
  silent refresh on route, SPA login redirect, Pinia auth + router

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Access/refresh JWT lifecycle, rotation, storage | `jwt-refresh-token-patterns` |
| JWT crypto, alg/kid, claim forgery assessment | `api-auth-and-jwt-abuse` |
| Session fixation / SID regenerate on login | `session-fixation-management` |
| Open redirect as a standalone vuln class | `open-redirect` |
| General reliability, typing, tests | `code-quality-standards` |

## Repo Config First

Repo router and auth modules **outrank** examples below.

1. **Router layout:** Vue Router 4 `createRouter`, route modules, lazy imports
2. **Auth SSOT:** Pinia/Vuex / `useAuth` / BFF cookie — one place for
   `isAuthenticated`, roles, tokens
3. **Meta schema:** existing keys + TypeScript `RouteMeta` augmentation
4. **Login/logout paths:** canonical names, query params, SSO callback ownership
5. **HTTP layer:** existing 401 refresh interceptors — avoid double-refresh races
6. **SSR/SSG:** Nuxt middleware; align SPA guards with server gates
7. **Neighbors:** copy 2–3 mature protected routes’ meta + layout patterns

**Precedence:** Follow repo security rules. Surface client-only “protection”
with no API authz, open `redirect` targets, or infinite login loops.

## Workflow

1. **Classify routes.** Public, guest-only, authenticated, role/permission-gated,
   SSO callback. Default unmarked routes to **public** unless product says otherwise.
2. **Define meta contract.** `requiresAuth`, `roles`/`permissions`, `guestOnly`.
   Augment `RouteMeta` so typos fail typecheck.
3. **Single global `beforeEach`.** Use `to.matched` meta (parent + child): gate if
   any record needs auth; if `guestOnly` and authed, send home. Prefer one
   orchestrator over divergent `beforeEnter`s.
4. **Auth readiness.** Cold start: await restore **once** via shared `auth.ready`
   so concurrent navigations do not double-refresh.
5. **Redirect without loops.** Unauthed → login with **safe** return path only
   (same-origin relative allowlist; reject `//evil`, absolute foreign URLs).
   Authed on guest-only → home. Never re-enter the same failing condition.
   Failed auth on login stays/errors—do not bounce login↔app.
6. **Token refresh on route.** Near-expiry access token: refresh **before**
   protected navigation; failure → clear session → login. Deduplicate in-flight
   refresh (one shared promise). Lifecycle details → `jwt-refresh-token-patterns`.
7. **Roles/permissions in meta.** UX prefilter only (menus, 403 page). Server
   enforces the same rules on every API.
8. **API still authoritative.** Direct URL, crafted history, disabled JS, or
   tampered storage must not grant data. 401/403 clears session consistently.
   Use `afterEach` for titles/analytics only—never sole security decision.
9. **Test.** Unauthed deep link; authed guest-only; refresh success/fail mid-nav;
   nested meta; malicious `?redirect=`; no loop; role mismatch → 403, no data leak.

## Design Notes

| Topic | Practice |
| --- | --- |
| Meta inheritance | `to.matched.some(r => r.meta.requiresAuth)`; child can tighten |
| Guard return API | Vue Router 4: return `true` / path / `{ name }` / `false` |
| Private UI flash | Gate layout on `auth.ready`; no secret props pre-bootstrap |
| 401 interceptor vs guard | One refresh owner; the other awaits the same promise |
| Logout | Clear store/tokens, server revoke, `router.push(login)` |

**Good — global guard sketch**

```ts
router.beforeEach(async (to) => {
  await auth.whenReady();
  const needsAuth = to.matched.some((r) => r.meta.requiresAuth);
  const guestOnly = to.matched.some((r) => r.meta.guestOnly);
  if (needsAuth && !auth.isAuthenticated) {
    if (!(await auth.refreshIfNeeded())) {
      return { name: "login", query: { redirect: safeReturnPath(to.fullPath) } };
    }
  }
  if (guestOnly && auth.isAuthenticated) return { name: "home" };
  if (needsAuth && !auth.hasMetaAccess(to.meta)) return { name: "forbidden" };
  return true;
});
```

**Bad:** trust `localStorage.isAdmin`; allow `redirect=https://evil.example`;
refresh every nav without dedupe; parent layout fetches private data before
meta gate; no API authz.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Vue Router guards, `meta.requiresAuth`, SPA login redirect UX | **This skill** | — |
| Refresh rotation, storage, reuse detection | `jwt-refresh-token-patterns` | this for navigate-time refresh |
| JWT/API auth testing or claim issues | `api-auth-and-jwt-abuse` | this for client routing only |
| Open redirect via return URL | `open-redirect` | this for guard query handling |
| Session fixation on login cookie | `session-fixation-management` | — |
| Implementation quality, tests | `code-quality-standards` | **always** on code changes |

Keep **this skill primary** for guard/meta design. Always apply
**`code-quality-standards`**. Hand token lifecycle to
**`jwt-refresh-token-patterns`**. Never treat client meta as server authz.

## Output Checklist

- [ ] Routes classified; meta keys typed and consistent with repo `RouteMeta`
- [ ] Single global guard (or documented exception); nested `matched` respected
- [ ] Bootstrap/`auth.ready` before decisions; no private UI flash
- [ ] Unauthed → login with **allowlisted** return path; guest-only → home if authed
- [ ] No login↔app redirect loop; failure paths do not re-enter the same trap
- [ ] Refresh on navigate deduped; failure clears session and routes to login
- [ ] Role/permission meta is UX-only; API/SSR enforce the same rules
- [ ] 401/403 handlers align with guard session clearing
- [ ] Tests: deep link, refresh fail, malicious redirect, role 403, cold start
- [ ] `code-quality-standards` applied; tokens redacted in logs
