---
name: graphql-persisted-queries
description: >
  GraphQL persisted and allowlisted queries: Automatic Persisted Queries (APQ),
  trusted-document / operation allowlists, hash registration, full-query bypass,
  and production hardening for Apollo, Relay, and similar clients. Use when
  traffic shows extensions.persistedQuery, sha256Hash operation IDs, persisted
  query manifests, allowlisted documents, or you must assess whether the server
  enforces hash-only mode versus accepting arbitrary query bodies.
---

# GraphQL Persisted Queries

## When To Use

- Client traffic uses `extensions.persistedQuery` (Apollo APQ), `documentId`,
  operation hashes, or a build-time persisted-query manifest instead of full
  GraphQL text on every request.
- Keywords: persisted queries, APQ, Automatic Persisted Queries, trusted
  documents, operation allowlist, query allowlisting, sha256Hash, persisted
  query not found, GET APQ, Relay persisted queries.
- Hardening review: public SPA/mobile must not send free-form `query` strings;
  CI registers an allowlist; gateway rejects unknown hashes.
- After `graphql-and-hidden-parameters` notes hashes in bundles, or after
  `graphql-query-complexity` flags cost only if open query mode remains.

**Not primary for:** schema recon / BOLA / injection (handoff skills); depth and
field-cost scoring (`graphql-query-complexity`); array batch / alias limits
(`graphql-batching-limits`); generic API inventory (`api-recon-and-docs`).

## Workflow

### 1. Detect mode and transport

1. Capture honest client requests. Classify each endpoint as:
   - **Hash-only (strict allowlist):** body has `extensions.persistedQuery` or
     `documentId` / hash fields; no free-form `query` accepted.
   - **APQ hybrid:** first request may send full `query` + hash to register;
     later requests send hash only.
   - **Open mode:** full `query` always accepted; hashes optional (CDN/cache).
2. Note method: POST JSON vs GET with query-string `extensions` (common for APQ
   caches). Record auth: anonymous, cookie, Bearer.
3. Sample hash algorithms and encoding (usually SHA-256 hex of the query text).
   Match hashes from JS bundles / mobile assets to known operations when useful.

### 2. Test allowlist enforcement (authorized, low volume)

| Probe | Expected if strict | Finding if weak |
| --- | --- | --- |
| Known good hash only | 200 / normal data | — |
| Unknown / random hash | PersistedQueryNotFound or 4xx | Silent ignore or fallback |
| Full expensive or admin `query` body without hash | Rejected | **Allowlist bypass** |
| Full `query` + matching hash (APQ register) | Rejected in prod | Runtime registration open |
| Mutated body, same hash | Rejected (hash must bind body) | Hash not verified |
| GET APQ vs POST | Same policy | Method-split bypass |

1. Replay a client hash with **no** `query` field; confirm resolution from store.
2. Send a minimal non-allowlisted document as full `query` (e.g. `{ __typename }`
   or a safe test field). If accepted, document **open query surface**.
3. For APQ: send full document once with `extensions.persistedQuery.sha256Hash`
   then hash-only. Note who may **persist** (anonymous vs authed vs disabled).
4. Try hash of operation A with variables/body of operation B only if the
   protocol allows mixed fields — prove binding integrity without inventing
   crypto attacks.
5. If batching is enabled, ensure each array element still hits the allowlist
   (`graphql-batching-limits` for multipliers).

### 3. Map registration and trust boundary

1. Find how documents enter the allowlist: build artifact (safest), CDN manifest,
   admin API, or automatic first-seen APQ.
2. Runtime APQ registration on public endpoints = deferred arbitrary-query surface
   (complexity, authZ, and introspection still apply later via hash).
3. Review storage: in-memory, Redis, DB, CDN. Stale or world-writable stores
   undermine the allowlist.
4. Confirm production **disables** free-form queries for untrusted clients even
   when developers use full queries in staging.

### 4. Client and gateway checklist

- Prefer **build-time trusted documents** (Relay/persisted manifest, Apollo
  operation registry) over open APQ registration for internet-facing APIs.
- If APQ remains for cache warming: require auth, signed upload, or private
  network to register; public path hash-only.
- Bind rate limits and cost to **operation id/hash** as well as IP/user.
- Keep **depth/complexity limits** and resolver authZ even for allowlisted ops
  (allowlist reduces novelty, not IDOR or expensive listed fields).
- Disable or restrict introspection in production; allowlist does not replace it.
- Log unknown-hash rate, full-query rejects, and registration attempts.

### 5. Remediation summary

1. Production public clients: **reject** bodies with free-form `query` unless on
   an explicit break-glass allowlist (admin network).
2. Ship a signed/versioned operation manifest; deploy server allowlist with app.
3. Turn off automatic persist from untrusted clients; or gate registration hard.
4. Verify hash of canonical query text; reject mismatch.
5. Pair with cost/depth limits and per-operation authZ; implement with
   `code-quality-standards`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Persisted / allowlisted ops, APQ, hash-only enforcement | **This skill** | — |
| Schema recon, hidden fields, GraphiQL | `graphql-and-hidden-parameters` | this when hashes appear |
| Depth / cost / nested DoS | `graphql-query-complexity` | this for allowlist posture |
| Array batch / alias multiplication | `graphql-batching-limits` | this if batch skips allowlist |
| GraphQL node/edge IDOR | `idor-graphql-nodes` | allowlisted ops still need authZ |
| API surface map missing | `api-recon-and-docs` | then this skill |
| Implement server plugins / clients | `code-quality-standards` | always on code changes |

## Output Checklist

- [ ] Endpoint(s), methods (GET/POST), auth mode
- [ ] Mode: hash-only / APQ hybrid / open full-query
- [ ] Hash field names and algorithm (if observable)
- [ ] Full-query without allowlist: accept vs reject (evidence)
- [ ] Registration path: build-time, admin, or public APQ
- [ ] Hash–body binding and unknown-hash error behavior
- [ ] Interaction with batching (if present)
- [ ] Client manifest / bundle hash samples (paths only; redact tokens)
- [ ] Remediation: strict allowlist, no public runtime persist, keep cost+authZ
- [ ] Handoffs: complexity, batching, IDOR, recon as needed
- [ ] Artifacts redacted; originals immutable

## Scope And Authorization

- Authorized assessments, labs, CTFs, and systems you own or are contracted to
  harden only. Do not register or flood hashes on third-party production without
  written scope.
- Prefer staging for registration and bypass probes. On shared prod: minimal
  documents, low rate, stop at clear accept/reject evidence — no cache-store
  exhaustion or mass registration.
- Redact tokens, cookies, operation variables with PII, and internal type names
  when required. Treat manifests and full operation lists as sensitive maps of
  the API surface.
- Persisted queries reduce arbitrary GraphQL text; they do **not** replace field
  authZ, input validation, or cost limits. Report residual risk honestly.
