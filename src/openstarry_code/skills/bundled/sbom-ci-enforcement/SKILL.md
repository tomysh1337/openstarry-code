---
name: sbom-ci-enforcement
description: >
  Enforce Software Bill of Materials (SBOM) generation in CI: CycloneDX and/or
  SPDX artifacts, build-linked attestation, publish-with-release, and hard gates
  when an SBOM is missing or empty. Use when wiring SBOM jobs in GitHub Actions,
  GitLab CI, or similar; requiring SBOM on merge/release; cosign/in-toto/SLSA
  attestations of SBOM-to-image; or failing pipelines that ship without inventory
  — hand license policy to license-compliance-scan and CVE fix clocks to
  vulnerability-sla-process.
---

# SBOM CI Enforcement

Make **SBOM production mandatory and build-linked** in CI for owned products:
generate CycloneDX/SPDX from the real resolve path, attach/attest the SBOM to
the release artifact or image digest, and **fail closed** when the SBOM is
missing, empty, or not uploaded. Owns **pipeline gates and attestation wiring**,
not broad SCA triage or license legal review.

## When To Use

- CI must emit CycloneDX and/or SPDX on release (or every main build)
- Policy: no merge/release/deploy without a published SBOM artifact
- Need SBOM **attestation** (cosign/in-toto/SLSA: commit → build → SBOM → digest)
- Gate failures: missing file, zero components, wrong format, unsigned attach
- Mentions: SBOM CI gate, CycloneDX/SPDX pipeline, sbom attestation, fail if no SBOM

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Full dep hygiene, pins, confusion, broad SCA | `sbom-and-supply-chain` |
| License allow/deny, copyleft, SPDX legal | `license-compliance-scan` |
| CVE severity clocks, exceptions, ticket SLA | `vulnerability-sla-process` |
| Pipeline layout, caches, fork PR trust | `ci-cd-pipeline-patterns` |
| Image layer/runtime hygiene | `dockerfile-best-practices` |
| Implementation quality of scripts/IaC | `code-quality-standards` |

## Repo Config First

Repo and org CI config **outrank** examples here.

1. Workflows: `.github/workflows/*`, `.gitlab-ci.yml`, Jenkinsfile, Azure Pipelines
2. Lockfiles and install commands already used in build jobs
3. Org SBOM standard (CycloneDX vs SPDX vs both) and artifact retention
4. Signing (cosign/OIDC/Sigstore/in-toto) and landing path (GH Releases, OCI, Artifactory)
5. Required checks / deploy envs; neighbor jobs (SCA, license, image); monorepo matrix

Extend existing jobs; do not invent a second install path that diverges from prod.

## Workflow

### 1. Anchor generation to the real build

1. Use the CI job that installs deps and builds the shippable artifact.
2. Generate **after** lockfile-faithful install (`npm ci`, `poetry install`,
   `go mod download`, Maven/Gradle restore) on the same roots CI builds.
3. Tools: Syft, cdxgen, Trivy, ecosystem CycloneDX plugins; containers by
   final runtime **image digest**. Name: `sbom-<product>-<gitsha>.cdx.json` / `.spdx.json`.
4. Never gate on a hand-edited component list or partial manifest dump.

### 2. Formats and multi-target matrix

| Target | SBOM source | Notes |
| --- | --- | --- |
| App/repo | Post-install tree or lockfile tools | One SBOM per deployable in monorepos |
| Container | Final **runtime** image **digest** | Prefer digest over mutable tag |
| Multi-arch / library | Per-arch or publish dir | Match attested digest / customer version |

Emit **CycloneDX** for AppSec/SCA; **SPDX** when license/questionnaires require
it (or both). Do not satisfy only one format if policy demands both.

### 3. Publish and attest

1. Upload SBOM as CI artifact; attach to release (GH asset, side-car, OCI) — not log-only.
2. `sha256` the SBOM; record in notes/provenance.
3. Prefer **attestation** (cosign/in-toto/GitHub) binding commit + artifact digest + SBOM hash.
4. On deploy, verify signature/attestation before prod when tooling exists.

### 4. Hard gates (fail closed)

| Gate | Fail when |
| --- | --- |
| Presence | Expected SBOM path(s) missing after generate |
| Non-empty | Zero components / empty JSON / parse error |
| Format | Not valid CycloneDX or SPDX per org schema |
| Upload | Artifact upload skipped or failed |
| Attestation | Sign/attest failed or digest mismatch (if required) |
| Image link | Ship job has no SBOM for the **same** digest |

Soft/warn-only until hardened: component count delta, missing PURL. License →
`license-compliance-scan`; CVE severity → scanner + `vulnerability-sla-process`.

### 5. Stages, verify, hand off

1. **PR:** optional fast generate; fail if install mutates lock without review.
2. **Main/tag:** full SBOM + upload + attest; **Deploy:** digest pull + require SBOM.
3. Dry-run: remove SBOM path → fail; restore → green; release shows shipped SBOM.
4. Pair with `ci-cd-pipeline-patterns` / `secrets-management-hygiene`; apply
   `code-quality-standards` to scripts and workflow YAML.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| CI SBOM generate, publish, attest, missing gate | **This skill** | — |
| Broad inventory, SCA, pins, confusion | `sbom-and-supply-chain` | this for CI gate shape |
| License allow/deny and legal SPDX review | `license-compliance-scan` | this if SBOM is input |
| CVE SLA, exceptions, ticket clocks | `vulnerability-sla-process` | this if presence-only gate |
| Pipeline structure, caches, required checks | `ci-cd-pipeline-patterns` | this for SBOM job content |
| Image contents / multi-stage | `dockerfile-best-practices` | this for image SBOM gate |
| Workflow/script quality | `code-quality-standards` | always with this skill |

**Required hand-offs:** license policy → `license-compliance-scan`; severity SLA
matrices → `vulnerability-sla-process`. Keep SBOM bytes/attestations as shared evidence.

## Output Checklist

- [ ] Repo CI and org SBOM format/retention policy read first
- [ ] SBOM from CI-equivalent install/build path (not laptop-only)
- [ ] CycloneDX and/or SPDX named with product + git SHA/version
- [ ] Uploaded as artifact and attached to release or image digest
- [ ] Hash and (if required) attestation bind commit ↔ SBOM ↔ artifact
- [ ] Hard gate fails on missing, empty, invalid, or unuploaded SBOM
- [ ] Container gates use digest-linked SBOM for the shipped image
- [ ] PR/main/release stages match risk (full attest on ship path)
- [ ] License → `license-compliance-scan`; CVE clocks → `vulnerability-sla-process`
- [ ] Tokens redacted; `code-quality-standards` + `ci-cd-pipeline-patterns` applied

## Rules

- Owned repos/registries only; fail closed on missing ship-path SBOM.
- Generate from the real resolve path; never gate on a hand-curated fake list.
- Presence/attestation gates here; license and vuln **policy** elsewhere.
- Prefer digests and signed attestations over mutable tags and unsigned side files.
- Redact credentials; keep originals immutable; store derived reports separately.
