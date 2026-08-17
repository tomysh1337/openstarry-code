---
name: cloud-metadata-ssrf-defenses
description: >
  Defend applications and workloads against SSRF that reaches cloud instance
  metadata (IMDS): block link-local targets, enforce IMDSv2/hop limits, harden
  URL fetchers, and reduce role blast radius. Use when hardening against
  169.254.169.254, metadata.google.internal, Azure IMDS, webhook/preview SSRF
  defenses, or cloud credential theft via SSRF — authorized/org-owned systems.
---

# Cloud Metadata SSRF Defenses

Design and verify **defenses** that stop SSRF from reaching **cloud metadata
(IMDS)** and exfiltrating temporary credentials. Defensive hardening only.

## Scope And Authorization

- **In scope:** Org-owned apps/workers/proxies/serverless/VMs/containers where
  URL fetch or open egress could hit IMDS; authorized review; own-project labs.
- **Out of scope:** Third-party cloud accounts; dumping/using foreign IMDS creds;
  cloud API pivots beyond agreed validation.
- Prefer verifying **controls** over retrieving live role credentials. Accidental
  exposure: stop, secure evidence, **rotate/revoke**, redact reports. Offensive
  proofs without fixes → `ssrf-server-side-request-forgery`; this skill owns
  **defense design and verification**.

## Use When

- Server-side user URL fetch (webhooks, previews, importers, PDF/HTML, SSO
  metadata URL, unfurl) on cloud-hosted workers
- Hardening AWS **IMDSv2**, hop limit, or disabling IMDSv1
- GCP/Azure metadata headers and workload identity alternatives
- Egress policies, link-local denies, egress proxies, or role blast-radius cuts
- Mentions: cloud metadata SSRF, IMDS hardening, `169.254.169.254`

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Offensive SSRF testing / bypass catalog | `ssrf-server-side-request-forgery` |
| CI OIDC keys and pipeline secret stores | `secrets-in-ci-pipelines` / `ci-cd-pipeline-patterns` |
| General vault and .env hygiene | `secrets-management-hygiene` |
| Implementation quality baseline for fetch code | `code-quality-standards` |

## Why Metadata Matters

| Provider | Defense-relevant notes |
| --- | --- |
| AWS | `169.254.169.254` — IMDSv2 + hop limit 1; note `169.254.170.2` task channels |
| GCP | `metadata.google.internal` — requires `Metadata-Flavor: Google` |
| Azure | `169.254.169.254` — requires `Metadata: true` and API version |
| Containers | Prefer IRSA/WIF/pod identity over fat node roles via host IMDS |

Impact: temporary cloud credentials → actions allowed by the attached role.
Layer: no arbitrary URL fetch, block metadata, harden IMDS, minimize roles.

## Workflow

### 1. Map fetchers and compute identity

1. Inventory server-side HTTP/TCP paths driven by user input (URL params,
   webhooks, server-followed redirects).
2. Note runtime (EC2, ECS/EKS, Cloud Run, Functions, GCE, …) and attached roles;
   whether the app needs IMDS; egress paths (NAT, proxy, mesh).

### 2. Application-layer URL controls

Implement/review with `code-quality-standards`:

1. Prefer **allowlists** of HTTPS + exact hostnames over deny-lists alone.
2. Resolve DNS → classify IP → connect only if safe; **re-check every redirect**.
3. Deny loopback, RFC1918 (unless required), link-local (`169.254.0.0/16`,
   `fe80::/10`), and metadata hostnames.
4. Disable unused schemes (`file`, `gopher`, `dict`, `ftp`); cap size/time.
5. Validate **at connect time** against encoding, userinfo, and DNS rebinding.

### 3. Platform IMDS hardening

| Control | Intent |
| --- | --- |
| AWS IMDSv2 required | Blocks simple anonymous GET credential theft |
| AWS hop limit = 1 | Often blocks container/pod → host IMDS |
| Avoid host networking by default | Reduces accidental IMDS reachability |
| Do not forge metadata headers on user fetches | GCP/Azure header gates stay meaningful |
| Workload identity (IRSA, WIF, Azure WI) | Narrower than node IMDS role |
| Org policy disables IMDSv1 | Estate-wide defense in depth |

Verify via describe APIs / launch templates on owned accounts — not secret dumps.

### 4. Network egress and blast radius

1. Default-deny egress for pure user-driven fetch workers; allowlist or proxy.
2. Block app → `169.254.169.254/32` / metadata hosts when agents still need IMDS;
   proxies must not honor arbitrary `Host` to link-local.
3. Least-privilege roles; no standing long-lived keys (`secrets-management-hygiene`).
4. Split “edge fetcher” (almost no cloud perms) from “worker with SM read.”
5. Alert on unusual role use after suspected SSRF.

### 5. Verify defenses (authorized)

1. Staging: app rejects metadata URLs/encoded variants without retrieving creds.
2. Confirm IMDSv2-only, hop limit, and network/CNI drops on app→IMDS paths.
3. Regression tests for the URL filter (`code-quality-standards`).
4. Residual offensive proofs → `ssrf-server-side-request-forgery` (in scope);
   redact and rotate on any accidental credential material.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Defend against cloud metadata SSRF; IMDS hardening | **This skill** | — |
| Authorized offensive SSRF proof / bypass testing | `ssrf-server-side-request-forgery` | this skill for remediation |
| Implement/review fetch allowlist code | `code-quality-standards` | this skill for metadata denials |
| CI secrets / OIDC to cloud (not app IMDS) | `secrets-in-ci-pipelines`, `ci-cd-pipeline-patterns` | — |
| Rotate after credential exposure | `secrets-management-hygiene` | this skill for IMDS path |

- **`ssrf-server-side-request-forgery`:** find/prove SSRF; remediate metadata here.
- **`code-quality-standards`:** when changing fetchers, redirects, proxies.
- **`secrets-management-hygiene`:** rotate/revoke if temporary cloud creds leaked.
- **`ci-cd-pipeline-patterns` / `secrets-in-ci-pipelines`:** CI identity, not IMDS
  (unless the runner itself is the compromised workload).

## Checklist

- [ ] User-driven server fetch paths inventoried
- [ ] Allowlist + scheme limits; private/link-local/metadata blocked at connect time
- [ ] Redirects re-validated; unsafe schemes disabled
- [ ] AWS: IMDSv2 required; hop limit 1 where containers share host path
- [ ] GCP/Azure metadata headers not forged for user-driven requests
- [ ] Network policy blocks workload → IMDS when not required; egress controlled
- [ ] Roles least privilege; workload identity over fat node roles; no disk keys
- [ ] Tests cover metadata variants; no live secrets in fixtures
- [ ] Exposure: redact + rotate (`secrets-management-hygiene`)
- [ ] `code-quality-standards` on code changes; residual risk documented

## Rules

- Defense in depth: app filter **and** IMDS config **and** network **and** IAM.
- Prefer allowlists and connect-time IP checks over deny-lists alone.
- Never paste live IMDS credentials into tickets or prompts; rotate on exposure.
- Authorized hardening only; internal access via service auth/private network —
  not “fetch any URL.”
