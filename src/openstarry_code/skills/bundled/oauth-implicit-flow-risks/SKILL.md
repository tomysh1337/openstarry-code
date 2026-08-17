---
name: oauth-implicit-flow-risks
description: >-
  Authorized assessment of OAuth 2.0 / OIDC implicit and hybrid token-in-browser
  flows: response_type=token/id_token leakage, fragment handling, migration to
  authorization code + PKCE. Use when SPA or legacy SSO still issues access or
  ID tokens at the authorize redirect without a token endpoint exchange.
---

# OAuth Implicit Flow Risks And Migration

Focused skill for **implicit** (`response_type=token`, `id_token`, or
`id_token token`) and related browser-delivered token patterns. Broad OAuth
redirect/state → `oauth-oidc-misconfiguration`; PKCE → `oauth-pkce-checklist`.

## When To Use

| Situation | Direction |
| --- | --- |
| Authorize response returns tokens in **fragment** or query (no `code` exchange) | **This skill** (primary) |
| `response_type` includes `token` and/or bare `id_token` | **This skill** |
| Legacy SPA / hash routing with tokens in the URL | **This skill** |
| Migration design: implicit → auth code + PKCE | **This skill** + `oauth-pkce-checklist` |
| Full `redirect_uri` / `state` / mix-up program | `oauth-oidc-misconfiguration` |
| Only PKCE challenge/verifier bugs on code flow | `oauth-pkce-checklist` |

Keywords: implicit grant, `response_type=token`, fragment leak, hybrid,
OAuth Security BCP, migrate to PKCE.

## Scope And Authorization

- Authorized apps and **in-scope** authorization servers only. Do not attack
  third-party production IdPs unless the program **names** them; prefer the
  **client’s** configuration and any AS you own.
- Use test users/clients **you control**. Do not harvest real-user tokens.
- Treat access tokens and `id_token` values as credentials: redact, store
  offline, rotate after demos.
- Assessment and hardening only—not mass token interception.
- Pair remediation with `code-quality-standards`.

## Workflow

### 1. Confirm grant and delivery mode

From authorize redirects, client config, and OIDC discovery:

| Field | Capture |
| --- | --- |
| `response_type` | `token`, `id_token`, `id_token token`, hybrid variants |
| Delivery | fragment (`#`), query (`?`), `form_post` |
| Client type | public SPA/native vs confidential |
| Storage | memory, `sessionStorage`, `localStorage`, cookies |

Baseline: one honest login; record redirect shape (redact secrets) and where JS
reads tokens. If refresh appears, pure implicit is unlikely—document the real grant.

### 2. Risk model (why implicit is legacy)

Implicit let browser apps obtain tokens **without** a client secret. Modern BCP:
public clients use **authorization code + PKCE** so tokens are not front-channel
only and codes bind to a verifier.

| Risk | Mechanism | Typical impact |
| --- | --- | --- |
| Token in URL | Fragment/query to scripts, extensions, history | Session / API theft |
| Referer / analytics | Query mode or captured full URLs | Token exfil |
| XSS | Script on redirect origin reads `location.hash` | Account compromise |
| postMessage bridge | `*` targetOrigin / weak origin check | Cross-origin theft |
| Logs / shared devices | Proxy logs, browser history | Token replay |
| Weak binding | Missing `state` / OIDC `nonce` | Login CSRF, injection |

### 3. Detection and evidence probes

For each in-scope `client_id`:

1. **Enumerate types** the AS accepts: `token`, `id_token`, `id_token token`
   vs `code` / `code id_token`.
2. **Fragment vs query:** query usually worse (Referer, logs); fragment still
   fails against XSS and hostile JS.
3. **Leak surfaces (lab, your account):** third-party assets on callback
   (Referer), history after login, analytics beacons, insecure storage.
4. **OIDC `id_token`:** client must check `nonce`, `iss`, `aud`, signature,
   `exp`. Failures → `oauth-oidc-misconfiguration` / `api-auth-and-jwt-abuse`.
5. **Silent renew / iframe:** same leak class if renew still uses implicit.

**High severity:** production SPA still allowed `response_type=token` **and**
tokens are usable on APIs (especially long TTL / broad scopes).

### 4. Controls that still apply

Migrating off implicit does not skip exact-match `redirect_uri`, session-bound
`state`, OIDC `nonce` when ID tokens issue, short TTLs, one-time codes, or
HTTPS callbacks. Full redirect/state/mix-up → `oauth-oidc-misconfiguration`.

### 5. Migration path

| Step | Action |
| --- | --- |
| 1 | Disable `token` / bare `id_token` response types for the client at AS |
| 2 | Implement **PKCE S256** for public clients (`oauth-pkce-checklist`) |
| 3 | Exchange `code` at token endpoint; prefer **BFF** so tokens stay server-side |
| 4 | If browser must hold AT: memory-only, short TTL, tight audience/scope |
| 5 | Replace silent implicit iframe with server-side refresh or re-auth + PKCE |
| 6 | Remove SDK flags (`responseType: 'token'`, implicit); add regression tests |

Remediation summary: AS disallows front-channel tokens for public clients;
client stops reading `location.hash`/query tokens; BFF holds session cookies
(Secure, HttpOnly, SameSite); CSP + no third-party scripts on callback;
`Cache-Control: no-store`. Implementation quality → `code-quality-standards`.

## Routing

| Need | Skill |
| --- | --- |
| Broad OAuth/OIDC (redirect_uri, state, nonce, mix-up, code injection) | `oauth-oidc-misconfiguration` |
| PKCE challenge/verifier enforcement and S256 checklist | `oauth-pkce-checklist` |
| Secure client/AS/BFF implementation and tests | `code-quality-standards` |
| Resource-server JWT alg/aud/claim abuse | `api-auth-and-jwt-abuse` |
| postMessage token bridge / XSS amplifier | `postmessage-security` / `xss-cross-site-scripting` |

**Selection:** tokens at authorize without code exchange, or implicit→code+PKCE
migration → **this skill**. General OAuth program →
`oauth-oidc-misconfiguration` primary. After code+PKCE →
`oauth-pkce-checklist` helper.

## Output Checklist

- [ ] `client_id`, `response_type`, response_mode, redirect URI recorded
- [ ] Token placement evidence (fragment/query/form_post) redacted
- [ ] Leak surfaces: history, Referer, storage, postMessage, silent iframe
- [ ] AS accept/reject for implicit types documented
- [ ] Residual `state`/`nonce` gaps handed to OAuth skill if needed
- [ ] Impact for **test accounts only** (scopes, TTL, APIs)
- [ ] Migration: code + PKCE (± BFF); types to disable; AS vs client owners

## Rules

- Authorized only; no out-of-scope IdP abuse or real-user token theft.
- Cite OAuth Security BCP: new apps should not use implicit; prefer code + PKCE.
- “Implicit enabled” without usable tokens or a leak chain is config debt—
  severity needs token usability or a concrete theft path. Redact tokens.
- Front-channel tokens (**this skill**) ≠ PKCE bugs (`oauth-pkce-checklist`) ≠
  redirect flaws (`oauth-oidc-misconfiguration`).
