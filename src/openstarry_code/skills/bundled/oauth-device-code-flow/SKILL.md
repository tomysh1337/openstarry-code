---
name: oauth-device-code-flow
description: >-
  Authorized assessment of the OAuth 2.0 Device Authorization Grant (RFC 8628):
  device_code / user_code issuance, verification URI integrity, polling and
  rate limits, client binding, and token exchange abuse. Use when CLI tools,
  smart TVs, IoT, headless clients, or “enter the code at …” flows appear in
  scope for OAuth device login.
---

# OAuth Device Code Flow (Authorized Assessment)

Device Authorization Grant (`urn:ietf:params:oauth:grant-type:device_code`) only.
For browser redirect/state/nonce, use `oauth-oidc-misconfiguration`.

## When To Use

| Situation | Direction |
| --- | --- |
| CLI/TV/IoT/headless shows **user code** + verification URL | **This skill** |
| Traffic has `device_authorization_endpoint`, `device_code`, `user_code`, or device grant | **This skill** |
| Device-code phishing, polling abuse, unbound token issue | **This skill** |
| Broad OAuth redirect/state/nonce/mix-up | `oauth-oidc-misconfiguration` |
| RS JWT crypto / claim forgery only | `api-auth-and-jwt-abuse` |

Keywords: RFC 8628, device_code, user_code, verification_uri, verification_uri_complete, slow_down, authorization_pending, expired_token, access_denied.

## Scope And Authorization

- Authorized apps and **in-scope** AS only. Do not attack third-party IdPs (Google, Microsoft, GitHub, etc.) outside explicit permission — test the **client integration** and any AS you own or the program names.
- Prefer test users/clients **you control**. Do not harvest real-user `user_code` values from shared screens or production displays.
- Treat `device_code`, `user_code`, and tokens as credentials: redact; store offline; rotate after production demos.
- Assessment only — not mass phishing or credential stuffing. Require accept/reject evidence. Hardening pairs with `code-quality-standards`.

## Workflow

### 1. Map the deployment

From discovery and traffic, record:

| Field | Capture |
| --- | --- |
| Roles | Device client, AS, verification UX, resource server |
| Endpoints | `device_authorization_endpoint`, `token_endpoint`, verify host |
| Client | `client_id`; public vs confidential; secret at token? |
| Codes | `device_code` entropy/TTL; `user_code` charset/length; `expires_in` |
| URIs | `verification_uri`, `verification_uri_complete` |
| Polling | `interval`; pending / slow_down / expired_token errors |
| Scopes | Requested vs granted; consent surface |

Baseline: device-auth → display code+URI → user approves on **second device** → poll token until approved/denied/expired.

### 2. Device authorization request integrity

1. Issue legitimate device-auth; capture JSON (`device_code`, `user_code`, `verification_uri`, `expires_in`, `interval`).
2. Probe missing/invalid `client_id`, over-broad `scope`, unexpected params.
3. Confirm confidential clients authenticate at device-auth and/or token as required.
4. Check whether unregistered `client_id` values can mint codes.

```http
POST /device_authorization HTTP/1.1
Host: as.example
Content-Type: application/x-www-form-urlencoded

client_id=<ID>&scope=openid%20profile
```

### 3. User code and verification URI

| Check | Secure expectation |
| --- | --- |
| `user_code` entropy | Sufficient length/charset; not sequential |
| Rate limit on verify | Online brute-force throttled/locked |
| `verification_uri` host | Stable HTTPS AS/branded — not attacker-influenced |
| `verification_uri_complete` | TLS; no open redirect after login |
| Phishing surface | Client hardcodes/allowlists trusted verify host |
| Display channel | Codes not in analytics, crash dumps, world-readable logs |

Note if shoulder-surf of `user_code` alone completes consent unbound from the original `device_code`/client.

### 4. Polling and token endpoint

| # | Probe | Secure behavior |
| --- | --- | --- |
| 1 | Poll before approve | `authorization_pending` (no tokens) |
| 2 | Faster than `interval` | `slow_down`/throttle; no tokens |
| 3 | After deny | `access_denied`; no tokens |
| 4 | After `expires_in` | `expired_token`; not reusable |
| 5 | Redeem code twice | Second fails |
| 6 | Swap code across `client_id`s | Fail (client binding) |
| 7 | Wrong/missing client auth | Fail for confidential clients |
| 8 | Parallel flood | Rate limit; no double refresh issue |

```http
POST /token HTTP/1.1
Host: as.example
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:device_code
&device_code=<DEVICE_CODE>&client_id=<ID>
```

**High severity:** tokens without consent; cross-client redeem; weak codes + no backoff enabling online guessing.

### 5. Consent and post-token

1. Verify UX authenticates user and shows **client + scopes** before approve.
2. Browser login CSRF/session issues on verify → `oauth-oidc-misconfiguration`.
3. Short access TTL; refresh rotation/revocation; device logout.
4. JWT `alg`/`kid`/`aud` on API → `api-auth-and-jwt-abuse`.
5. Shared TV/kiosk refresh storage: impact for **test accounts only**.

### 6. Remediation

Via `code-quality-standards`: high-entropy one-time `device_code`; strong `user_code` + verify rate limits; client-allowlisted HTTPS verify host; enforce `interval`/`slow_down`; bind code to `client_id` (+ auth if confidential); clear consent; never log codes/tokens; RFC 8628 errors.

## Routing

| Need | Skill |
| --- | --- |
| Broad OAuth/OIDC redirect, state, nonce, mix-up | `oauth-oidc-misconfiguration` |
| Access/refresh JWT forgery, `alg`/`kid`/`aud` on RS | `api-auth-and-jwt-abuse` |
| Secure client/AS implementation standards | `code-quality-standards` |

**Selection:** device grant / user codes / verify URI / polling → **this skill**. Browser SSO → `oauth-oidc-misconfiguration`. API JWT after tokens → `api-auth-and-jwt-abuse`. Code fixes → `code-quality-standards`.

## Output Checklist

- [ ] `client_id`, grant, device-auth + token + verification endpoints (in-scope)
- [ ] Baseline device flow success with test user
- [ ] `user_code` strength, verify rate limits, URI integrity
- [ ] Polling matrix: pending / slow_down / deny / expire / replay / client swap
- [ ] Consent shows client+scopes; approval bound to original device request
- [ ] Token/refresh notes; JWT issues routed to `api-auth-and-jwt-abuse`
- [ ] Test-account impact only; codes/tokens redacted
- [ ] Remediation: entropy, rate limits, client binding, one-time codes, trusted verify host, no logging
