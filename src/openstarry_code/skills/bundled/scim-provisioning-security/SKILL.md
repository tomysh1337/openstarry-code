---
name: scim-provisioning-security
description: >
  Authorized assessment and hardening of SCIM 2.0 user/group provisioning:
  token auth, endpoint exposure, filter/PATCH abuse, privilege via attributes,
  deprovisioning gaps, and cross-tenant isolation. Use when SCIM, /Users,
  /Groups, ServiceProviderConfig, bulk provisioning, IdP-to-app sync, or
  automated account lifecycle appears in scope for owned or authorized apps.
---

# SCIM Provisioning Security

Methodology for **SCIM 2.0** (RFC 7643/7644) provisioning APIs that IdPs use to
create, update, disable, and delete users and groups in a service provider (SP).
Focus: trust boundary, authZ, attribute safety, and lifecycle.

## Scope And Authorization

- **Authorized only:** owned apps, labs, CTFs, or written scope naming the SCIM
  base URL, tenant, and IdP connector you may exercise.
- Prefer **staging** and disposable canary users. No mass-create/delete or
  production workforce corruption outside approved change windows.
- Treat SCIM bearer tokens, Basic credentials, client secrets, and full
  User/Group payloads as **secrets** — redact in tickets and reports.
- Do **not** use discovered tokens against third-party SaaS tenants you do not
  own. Cross-tenant probes need explicit multi-tenant scope.
- Destructive tests (DELETE, hard wipe, Bulk) need prior approval; prefer
  `active:false` and reversible PATCH on canaries.
- Assessment and **defensive design** only — not persistent backdoors or shadow admins.

## When To Use

| Situation | Direction |
| --- | --- |
| App exposes SCIM `/Users`, `/Groups`, `/Schemas`, `/ServiceProviderConfig`, `/Bulk` | **This skill** |
| IdP **auto-provisions** accounts into the app | **This skill** |
| Orphan accounts, delayed deprovision, or role-sync bugs | **This skill** |
| SCIM token weak, leaked, or SCIM base missing auth | **This skill** |
| SAML/OIDC login only (no provisioning API) | `saml-sso-basics` / `oauth-oidc-misconfiguration` |
| End-user object access (not IdP SCIM principal) | `idor-broken-object-authorization` |
| ATO where SCIM is one path | `account-takeover-methodology` + this skill |
| Token vault/rotation only | `secrets-management-hygiene` |

Keywords: SCIM 2.0, externalId, userName, active, PATCH, filter, Bulk, provisioning token, deprovision, IdP sync.

## Workflow

### 1. Map the surface

1. Find base URL (`/scim/v2`, `/api/scim/v2`) via docs, IdP connector, or `api-recon-and-docs`.
2. GET `ServiceProviderConfig`, `Schemas`, `ResourceTypes` — note patch, filter, bulk, auth schemes.
3. Record auth (Bearer, OAuth client credentials, Basic, mTLS) and tenant routing (path/host/token).
4. List which IdP attributes map to roles/groups/custom extensions.

### 2. Authentication and transport

| Check | Secure expectation | Probe (authorized) |
| --- | --- | --- |
| Auth required | All routes 401/403 without creds | Strip `Authorization` on GET/POST/PATCH/DELETE |
| Token strength | High entropy; not in JS/mobile/public git | Search assets and configs for leaked tokens |
| Scope | One tenant + SCIM only | Reuse token on other tenants if multi-tenant in scope |
| TLS | HTTPS only | Confirm no cleartext SCIM |
| Rotation | Revoke path works | Old token fails after rotate |
| Audit | Writes attributed to connector | Create canary; verify audit entry |

**Findings:** unauthenticated SCIM, global multi-tenant token, client-exposed secret, or public SCIM when policy requires private access.

### 3. Authorization and isolation

1. Token for tenant A must not read/write tenant B (cross-tenant IDOR).
2. Predictable `/Users/{id}` must not leak other customers under a mis-scoped token.
3. End-user sessions must **not** reach SCIM admin APIs.
4. Group membership changes must stay inside tenant and mapped roles.

Hand residual end-user BOLA to `idor-broken-object-authorization`.

### 4. Create / PUT / PATCH attribute safety

On canaries only:

| Risk | Test idea | Secure behavior |
| --- | --- | --- |
| Privilege attrs | Set `roles`, `admin`, entitlements, custom flags | Allowlisted IdP mapping; server-side authZ |
| Schema extensions | Unexpected `urn:...` attrs | Ignore/reject; no silent superuser |
| userName / externalId clash | Victim identifiers on create | Unique constraints; no silent merge ATO |
| Email linking | Provision email of existing local user | Explicit link policy |
| Immutable fields | Mutate `id` / `externalId` | Reject |
| PATCH ops | `add`/`replace`/`remove` on members, active, nested paths | No illegal privilege strip/add |

### 5. Filter, list, deprovision, bulk

- **List/filter:** pagination; PII minimization; multi-tenant filters return empty/403; rate limits on full directory dump.
- **Filter input:** quotes/parens/`or` as validation tests only — document errors vs leaks; no out-of-scope DB attacks.
- **Deprovision:** `active:false` and (if approved) DELETE must block app login **and** revoke sessions/refresh tokens/PATs within SLA; group removal drops privileges; rehire same `externalId` has no leftover admin.
- **Bulk:** auth on `/Bulk`; partial failure behavior; no cross-tenant side effects.
- **Errors:** no stack traces, other-tenant ids, or secrets in bodies.
- **Idempotency:** repeated POST same `externalId` must not fork divergent privileges.

### 6. Remediation (report-ready)

- Tenant-scoped, rotatable SCIM credentials in vault (`secrets-management-hygiene`); mTLS or short-lived OAuth when available.
- Network-restrict SCIM (private link / IdP egress allowlist) when feasible.
- Allowlist provisioned attributes; explicit group→role maps; no free-form admin from optional schemas.
- Unique `userName`/`externalId`; documented account-link rules for matching emails.
- Deprovision = disable **plus** revoke sessions/tokens; audit every SCIM write.
- Paginate/rate-limit list/filter; minimize PII in responses.
- Maintained SCIM libraries + `code-quality-standards` for auth middleware.

## Routing

| Need | Skill |
| --- | --- |
| SCIM auth, attrs, deprovision, filter/bulk | **This skill** |
| SAML SSO assertion/ACS | `saml-sso-basics` |
| OAuth/OIDC interactive login | `oauth-oidc-misconfiguration` |
| App user JWTs after provision | `api-auth-and-jwt-abuse` |
| End-user object IDOR | `idor-broken-object-authorization` |
| API discovery | `api-recon-and-docs` |
| SCIM token storage/rotation | `secrets-management-hygiene` |
| ATO chaining incl. rogue provision | `account-takeover-methodology` |
| Implementation baseline | `code-quality-standards` |

## Output Checklist

- [ ] Scope covers SCIM URL, tenant, and IdP connector used
- [ ] ServiceProviderConfig / Schemas / auth scheme documented
- [ ] Unauthenticated and cross-tenant results recorded
- [ ] Token exposure/scope/rotation noted (values redacted)
- [ ] Attribute/role probes on canaries (add/replace/remove)
- [ ] userName/externalId uniqueness and account-link behavior
- [ ] Filter/list pagination, limits, cross-tenant filter results
- [ ] Deprovision vs live session/token access after disable
- [ ] Bulk auth and partial-failure behavior (if present)
- [ ] Audit evidence for create/update/disable
- [ ] Impact + remediations (scoped token, allowlist attrs, revoke-on-disable)
- [ ] No mass-delete; no third-tenant abuse; PII redacted
