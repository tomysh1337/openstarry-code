---
name: idor-graphql-nodes
description: >-
  GraphQL node/edge object-level authorization (BOLA/IDOR): Relay global IDs,
  nested resolvers, connections, mutations, and field-level leaks. Use when
  node(id), edges, or ID arguments appear under GraphQL and classic REST IDOR
  coverage is incomplete. Authorized assessments only.
---

# GraphQL Node / Edge IDOR

## Scope And Authorization

- Use only on systems you own, labs, CTFs, or engagements with written scope that includes GraphQL endpoints and test data classes.
- Prefer dual test accounts (User A / User B) plus a cross-tenant or lower-privilege account when allowed. Do not bulk-export foreign PII beyond minimal proof.
- Store schema dumps and HAR captures as sensitive artifacts; redact tokens, cookies, emails, and internal IDs in reports.
- Throttle alias/batch enumeration. Avoid production DoS via deep nested queries unless capacity testing is explicit.
- Destructive mutations (delete, transfer ownership, billing) need an explicit exception in the test plan.

## Use When

- Traffic or schema shows `node(id:)`, `nodes(ids:)`, Relay global IDs, or connection/edge patterns (`edges { node { ... } }`).
- Root queries take `id` / `uuid` / `slug` and nest sensitive fields (`user`, `order`, `paymentMethod`, `internalNote`).
- Mutations update or delete by ID while the UI only exposes “owned” objects.
- After `graphql-and-hidden-parameters` maps operations but node/edge **authZ** is unproven.
- After `idor-broken-object-authorization` covers REST but GraphQL nested resolvers remain untested.
- Not primary for pure JWT/crypto failures (`api-auth-and-jwt-abuse`), injection in args (`injection-checking`), or WebSocket subscriptions auth after upgrade (`websocket-authz-deep` / `websocket-security`).

## Workflow

1. **Inventory ID-bearing surfaces**  
   From introspection, client operations, or proxy history, list every place an object is selected:

   | Surface | Examples |
   | --- | --- |
   | Root query | `user(id:)`, `order(id:)`, `node(id:)` |
   | Batch | `nodes(ids:)` , aliases `a: user(id:"1")` |
   | Connection | `viewer { orders(first:) { edges { node { id } } } }` |
   | Nested field | `order { customer { email ssn } }` |
   | Mutation | `updateOrder(id:, input:)`, `deleteNode(id:)` |
   | Subscription | `orderUpdated(id:)` (hand long-lived channel auth to WS skills) |

   Tag each ID as owned / shared / admin for account A and B. Decode Relay global IDs (`base64("TypeName:dbId")`) only to understand type confusion risk — ACL still applies per type.

2. **Dual-session fixtures**  
   Capture honest queries as A for A-owned nodes. Hold B’s session (cookie or Bearer) separately. Never mix tokens. Record baseline field sets so over-fetch is measurable.

3. **Horizontal node swap (core GraphQL BOLA)**  
   Replay A’s ID under B’s auth:

   ```graphql
   query {
     node(id: "A_RELAY_ID") {
       ... on Order { id total status customer { email } }
     }
     order(id: "A_RAW_ID") { id total }
   }
   ```

   Expect deny (null + auth error, or 200 with null field) — not full foreign data. Test **status and body**: GraphQL often returns HTTP 200 with partial errors.

4. **Edge and nested resolver authZ**  
   Root may authorize while children leak:

   ```graphql
   query {
     me {
       friends(first: 50) {
         edges {
           node {
             email phone privateNotes
             orders { id total }   # friend → their orders?
           }
         }
       }
     }
   }
   ```

   Also try: start from a legit parent B can see, then walk edges to A-only children; cross-link `order(id:A) { organization { secrets } }`. **Every resolver** that returns an object must re-check principal vs object.

5. **Type confusion and global ID tricks**  
   - Swap type prefix: encode `AdminUser:1` / `Order:A` variants the server might resolve without ACL.  
   - Pass raw DB ids where Relay IDs expected (and reverse).  
   - `nodes(ids: [A, B, C])` under B — note which indices return data (batch ACL gaps).  
   - Interface/union fragments: `... on AdminProfile` on a node B should not see.

6. **Mutations and partial success**  
   As B, run `update*`, `delete*`, `addEdge`, `invite`, `transfer` with A’s IDs. Confirm no silent partial apply (edge created but field error elsewhere). Re-fetch as A to prove integrity. Prefer read-only proof first.

7. **Alias and batch ACL gaps**  
   One HTTP request, many aliased foreign reads; JSON array batching if enabled. Document whether authZ/rate limits are per-operation or per-HTTP-request. Stay within attempt budgets.

8. **Field-level and error oracles**  
   Forbidden fields returning “not found” vs “not authorized” can enumerate IDs. Error `extensions` that echo internal ids or stack traces are secondary findings. Prefer one clean A/B pair over noisy sweeps.

9. **Evidence and remediation notes**  
   Save operation name, variables, redacted response, and account matrix. Remediation: authorize in resolvers or a central authZ layer **per node type and edge**; never trust client type labels in global IDs; apply same checks to mutations and subscriptions; complexity limits do not replace ACL.

## Routing

| Need | Skill |
| --- | --- |
| Classic BOLA methodology, dual-account matrix | `idor-broken-object-authorization` |
| Schema recovery, hidden args, batching survey | `graphql-and-hidden-parameters` |
| Subscription transport / post-upgrade authZ | `websocket-security`, `websocket-authz-deep` |
| JWT/session broken authN | `api-auth-and-jwt-abuse` |
| Implement resolver ACL / deny-by-default | `code-quality-standards` |

## Checklist

- [ ] Scope and test accounts documented (A/B/tenant)
- [ ] ID surface inventory (root, node/nodes, edges, mutations)
- [ ] Horizontal swap: B reads A’s node (status + body + errors)
- [ ] Nested/edge resolver tests (parent allowed, child foreign)
- [ ] `nodes(ids:)` / alias batch behavior recorded
- [ ] Relay/global ID and type-confusion attempts
- [ ] Mutation IDOR results or explicit read-only scope
- [ ] Field-level leak / error-oracle notes
- [ ] Proof pair saved redacted; remediation: per-resolver object ACL
