---
name: pkce-public-client-checklist
description: >-
  Authorized design and assessment checklist for OAuth 2.0 PKCE on public
  clients (SPA, mobile, native, desktop): mandatory S256 code_challenge,
  code_verifier lifecycle, no embedded client secrets, and token-endpoint
  binding. Use when public clients run authorization code + PKCE, when
  code_challenge / code_verifier appear for a public client_id, or when
  migrating off implicit / password grants for SPA or mobile apps.
---

# PKCE Public Client Checklist

Focused **public-client** PKCE checklist (RFC 7636 + OAuth 2.1 public-client
guidance) for SPA, mobile, native, and desktop clients that **cannot** keep a
client secret. Complements broader OAuth review; not a full IdP audit.

## When To Use

| Situation | Direction |
| --- | --- |
| SPA / mobile / native / desktop is a **public** OAuth client | **This skill** (primary) |
| Auth code + PKCE; `code_challenge` / `code_verifier` / `S256` | **This skill** |
| Public client still uses implicit, ROPC, or embedded secret | **This skill** (migrate / fail) |
| Only confidential server-side client with secret | Optional PKCE; not primary |
| Broad redirect / state / nonce / mix-up / issuer issues | `oauth-oidc-misconfiguration` |
| General PKCE matrix already primary elsewhere | `oauth-pkce-checklist` |
| Access/refresh JWT crypto or rotation only | `api-auth-and-jwt-abuse` / `jwt-refresh-token-patterns` |

Keywords: PKCE, public client, SPA, mobile, native, RFC 7636, S256, code_verifier, code_challenge, no client secret.

## Scope And Authorization

- Owned apps, labs, CTFs, or **named** engagement targets only. Do not attack
  third-party IdPs unless named—test **your** public client and in-scope AS.
- Prefer test users/`client_id` **you control**. Do not redeem real-user codes.
- Treat `code`, `code_verifier`, and tokens as credentials: redact; store offline; rotate after demos.
- Custom-scheme/loopback hijack proofs only on devices/apps **you own**.
- Assessment and hardening only. Pair implementation with `code-quality-standards`.

## Workflow

### 1. Confirm public client and AS policy

| Field | Capture |
| --- | --- |
| Client type | Public: no confidential secret in binary/bundle/JS |
| `client_id` | Registered as public; auth method `none` or public-only |
| Redirect | HTTPS app URL, claimed app link, loopback, or custom scheme |
| Discovery | `code_challenge_methods_supported` includes `S256` |
| AS policy | PKCE **required** for this public `client_id` |
| Token auth | Must **not** require a client secret for this client |

**Fail:** “public” client ships a hard-coded secret, or AS accepts secret-less
token redeem **without** PKCE for that client.

### 2. Baseline honest S256 flow

1. CSPRNG `code_verifier`: 43–128 chars from RFC 7636 unreserved set.
2. `code_challenge = BASE64URL(SHA256(ascii(verifier)))`, method **`S256`**.
3. Authorize: `response_type=code`, exact `redirect_uri`, `client_id`,
   `code_challenge`, `code_challenge_method=S256`, `state` (OIDC: `nonce`).
4. Token: same `code`, `redirect_uri`, `client_id`, matching `code_verifier`.

```http
POST /token HTTP/1.1
Host: as.example
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code=<CODE>&redirect_uri=<URI>
&client_id=<ID>&code_verifier=<VERIFIER>
```

### 3. Public-client enforcement matrix

Accept/reject evidence per row for the **in-scope** public `client_id`:

| # | Probe | Secure behavior |
| --- | --- | --- |
| 1 | Authorize without `code_challenge` | Reject (PKCE mandatory) |
| 2 | Token without `code_verifier` | Reject |
| 3 | Wrong / other-session verifier | Reject |
| 4 | Empty, truncated, or overlong verifier | Reject |
| 5 | `code_challenge_method=plain` | Reject for public clients |
| 6 | Method omitted / case weird (`s256`) | Reject or strict S256 only |
| 7 | Victim `code` + attacker verifier | Reject (bound to challenge) |
| 8 | Replay same `code` after success | Second redeem fails |
| 9 | Wrong `redirect_uri` or `client_id` at token | Reject |
| 10 | Fabricated client secret at token | Ignore secret; still require PKCE |

**High severity:** public client gets tokens with missing/wrong PKCE, or
challenge is optional so a stolen `code` redeems alone.

### 4. Verifier and code storage (public surfaces)

| Surface | Expectation |
| --- | --- |
| SPA | Verifier in memory for the flow only—not logs or long-lived storage |
| Mobile/native | OS-secure store or process memory; clear after redeem |
| URL / Referer | Never put verifier in query; avoid `code` Referer leaks |
| WebView | Prefer system browser + claimed redirect |
| Custom scheme | Assume another app may see `code`; PKCE must hold |

If attacker has **both** code and verifier (XSS, malware), PKCE is insufficient.

### 5. Related controls and remediation

PKCE does **not** replace exact `redirect_uri`, session-bound `state`, OIDC
`nonce`, short-lived one-time codes, or HTTPS. Refresh → `jwt-refresh-token-patterns`;
DPoP → `oauth-token-binding-dpop`.

Remediation (`code-quality-standards`): register **public** client; mandatory
**S256**; reject `plain`/missing challenge/verifier; CSPRNG verifier; bind code
to `client_id` + `redirect_uri` + challenge; never log codes/verifiers;
`Cache-Control: no-store`; automate matrix rows; no secrets in packages/bundles.

## Routing

| Need | Skill |
| --- | --- |
| Public-client PKCE mandatory S256 checklist | **This skill** |
| General PKCE probe list (any client type) | `oauth-pkce-checklist` |
| Full OAuth/OIDC redirect, state, nonce, mix-up | `oauth-oidc-misconfiguration` |
| Implicit / front-channel token migration | `oauth-implicit-flow-risks` |
| Refresh rotation / JWT crypto / DPoP | `jwt-refresh-token-patterns` / `api-auth-and-jwt-abuse` / `oauth-token-binding-dpop` |
| Secure implementation baseline | `code-quality-standards` |

**Selection:** public SPA/mobile/native PKCE → **this skill**. Full IdP/redirect
→ `oauth-oidc-misconfiguration` primary. Generic PKCE matrix → `oauth-pkce-checklist`.

## Output Checklist

- [ ] Public `client_id`, redirect style, AS PKCE policy, discovery methods recorded
- [ ] Confirmed: no usable client secret in client artifact / bundle
- [ ] Baseline S256 authorize → code → token success with controlled client
- [ ] Matrix: omit challenge/verifier, wrong verifier, plain downgrade, replay, binding
- [ ] Verifier storage and code interception surface described (lab-only)
- [ ] Residual state/redirect/OIDC gaps handed off; codes/verifiers redacted
- [ ] Remediation: mandatory S256, reject plain, bind code, no secret, tests
