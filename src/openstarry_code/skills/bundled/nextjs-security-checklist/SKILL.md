---
name: nextjs-security-checklist
description: >
  Next.js security checklist for org-owned apps: App Router / RSC data exposure,
  middleware authz, env public vs server split, Server Actions, headers, and
  route handlers. Use when Next.js security, RSC leak, middleware bypass,
  NEXT_PUBLIC secrets, Server Actions CSRF, or hardening Next.js deployments.
---

# Next.js Security Checklist

Harden **Next.js** (App Router and Pages) for systems you own or are authorized
to review. Focus on **server/client trust boundaries**, **middleware limits**,
**env exposure**, and **safe rendering** — not attacking third-party apps.

## Use When

- Reviewing App Router, RSC, Server Actions, or route handlers
- Auth lives in `middleware.ts` and may be incomplete or matcher-gapped
- Risk of leaking server-only data via RSC props, client bundles, or `NEXT_PUBLIC_*`
- Security headers, cookies, or CSRF for Server Actions / forms
- Mentions: Next.js security, RSC leak, middleware bypass, `NEXT_PUBLIC`, Server Actions

Do **not** use as primary for: secrets vault (`secrets-management-hygiene`),
schema design (`input-validation-patterns`), XSS encoding
(`output-encoding-patterns`), code baseline (`code-quality-standards`),
OAuth deep-dive (`oauth-oidc-misconfiguration`), nginx-only TLS
(`nginx-security-headers`).

## Repo Config First

Repo conventions **outrank** defaults below.

1. **Next version & router:** `package.json`, App vs Pages, `src/app`
2. **Config:** `next.config.js` / `.mjs` (headers, redirects, images)
3. **Auth stack:** Auth.js/Clerk/custom — extend; do not fork a second session model
4. **Env samples:** `.env.example`; public vs server naming already documented
5. **Middleware matchers** and edge runtime limits
6. **Hosting:** Vercel/Node/Docker — cookie `Secure` and URL assumptions
7. **Data layer:** Server Component fetch/ORM patterns in-repo

**Precedence:** Follow the repo. Flag secrets in `NEXT_PUBLIC_*`, middleware-only
authz, or disabled CSRF/origin checks.

## Workflow

1. **Inventory** — routes, Server Actions, middleware matchers, env keys, third-party scripts.
2. **Env boundary** — non-secrets only in `NEXT_PUBLIC_*`; server secrets only in
   server modules, Route Handlers, Server Actions — never Client Components.
3. **RSC serialization** — props to Client Components are browser-public; strip
   secrets, privileged flags, and full DB rows from the client graph.
4. **AuthZ** — verify session in Server Components, Route Handlers, and Actions;
   middleware is a coarse gate (matcher gaps), not sole authorization.
5. **Mutations** — keep CSRF/origin protections; re-check authz; validate input
   every Action (`input-validation-patterns`).
6. **Output** — encode untrusted HTML / use safe components
   (`output-encoding-patterns`); parameterize data access.
7. **Headers & cookies** — CSP, HSTS (HTTPS), nosniff, frame controls; session
   cookies `HttpOnly` + `Secure` + suitable `SameSite`; tight `images.remotePatterns`.
8. **Verify** — grep secret-shaped `NEXT_PUBLIC_`; dual-account authz tests;
   inspect client bundle; apply `code-quality-standards`.

## Good / Bad

**Good — server-only secret**

```ts
// app/api/billing/route.ts
import { stripeKey } from "@/lib/secrets"; // not NEXT_PUBLIC_
```

**Bad:** `NEXT_PUBLIC_STRIPE_SECRET_KEY=sk_live_…` (ships to the browser).

**Good — authz in the action**

```ts
"use server";
export async function deleteItem(id: string) {
  const session = await requireUser();
  await assertCanDelete(session, id);
}
```

**Bad:** middleware sets unverified `x-user-id`; Action trusts it for privilege.

**Good:** `z.object({ page: z.coerce.number().int().min(1).max(100) })` on searchParams.

**Bad:** raw `searchParams` into SQL/HTML or open redirects.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Next.js RSC, middleware, env, Actions | **This skill** | — |
| Implementation / tests | `code-quality-standards` | **always** on code changes |
| Body/searchParam allowlists | `input-validation-patterns` | this for Next placement |
| XSS / HTML encoding in UI | `output-encoding-patterns` | this for RSC/client boundary |
| API keys, session secrets, vault | `secrets-management-hygiene` | this for `NEXT_PUBLIC_*` split |

### Required helpers

- **`code-quality-standards`:** loaders, actions, fail-closed paths, tests.
- **`input-validation-patterns`:** schemas at Actions, handlers, forms.
- **`output-encoding-patterns`:** safe render of untrusted content.
- **`secrets-management-hygiene`:** lifecycle; this skill enforces public vs server keys.

## Checklist

- [ ] Router, `next.config`, auth, hosting inventoried
- [ ] No secrets in `NEXT_PUBLIC_*`, client components, or RSC client props
- [ ] Authz in Server Components/Actions/Handlers (not middleware alone)
- [ ] Middleware matchers cover sensitive paths; gaps documented
- [ ] Actions: authz + validation + CSRF/origin protections
- [ ] Inputs validated; outputs encoded (`input-validation-patterns` / `output-encoding-patterns`)
- [ ] Headers/cookie flags correct; image remote allowlist tight
- [ ] Client bundle checked; secrets hygiene + `code-quality-standards` applied
- [ ] Residual risks documented (third-party scripts, edge limits)

## Rules

- **Client boundary is public.** Middleware assists; **server handlers authorize.**
- Repo config first; fail closed on missing session/invalid input.
- Defense and **authorized** hardening only; redact tokens from reports.
---

# Note

Owns **Next.js security boundaries** (RSC, middleware, env, Actions). Pair with
`code-quality-standards`, `input-validation-patterns`, `output-encoding-patterns`,
and `secrets-management-hygiene`.
