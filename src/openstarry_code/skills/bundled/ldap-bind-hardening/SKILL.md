---
name: ldap-bind-hardening
description: >
  Harden and assess LDAP/AD directory binds for owned systems: disable anonymous
  and unauthenticated binds, prefer LDAPS or StartTLS, least-privilege service
  accounts, simple vs SASL bind choices, AD LDAP signing/channel binding, lockout-
  safe auth, and secret hygiene for bind credentials. Use when reviewing OpenLDAP,
  Active Directory, FreeIPA, or app LDAP client config (bind DN, service account,
  plain LDAP on 389) during authorized hardening or config review — not for
  unauthorized directory attacks or credential stuffing third-party LDAP.
---

# LDAP Bind Hardening

Harden **how clients authenticate to LDAP directories** (bind phase) for systems
you own or are explicitly authorized to assess. Focus on transport, bind types,
service-account privilege, and client configuration — not filter injection
(`ldap-injection`) or full AD attack paths.

## Scope And Authorization

- **In scope:** org-owned AD/OpenLDAP/FreeIPA, app LDAP clients, lab/CTF directories,
  config/IaC review under written engagement.
- **Out of scope:** mass anonymous bind scans; password spraying or lockout storms
  on production; unauthorized directory object modification.
- Prefer **config review and non-destructive probes** (`whoami`, rootDSE) with lab
  credentials. Gate bind-as-user testing behind SOW and rate limits.
- Redact bind DNs, passwords, service accounts, and employee IDs in reports. Keep
  secrets out of VCS (`secrets-management-hygiene` when applicable).
- Do not weaken production TLS or re-enable anonymous bind without change control
  and rollback.

## When To Use

- Reviewing app/middleware LDAP settings: bind DN/password, base DN, `ldap://` vs
  `ldaps://`, StartTLS flags, connection pools
- Directory allows **anonymous bind**, unauthenticated bind, or cleartext simple
  bind on routable networks
- Service accounts use Domain Admin / full subtree write for “read-only” app login
- AD guidance mentions **LDAP signing**, **channel binding**, or simple bind over
  unsigned LDAP
- Hardening checklists for IdP/SSO backends that still bind to AD/LDAP
- Differentiating from **LDAP injection** (filter/DN strings) and **JNDI** gadgets
  (`jndi-injection`)

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Filter/DN injection in search strings | `ldap-injection` |
| `${jndi:ldap://…}` / Log4Shell-style lookups | `jndi-injection` |
| JWT/session issues after directory login | `api-auth-and-jwt-abuse` |
| Secret storage/rotation of bind passwords | `secrets-management-hygiene` |
| App code reliability around LDAP clients | `code-quality-standards` |
| Multi-vector account takeover chaining | `account-takeover-methodology` |

## Workflow

### 1. Inventory binds and trust paths

1. List directories: host, ports (389/636/3268/3269), AD vs OpenLDAP, forest/domain.
2. List **bind clients**: apps, VPN/RADIUS, mail, CI, legacy scripts, admin tools.
3. Record bind mode: anonymous, simple (DN+password), SASL (GSSAPI/EXTERNAL),
  unauthenticated (DN without password — should usually be rejected).
4. Note shared credentials across env (dev==prod) or secrets checked into repo.

### 2. Transport: never leave simple bind in the clear

1. Prefer **LDAPS (636)** or **StartTLS on 389** before any password simple bind.
2. Validate server cert (CA trust, hostname/SAN); reject skip-verify in production.
3. On AD, treat **LDAP signing** and **channel binding** as first-class controls.
4. Restrict ports with firewall/SG/private DNS — no public 389/636 unless required
   and TLS-enforced.

### 3. Disable weak bind types

| Control | Hardened direction |
| --- | --- |
| Anonymous bind | Off in production; allow only with tight ACLs if product-required |
| Unauthenticated bind | Reject (DN present + empty password must not become effective auth) |
| Guest / well-known weak accounts | Disabled or ACL-denied for network binds |
| Simple bind without TLS | Forbidden on non-localhost paths |
| Over-broad ACLs after bind | Read-only, least attributes; no write for app binds |

Config cues: OpenLDAP `olcDisallows: bind_anon`, `olcRequire: authc`; AD LDAP
signing requirements + channel binding GPO/registry; apps force `ldaps://` or
StartTLS with cert validation.

### 4. Service account least privilege

1. Dedicated bind account per app/environment; no shared “ldap-admin” for apps.
2. Grant **search/read** on required OUs/attributes only; deny modify/delete/reset.
3. Prefer gMSA/machine identity or vault-rotated secrets over static passwords.
4. If user-bind is required, enforce TLS, lockout-aware retries, generic errors.
5. Log failed binds with rate limits; never log plaintext passwords.

### 5. Client review and safe verification

1. No bind passwords in source, Compose, or world-readable env samples.
2. Timeouts, pool limits, referral handling documented; user-facing errors generic.
3. Retest with authorized accounts; apply `code-quality-standards` to clients.
4. Authorized checks only: anonymous `whoami` fails or is unprivileged; cleartext
   simple bind blocked; service account search limited; modify/delete denied.
5. No password sprays, mass enum binds, or lockout tests on shared prod without
   explicit approval and monitoring.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| LDAP/AD bind transport, anonymous bind, service privilege | **This skill** | — |
| Filter/DN injection in application queries | `ldap-injection` | — |
| JNDI LDAP URL lookups / deserialization gadgets | `jndi-injection` | — |
| Bind password lifecycle, vault, rotation | `secrets-management-hygiene` | this skill |
| Client libraries, IaC, LDAP connectivity tests | `code-quality-standards` | this skill |
| Broader ATO across reset/session/IdP | `account-takeover-methodology` | this if bind is a vector |
| SAML SSO assertion issues (not LDAP bind) | `saml-sso-basics` | — |

## Output Checklist

- [ ] Scope/authorization recorded; only in-scope directories exercised
- [ ] Inventory of directory endpoints, ports, and bind clients
- [ ] Bind types documented (anonymous / simple / SASL / unauthenticated)
- [ ] TLS path verified (LDAPS or StartTLS + cert validation) for password binds
- [ ] AD signing/channel binding (or OpenLDAP equivalent) status noted
- [ ] Anonymous and unauthenticated binds disabled or justified with ACLs
- [ ] Service accounts least-privilege; no shared admin bind for apps
- [ ] Secrets not in git; rotation path identified
- [ ] Non-destructive verification evidence (whoami, ACL deny on write)
- [ ] Residual risks and hand-offs (`ldap-injection`, `secrets-management-hygiene`)
