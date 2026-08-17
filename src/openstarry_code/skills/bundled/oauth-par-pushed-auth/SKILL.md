---
name: oauth-par-pushed-auth
description: >-
  Authorized assessment and hardening of OAuth 2.0 Pushed Authorization Requests
  (PAR, RFC 9126): back-channel request push, request_uri lifecycle, client auth
  at the PAR endpoint, and front-channel reduction. Use when AS discovery shows
  pushed_authorization_request_endpoint, require_pushed_authorization_requests,
  or flows that replace long authorize query strings with request_uri references.
---

# OAuth PAR (Pushed Authorization Requests)

Methodology for **OAuth 2.0 PAR** (RFC 9126): clients POST authorization parameters
to the AS, receive a short-lived `request_uri`, then send the browser to `/authorize`
with only `client_id` + `request_uri` (plus any profile-required fields). Complements
PKCE, JAR, and general OAuth redirect work — does not replace them.

## When To Use

- Metadata or docs expose `pushed_authorization_request_endpoint` or PAR-only policy
  (`require_pushed_authorization_requests` / equivalent vendor flag).
- Capture shows `POST` to a PAR URL returning `request_uri` + `expires_in`, then a
  slim authorize redirect.
- Reviewing confidential or public clients that should stop putting scopes, claims,
  or large `request` objects only on the front channel.
- Keywords: PAR, RFC 9126, `request_uri`, pushed authorization, back-channel authz
  request, require PAR.

**Not primary for:** classic redirect_uri / `state` / code theft without PAR →
`oauth-oidc-misconfiguration`; PKCE-only checklist → `oauth-pkce-checklist` (if present)
or general OAuth skill; JWT access-token crypto → `api-auth-and-jwt-abuse`; DPoP /
sender-constrained tokens → `device-binding-tokens`.

## Scope And Authorization

- Owned apps, labs, CTFs, or **named** engagement targets only. Prefer test clients
  and users you control on in-scope authorization servers.
- Do not register clients, mint PAR objects, or replay `request_uri` values against
  third-party production IdPs outside written scope.
- Treat `request_uri`, authorization codes, client secrets, private_key_jwt material,
  and PAR request bodies as credentials: redact; store captures offline; rotate after
  production demos if values could remain valid.
- Non-destructive first: prove accept/reject of PAR policy with clients you own.

## Workflow

### 1. Map discovery and deployment

| Field | Capture |
| --- | --- |
| PAR endpoint | `pushed_authorization_request_endpoint` (absolute URL) |
| PAR required? | `require_pushed_authorization_requests` or AS policy |
| Client type | Confidential, public, SPA, native, M2M-adjacent |
| Client auth at PAR | `client_secret_*`, `private_key_jwt`, mTLS, none |
| Front-channel | Remaining authorize params (`client_id`, `request_uri`, …) |
| Related profiles | PKCE, JAR (`request` / `request_uri` JWT), RAR, PAR+JAR |

Baseline happy path (authorized client):

```text
POST /par  (auth + response_type, client_id, redirect_uri, scope, state, code_challenge…)
  → 201 { "request_uri": "urn:…", "expires_in": 60 }
GET  /authorize?client_id=…&request_uri=urn:…
  → login / consent → code (or hybrid) at redirect_uri
```

### 2. Client authentication at PAR

| Probe | Secure behavior |
| --- | --- |
| No client auth on confidential client | Reject |
| Wrong secret / wrong JWT `aud` for PAR URL | Reject |
| Public client without required PKCE on PAR body | Reject if policy requires PKCE |
| Cross-client: client A auth, `client_id` of B in body | Reject |

PAR is where secrets and large parameters belong; weak PAR auth undoes the model.

### 3. `request_uri` lifecycle

| Probe | Secure behavior |
| --- | --- |
| Reuse same `request_uri` after successful authorize | Reject (one-time) |
| Use after `expires_in` | Reject |
| Guess / brute sibling URNs or IDs | Impractical entropy; rate-limit |
| Authorize with `request_uri` issued to another client | Reject |
| Strip `request_uri`, send full params on front channel when PAR required | Reject |

### 4. Parameter integrity (front vs back channel)

- When PAR is used, AS must **not** let front-channel query params override pushed
  values (`redirect_uri`, `scope`, `state`, `code_challenge`, resource/RAR, etc.).
- If both JAR and PAR appear, document which object is authoritative; reject
  conflicting sets.
- Confirm pushed `redirect_uri` is still exact-match allowlisted (PAR does not
  relax redirect rules).

### 5. Policy and abuse cases

| Risk | What to prove (authorized) |
| --- | --- |
| PAR optional but claimed “required” | Front-channel-only authorize still succeeds |
| Unauthenticated PAR spam | Resource exhaustion / unauthenticated push accepted for confidential clients |
| Leaked `request_uri` in logs/Referer | Shorter window still allows login completion if not one-time |
| Missing PKCE with public + PAR | Code interception still viable at redirect |

### 6. Remediation themes

Pair implementation with `code-quality-standards`:

- Advertise PAR in discovery; set **require PAR** for high-risk or all clients when ready.
- Authenticate confidential clients at PAR; bind `request_uri` to `client_id`.
- Short `expires_in` (seconds–few minutes); single-use `request_uri`; high entropy.
- Ignore or reject front-channel overrides of pushed parameters.
- Keep PKCE for public clients; exact `redirect_uri`; server-side `state` binding.
- Log PAR failures without full secrets; never log raw client secrets or codes.

## Routing

| Need | Skill |
| --- | --- |
| PAR endpoint, `request_uri`, require-PAR policy | **This skill** |
| Redirect URI, `state`, code flow, mix-up (non-PAR focus) | `oauth-oidc-misconfiguration` |
| PKCE challenge/verifier only | `oauth-pkce-checklist` / OAuth skill |
| Access/refresh JWT crypto and claims | `api-auth-and-jwt-abuse`, `jwt-audience-issuer-checks` |
| DPoP / mTLS-bound tokens after issue | `device-binding-tokens` |
| RP session not rotated after code exchange | `session-fixation-management` |
| Multi-vector ATO including OAuth | `account-takeover-methodology` |
| Secure AS/client implementation and tests | `code-quality-standards` |

**Selection:** primary when **pushed requests** / `request_uri` lifecycle / PAR client
auth are the question. General OAuth redirect bugs without PAR →
`oauth-oidc-misconfiguration`. Token crypto → JWT skills. Fixes →
`code-quality-standards`.

## Output Checklist

- [ ] Discovery: PAR URL, require-PAR flag, client auth methods documented
- [ ] Baseline PAR → authorize → code path captured (redacted)
- [ ] Confidential client auth failures at PAR recorded
- [ ] `request_uri` one-time use, expiry, and cross-client binding tested
- [ ] Front-channel override of pushed params attempted; result noted
- [ ] PAR-required bypass (plain authorize) checked when policy claims required
- [ ] PKCE / redirect_uri interaction with PAR stated
- [ ] Impact, redacted evidence, remediation (require PAR, bind URI, no overrides)
