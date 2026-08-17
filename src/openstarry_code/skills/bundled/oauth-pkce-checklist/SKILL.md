---
name: oauth-pkce-checklist
description: >-
  Authorized assessment checklist for OAuth 2.0 PKCE (RFC 7636): code_challenge,
  code_verifier, S256 vs plain, public-client enforcement, and related code
  interception controls. Use when SPA, mobile, native, or public clients use
  authorization code + PKCE under explicit engagement scope.
---

# OAuth PKCE Checklist (Authorized Assessment)

Focused **PKCE** methodology for OAuth 2.0 authorization-code flows. Complements
broad OAuth/OIDC review; does not replace `redirect_uri`, `state`, or IdP policy tests.

## Use When

| Situation | Direction |
| --- | --- |
| SPA/mobile/native uses **auth code + PKCE** | **This skill** (primary for PKCE) |
| `code_challenge` / `code_verifier` / method params present | **This skill** |
| Code interception, challenge downgrade, verifier mix-up | **This skill** |
| Full OAuth redirect/state/nonce/mix-up surface | `oauth-oidc-misconfiguration` |
| Resource-server JWT crypto only | `api-auth-and-jwt-abuse` |
| Third-party IdP out of program scope | Test **client** only; do not attack IdP |

Keywords: PKCE, RFC 7636, S256, code_verifier, code_challenge, public client, code interception.

## Scope And Authorization

- Authorized apps and **in-scope** authorization servers only. Do not attack
  Google/Microsoft/GitHub production unless the program **names** them.
- Prefer test users/clients **you control**. Do not steal real-user codes.
- Treat `code`, `code_verifier`, and tokens as credentials: redact; store offline; rotate after demos.
- Assessment only—not mass interception of production codes.
- Implementation hardening pairs with `code-quality-standards`.

## Workflow

### 1. Identify client and AS PKCE policy

From authorize/token traffic and discovery (`code_challenge_methods_supported`):

| Field | Capture |
| --- | --- |
| Client type | public (SPA/native) vs confidential; secret at token? |
| Challenge method | `S256`, `plain`, or absent |
| AS policy | PKCE required / optional / ignored for this `client_id` |
| Code delivery | HTTPS redirect, custom scheme, loopback, app link |

### 2. Baseline honest PKCE

1. Generate `code_verifier` (43–128 chars, RFC 7636 unreserved set).
2. `code_challenge = BASE64URL(SHA256(verifier))`, method `S256`.
3. Authorize → `code` → token with matching `code_verifier` → success.

```http
POST /token HTTP/1.1
Host: as.example
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code=<CODE>&redirect_uri=<URI>
&client_id=<ID>&code_verifier=<VERIFIER>
```

### 3. Core enforcement probes

One accept/reject pair per row for the **in-scope** `client_id`:

| # | Probe | Secure behavior |
| --- | --- | --- |
| 1 | Omit `code_challenge` on authorize | Reject or force PKCE for public clients |
| 2 | Token without `code_verifier` | Fail |
| 3 | Wrong verifier (other session) | Fail |
| 4 | Empty / truncated / overlong verifier | Fail |
| 5 | `code_challenge_method=plain` when S256 required | Reject plain |
| 6 | Method omitted (AS default) | Document; prefer mandatory S256 |
| 7 | Victim `code` + attacker verifier | Fail (binding) |
| 8 | Replay same `code` after success | Second redeem fails |
| 9–10 | Wrong `redirect_uri` or `client_id` at token | Fail |

**High severity:** token without/wrong verifier, or missing challenge accepted for a public client.

### 4. Downgrade and method confusion

- `plain` vs S256 mismatch; duplicate `code_challenge` (which value wins?); case (`s256`/`Plain`).
- Confidential+secret: optional PKCE is defense-in-depth; public clients must not embed secrets.

### 5. Interception surfaces

| Surface | Check |
| --- | --- |
| Custom URI scheme | Lab device you own: malicious app races for `code` |
| Loopback / WebView | Port confusion; prefer system browser + PKCE |
| SPA Referer / logs | `code` not on third parties; verifier never in URL |

If attacker has `code` but not verifier, AS must refuse token. Both leak (XSS/debug) → PKCE insufficient.

### 6. Related controls and remediation

PKCE does **not** replace exact `redirect_uri`, session-bound `state`, OIDC `nonce`, or one-time short codes.
Deeper OAuth → `oauth-oidc-misconfiguration`. Refresh lifecycle → `jwt-refresh-token-patterns`.

Remediation (`code-quality-standards`): mandatory **S256** PKCE for public clients; reject `plain`/missing
challenge; CSPRNG verifier in memory/OS store only; AS binds code to client+redirect+challenge;
never log codes/verifiers; `Cache-Control: no-store`; automate probes above.

## Routing

| Need | Skill |
| --- | --- |
| Broad OAuth/OIDC (redirect, state, nonce, mix-up) | `oauth-oidc-misconfiguration` |
| Access/refresh JWT lifecycle, rotation, storage | `jwt-refresh-token-patterns` |
| JWT alg/kid/claim forgery on RS | `api-auth-and-jwt-abuse` |
| Secure client/AS implementation | `code-quality-standards` |

**Selection:** PKCE challenge/verifier enforcement → **this skill**. Full OAuth program →
`oauth-oidc-misconfiguration` primary; this skill as checklist helper.

## Checklist

- [ ] Client type, `client_id`, redirect style, AS PKCE policy recorded
- [ ] Baseline S256 success; discovery methods noted
- [ ] Omit challenge / omit verifier / wrong verifier results captured
- [ ] `plain` downgrade, method-case, code replay, client/redirect binding tested
- [ ] Scheme/loopback/SPA interception surface described (lab-only)
- [ ] Residual `state`/`redirect_uri` gaps handed to OAuth skill
- [ ] Codes/verifiers redacted; remediation: mandatory S256 for public clients

## Rules

- Authorized only; no out-of-scope IdP abuse or real-user code theft.
- Findings need **token endpoint accept/reject evidence**, not theory alone.
- “PKCE absent” on confidential server-only clients needs a code-theft path for critical severity.
- Custom-scheme hijack proofs only on devices/apps **you own**. Redact codes/verifiers.
