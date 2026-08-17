---
name: kerberos-spn-basics
description: >-
  Authorized basics for Kerberos Service Principal Names (SPNs): registration,
  format, ticket targeting, missing/duplicate SPNs, and service identity hygiene
  on owned Active Directory or lab domains. Use when apps fail negotiate/Kerberos
  SSO, setspn/AD attributes need review, or TGS issues for HTTP/CIFS/MSSQL/LDAP
  service identities are in an owned lab or engagement scope.
---

# Kerberos SPN Basics (Owned Environments)

Practical SPN literacy for **owned** Active Directory, hybrid lab, or CTF domains.
Focus: SPN format, ticket targeting, registration hygiene, and common misconfig
symptoms — not full Kerberos crypto or lateral-movement tradecraft.

## When To Use

- Browser or app SSO fails with **Negotiate/Kerberos** while NTLM still works.
- Need to map **which account** a service ticket targets (`HTTP/…`, `CIFS/…`, `MSSQLSvc/…`).
- Reviewing **`servicePrincipalName`**, `setspn`, or gMSA/computer identity for an
  owned web, file, SQL, or LDAP service.
- Diagnosing **duplicate SPNs**, wrong hostname/FQDN, or SPN on a user account that
  should be a computer/gMSA.
- Keywords: SPN, setspn, `servicePrincipalName`, TGS, sname, principal name, Kerberos SSO.

**Not primary for:** Windows host privesc chains → `windows-privilege-escalation`;
engagement planning → `recon-and-methodology`; SAML/OAuth → `saml-sso-basics` /
`oauth-oidc-misconfiguration`; JWT APIs → `api-auth-and-jwt-abuse`.

## Scope And Authorization

- **Owned domains, labs, CTFs, or written engagement scope only.** Do not enumerate
  or request tickets against third-party AD without permission.
- Prefer passive AD attribute review and client logs first. Active TGS requests,
  offline hash work (Kerberoasting-class), and delegation abuse need **explicit**
  authorization and named accounts/OUs.
- Treat tickets, keytabs, and service credentials as **secrets**: redact; store offline.
- Basics and hygiene only — not a playbook against production you do not own.

## Workflow

### 1. SPN model

```text
Client → AS (TGT) → TGS-REQ sname=SPN → KDC maps SPN to AD account
  → ST encrypted to that account → client AP-REQ to service
```

| Concept | Meaning |
| --- | --- |
| **SPN** | Service instance string (`class/host[:port][/…]`) |
| **Account** | User, computer, or gMSA that **owns** the SPN and decrypts the ST |
| **sname** | Service name in TGS-REQ — must match a registered SPN |
| **Realm** | Usually the AD domain (e.g. `CORP.EXAMPLE`) |

Common classes: `HTTP`, `HOST`, `CIFS`, `MSSQLSvc`, `LDAP`, `TERMSRV`.

### 2. Inventory expected SPNs

| Field | Capture |
| --- | --- |
| Hostnames clients use | NetBIOS, FQDN, aliases, VIP names |
| Service class | HTTP / CIFS / MSSQLSvc (+ port if required) |
| Run-as identity | Computer account, domain user, gMSA |
| Client path | Browser URL host, SQL host, UNC path |

The **hostname the client authenticates to** must appear in an SPN on the account
that actually runs the service.

### 3. Read registration (owned AD)

```text
setspn -Q */hostname*
setspn -L DOMAIN\account
# LDAP: servicePrincipalName on the object
```

Record: owning account per SPN; **duplicates** (same SPN on two objects); short name
vs FQDN clients use; orphans after rename/migration.

### 4. Symptom → hypothesis

| Symptom | Likely SPN issue |
| --- | --- |
| Falls back to NTLM; KRB errors | Missing SPN or SPN on wrong account |
| Intermittent / wrong principal | **Duplicate SPN** |
| Works by IP, fails by name (or reverse) | No SPN for that name; Kerberos needs names |
| Ticket for unexpected account | SPN registered on a different identity |
| Service rejects ticket | Clock skew, wrong realm, host mismatch |

Validate with **one** controlled client (good account, clear DNS): confirm TGS for the
expected SPN via klist/protocol log — no mass scanning.

### 5. Hygiene and remediation

| Practice | Guidance |
| --- | --- |
| Unique registration | One SPN → one account; purge stale/duplicates |
| Match client names | Every Kerberos alias/FQDN needs an SPN |
| Prefer computer/gMSA | Avoid long-lived user passwords on SPN accounts |
| Ports | Include `:port` when the stack requires it (SQL) |
| Least privilege | No interactive admin on service identities; rotate |

Illustrative shapes: `HTTP/app.corp.example`, `HTTP/app`, `MSSQLSvc/sql01.corp.example:1433`.

**Security awareness (authorized only):** user accounts with SPNs and weak passwords
enable Kerberoasting-class offline work if TGS can be requested; mis-registration can
steer tickets to a rogue account; extra aliases expand that identity’s surface. Prefer
reporting uniqueness, password policy, and unnecessary user SPNs over weaponized steps.

Ops: align SPNs with DNS/URLs; after renames re-register and purge; recycle services
and keytabs; monitor unexpected `servicePrincipalName` changes.

## Routing

| Need | Skill |
| --- | --- |
| SPN format, registration, ticket target basics | **This skill** |
| Windows host privilege escalation (lab) | `windows-privilege-escalation` |
| Engagement planning / passive recon | `recon-and-methodology` |
| SAML / OAuth enterprise SSO | `saml-sso-basics` / `oauth-oidc-misconfiguration` |
| JWT audience/issuer or API auth | `jwt-audience-issuer-checks` / `api-auth-and-jwt-abuse` |
| Secure service-account implementation notes | `code-quality-standards` |

**Selection:** primary when the issue is **which principal name Kerberos uses** and
how AD maps SPN → account. Hand full AD attack chains to privesc/recon under scope.

## Output Checklist

- [ ] Authorization: owned/lab domain or named accounts/hosts in scope
- [ ] Client names (URL/UNC/SQL host) and service class documented
- [ ] Expected owning account (computer / user / gMSA) identified
- [ ] Registered SPNs listed; duplicates and orphans called out
- [ ] Symptom linked to missing, wrong-account, or duplicate SPN with evidence
- [ ] klist/client log shows expected SPN TGS or clear failure reason
- [ ] Hygiene: unique SPNs, FQDN coverage, least-privilege service identity
- [ ] Tickets/hashes/keytabs redacted; security notes only within scope
- [ ] Remediation: re-register, purge stale, prefer gMSA, monitor SPN changes
