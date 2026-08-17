---
name: protobuf-api-design
description: >
  Design and evolve Protobuf/gRPC API contracts: package and naming style,
  field numbers, types, oneof/map/repeated rules, compatibility, errors,
  pagination, and service layout. Use when writing or reviewing .proto files,
  gRPC service APIs, buf/lint rules, or schema evolution — not for offensive
  wire reverse engineering alone.
---

# Protobuf API Design

Style guide for **Protobuf messages and gRPC services** as long-lived contracts.
Repository `buf` lint, package layout, and existing design docs outrank defaults
below. Do not introduce a second style mid-repo without an explicit migration.

## Use When

- Authoring or reviewing `.proto` files, gRPC services, or shared message packages
- Choosing field types/numbers, `oneof`/`map`/`repeated`, enums, nested messages
- Planning additive evolution, `reserved` fields, or breaking-change policy
- Aligning errors, pagination, and resource names with org standards
- Keywords: Protobuf API design, `.proto` style, gRPC service design, `buf lint`,
  field numbers, proto compatibility, AIP-style resources

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Recovering unknown schemas from captures | `protobuf-grpc-reverse-engineering` |
| Authorized gRPC authn/authz testing | `grpc-security-testing` |
| JWT/metadata attack techniques | `api-auth-and-jwt-abuse` |
| HTTP/JSON REST versioning paths | `api-versioning-design` |
| JSON Schema / OpenAPI-only models | `json-schema-design` |

## Repo Config First

1. **Lint/breaking:** `buf.yaml`, `buf lint`, `buf breaking`, CI gates
2. **Packages:** `company.product.v1`, directory mirrors package
3. **Codegen:** edit authoritative `.proto` only — never hand-edit generated stubs
4. **Style source:** Google AIPs / internal docs; copy mature neighbor protos
5. **Errors/auth annotations:** `google.rpc.Status`, HTTP mappings if dual-protocol

Repo rules win; surface conflicts that break wire compatibility.

## Workflow

1. **Domain boundary** — resources, standard RPCs (Get/List/Create/Update/Delete/Custom), public vs internal package ownership.
2. **Package version** — `example.billing.v1` under matching dirs; mint `v2` only for intentional breaks; avoid unversioned public APIs.
3. **Services and RPCs** — one service per bounded context; verb+noun RPCs; dedicated `*Request`/`*Response` types per RPC.
4. **Field numbers** — never reuse meaning; `reserved` removed numbers/names; frequent fields in 1–15 when optimizing tags.
5. **Types** — opaque string names or documented integer IDs; money as minor units or decimal string + currency (never float); `google.protobuf.Timestamp`; enums for closed sets.
6. **Composition** — paginated `repeated`; `map` for key/value; `oneof` for exclusive variants; avoid deep JSON-shaped nesting.
7. **Compatibility** — additive: optional field, new RPC, new enum value (if clients tolerate unknowns). Breaking: renumber, type change, remove without `reserved`. Document unknown-enum policy.
8. **Errors and lists** — consistent gRPC statuses; List uses `page_size`/`page_token`/`next_page_token`; no unbounded dumps.
9. **Docs, CI, security shape** — comment public RPCs; lint+breaking+codegen one-way; no secrets in examples; no client `user_id` as sole authz; bound `bytes`/`repeated` (`code-quality-standards`); separate admin RPCs (`grpc-security-testing` for live tests).

## Design Rules (defaults when repo is silent)

| Element | Convention |
| --- | --- |
| Package | `org.product.area.v1` lowercase |
| Messages / services / RPCs | `UpperCamelCase` |
| Fields | `lower_snake_case` |
| Enum values | `ENUM_VALUE_UNSPECIFIED = 0` first |
| Files | `lower_snake_case.proto` |

- Prefer proto3 `optional` when unset vs default matters; avoid proto2 `required`.
- Keep `Any` rare; prefer concrete types or `oneof`. Dual REST/gRPC: same authz on both paths.

## Good / Bad Examples

**Good**

```protobuf
syntax = "proto3";
package example.billing.v1;

message Invoice {
  string name = 1;       // invoices/{invoice_id}
  int64 total_cents = 2;
  string currency_code = 3;
  reserved 4;
  reserved "legacy_total";
}

enum InvoiceState {
  INVOICE_STATE_UNSPECIFIED = 0;
  INVOICE_STATE_DRAFT = 1;
  INVOICE_STATE_PAID = 2;
}
message GetInvoiceRequest { string name = 1; }
service InvoiceService {
  rpc GetInvoice(GetInvoiceRequest) returns (Invoice);
}
```

**Bad** — unversioned package, float money, unclear RPC identity, zero enum is a real state:

```protobuf
package billing;
message Invoice { double total = 1; }
enum InvoiceState { DRAFT = 0; PAID = 1; }
service S { rpc Get(Invoice) returns (Invoice); }
```

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| `.proto` / gRPC contract design | **This skill** | — |
| Wire recovery / unknown schema | `protobuf-grpc-reverse-engineering` | this when cleaning recovered protos |
| Live gRPC security testing | `grpc-security-testing` | this for contract fixes |
| JWT/metadata under test | `api-auth-and-jwt-abuse` | `grpc-security-testing` |
| Implementing servers/clients/tests | `code-quality-standards` | **always** on code changes |
| REST version path/header policy | `api-versioning-design` | this for dual packages |

### Shared skills

- **`protobuf-grpc-reverse-engineering`:** field recovery from captures; then apply this skill’s naming/`reserved` rules.
- **`api-auth-and-jwt-abuse`:** keep resource authz from collapsing to forgeable claims alone.
- **`code-quality-standards`:** boundary validation, default-deny interceptors, redacted logs, compatibility tests.

## Checklist

- [ ] Lint/breaking config and version strategy identified
- [ ] Service/RPC layout and naming match neighbors
- [ ] Field numbers stable; removals use `reserved`
- [ ] Safe types (money, time, IDs, `_UNSPECIFIED = 0`)
- [ ] Pagination; intentional `oneof`/`map`/`repeated`
- [ ] Additive vs breaking classified; `v2` if breaking
- [ ] Errors documented; comments on public RPCs; CI green
- [ ] Authz-friendly shapes; `code-quality-standards` on implementation

## Rules

- Wire compatibility beats cosmetic renames; prefer new fields over renumbering.
- Generated code is not source of truth; schema validity is not authorization.
- Recovered protos: validate with `protobuf-grpc-reverse-engineering` before locking numbers.
