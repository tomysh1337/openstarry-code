---
name: deserialization-safe-formats
description: >
  Defensive guidance for safe interchange formats and deserializers: prefer
  JSON, Protobuf, and schema-bound codecs over pickle, native Java serialization,
  BinaryFormatter-class APIs, and unrestricted YAML load. Use when choosing or
  hardening serializers, reviewing untrusted payload parsers, configuring
  allowlists/ObjectInputFilters/safe loaders, migrating off native object graphs,
  or remediating insecure deserialization without exploit gadgets.
---

# Safe Deserialization Formats

Choose **data formats and library settings** that cannot execute code or
reconstruct arbitrary types from untrusted bytes. Prefer **schema-bound,
non-executable** interchange over language-native object serialization.
Defense and authorized hardening only — no gadget chains or RCE PoCs.

## Scope And Authorization

- **In scope:** Formats, parsers, and library config in systems you own or are
  authorized to design, review, or harden.
- **Out of scope:** Weaponized gadget delivery, ysoserial-style payloads, or
  testing third-party systems without written authorization.
- For **authorized sink finding and safe confirmation**, use
  `deserialization-insecure` — not this skill as an attack playbook.
- Redact tokens, session blobs, and personal data from reports and examples.
- Prefer lab or non-production traffic when validating parser changes.

## When To Use

- Designing APIs, queues, caches, cookies, or file imports that accept structured
  payloads from untrusted or semi-trusted sources
- Replacing or reviewing **pickle**, `yaml.load`, Java `ObjectInputStream`,
  PHP `unserialize`, .NET `BinaryFormatter` / weak ViewState, Ruby `Marshal`
- Configuring **allowlists**, type filters, SafeLoader, Jackson polymorphic
  typing off, or schema validation at the boundary
- Migrating internal RPC/cache formats to **JSON, Protobuf, MessagePack, or
  CBOR** with explicit DTOs
- Remediation after a deserial finding: “use safer format / config” as the fix
- Pairing with `input-validation-patterns` and `json-schema-design` for bounds
  and contracts

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Finding / safely proving insecure deserial sinks | `deserialization-insecure` |
| JNDI/LDAP lookup strings (Log4Shell-class) | `jndi-injection` |
| JSON Schema / OpenAPI field design | `json-schema-design` |
| General allowlists at HTTP boundaries | `input-validation-patterns` |
| Authorized injection class triage | `injection-checking` |

## Workflow

### 1. Map trust boundaries and formats

1. List every path that **parses bytes/text into objects**: HTTP body, cookie,
   header, queue/Kafka/JMS, Redis/cache, RPC, admin import, CLI, mobile offline
   store.
2. Tag each path: **untrusted client**, peer service, or same-process only.
3. Record current codec (JSON, Protobuf, pickle, Java serial, YAML, XML, custom).
4. Note integrity controls (TLS only vs HMAC/AEAD over opaque tokens).

### 2. Prefer non-executable interchange

| Preference | Use for | Avoid for untrusted input |
| --- | --- | --- |
| **JSON** + schema/DTO | Public APIs, configs, events | — (still validate shape/size) |
| **Protobuf / gRPC** | Service RPC, versioned binary APIs | Dynamic “any type” without bounds |
| **MessagePack / CBOR** | Compact binary DTOs with schema | Codec modes that embed code/types |
| **YAML** | Human configs from **trusted** operators only | Network payloads; never unrestricted load |
| **Native object serial** | None across trust boundaries | Pickle, Java serial, BinaryFormatter, Marshal, PHP unserialize of user data |

**Rule:** If the format can instantiate **arbitrary classes** or run
**reducers/magic methods**, it is not an untrusted-input format.

### 3. Library configuration (when a risky API remains)

Only if migration is blocked short-term; treat as debt with an exit plan.

| Stack | Safer config direction |
| --- | --- |
| Python | `json` / pydantic / msgspec; **never** `pickle` on network/cache boundaries; `yaml.safe_load` only (or SafeLoader); ban `yaml.load` without loader |
| Java | Prefer JSON (Jackson **without** default typing) or Protobuf; if `ObjectInputStream` unavoidable: **JEP 290 `ObjectInputFilter`** allowlist; avoid `XMLDecoder` for untrusted XML; harden XStream allowlists |
| Jackson / polymorphic JSON | Disable default typing; explicit `@JsonTypeInfo` only with **allowlisted** subtypes |
| PHP | Prefer `json_decode` + DTOs; if `unserialize` remains: `allowed_classes` allowlist; block Phar in user-controlled paths |
| .NET | Prefer System.Text.Json / Protobuf; do **not** use `BinaryFormatter` for untrusted data; protect ViewState with MAC + app secrets |
| YAML (any language) | Safe/core loaders only; no custom tags that construct objects |
| Node | Prefer JSON + schema (Zod/AJV); avoid packages that `eval` or revive functions from serialized form |

### 4. Allowlists, schemas, and bounds

1. Decode to a **fixed DTO / schema**, not `Object` / `Any` / open maps driving logic.
2. Allowlist **enums, message types, and polymorphic discriminators**; reject unknown types fail-closed.
3. Cap **size, depth, array length**, and decode time (DoS from hostile graphs).
4. Integrity: sign or AEAD-encrypt opaque client-held blobs; bind to user/session
   where needed — signing does not make pickle safe; still use safe formats.
5. Validate after decode (`input-validation-patterns`); contracts via
   `json-schema-design` or `.proto` as SSOT.

### 5. Migrate and verify

1. Introduce safe reader alongside old format if needed; version field or content-type.
2. Stop writing native-serial forms; dual-read only for a defined window.
3. Remove risky sinks and dependencies when unused.
4. Tests: accept golden safe payloads; reject oversize, unknown types, and
   wrong content-type; no gadget fixtures in product repos.
5. Apply `code-quality-standards` on implementation (errors, limits, no secret logs).

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Safe format choice, allowlists, library hardening, migration off native serial | **This skill** | — |
| Authorized deserial sink discovery / impact class | `deserialization-insecure` | this for remediation |
| Boundary allowlists / size caps / fail-closed parse | `input-validation-patterns` | this for codec choice |
| JSON Schema / OpenAPI shapes | `json-schema-design` | this for “JSON not pickle” policy |
| Protobuf/gRPC schema recovery (RE) | `protobuf-grpc-reverse-engineering` | this for service hardening |
| JNDI strings / log lookup | `jndi-injection` | — |
| Implementation quality, tests, error paths | `code-quality-standards` | **always** on code changes |

## Output Checklist

- [ ] Trust boundaries and codecs inventoried (who can send bytes)
- [ ] Untrusted paths use JSON/Protobuf/schema-bound codecs — not pickle/Java serial/unrestricted YAML/BinaryFormatter-class APIs
- [ ] Residual risky APIs have allowlists/filters/safe loaders and tracked removal
- [ ] Polymorphic typing disabled or subtype-allowlisted
- [ ] Schema/DTO validation + size/depth caps at parse boundary
- [ ] Opaque client blobs integrity-protected **and** still non-executable format
- [ ] Migration/dual-read plan and removal of dead serial sinks
- [ ] Positive/negative parse tests; no weaponized gadget artifacts
- [ ] Remediations aligned with `deserialization-insecure` findings when from assessment
- [ ] `code-quality-standards` applied on parser/config changes
