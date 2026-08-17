---
name: grpc-security-testing
description: >
  Authorized gRPC security testing: service/method inventory, metadata auth,
  channel security (TLS/mTLS), interceptors, reflection abuse, message-level
  authz (IDOR), injection via fields, and gRPC-Web edge cases. Use when testing
  owned or in-scope gRPC/gRPC-Web APIs, labs, or CTFs — not unauthorized abuse
  of third-party services.
---

# gRPC Security Testing (Authorized)

## Scope And Authorization

- **In scope:** apps you own, written pentest/bug-bounty targets listing gRPC or gRPC-Web, and labs/CTFs.
- **Out of scope:** unauthorized reflection scans; stream/connection floods or DoS without capacity approval.
- Prefer staging and test accounts. Cap concurrent streams and message rates.
- Redact tokens, cookies, device IDs, and personal fields in reports. Keep derived captures separate from originals.
- Schema recovery from opaque bytes → primary `protobuf-grpc-reverse-engineering`; return here once RPCs are known.

## Use When

- Target speaks **gRPC** (`application/grpc`, HTTP/2), **gRPC-Web**, or gateway-transcoded gRPC.
- Need security properties: method authn/authz, metadata trust, TLS/mTLS, reflection, field IDOR — not pure wire RE.
- Keywords: gRPC security, server reflection, metadata bypass, gRPC-Web CORS, interceptors, unauthenticated RPC.

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Unknown Protobuf wire / schema recovery | `protobuf-grpc-reverse-engineering` |
| Designing `.proto` / package style | `protobuf-api-design` |
| JWT claim forgery in isolation | `api-auth-and-jwt-abuse` |
| HTTP/2 edge desync | `http2-specific-attacks` |

## Workflow

### 1. Inventory services and methods

1. Collect contracts: `.proto`, stubs, gateway maps, mobile/web assets, reflection (if authorized).
2. Build a method matrix: package, service, RPC, types, streaming kind, expected auth.
3. Note transport: plaintext vs TLS, edge proxy, gRPC-Web path prefix.

```bash
# Authorized lab — adjust host, certs, metadata
grpcurl -plaintext lab.example:50051 list
grpcurl -plaintext -d '{}' lab.example:50051 package.Service/Method
```

### 2. Channel and perimeter

| Check | Weak outcome |
| --- | --- |
| Cleartext on sensitive RPCs | Credentials/PII on wire |
| TLS / client cert validation | Bad certs accepted |
| mTLS required where designed | Optional cert still grants access |
| Public edge reaches internal admin RPCs | Privilege surface expanded |
| gRPC-Web Origin/CORS + cookies | Cross-site calls with session |

### 3. Authentication (metadata and peers)

Auth is often metadata (`authorization`), gRPC-Web cookies, or mTLS — not path ACLs alone.

| Check | Weak outcome |
| --- | --- |
| No credentials | `OK` instead of `UNAUTHENTICATED` |
| Expired/wrong token | Still accepted |
| JWT alg/claim abuse | Privileged RPC succeeds → `api-auth-and-jwt-abuse` |
| Client `x-user-id` / `x-role` trusted | Tenancy or privilege bypass |
| Wrong/missing client cert | Accepted as another principal |
| Interceptor gaps (service A only) | Unlisted RPC open |

### 4. Authorization per RPC

Authn ≠ authz. With two test accounts, mutate one resource/tenant/user id at a time:

- Cross-account read/update/delete on RPC args (BOLA on gRPC).
- Admin methods as normal user; list RPCs ignoring ownership.
- Streaming: wrong stream id; inject on bidi channels.
- Gateway JSON mass-assignment into privileged proto fields.

### 5. Input trust and reflection

- String/`bytes`/`Any` into SQL, command, template, or URL fetch sinks → `injection-checking` then class skill.
- Cap `repeated`/payload size in lab; stop at evidence of missing limits (no shared-prod crash).
- Public **Server Reflection**, Channelz, or debug services accelerate recon — restrict or auth-wrap in prod.

### 6. Remediation (implementers)

Apply `code-quality-standards` when fixing:

- Authenticate in interceptors first; **default deny** unknown methods.
- Authorize from server-side identity, not client `user_id` metadata alone.
- Disable public reflection; TLS everywhere; bound field sizes; pin JWT algorithms.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| gRPC authn/authz, reflection, channel testing | **This skill** | — |
| Opaque bodies / unknown schema | `protobuf-grpc-reverse-engineering` | this after decode |
| JWT/metadata token forgery | `api-auth-and-jwt-abuse` | this for RPC matrix |
| `.proto` style and compatibility | `protobuf-api-design` | this for threat review |
| Implementing interceptors/validation/tests | `code-quality-standards` | **always** on code fixes |
| TLS plaintext for captures | `tls-plaintext-acquisition` | this for tests |

### Shared skills

- **`protobuf-grpc-reverse-engineering`:** framing and candidate `.proto` from captures.
- **`api-auth-and-jwt-abuse`:** Bearer/JWT in metadata; retest RPCs with forged identity only if authorized.
- **`code-quality-standards`:** default-deny interceptors, validation, redacted logs, deny-path tests.

## Checklist

- [ ] Scope/environment recorded; secrets redacted
- [ ] Method matrix (streaming, gateway paths) complete
- [ ] TLS/mTLS/plaintext and public vs internal exposure noted
- [ ] Authn: missing, expired, spoofed metadata/peer cert
- [ ] JWT issues via `api-auth-and-jwt-abuse` when applicable
- [ ] Authz: cross-account IDs; streaming cases
- [ ] Reflection/debug exposure assessed
- [ ] gRPC-Web CORS/cookie notes if browser clients
- [ ] Injection/size findings with safe evidence
- [ ] Status codes per case; remediation linked to CQS

## Rules

- Authorized targets only; no third-party reflection or credential stuffing.
- One variable per probe; prefer status-code evidence over speculation.
- No volumetric floods without capacity scope.
- Unknown wire format → RE skill first.
