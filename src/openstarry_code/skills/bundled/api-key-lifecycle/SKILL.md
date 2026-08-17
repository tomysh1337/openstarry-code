---
name: api-key-lifecycle
description: >
  Design and operate the API key lifecycle: create, issue, store references,
  dual-run rotate, revoke, and audit. Use when API key creation, rotation,
  revocation, key grace periods, key metadata (prefix/last4/scopes), emergency
  kill switches, or partner/machine credentials need a controlled lifecycle on
  owned or authorized systems.
---

# API Key Lifecycle

Own **create → issue → use → rotate → revoke** for long-lived API keys (service,
partner, machine credentials). Prefer org vaults and existing key tables.
Defensive design for owned/authorized systems only.

## When To Use

- Adding or redesigning **API key mint, list, rotate, revoke** endpoints or admin UX
- Planning **dual-running** rotation (old + new valid for a grace window) or emergency kill
- Modeling **key metadata**: `kid`/prefix, last4, scopes, owner, env, expiry, last-used
- Post-leak or offboarding: **revoke first**, then inventory consumers and logs
- Distinguishing **opaque API keys** from JWT/session auth
- Keywords: API key lifecycle, rotate/revoke key, grace period, `X-Api-Key`,
  sk_live, partner key, machine credential

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Vault/SM, .env, secret scanning, org-wide secret policy | `secrets-management-hygiene` |
| JWT alg/kid/claim abuse, Bearer crypto, session forgery | `api-auth-and-jwt-abuse` |
| Implementation reliability, tests, logging hygiene | `code-quality-standards` |
| Rate limits keyed by API key | `api-rate-limit-design` |
| OAuth client secrets / AS flows | `oauth-oidc-misconfiguration` |

## Repo Config First

Repo and platform conventions **outrank** defaults below.

1. **Existing key store:** DB tables, Secrets Manager, vault, gateway consumers—**extend** them
2. **Hashing and display:** hash (or HSM-wrapped) at rest; plaintext **once** on create/rotate; prefix/last4 for UI
3. **Transport:** `Authorization: Bearer` vs `X-Api-Key`; ban query-string keys if the repo already does
4. **Scope model:** roles, product scopes, env (live/test), optional IP allowlists in ADRs
5. **Admin authz:** who may mint/rotate/revoke (org admin, project owner, break-glass)
6. **Audit sinks:** SIEM/audit fields for key events (never full secret)
7. **Neighbors:** match monorepo prefix format, grace TTL, error codes

**Precedence:** Follow the repo on conflict. Surface plaintext-at-rest, keys in
git/query strings, or rotate-without-retiring previous material.

## Workflow

### 1. Inventory

| Field | Capture (no full secret in tickets) |
| --- | --- |
| Identity | `key_id`, public prefix, last4 |
| Owner / env | team/service, tenant, test vs live, scopes |
| Consumers | services, CI, partners that present the key |
| State / store | active, grace, revoked, expired; table/vault path; last_used_at |

### 2. Create (mint)

1. Authorize mint under least privilege; require purpose/owner.
2. Generate high-entropy secret server-side (CSPRNG); never accept client-chosen secrets.
3. Persist **hash** + metadata; return plaintext **once**.
4. Attach scopes, env, optional expiry and allowlist.
5. Audit `key.created` with `key_id`, actor, scopes—not the secret.
6. Deliver via one-time UI/vault write; never email/Slack plaintext.

### 3. Use (verify)

1. Read key from approved header only; reject body/query unless legacy exception.
2. Constant-time hash compare; accept only `active`/`grace`.
3. Enforce scope per route; update `last_used_at` without logging raw key.
4. Fail closed on revoked/expired; stable error code.

### 4. Rotate (dual-run)

1. Mint **new** material; keep old in **grace** for a documented window.
2. Update consumers (deploy, partner notice, vault version) to the new secret.
3. Verify traffic on new `key_id`/prefix; monitor 401 rate.
4. Retire old: grace → **revoked**; no unlimited dual validity.
5. Audit `key.rotated` linking old/new ids, actor, grace_until.

### 5. Revoke

| Trigger | Action |
| --- | --- |
| Offboarding / contract end | Revoke; confirm consumers stopped |
| Suspected leak | **Immediate revoke**; rotate survivors; review access logs |
| Scope shrink | Mint narrower key, then revoke the broad one |
| Shared-key compromise | Revoke shared; split to per-consumer keys |

Mark revoked server-side (authoritative). Reject on next request. Audit
`key.revoked` with reason. After leak: revoke-first via `secrets-management-hygiene`.

### 6. Implement (`code-quality-standards`)

Hash at rest; timing-safe verify; no secret in logs/metrics/traces. Tests:
create-once display, grace accepts both, post-revoke rejects, scope deny,
concurrent rotate. Authz on mint/rotate/revoke; document partner runbook and grace end.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| API key create / rotate / revoke / grace / metadata | **This skill** | — |
| Vault, .env, scanning, org secret inventory, leak IR | `secrets-management-hygiene` | this for key-shaped credentials |
| JWT/Bearer crypto, alg confusion, session tokens | `api-auth-and-jwt-abuse` | this only if opaque API keys coexist |
| Code, tests, safe logging, error handling | `code-quality-standards` | **always** on implementation |

- **`secrets-management-hygiene`:** vault/git/scanning/leak IR. This skill owns
  API key **product lifecycle** (mint, dual-run, revoke, metadata).
- **`api-auth-and-jwt-abuse`:** JWT/session crypto—not opaque key hash verify.
  Do not relabel missing JWT `exp` as “API key rotation.”
- **`code-quality-standards`:** always on mint/verify/rotate code, admin authz,
  tests, and redaction.

Keep **this skill primary** for key lifecycle; switch for full vault design or JWT attacks.

## Output Checklist

- [ ] Inventory: ids, owners, env, scopes, store, state (no plaintext secrets)
- [ ] Repo store, hash scheme, header contract, admin authz confirmed
- [ ] Create: CSPRNG, hash-at-rest, one-time plaintext, audit event
- [ ] Verify: approved transport, constant-time, scopes, no secret logging
- [ ] Rotate: dual-run grace documented; consumers updated; old retired on schedule
- [ ] Revoke: immediate server-side kill; leak path prioritizes revoke-before-writeup
- [ ] Audit events for create/rotate/revoke with actor and key_id only
- [ ] Tests for grace, revoke, scope deny, concurrent rotate
- [ ] Routed: storage/leak → `secrets-management-hygiene`; JWT → `api-auth-and-jwt-abuse`; code → CQS

## Rules

- Plaintext secret shown **at most once**; store hashes or envelope-encrypted material only.
- **Revoke before** documenting a live leaked value in tickets or chat.
- Prefer **per-consumer** keys; finite owned grace (unlimited dual keys ≠ rotation).
- Redact secrets; correlate with prefix/last4/`key_id`. Authorized systems only.
