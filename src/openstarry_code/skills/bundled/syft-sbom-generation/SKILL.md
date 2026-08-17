---
name: syft-sbom-generation
description: >
  Generate Software Bills of Materials with Anchore Syft from source trees,
  container images, archives, and OCI digests: output formats (CycloneDX, SPDX,
  Syft JSON), scope and cataloger selection, reproducible CI-equivalent scans,
  and named hashed artifacts. Use when running syft packages, syft scan, image
  SBOM by digest, CycloneDX/SPDX from Syft, pinning the Syft CLI, or wiring
  Syft generate steps before SCA or release attach — hand missing-SBOM CI gates
  to sbom-ci-enforcement and broad SCA/pin hygiene to sbom-and-supply-chain.
---

# Syft SBOM Generation

Own **Syft-driven SBOM production** for owned repos and images: pin the CLI,
choose target and catalogers, emit CycloneDX and/or SPDX (plus Syft JSON when
useful), name and hash outputs from a **CI-equivalent resolve path**. Generator
only — presence gates, attest, and broad supply-chain policy live elsewhere.

## When To Use

- Generate an SBOM with **Syft** from a directory, image, archive, or OCI ref
- Choose **CycloneDX** / **SPDX** / Syft JSON; pin Syft for local/CI parity
- Scan a **container by digest** (runtime image); debug empty/thin component lists
- Keywords: `syft`, `syft packages`, `syft scan`, Anchore SBOM, cdx/spdx from Syft

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Fail-if-missing SBOM, attest, release upload gates | `sbom-ci-enforcement` |
| Broad SCA, pins, confusion, provenance policy | `sbom-and-supply-chain` |
| License allow/deny; CVE clocks/exceptions | `license-compliance-scan` / `vulnerability-sla-process` |
| Image signing; pipeline layout; Dockerfile surface | `container-image-signing` / `ci-cd-pipeline-patterns` / `dockerfile-best-practices` |
| Script/workflow quality baseline | `code-quality-standards` |

## Repo Config First

Repo and org policy **outrank** defaults below.

1. **Existing SBOM job:** Syft flags, output path, format (CycloneDX vs SPDX)
2. **Lockfiles and install:** same command CI uses before scan (`npm ci`, etc.)
3. **Targets:** monorepo package roots, final image digest, multi-arch matrix
4. **Syft pin:** release tag or image digest — not floating `:latest` on gates
5. **Cataloger/scope:** `.syft.yaml` / env if present; org cataloger allowlist
6. **Neighbors:** SCA after SBOM, license job, cosign attest, artifact retention

Extend the real build path; do not invent a second install that diverges from prod.

## Workflow

### 1. Install and pin Syft

Prefer an **org-approved pin** (release binary, package, or pinned container).
Record version in CI and reports. Never leave release gates on floating latest.

```bash
syft version
```

### 2. Prefer CI-equivalent inputs

1. Install/restore deps the **same way CI does** before scanning a source tree.
2. Containers: scan the **shipped runtime image by digest**, not a mutable tag alone.
3. Monorepos: one SBOM per deployable root/image unless policy demands a rollup.

### 3. Generate (common invocations)

```bash
# Source / project directory (after lockfile-faithful install)
syft dir:. -o cyclonedx-json=sbom.cdx.json
syft dir:. -o spdx-json=sbom.spdx.json
syft dir:. -o syft-json=sbom.syft.json

# Container by digest (preferred); local image / archive
syft "registry:ghcr.io/org/app@sha256:…" -o cyclonedx-json=sbom-image.cdx.json
syft docker:myapp:local -o cyclonedx-json=sbom.cdx.json
syft file:./app.tar -o spdx-json=sbom.spdx.json
```

| Format (illustrative) | When |
| --- | --- |
| `cyclonedx-json` / `cyclonedx-xml` | AppSec, SCA, most security pipelines |
| `spdx-json` / `spdx-tag-value` | License/compliance questionnaires |
| `syft-json` | Debug catalogers/reprocess; often not customer-facing |
| table / text | Human triage only — not release inventory |

Name with product + git SHA or digest short id (`sbom-api-a1b2c3d.cdx.json`).
`sha256` the file and keep with release evidence.

### 4. Scope, catalogers, and thin SBOMs

1. Confirm package managers present (lockfiles; OS packages in image layers).
2. Near-zero components: wrong root, scan-before-install, wrong image stage, or
   disabled catalogers — fix input before blaming the tool.
3. Honor repo `.syft.yaml`; document cataloger excludes that drop prod languages.
4. Multi-stage Docker: SBOM the **final runtime** image; document build-stage
   tooling only if policy requires compiler inventory.

### 5. Hand off and verify

1. **Publish / fail-if-missing / attest** → `sbom-ci-enforcement`
2. **SCA, pins, confusion, hygiene** → `sbom-and-supply-chain`
3. **License** → `license-compliance-scan`; **CVE SLA** → `vulnerability-sla-process`
4. Apply `code-quality-standards` when editing scripts/workflows that call Syft

**Verify:** same pin/flags as CI; digest-linked image SBOM matches what you ship;
no tokens in command logs.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Syft install, scan targets, formats, thin-SBOM debug | **This skill** | — |
| CI missing/empty SBOM gates, attest, release attach | `sbom-ci-enforcement` | this for generate command |
| Broad dep hygiene, SCA triage, pins, provenance | `sbom-and-supply-chain` | this for Syft bytes |
| License allow/deny | `license-compliance-scan` | Syft SPDX/CDX as input |
| Image signature identity | `container-image-signing` | this for SBOM side-car |
| Pipeline structure, caches, required checks | `ci-cd-pipeline-patterns` | this for Syft step body |
| Dockerfile runtime contents | `dockerfile-best-practices` | this for image SBOM |
| Implementation quality of wrappers/CI | `code-quality-standards` | **always** with this skill |

Keep **this skill primary** until Syft pin, target, format, and output integrity
are correct; then hand gates and SCA policy to neighbors.

## Output Checklist

- [ ] Repo Syft config, CI job, lockfile install path, and format policy read first
- [ ] Syft version pinned; `syft version` recorded with the artifact
- [ ] Scan after CI-equivalent install (dir) or on **final image digest** (container)
- [ ] CycloneDX and/or SPDX per org standard; names include product + SHA/digest
- [ ] SBOM hashed (`sha256`); stored as artifact — not log-only text table
- [ ] Thin/empty SBOM investigated (root, stage, catalogers) before sign-off
- [ ] Monorepo/multi-image matrix covers each shippable target
- [ ] Secrets/registry tokens redacted; originals immutable
- [ ] Hand-offs: gates → `sbom-ci-enforcement`; SCA → `sbom-and-supply-chain`;
      license/SLA/signing/pipeline/CQS as routed above
- [ ] Rules: owned targets only; digest over mutable tag; real resolve path only
