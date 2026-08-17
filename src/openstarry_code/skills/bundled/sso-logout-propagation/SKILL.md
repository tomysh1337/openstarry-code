---
name: sso-logout-propagation
description: >-
  Authorized assessment of SSO single logout (SLO) and cross-app session
  propagation: IdP/SP logout, front- vs back-channel termination, RP-initiated
  logout, refresh-token and cookie invalidation, and residual sessions after
  “logout everywhere.” Use when SSO logout, SLO, end_session, LogoutRequest,
  or peer apps staying signed in after logout appear in scope.
---

# SSO Logout Propagation (Authorized Assessment)

Methodology for **single logout**, **logout propagation**, and **residual sessions** across IdP and relying parties (SPs/RPs). Focus: whether logout at one place ends sessions and tokens elsewhere — not login-time crypto (hand those off).

## When To Use

| Situation | Direction |
| --- | --- |
| “Log out”, “Sign out everywhere”, SSO portal exit, multi-app suite logout | **This skill** |
| Traffic shows `end_session_endpoint`, `LogoutRequest`/`LogoutResponse`, `post_logout_redirect_uri`, front-channel iframes, or back-channel logout POSTs | **This skill** |
| Logout of IdP or App A leaves App B / mobile / API accepting old session or refresh token | **This skill** |
| OAuth/OIDC login misconfig (redirect_uri, state, code) | `oauth-oidc-misconfiguration` |
| SAML assertion signature, Audience, ACS acceptance | `saml-sso-basics` |
| Login/ACS does not regenerate local SID (fixation) | `session-fixation-management` |
| Multi-vector ATO beyond logout lifecycle | `account-takeover-methodology` |

Keywords: SLO, single logout, RP-initiated logout, front-channel logout, back-channel logout, `end_session`, `id_token_hint`, `LogoutRequest`, residual refresh token, logout CSRF.

## Scope And Authorization

- **Authorized only**: owned apps, labs, CTFs, or written scope naming the IdP/tenant and every RP/SP exercised.
- Prefer **test users** and staging. Do **not** mass-logout production workforces or attack third-party IdP infrastructure outside the engagement.
- Dual browsers/devices for “still logged in elsewhere” proofs. Never terminate real-user sessions you do not control.
- Treat logout tokens, session cookies, refresh tokens, and SLO signatures as **secrets**: redact; store offline; rotate test sessions after demos.
- Assessment methodology only — not disruption of production SSO for all tenants. Gate “logout all devices” on shared accounts behind explicit approval.

## Workflow

### 1. Map the identity topology

| Field | Capture |
| --- | --- |
| Roles | IdP/AS, RP/SP apps, APIs, mobile clients |
| Protocol | OIDC, OAuth2, SAML2, proprietary portal SSO |
| Session types | Browser SID, IdP SSO cookie, refresh token, access token, device session |
| Logout entry points | App button, IdP menu, admin revoke, password change |
| SLO mechanisms | Front-channel (redirect/iframe), back-channel POST, SAML SLO binding |
| Endpoints / redirects | `end_session`, SAML SLO URL, `/logout`, revoke URL, `post_logout_redirect_uri` |

Graph: **User → App A / App B / API → IdP**. State which edges logout claims to cut.

### 2. Baseline multi-session setup

With **test user V** only: open concurrent sessions (App A, App B or second profile, optional mobile/API with refresh token). Record canaries (whoami, account page) and hash/last-4 of SIDs or refresh ids. Without concurrent sessions, propagation failure is not demonstrable.

### 3. RP-initiated logout (app-first)

From App A, trigger normal logout:

| Check | Secure expectation | Weak signal |
| --- | --- | --- |
| Local App A session | Cookie cleared **and** server record destroyed | Client clear only; SID still valid if replayed |
| IdP SSO session | Ended when product claims global logout | Silent SSO re-enters App A |
| App B session | Ended if SLO advertised | App B still serves V’s canary |
| Access / refresh tokens | AT rejected or short residual; RT revoked | RT still mints AT |
| `post_logout_redirect_uri` | Exact allowlist | Open redirect after logout |

Replay pre-logout Cookie/Bearer from a second client. **Finding:** server still accepts it after “logout.”

### 4. IdP-initiated / global logout

