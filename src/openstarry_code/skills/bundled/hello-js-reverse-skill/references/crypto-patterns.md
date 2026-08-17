# Signature Format Triage and Canonicalization

Use output shape to decide what to inspect next, not to name an algorithm.

## Format Rules

| Observation | Honest conclusion | Required verification |
|---|---|---|
| Even-length hexadecimal | Hex-encoded bytes | Trace the producer and compare known input with intermediate bytes |
| Canonical Base64 with padding or `+`/`/` | Base64 encoding is plausible | Decode, re-encode, and locate the encoding call |
| URL-safe `-` or `_` alphabet | Base64url encoding is plausible | Decode, re-encode, and locate the encoding call |
| Fixed output length | The producer emits a fixed-size value | Compare multiple inputs; fixed length does not identify a digest, MAC, cipher, or token |
| Three dot-separated URL-safe segments | Compact token structure is plausible | Decode structure and validate the actual signing flow separately |

Do not classify a hexadecimal value as Base64 merely because its characters also belong to the Base64 alphabet. Do not infer encryption from decoded byte length or block-size divisibility.

Use `scripts/crypto-identifier.js` for this format triage. Its candidates intentionally contain no algorithm confidence score.

## Recover the Pre-Transform Bytes

For each sample, record:

1. The complete input object before canonicalization.
2. Included and excluded keys, duplicate keys, and key order.
3. Empty, missing, `null`, boolean, numeric, array, and object handling.
4. JSON separators, property order, escaping, and repeated serialization.
5. URL encoding, including reserved characters and space as `+` or `%20`.
6. Unicode normalization and the exact text-to-byte encoding.
7. Timestamp units, clock source, nonce, counter, and random input.
8. Cookie, token, device, and browser-derived inputs with provenance.
9. The exact byte buffer entering the decisive transform.
10. The final output encoding and case.

Compare intermediate values after changing one field. Only implement a direct Node.js or Python replay after the browser and replay agree on the pre-transform bytes.

## Verification Standard

A hypothesis is supported only when it reproduces multiple captured samples and succeeds from a clean or reset baseline. A matching output shape is not validation.
