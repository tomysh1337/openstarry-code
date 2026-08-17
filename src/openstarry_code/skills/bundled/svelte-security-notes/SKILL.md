---
name: svelte-security-notes
description: >
  Brief Svelte/SvelteKit security notes: {@html} sinks, CSP, SSR XSS, client
  store secret hygiene, and hooks.server auth patterns. Use when reviewing or
  hardening SvelteKit apps, {@html} rich text, handle/hooks session guards,
  PUBLIC_ env leakage, or Svelte SSR markup escaping — authorized/owned only.
---

# Svelte Security Notes

Defensive notes for **Svelte / SvelteKit** you own or may harden. Default
interpolation is safe; risk concentrates on **`{@html}`**, **SSR-injected
markup**, **client-visible secrets**, and **auth only in the UI**.

## When To Use

- Reviewing Svelte/SvelteKit for XSS, CSP, or session/auth wiring
- `{@html ...}` or custom elements rendering untrusted markup
- SSR/hydration paths that inject HTML, attributes, or JSON into documents
- Secrets or tokens in writable stores, `$page.data`, or non-`PRIVATE_` env
- `hooks.server.ts` / `handle` / `locals` auth and route protection patterns
- Mentions: SvelteKit security, `{@html}`, CSP nonces, `hooks.server`, `app.d.ts` locals

Do **not** use as primary for general XSS methodology (`xss-cross-site-scripting`),
sanitizer library choice (`html-sanitizer-selection`), JWT crypto abuse
(`api-auth-and-jwt-abuse`), or generic code quality (`code-quality-standards`).

## Repo Config First

Repo conventions **outrank** samples below.

1. SvelteKit version; adapter (`adapter-node`, Vercel, Cloudflare, static)
2. Auth stack: cookies/session, Lucia, Auth.js, custom JWT, external IdP
3. `hooks.server.ts` / `hooks.client.ts`; `src/app.d.ts` `Locals` / `PageData`
4. Env: `PRIVATE_*` vs `PUBLIC_*`; `$env/static/private` vs dynamic public
5. CSP: `kit.csp` in `svelte.config.js`, headers in `handle`, or edge config
6. Existing `{@html}` call sites and sanitizer (DOMPurify / isomorphic)
7. Form actions, `+server.ts` endpoints, and `depends` / invalidation patterns
8. Cookie flags: `httpOnly`, `secure`, `sameSite`, path, multi-domain

**Precedence:** Follow existing `handle` and layout `load` guards. Flag
`{@html}` on user content, secrets in `PUBLIC_` env, or auth checks only in
client components.

## Workflow

1. **Map trust boundaries** — browser vs server `load` / actions / `+server`;
   what reaches `data`, stores, and HTML. Prefer server-only for secrets and
   authorization decisions.
2. **Escaping vs `{@html}`** — `{value}` / attributes auto-escape in Svelte.
   Treat `{@html html}` as an intentional raw sink: allow only after server-side
   sanitize (`html-sanitizer-selection`); never pipe request/DB strings straight
   in. Prefer plain text or structured components over rich HTML.
3. **SSR XSS** — untrusted data in SSR HTML, `<script>` JSON blobs, `style`,
   event-handler attrs, or `srcdoc` bypasses “client-only” assumptions. Sanitize
   or encode **before** first paint; re-check hydrated markup matches policy.
4. **CSP** — prefer nonces/hashes via SvelteKit `csp` / response headers; tight
   `script-src` / `object-src` / `base-uri`; avoid `unsafe-inline` without nonce.
   CSP is defense-in-depth, not a substitute for removing `{@html}` abuse.
   Bypass research → `content-security-policy-bypass`.
5. **Store / env secrets** — never put API keys, session tokens, or service
   credentials in writable stores, `localStorage`, or non-httpOnly cookies.
   Use `PRIVATE_` + `$env/static/private` (or dynamic private) on the server only;
   `PUBLIC_` is always client-visible. Strip secrets from `PageData` / `serialize`.
6. **`hooks.server` auth** — centralize session resolve in `handle`; set
   `event.locals.user` (typed in `app.d.ts`); protect with server `load`, layout
   guards, and `+server`/actions — not `if (!user) goto` alone. Prefer httpOnly
   session cookies; regenerate on login; validate origin/CSRF for cookie mutations.
7. **Verify** — guest vs auth routes (401/302/403); `{@html}` fixtures; CSP
   report-only then enforce; confirm no secrets in client bundles or HTML.

**Good:** server sanitize → trusted fragment → `{@html safe}`; session in
httpOnly cookie; `locals.user` set in `handle`; private env only in server modules.

**Bad:** `{@html comment.body}` raw; `PUBLIC_API_SECRET`; JWT in `localStorage`
or a store synced to it; auth only inside a client `+page.svelte`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| SvelteKit `{@html}`, CSP, SSR XSS, stores, `hooks.server` | **This skill** | — |
| Full XSS mapping / PoC methodology | `xss-cross-site-scripting` | this for Svelte sinks |
| Sanitizer library + allowlist policy | `html-sanitizer-selection` | this for `{@html}` wiring |
| CSP bypass research | `content-security-policy-bypass` | this for Kit CSP placement |
| Cookie CSRF / session fixation | `csrf-cross-site-request-forgery`, `session-fixation-management` | this for Kit cookies |
| JWT/Bearer crypto and claims abuse | `api-auth-and-jwt-abuse` | this for Kit placement |
| Secret storage/rotation process | `secrets-management-hygiene` | this for `PUBLIC_`/`PRIVATE_` |
| Implementation quality and tests | `code-quality-standards` | **always** on code changes |

Keep **this skill primary** for Svelte/SvelteKit wiring. Always apply
**`code-quality-standards`** when changing app code.

## Output Checklist

- [ ] Trust map: server vs client data, loads, actions, endpoints
- [ ] All `{@html}` sites inventoried; untrusted HTML sanitized server-side
- [ ] No raw user/DB HTML into SSR attributes, JSON script tags, or `srcdoc`
- [ ] CSP configured (nonce/hash preferred); residual `unsafe-*` justified
- [ ] No secrets in stores, `localStorage`, client bundles, or `PUBLIC_*` env
- [ ] Session via httpOnly cookie (or reviewed equivalent); flags match deploy
- [ ] `hooks.server` sets `locals`; server guards on sensitive routes/actions
- [ ] Client-only redirects not sole auth control
- [ ] Fixtures: XSS payloads on `{@html}`, guest access, missing session
- [ ] Handoffs: XSS / sanitizer / CSP / CSRF / secrets skills as needed
- [ ] Authorized/owned scope; tokens and cookies redacted from reports
- [ ] `code-quality-standards` applied on code changes

## Rules

- `{value}` is not `{@html value}` — raw HTML is always explicit and reviewed.
- Authorization and secrets stay on the server; UI checks are UX only.
- `PUBLIC_` means public. Prefer private env + server modules for credentials.
- CSP complements sanitization and escaping; it does not replace them.
- Authorized hardening and assessment only; redact session material from notes.
