---
name: api-pagination-security
description: >
  Authorized testing of API pagination controls: offset vs cursor designs, max
  page size enforcement, authorization across pages, filter/sort injection via
  list params, total-count and metadata leaks, and cursor integrity/signing.
  Use when list endpoints expose page/offset/limit/cursor/after/before/pageSize,
  bulk exports, GraphQL connections, or scraped multi-page dumps need hardening.
---

# API Pagination Security

## Scope And Authorization

- Use only on systems you own, lab/CTF targets, or engagements with written authorization that names environments and data classes.
- Prefer dual test accounts under your control. Do not bulk-scrape third-party production lists or harvest PII beyond minimum proof.
- Cap page-size and page-count probes; stop before shared databases or search backends degrade. Pagination abuse testing is not a DoS skill.
- Keep HAR/PCAP originals immutable; store redacted request/response evidence separately.
- Redact tokens, cookies, signed cursors, device IDs, and personal fields in reports and samples.

## When To Use

- List/search/export endpoints accept `page`, `offset`, `limit`, `per_page`, `pageSize`, `cursor`, `after`, `before`, `starting_after`, or Relay `first`/`last`/`after`/`before`.
- Clients walk multi-page results, admin tables, mobile infinite scroll, or GraphQL connections.
- Suspected issues: oversized pages, predictable offsets into foreign data, unsigned/mutable cursors, filter injection via sort/filter query params, or `total`/`totalCount` leaking hidden inventory.
- After `api-recon-and-docs` maps list APIs but pagination ACL and resource bounds are unproven.
- Not primary for single-object IDOR without list context — hand object swaps to `idor-broken-object-authorization`. Not primary for pure SQLi/NoSQLi sinks once confirmed — hand to the matching injection skill.

## Workflow

1. **Inventory list surfaces**  
   From proxy history, OpenAPI, GraphQL schema, and mobile traffic, list every paginated endpoint. Record param names, defaults, response envelope (`items`, `data`, `edges`, `next`, `has_more`, `total`), auth context, and whether filters/sorts are client-controlled.

2. **Map the pagination model**

   | Model | Typical params | Security notes |
   | --- | --- | --- |
   | Offset/limit | `offset`/`skip` + `limit` | Easy skip into deep rows; expensive large offsets; stable only if sort is fixed |
   | Page index | `page` + `pageSize` | Same as offset (`(page-1)*size`); off-by-one and huge page tests |
   | Cursor/keyset | `cursor`/`after` + `limit` | Opaque token should bind query, sort, and ACL; not a raw row id alone |
   | Relay connection | `first`/`last` + `after`/`before` | Cap `first`/`last`; validate cursor against connection type |

   Capture one baseline page as User A with a known owned subset.

3. **Enforce max page size**  
   Request `limit`/`pageSize`/`first` at boundary values: default, documented max, max+1, 0, negative, very large (`999999`), and type confusion (`limit=1e9`, string, array). Confirm server clamps or rejects — never returns unbounded rows. Measure response size, row count, and latency; oversized pages are availability and data-exfil amplifiers.

4. **Authorization across pages (IDOR-adjacent)**  
   With User A and User B sessions:
   - Page through A’s list as B (and reverse): every page must apply the same ownership/tenant filter, not only page 1.
   - Jump deep: large `offset`/`page`, or B’s cursor replayed as A.
   - Change filter keys that imply ownership: `user_id`, `orgId`, `accountId`, `owner`, `tenant` while holding B’s token.
   - If any page returns foreign objects, treat as list-level BOLA and continue deep testing under **`idor-broken-object-authorization`** (object inventory, horizontal swap, batch/export surfaces).

5. **Cursor integrity and signing**  
   Decode cursors (Base64/URL-safe/JWT-like). Probe:
   - Mutate embedded ids, offsets, timestamps, or sort keys; re-encode and replay.
   - Strip signature / change alg if JWT-shaped; test none/empty signature only in-scope.
   - Reuse cursor from User A under User B’s session; reuse expired or post-delete cursors.
   - Swap cursor across endpoints or sort orders (orders cursor on invoices list).  
   **Expect:** server-signed or HMAC’d payload bound to subject/tenant, query fingerprint, and expiry; reject tampered or cross-user cursors with stable 4xx and no foreign rows.

