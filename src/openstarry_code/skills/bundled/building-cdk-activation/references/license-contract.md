# Offline CDK License Contract

## Trust boundary

The issuer keeps the Ed25519 private key offline. The client embeds only the public key and verifies every token and every cached load. UI code receives an `ActivationResult`; it never parses claims or decides validity.

## Token envelope

Use a versioned three-segment form:

```text
<prefix>1.<base64url(canonical-json)>.<base64url(ed25519-signature)>
```

The product chooses `<prefix>`. Sign the ASCII bytes of `<prefix>1.<payload-segment>`. Base64url is unpadded and canonical: decode then re-encode and require exact equality.

The canonical JSON payload contains exactly:

| Field | Type | Rule |
|---|---|---|
| `product` | string | Exact compiled product identifier |
| `serial` | string | Unique issuer-generated identifier |
| `version_rule` | string | Explicit supported rule such as `*`, `1.x`, or `1.2.3` |
| `license_type` | string | `trial` or `permanent` |
| `duration_days` | integer/null | Positive integer for trial; null for permanent |

Serialize UTF-8 JSON with sorted keys and compact separators. Reject unknown/missing fields, non-canonical JSON, invalid UTF-8, oversized input, wrong product, unsupported version, invalid combinations, and forged/truncated signatures.

## Service result

The service maps outcomes to the activation states defined in `SKILL.md` and returns a user-safe message plus diagnostic code. Do not expose raw CDK values in logs.

## Cache

Persist the original token, UTC `activated_at`, and UTC `last_seen_at` under the current user's application-data directory. Write through a same-directory temporary file and atomic replace.

On every load:

1. Parse a strict document shape.
2. Reverify token signature and claims.
3. Recompute expiry from the first activation time.
4. Reject time earlier than `last_seen_at` beyond the documented clock tolerance.
5. Advance `last_seen_at` atomically only after successful validation.

Cache integrity is not secrecy. A purely offline CDK cannot reliably prevent sharing; document that product limitation instead of implying server-grade revocation.

## Key separation

Use separate key pairs for CDK issuance and update signing. Test keys must be generated at test runtime and must never match production public keys.
