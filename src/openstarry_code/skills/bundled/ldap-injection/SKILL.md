---
name: ldap-injection
description: >
  Detect and safely test LDAP injection in directory search filters and bind
  DNs, including filter syntax metacharacters, boolean result differentials,
  and blind extraction discipline. Use when apps query Active Directory, OpenLDAP,
  or other LDAP directories with user-controlled usernames, emails, group filters,
  or search boxes during authorized assessments.
---

# LDAP Injection

## Scope And Authorization

- Authorized targets only: owned apps, labs, CTFs, or written engagement scope.
- Prefer boolean/result-set proofs over dumping entire directory trees.
- Avoid destructive binds, mass modify/delete operations, and lockout-prone auth storms on production.
- Redact DNs, emails, employee IDs, phone numbers, and service account names from reports.
- Rate-limit search probes; broad filters can stress directory infrastructure.

## When To Use

- Features that search people, groups, or devices against AD/LDAP (login, SSO attribute lookup, address book, “find user”, ACL builders).
- Parameters: `username`, `uid`, `cn`, `mail`, `sAMAccountName`, `filter`, `search`, `group`, `dn`.
- Errors or logs mention `javax.naming`, `ldap_search`, `InvalidSearchFilterException`, `LDAPException`, `Bad search filter`.
- `injection-checking` triage showed `*)(`, unbalanced parentheses, or directory-style errors rather than SQL/Mongo signals.
- White-box code builds filter strings with concatenation instead of parameterized/escaped APIs.

## Workflow

### 1. Baseline and filter surface map

1. Capture a clean search or login that hits the directory (proxy history + normal values).
2. Note success criteria: result count, user card fields, auth session, error text, timing.
3. Infer filter shape from docs/errors/code, e.g.  
   `(&(objectClass=user)(uid=INPUT))` or `(|(mail=INPUT)(cn=INPUT))`.
4. Identify whether input lands in **filter**, **DN**, or **attribute value** positions — metacharacter impact differs.

### 2. Filter syntax cheatsheet (what to inject)

LDAP search filters (RFC 4515 style) use parentheses and operators. User input that closes/opens clauses can change logic:

| Metachar | Role in filters |
| --- | --- |
| `*` | Wildcard (substring match) |
| `(` `)` | Grouping / clause boundaries |
| `&` `|` `!` | AND / OR / NOT |
| `\` | Escape introducer |
| NUL / control | Truncation or parser quirks (rare, legacy) |

**Escaping (correct server-side)** for filter values typically maps:

| Char | Escaped form |
| --- | --- |
| `*` | `\2a` |
| `(` | `\28` |
| `)` | `\29` |
| `\` | `\5c` |
| NUL | `\00` |

If the app does **not** escape, your probes alter the filter AST.

### 3. Detection probes (one change at a time)

Submit minimal mutations. Classic lab patterns (illustrative — adapt to observed filter):

| Goal | Example payload idea | Signal |
| --- | --- | --- |
| Wildcard broaden | `*` or `a*` | Far more results than baseline, or always-true login path |
| Clause break | `*)(uid=*` / `*)(|(uid=*` | Error, empty set flip, or full directory match |
| OR inject | `x)(|(uid=*` | Broader match than exact username |
| AND neutralize | `*)(objectClass=*` | Unexpected object classes returned |
| Boolean true-ish | `*)(&(objectClass=*)` style close/reopen | Auth or search succeeds without valid secret **only if** filter alone gates access |
| Comment-like trailing | `*)(cn=*` then junk | Differential vs invalid username |

Also test:

1. **Login vs search separately** — bind with fixed service account + injected search filter is more common than injected bind password.
2. **JSON/form dual** — same field via query string and JSON body if both accepted.
3. **Encoding** — URL-encoded `*`, `%00`, Unicode lookalikes only if the app decodes before LDAP.
4. **Attribute injection** — if client controls attribute list, attempt to request extra attrs only within SOW (minimize PII).

Success requires a **differential**: baseline exact match vs payload changes count, identity, or error class. One `500` alone is not LDAP injection.

### 4. Blind and restricted directories

When results are fixed-shape (yes/no login, constant error page):

1. **Boolean:** compare valid-user + payload that should always-match vs always-fail (wildcard vs impossible value).
2. **Content length / field presence:** some portals hide names but change JSON keys or avatar URLs.
3. **Timing:** only if necessary; directory latency varies — use ≥3 samples and short filters, not `(|(cn=a*)(cn=b*)…)` bombs.
4. Extract **minimum** proof (e.g. confirm filter control via own test account prefix) unless SOW allows broader enum.

### 5. DN injection and bind paths

1. If user input is concatenated into a DN (`cn=INPUT,ou=users,dc=…`), test RDN special characters (`,`, `+`, `"`, `\`, `<`, `>`, `;`) per DN escaping rules.
2. Prove impact as unexpected bind target or search base shift — not password guessing.
3. Do not attempt mass bind as arbitrary employees on production.

### 6. Differentiate related classes

| Observation | Route |
| --- | --- |
| SQLSTATE / `SELECT` syntax | `sqli-sql-injection` |
| Mongo `$ne` / JSON operators | `nosql-injection` |
| `${jndi:ldap://…}` in logs | `jndi-injection` (client lookup, not filter injection) |
| Object IDs without filter syntax | `idor-broken-object-authorization` |
| Unclear metachar class | `injection-checking` |
| Session/JWT after directory login | `api-auth-and-jwt-abuse` for token issues |

### 7. Code review and remediation

- Never string-build filters from raw input. Use framework escaping:  
  Java `encodeForLDAP` / proper `LdapName` + parameterized filter APIs;  
  .NET `LDAPFilter` helpers; Python `ldap3` / `python-ldap` filter builders with escape utilities.
- Allowlist expected attribute values (username charset) **and** escape.
- Least-privilege service bind; deny anonymous broad search in production.
- Return generic auth errors; do not reflect raw LDAP diagnostics to users.
- Retest original `*)(` payloads after fix; apply `code-quality-standards` to validation layers.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Class unknown | `injection-checking` | — |
| LDAP filter/DN injection confirmed | `ldap-injection` (this) | — |
| JNDI/Log4j LDAP lookup | `jndi-injection` | — |
| Post-auth object access by DN/id | `idor-broken-object-authorization` | this if filter widens objects |
| Broken token/session after LDAP login | `api-auth-and-jwt-abuse` | — |
| Implementation hardening | `code-quality-standards` | this |

## Output Checklist

- [ ] Endpoint, parameter, filter vs DN position
- [ ] Baseline vs payload differential (count/identity/error)
- [ ] Working metacharacters and hypothesized filter template
- [ ] Directory stack clues (AD/OpenLDAP/JNDI client)
- [ ] Blind method if used (boolean/timing stats)
- [ ] Impact scoped (auth bypass, data widen, attribute leak) with redactions
- [ ] Root cause (concatenated filter) and fix/retest

## Rules

- No unauthorized full-directory dumps or mass user enumeration beyond SOW.
- Prefer own test accounts and non-destructive search-only proofs.
- Respect lockout and rate limits; stop if directory latency spikes.
- One syntactic change per request for clean evidence.
- Do not confuse JNDI callback gadgets with application LDAP filter injection.
- Never claim LDAP injection from a single wildcard without control of logic/results.