6. **Filter, sort, and search injection via list params**  
   On `sort`, `orderBy`, `filter`, `q`, `where`, field allow-lists: try column names outside the schema, SQL/NoSQL fragments, nested operators (`$gt`, `$where`), and path traversal in field names. Confirm parameterized queries and allow-listed sort fields. If a sink is confirmed, hand off to `injection-checking` then the class skill (`sqli-sql-injection`, `nosql-injection`, etc.). Keep pagination primary when the issue is missing allow-lists or ACL on filtered pages rather than raw injection.

7. **Total count and metadata leaks**  
   Compare `total`, `totalCount`, `X-Total-Count`, `has_more`, empty-page behavior, and timing for:
   - Authenticated vs anonymous; User A vs B; filtered by foreign id.  
   Hidden totals can reveal inventory size, other tenants’ counts, or existence of resources (user enum via `filter=email:`). Prefer boolean `has_more` or ACL-scoped counts over global totals when data is sensitive.

8. **Consistency, exports, and secondary surfaces**  
   Re-test pagination on CSV/PDF export, admin “download all”, GraphQL nested connections, webhooks that fan out list fetches, and search-after-write. Look for export paths that ignore page caps or ACL applied only on the HTML/API first page.

9. **Remediation notes** (pair with `code-quality-standards`)  
   Cap page size server-side; prefer keyset/cursor over deep offset for large tables; sign and bind cursors; apply the same authZ predicate on every page and on count queries; allow-list sort/filter fields; avoid leaking cross-tenant totals; rate-limit expensive deep pages and exports (`api-rate-limit-design` / `rate-limit-bypass-testing` when adversarial).

## Routing

| Need | Skill |
| --- | --- |
| Map list endpoints, schemas, auth entry points | `api-recon-and-docs` |
| Per-object horizontal/vertical BOLA after list leak | **`idor-broken-object-authorization`** (hand off) |
| GraphQL connection/node ACL beyond pagination shape | `idor-graphql-nodes` / `graphql-and-hidden-parameters` |
| Confirmed SQLi/NoSQLi/filter injection sink | `injection-checking` → class skill |
| JWT/session broken authN on list APIs | `api-auth-and-jwt-abuse` |
| Quota / scrape throttle design or bypass | `api-rate-limit-design` / `rate-limit-bypass-testing` |
| Implement clamps, cursor MAC, ACL, tests | `code-quality-standards` |

### Hand-off to `idor-broken-object-authorization`

Keep **this skill primary** for page size, cursor crypto/binding, count leaks, and pagination param abuse. Switch to **`idor-broken-object-authorization`** when:

- Any page returns another user’s or tenant’s objects
- List filters accept foreign `user_id` / `orgId` and return those rows
- Export/batch list is a multi-object IDOR amplifier  
  Feed list endpoints and identifiers back into the IDOR object inventory.

## Output Checklist

- [ ] Scope, accounts, and list endpoints inventoried (params + envelope)
- [ ] Pagination model documented (offset / page / cursor / Relay)
- [ ] Max page size: clamp/reject evidence for oversize and edge values
- [ ] Cross-account multi-page results: same ACL on every page
- [ ] Cursor decode, tamper, cross-user, and cross-endpoint results
- [ ] Filter/sort allow-list tests; injection hand-off if sink confirmed
- [ ] Total/count/has_more leak notes (tenant/user enum risk)
- [ ] Export/secondary surface coverage
- [ ] Redacted proof pairs; remediation (cap, signed cursor, per-page ACL, scoped counts)
- [ ] Explicit hand-off to `idor-broken-object-authorization` when foreign objects appear

## Rules

- Authorized testing only; bound volume and page depth — do not degrade shared infra.
- Authentication ≠ authorization: a valid token must still scope every page and count query.
- Opaque cursors are not security unless integrity-protected and ACL-bound.
- Hash/UUID object ids reduce guessing but do not fix missing list filters.
- Test status **and** body; empty `200` with wrong totals still matters.
- One variable family per experiment (size vs cursor vs filter vs account).
- Report only findings reproducible with in-scope accounts and traffic.
