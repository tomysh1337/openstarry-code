---
name: password-policy-design
description: >
  Design NIST-oriented password policies: length, deny/breach lists, no
  composition theater or forced rotation, modern hashing, and manager-friendly
  UX. Use when defining or reviewing password requirements, signup/change
  validation, breached-password checks, or legacy complexity rules on owned systems.
---

# Password Policy Design (NIST-Oriented)

Design for **human-memorized secrets** (NIST SP 800-63B style): favor **length
and deny-lists** over composition rules; rotate on **compromise**, not a calendar;
store with **slow, salted, memory-hard** hashes. Prefer the repo’s IdP/framework
validators over a second ad-hoc rule engine.

## When To Use

- Setting min/max length, charset acceptance, deny-list / HIBP-style screening
- Replacing “upper+lower+digit+symbol + 90-day rotate” policies
- Signup, password-change, and admin-reset validation UX and API errors
- Hash algorithm choice, cost params, rehash-on-login / migration
- Keywords: password policy, NIST 800-63, composition rules, breached password,
  strength meter, forced rotation, argon2/bcrypt, 密码策略, 复杂度

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Login brute-force / progressive lockout | `account-lockout-design` |
| JWT/session claim or alg abuse | `api-auth-and-jwt-abuse` |
| Reset Host/token poisoning | `password-reset-poisoning` |
| Multi-vector ATO chaining | `account-takeover-methodology` |
| Implementation quality defaults | `code-quality-standards` |

## Repo Config First

Repo IdP settings, framework validators, and security ADRs **outrank** defaults.

1. **Enforcers:** Auth0/Cognito/Okta/Keycloak, Django validators, ASP.NET Identity,
   Spring Security, LDAP `pwdPolicy` — configure these before parallel rules
2. **Hashing:** algorithm (argon2id / scrypt / bcrypt / PBKDF2), cost, salt, rehash path
3. **Identity model:** email vs username login; SSO/passkey-only tenants
4. **Compliance overlays:** named mandates that still require composition/rotation —
   document conflict; do not invent extra theater
5. **Breach-check:** existing HIBP k-anonymity or internal deny-list — reuse it
6. **Org norms:** align min/max length and error envelope with mature sibling apps
7. **Config store:** dynamic min length / deny-list vs hard-coded constants

**Precedence:** follow the repo on conflict. Surface bans on paste, calendar-only
rotation, or unsalted MD5/SHA1 password storage.

## Workflow

1. **Inventory** signup, change, admin-reset, login errors, and storage params.
2. **Length and acceptance**
   - Min: typically **8+** user-chosen; often **12–16** by risk when password-only
   - Max: at least **64** (prefer 64–128); **never truncate silently**
   - Allow all printable Unicode and spaces unless a protocol forbids it
   - Allow **paste** and password-manager autofill; support show-password
3. **Screen secrets (not composition theater)**
   - Deny-list: common passwords, service/username/email local-part, sequences,
     and **breached** corpora (privacy-preserving when using external APIs)
   - Do **not** require mixed classes as the primary quality bar
   - Do **not** force periodic rotation; rotate on compromise, recovery, or risk;
     invalidate sessions/refresh tokens on change
4. **UX / API errors**
   - Authenticated change: specific reasons (too short, on deny-list, contains username)
   - Unauthenticated login: avoid user enumeration
   - Prefer passkeys/MFA as stronger authenticators; avoid hint/KBA fields
5. **Store and verify**
   - Prefer **argon2id** (or scrypt/bcrypt with modern cost); unique per-secret salt
   - Constant-time verify; rehash when parameters upgrade
   - Never log passwords; never reversible-encrypt login secrets
6. **Abuse hand-offs** — online guessing → `account-lockout-design`; issued JWTs →
   `api-auth-and-jwt-abuse`; code → `code-quality-standards`
7. **Tests** — min/max, unicode/spaces, deny-list, client-only bypass, no truncation,
   change revokes sessions, rehash-on-login

## Good / Bad Examples

| Topic | Good | Bad |
| --- | --- | --- |
| Length | Min 12 (risk-based), max 128, no truncate | Max 16 + silent cut to 8 |
| Quality | Deny-list + breach check; any characters | Must include `!@#`; block paste |
| Rotation | On breach/reset/user request + session revoke | Force every 90 days only |
| Storage | argon2id + unique salt + rehash-on-login | `md5(password)` or shared salt |
| Login abuse | Lockout/rate limit companion policy | Unlimited online guesses |

**Good (illustrative):**

```
min_length: 12
max_length: 128
require_composition_classes: false
deny_list: [common, contextual, breached]
forced_periodic_rotation_days: null
hash: argon2id  # document m/t/p
```

**Bad:**

```
min_length: 8; must: [upper, lower, digit, special]; max_length: 16
rotate_every_days: 90; hash: sha256(password+username); block_paste: true
```

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Requirements, deny-lists, hashing policy, change UX | **This skill** | — |
| Attempt budgets, lock duration, unlock, stuffing | `account-lockout-design` | this for set-password rules |
| JWT alg/kid/claims, bearer misuse | `api-auth-and-jwt-abuse` | this if password issues tokens |
| Validators, hashers, tests, safe errors | `code-quality-standards` | **always** on code changes |
| Reset link Host/token poisoning | `password-reset-poisoning` | this for new-password rules |
| Full ATO beyond policy | `account-takeover-methodology` | this for password surface |

- **`account-lockout-design`:** what happens on failed **login/verify** attempts —
  not what makes a password acceptable to **set**.
- **`api-auth-and-jwt-abuse`:** post-login token trust boundary; not composition rules.
- **`code-quality-standards`:** server-side enforcement; no secrets in logs; constant-time
  verify; migration tests; non-enumerating login errors.

## Output Checklist

- [ ] Repo IdP/framework validators, hash stack, compliance overlays inventoried
- [ ] Min/max length set; no silent truncation; paste and managers allowed
- [ ] Composition theater avoided or justified only by a named external mandate
- [ ] Deny-list / breached-password screening designed (privacy-preserving if external)
- [ ] No calendar-only forced rotation; change revokes sessions/tokens
- [ ] Hash algorithm + parameters documented; rehash or migration plan
- [ ] Signup/change/admin-reset and error UX specified
- [ ] Login abuse routed to `account-lockout-design`
- [ ] Token risks routed to `api-auth-and-jwt-abuse` when JWTs used
- [ ] `code-quality-standards` applied for implementation, tests, logging
- [ ] Legacy conflicts surfaced for product/security sign-off