From IdP “sign out” / “all applications”: note front-channel hits to each RP logout URL (missing RPs matter); if back-channel exists, check logout token verification (`iss`, `aud`, `sid`, signature). Retest App A, App B, and API.

**Secure baseline:** every registered V session dies, **or** docs clearly scope logout to “this app only” (then residual peers are not a bug — document expected behavior).  
**Finding:** UI claims “all apps” but peer RP or refresh token survives.

### 5. Protocol-specific SLO probes

**OIDC/OAuth:** `end_session` without `id_token_hint`/`sid` (wrong session or no-op?); weak `post_logout_redirect_uri`; revoke endpoint coverage (one RT vs siblings); front-channel iframe ignored; GET logout without binding (**logout CSRF** — integrity/availability note). Login redirect/state/PKCE → `oauth-oidc-misconfiguration`.

**SAML:** unsigned or attacker-signed `LogoutRequest`/`LogoutResponse` accepted?; SP clears local session but never notifies IdP (or inverse). Login signature/Audience/ACS → `saml-sso-basics`; keep this skill on **logout message** acceptance and teardown.

### 6. Propagation gaps

| Gap | Test |
| --- | --- |
| Offline mobile / closed tab | Logout elsewhere; reopen later still authed? |
| Shared subdomain cookies | Logout on `app.` leaves `admin.` valid |
| Secondary tokens | remember-me, WS ticket, impersonation cookie |
| Privilege cookies | MFA/step-up cookie survives primary logout |
| Race | Parallel API during logout still 200? |

Missing regenerate-**on-login** → `session-fixation-management`; here: **invalidate on logout**.

### 7. Remediation (report-ready)

Server-destroy sessions; clear cookies with matching flags; revoke refresh grants; complete SLO (OIDC front/back-channel; SAML SLO with signed requests and correct SessionIndex/NameID); exact-match `post_logout_redirect_uri`; verify back-channel logout tokens; honest product scope (“this app” vs “everywhere”); CSRF protection on state-changing logout; retest concurrent sessions. Pair implementation with `code-quality-standards`.

## Routing

| Need | Skill |
| --- | --- |
| SSO logout / SLO / residual peer sessions / RT after logout | **This skill** |
| OAuth/OIDC login: redirect_uri, state, PKCE, code theft | `oauth-oidc-misconfiguration` |
| SAML login: signature, Audience, ACS | `saml-sso-basics` |
| Pre-auth SID not regenerated on login/ACS | `session-fixation-management` |
| JWT crypto/claims on APIs (not logout lifecycle) | `api-auth-and-jwt-abuse` |
| Post-logout open redirect only | `open-redirect` |
| Logout / cookie state-change CSRF depth | `csrf-cross-site-request-forgery` |
| Multi-vector ATO including sticky sessions | `account-takeover-methodology` |
| Implement session destroy / cookie flags | `code-quality-standards` |

## Output Checklist

- [ ] Authz covers IdP/tenant and every RP/SP/API exercised
- [ ] Topology: apps, session types, logout entry points, SLO endpoints
- [ ] Concurrent baseline sessions for test user V (multi-browser/device)
- [ ] RP-initiated: local server session, IdP SSO, peer apps, AT/RT outcomes
- [ ] IdP/global logout: front/back-channel coverage; missing RPs
- [ ] Pre-logout cookie/token replay after logout (accept vs reject)
- [ ] `post_logout_redirect_uri` / return URL checked
- [ ] SAML LogoutRequest/Response signing (if SAML)
- [ ] Residuals: remember-me, WS tickets, subdomain cookies, offline mobile
- [ ] UI/docs claim vs actual scope of logout
- [ ] Impact for test accounts only; secrets redacted
- [ ] Remediation: server invalidate, RT revoke, complete SLO, redirect allowlist, logout CSRF

## Rules

- **Authorized only.** Test users and in-scope tenants — never mass-logout real workforces or third-party IdP production.
- Logout bugs need **before/after** evidence on a second surface (peer app or replayed token), not only a 302 to `/login`.
- Distinguish **local logout by design** from **broken SLO** when the product claims global termination.
- Do not relabel login fixation or OAuth code theft as logout propagation; route those skills correctly.
- Redact tokens/cookies; clean negatives (sessions die as documented) are valuable — state verified logout scope clearly.
