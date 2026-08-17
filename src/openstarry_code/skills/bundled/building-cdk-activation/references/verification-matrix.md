# Verification Matrix

## CDK core

| Case | Expected |
|---|---|
| Valid permanent token | Active, no expiry |
| Valid trial token | Active until first-activation time plus duration |
| Missing/unknown claim | Rejected |
| Trial without positive duration | Rejected |
| Permanent with duration | Rejected |
| Forged, truncated, non-canonical token | Rejected |
| Wrong product or unsupported version | Rejected |
| Modified cache/token | Cache ignored or locked; never active |
| Clock before last trusted time | `clock_rollback` |
| Restart after activation | Same valid state after complete revalidation |

## Update core

| Case | Expected |
|---|---|
| No/newer/same/older version | Up-to-date/available/rejected replacement/rejected downgrade |
| Wrong schema/product/channel/version | Rejected before download |
| Invalid manifest signature | Rejected before trusted parsing |
| Redirect to non-allowlisted or non-HTTPS host | Rejected |
| Size/hash/package signature mismatch | Temporary file deleted |
| Authenticode invalid or wrong publisher | Installation blocked |
| Network interruption/cancel/disk full | Retryable failure and cleanup |
| Installer launch failure | Current version remains usable |
| Unactivated/expired/corrupt license | Update still works |

## UI and concurrency

- Activation submit is disabled for empty input and while validating.
- Duplicate check/download/install actions cannot overlap.
- Background update check does not block startup, activation, navigation, or rendering.
- Error, cancel, retry, progress, ready, and install-confirmation states are visible and keyboard accessible.
- Narrow layout stacks controls without clipping status or release notes.
- UI process cannot supply arbitrary path, URL, shell command, or installer arguments.

## Release evidence

- Run targeted tests first, then the full suite and production build.
- Scan source, artifacts, logs, fixtures, and CI output for private-key material.
- Record manifest bytes/signature, package SHA-256, Authenticode publisher, commands, timestamps, and exit codes.
- Test at least one real upgrade from the oldest supported version to the candidate release in a disposable VM.
