---
name: oidc-backchannel-logout
description: >
  Authorized design, implementation review, and assessment of OpenID Connect
  Back-Channel Logout: logout_token JWT validation, backchannel_logout_uri
  delivery, sid/sub session binding, events claim, and propagation to local
  sessions and refresh tokens. Use when OIDC back-channel logout,
  backchannel_logout_uri, logout_token, sid claim, or IdP server-to-server
  logout POST appears in discovery, code, or traffic.
---

# OIDC Back-Channel Logout

Server-to-server OpenID Connect Back-Channel Logout 1.0: the IdP notifies RPs
with a signed `logout_token` so browser-independent sessions end. Prefer this
skill when the artifact is the BC contract; use `sso-logout-propagation` for
multi-protocol SLO maps.

## When To Use

| Situation | Direction |
| --- | --- |
| Discovery/metadata: `backchannel_logout_supported`, `backchannel_logout_session_supported`, or registered `backchannel_logout_uri` | **This skill** |
| IdP POST of `logout_token` (form field) to an RP endpoint in traffic/logs | **This skill** |
| Implement/review RP logout_token acceptance and session teardown by `sid` | **This skill** |
| Multi-app residual sessions after IdP logout (topology first) | `sso-logout-propagation` |
| OIDC login: `redirect_uri`, `state`, PKCE, code theft | `oauth-oidc-misconfiguration` |
| Front-channel only (iframe/`end_session`) without logout_token | `sso-logout-propagation` |
| JWT alg/`kid`/JWKS issues not tied to logout lifecycle | `api-auth-and-jwt-abuse` / `jwt-audience-issuer-checks` |

Keywords: back-channel logout, `logout_token`, `backchannel_logout_uri`, `sid`,
`events` `http://schemas.openid.net/event/backchannel-logout`, session-supported
BC logout, RP logout endpoint, IdP-initiated teardown.

## Scope And Authorization

- **Authorized only**: owned RPs/IdPs, labs, CTFs, or written scope naming the
  tenant and every `backchannel_logout_uri` exercised.
- Prefer **test users** and staging. Do not flood production RPs with forged or
  mass logout tokens; do not attack third-party IdP infrastructure outside scope.
- Treat `logout_token`, session cookies, refresh tokens, and JWKS as **secrets**:
  redact reports; store offline; rotate test sessions after demos.
- Assessment/hardening only — not production SSO disruption. Gate “logout all
  devices” proofs on accounts you control.

## Workflow

### 1. Map the BC logout contract

| Field | Capture |
| --- | --- |
| IdP discovery | `backchannel_logout_supported`, `backchannel_logout_session_supported`, `jwks_uri`, `issuer` |
| RP registration | `backchannel_logout_uri`, `backchannel_logout_session_required` (or equivalent) |
| Session model | Browser SID, server session store, refresh grants, device sessions |
| Binding | `sid` in `id_token` / session; `sub` only if sid unsupported |
| Delivery | HTTPS POST `application/x-www-form-urlencoded` with `logout_token` |
| Response | HTTP 200 on success; non-2xx must leave session state defined |

Confirm IdP can reach RP URI (network path, mTLS, allowlists, private hosts).

### 2. Validate `logout_token` (RP must enforce)

Before destroying any session, require:

1. **JWT**: compact JWS; reject unsigned/`none`; pin algs to IdP JWKS.
2. **`iss`**: exact IdP issuer (no host-header trust).
3. **`aud`**: this RP `client_id` (exact; multi-aud only with explicit policy).
4. **`iat`**: present; max skew / max age (reject ancient tokens).
5. **`events`**: includes `http://schemas.openid.net/event/backchannel-logout` → `{}`.
6. **`sid` and/or `sub`**: at least one; if session-supported prefer **`sid`** and tear down only matching sessions.
7. **No `nonce`**: logout tokens must not carry `nonce` (≠ `id_token`).
8. **Signature**: current JWKS + rotation; never fetch keys from token-controlled URLs.
9. **Replay**: cache `jti` or token hash; reject duplicates in retention window.
10. Ignore unknown claims safely; do not trust nested unsigned data.

### 3. Session and token teardown

| Target | Secure expectation |
| --- | --- |
| Server sessions for `sid`/`sub` | Destroy store records, not only clear cookies |
| Refresh tokens / grants | Revoke for that session or user per product scope |
| Access tokens | Short TTL and/or denylist if long-lived JWTs |
| Secondary tickets | Remember-me, WS, step-up cookies bound to same SSO |
| Multi-device | Document whether `sid` is per-browser or global; test both |

**Finding class:** valid POST ignored; 200 but session still valid; teardown by
`sub` only when `sid` was issued (wrong scope); accept without `events` or with
`nonce`.

### 4. IdP and RP negative tests (authorized)

- POST without `logout_token`; empty body; wrong content-type.
- Wrong `aud`/`iss`, bad `iat`/signature, missing `events`, injected `nonce`, attacker `sid`.
- Cross-client token (`aud` = other RP) accepted here.
- SSRF/open redirect on registered `backchannel_logout_uri` → `ssrf-server-side-request-forgery` if fetchable.
- IdP omits BC for some RPs while claiming global logout; front-channel-only peers → `sso-logout-propagation`.

### 5. Implementation hardening

- Idempotent handler; short timeout; async teardown OK if APIs **fail closed** once logged out.
- TLS only; optional IdP IP allowlist or mTLS (signature remains primary authN).
- Structured logs: outcome, `sid` hash, `jti` — never full token.
- Pair code changes with `code-quality-standards`.

## Routing

| Need | Skill |
| --- | --- |
| OIDC back-channel logout_token / URI / sid teardown | **This skill** |
| Broad SSO SLO / residual multi-app sessions / SAML SLO | `sso-logout-propagation` |
| OIDC/OAuth login misconfig | `oauth-oidc-misconfiguration` |
| JWT verify/alg/aud deep dive (API tokens) | `api-auth-and-jwt-abuse`, `jwt-audience-issuer-checks` |
| Refresh rotation and revoke endpoints | `jwt-refresh-token-patterns` |
| Cookie flags on local clear | `cookie-security-flags` |
| Login SID not rotated | `session-fixation-management` |
| Logout state-change CSRF (browser) | `csrf-cross-site-request-forgery` |
| Registration URI fetch abuse | `ssrf-server-side-request-forgery` |
| Implementation baseline | `code-quality-standards` |

## Output Checklist

- [ ] Authz covers IdP/tenant and every RP `backchannel_logout_uri` tested
- [ ] Discovery/registration: BC supported, session-supported, URIs, issuer/JWKS
- [ ] `logout_token` validation: iss, aud, iat, events, sid/sub, no nonce, sig, replay
- [ ] POST contract: content-type, field name, success/failure HTTP semantics
- [ ] Before/after: session store, RT, AT, peer surfaces for test user only
- [ ] Over/under teardown: sid vs sub scope documented
- [ ] Gaps: RPs without BC; front-channel-only; unreachable URI
- [ ] Remediation: full claim set; server destroy + RT revoke; jti cache; TLS; redacted logs
- [ ] Secrets redacted; no production mass-logout
