# Signed Static Update Contract

## Manifest

Host a UTF-8 JSON document over HTTPS. The signed payload contains exactly these fields:

```json
{
  "schema_version": 1,
  "product": "example-product",
  "channel": "stable",
  "version": "1.2.3",
  "published_at": "2026-07-14T00:00:00Z",
  "release_notes_url": "https://updates.example.com/releases/1.2.3",
  "package": {
    "url": "https://updates.example.com/packages/setup-1.2.3.exe",
    "size": 12345678,
    "sha256": "64-lowercase-hex-characters",
    "signature": "base64url-ed25519-signature"
  }
}
```

`package.signature` signs the 32-byte SHA-256 digest represented by `package.sha256`; this permits bounded-memory streaming verification of large installers. Distribute the manifest itself with a detached Ed25519 signature (for example `manifest.json.sig`) over the exact downloaded bytes. Do not place the detached manifest signature inside the signed document.

## Validation order

1. Fetch manifest with size/time limits and no credential forwarding.
2. Inspect every redirect; require HTTPS and an explicit hostname allowlist for the final URL.
3. Verify detached manifest signature before parsing trusted decisions.
4. Parse exact schema; require product, `stable`, semantic version, UTC timestamp, positive size, lowercase SHA-256, and HTTPS URLs.
5. Compare versions with a semantic-version library or a small tested comparator, never lexicographically.
6. Download to a random same-volume temporary file with size limits and cancellation.
7. Verify exact size, SHA-256, package Ed25519 signature, then Authenticode status and expected publisher identity.
8. Atomically rename to a ready path; only then expose install.

When using `validate-update-manifest.ps1`, always pass the compiled product identifier as `-ExpectedProduct`; the running client also passes `-CurrentVersion`. Package validation additionally requires the exact expected Authenticode certificate subject through `-ExpectedPublisher`.

Reject downgrade and same-version replacement by default. If a repair workflow is required, design and test it separately rather than weakening version checks.

## Installation and recovery

- Pass only fixed, application-owned installer arguments.
- Launch from the trusted background process, record non-sensitive evidence, then exit cleanly.
- Keep the current installation usable until the external installer commits its transaction.
- On cancellation or failure, delete partial/untrusted files and return to a retryable state.
- Never let activation status suppress update checks or validation.

## Hosting checklist

- Separate update-signing and CDK-signing keys.
- Restrict upload permissions; immutable versioned package paths are preferred.
- Publish manifest last after package upload and verification.
- Preserve old full installers for rollback/support, but never advertise them as newer.
