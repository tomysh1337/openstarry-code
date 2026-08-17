---
name: graphql-schema-design-style
description: >
  Design and evolve GraphQL schemas (SDL/code-first): types, nullability,
  connections, mutations, errors, and versioning style. Use when GraphQL schema
  design, SDL review, GraphQL API modeling, Relay connections, input types, or
  schema evolution—not for offensive GraphQL recon alone.
---

# GraphQL Schema Design Style

Standards for **GraphQL schema shape and evolution**: types, fields, arguments,
nullability, pagination, mutations, and error contracts. Prefer the repo’s
GraphQL stack and neighboring types. This is **design**, not live-endpoint recon.

## Use When

- Authoring or reviewing GraphQL SDL, code-first schemas, or schema modules
- Modeling objects, interfaces, unions, enums, inputs, and custom scalars
- Choosing nullability, pagination (Relay vs offset), and mutation payloads
- Evolving a public GraphQL API without silent breaks; aligning resolvers/codegen
- Triggers: GraphQL schema design, SDL, connections, mutation design, nullability

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Authorized GraphQL recon, introspection abuse, node BOLA | `graphql-and-hidden-parameters` |
| OpenAPI/REST operation prose and examples | `api-documentation-writing` |
| JSON Schema / OpenAPI `components/schemas` design | `json-schema-design` |
| Resolver authz, limits, tests, reliability | `code-quality-standards` |

## Repo Config First

Repo stack and neighboring types **outrank** defaults below.

1. **Stack:** Apollo, Yoga, Hot Chocolate, graphql-java, Absinthe, Hasura, federation
2. **Source of truth:** SDL-first vs code-first vs generated — edit only the authority
3. **Codegen:** client/server configs, fragment policy, scalar maps
4. **Conventions:** `PascalCase` types, `camelCase` fields, layout, `@auth`/`@deprecated`/`@key`
5. **Pagination & errors:** Relay vs offset; stable `extensions.code` taxonomy
6. **Auth model:** context + field directives vs resolver-only — do not fork
7. **Neighbors:** copy 2–3 mature domains for IDs, inputs, mutation payloads

**Precedence:** Follow the repo on conflict. Surface changes that break clients,
hide authz only via “secret” fields, or diverge published schema from runtime.

## Workflow

1. **Map domain** — resources, ownership, read vs write, clients.
2. **Inventory schema** — types, roots, scalars, deprecations, federation keys.
3. **Model reads** — explicit object types; interfaces/unions only when polymorphism is real.
4. **Nullability** — `Type!` only when always provided on promised success; list forms
   (`[Item!]!` vs `[Item]!`) chosen intentionally (empty vs null list).
5. **Inputs/mutations** — separate `CreateXInput`/`UpdateXInput`; never reuse output
   types as inputs; prefer `…Payload` (`entity`, `userErrors`) for extensibility.
6. **Pagination** — match repo; growing public lists → cursor/Relay + page-size caps.
7. **IDs** — stable opaque IDs (Relay global ID or UUID/ULID), not raw internal ints.
8. **Errors** — document GraphQL errors vs field-null + `extensions`; keep `code` stable.
9. **Evolve** — add optional fields/args; `@deprecated(reason:)` with replacement;
   no silent renames or nullability tightenings without dual-run/version plan.
10. **Verify** — schema lint, codegen, resolver tests; authz/complexity via
    `code-quality-standards`. Live security testing → `graphql-and-hidden-parameters`.

## Design Rules (defaults when repo is silent)

| Area | Prefer |
| --- | --- |
| Naming | Noun types; clear mutations (`updateOrderStatus`) |
| Inputs | Dedicated input objects; sparse documented custom scalars |
| Enums | Machine values; document tolerance for additive future values |
| Descriptions | Non-obvious elements; prose quality → `api-documentation-writing` |
| Lists | Connections or hard limits — no unbounded root lists |
| N+1 | Assume DataLoader/batching for list→child fields |

## Good / Bad Examples

**Good**

```graphql
type Order { id: ID!, note: String, items: [OrderItem!]! }
type Query { order(id: ID!): Order }
input UpdateOrderInput { id: ID!, note: String }
type UpdateOrderPayload { order: Order, userErrors: [UserError!]! }
type Mutation { updateOrder(input: UpdateOrderInput!): UpdateOrderPayload! }
```

**Bad**

```graphql
type Query { orders: [Order!]! }          # unbounded; over-non-null list
type Order { note: String! }              # fails whole parent when missing
type Mutation { updateOrder(order: OrderInput!): Order }
input OrderInput { id: ID, totalCents: Int, isAdmin: Boolean }  # output-as-input + mass-assign
```

**Good deprecation:** dual field + `@deprecated(reason: "Use displayName…")`.  
**Bad:** rename in place with no dual field or sunset.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| GraphQL schema shape, nullability, connections, mutations | **This skill** | — |
| Authorized live GraphQL testing (introspect, BOLA, batching) | `graphql-and-hidden-parameters` | this when hardening schema |
| Description prose quality | `api-documentation-writing` | this for type graph |
| REST/JSON Schema / OpenAPI models | `json-schema-design` | this only for GraphQL |
| Resolvers, authz, validation, tests, query limits | `code-quality-standards` | **always** on implementation |

- **`graphql-and-hidden-parameters`:** recon/abuse of live GraphQL; return here for schema fixes.
- **`api-documentation-writing`:** description quality; this skill owns SDL structure.
- **`json-schema-design`:** REST/event JSON — do not force OpenAPI idioms onto GraphQL.
- **`code-quality-standards`:** resolver authz, depth/complexity, DataLoader, tests,
  no secrets in error extensions.

## Checklist

- [ ] Stack, source of truth, codegen, and auth directives identified
- [ ] Neighbor naming, IDs, pagination, and mutation payloads matched
- [ ] Nullability intentional (field and list); growing lists capped/connected
- [ ] Inputs separate from outputs; no privileged fields without product+authz design
- [ ] Extensible mutation payloads; stable error `code`s; descriptions on non-obvious fields
- [ ] Additive evolution + `@deprecated`; schema/codegen/resolvers aligned
- [ ] Authz and complexity planned (`code-quality-standards`)
- [ ] Authorized review via `graphql-and-hidden-parameters` when in scope
- [ ] Prose → `api-documentation-writing`; REST twins → `json-schema-design`
