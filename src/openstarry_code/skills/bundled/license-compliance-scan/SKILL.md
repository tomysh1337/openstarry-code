---
name: license-compliance-scan
description: >
  Scan third-party OSS licenses against org allow/deny lists, flag copyleft and
  dual-license ambiguity, verify NOTICE/attribution artifacts, and wire CI license
  gates. Use when reviewing dependency license compliance, SPDX identifiers,
  forbidden licenses (GPL/AGPL/SSPL and org deny lists), missing NOTICE files,
  license CI failures, or release attribution packages — not legal advice; hand
  SBOM generation and CVE/SCA to sbom-and-supply-chain.
---

# License Compliance Scan

Inventory declared licenses on direct and transitive deps, compare them to **org
policy** (allow / deny / review), check **copyleft** and attribution obligations,
and enforce results in CI. **Not legal advice** — escalate dual-license,
proprietary, or distribution-model questions to counsel before shipping.

## When To Use

- Adding dependencies or reviewing lockfiles for **license policy** fit
- Release / questionnaire needs a **license bill** or attribution pack
- CI fails on FOSSA, License Finder, `license-checker`, Syft+policy, or similar
- Suspected **copyleft** (GPL/LGPL/AGPL), source-offer, or network-copyleft risk
- Missing or incomplete **NOTICE**, `LICENSE*`, or third-party attributions
- Keywords: SPDX, allowlist, denylist, copyleft, NOTICE, attribution, license gate

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| CycloneDX/SPDX SBOM, CVE/SCA, pins, provenance | `sbom-and-supply-chain` |
| Private vs public package namespace / resolve order | `dependency-confusion` |
| Secrets in package tarballs or CI logs | `secrets-management-hygiene` |
| Pipeline topology / fork isolation broadly | `ci-cd-pipeline-patterns` |
| Runtime injection or app vuln classes | `injection-checking` + class skill |

## Repo Config First

Repo and org license policy **outrank** defaults below.

1. **Policy source of truth:** legal-approved allow/deny/review lists, SPDX IDs, exception process
2. **Existing config:** `.licensee`, `deny.toml` (cargo-deny), `license_finder.yml`, FOSSA/Snyk, `.licenserc`, REUSE.toml
3. **Manifests + lockfiles:** scan the **resolved** tree CI uses, not hand-picked direct deps only
4. **Attribution layout:** root `NOTICE`, `THIRD_PARTY_NOTICES`, `licenses/`, about-screens, image layers
5. **Distribution model:** SaaS-only vs shipped binary/SDK/mobile/on-prem — copyleft impact differs
6. **Neighbors:** SBOM jobs, Dependabot/Renovate, base-image license jobs already in CI

**Precedence:** Follow repo policy and counsel-approved lists. Treat unknown,
missing, or conflicting SPDX as **blockers** — do not invent SPDX IDs.

## Workflow

### 1. Inventory resolve path

List manifests, lockfiles, base images, and vendored/third_party trees. Prefer
license data from the **same resolve path** as release builds. If no SBOM exists,
generate via `sbom-and-supply-chain`, then continue here for policy.

### 2. Collect license declarations

| Source | What to capture |
| --- | --- |
| Package metadata | SPDX from registry / lock metadata |
| On-disk texts | `LICENSE*`, `COPYING`, `NOTICE`, file headers |
| Scanner output | FOSSA, License Finder, Syft, Trivy license, `license-checker`, cargo-deny, scancode |
| SBOM | SPDX or CycloneDX license fields per component |

Table: **package × version × SPDX × evidence × direct/transitive × ships in prod?**

### 3. Apply allow / deny / review lists

| Bucket | Action |
| --- | --- |
| **Allow** (e.g. MIT, Apache-2.0, BSD-2/3) | Pass when evidence matches and attribution rules satisfied |
| **Deny** (org-specific; often AGPL, SSPL, unknown commercial-only) | Fail CI / block merge unless exception filed |
| **Review** (GPL, LGPL, MPL, EPL, dual-license, custom, NOASSERTION) | Human + legal; record link style and modified vs unmodified |
| **Missing / conflicting** | Review or deny per policy; never silently map to MIT |

Normalize to **SPDX** expressions (`Apache-2.0 OR MIT`). Flag `NOASSERTION`,
empty fields, and non-SPDX prose for manual LICENSE read.

### 4. Copyleft and distribution context

Scanners flag family, not legal clearance — record **use facts** for policy/counsel:

1. **Shipped binary / SDK / mobile / appliance:** strong- and many weak-copyleft cases need explicit legal review.
2. **SaaS / server-only:** still check **AGPL / network-copyleft** and SaaS-specific terms.
3. **Modified vs unmodified; static vs dynamic; combined work vs separate process** — facts only, no invented conclusions.
4. **Source-offer / written offer** if policy requires: plan location and retention (not a substitute for legal OK).

### 5. NOTICE and attribution

1. Preserve required **copyright / NOTICE** text (Apache-2.0 NOTICE aggregation is a common rebundle gap).
2. Ship a **third-party notice** pack for distributed products (file or in-app).
3. Do not strip license headers from vendored source without policy approval.
4. Optional: REUSE / `SPDX-License-Identifier` on first-party files.

### 6. CI license gates

1. **PR:** fail deny-list and missing-license on **prod** scopes; warn on review-list with linked exception when process allows.
2. **Release / main:** full tree + image layers; attach license report or SBOM license fields with artifacts.
3. Pin scanner versions; run after lockfile resolve. No blanket ignore without owner + **expiry**.
4. Pipeline wiring → `ci-cd-pipeline-patterns`; gate scripts → `code-quality-standards`.

### 7. Exceptions and verify

Document exceptions: package, version range, SPDX, rationale, approver, expiry.
Re-scan after upgrades; regenerate NOTICE on lockfile change. Unknown licenses at
ship time fail unless counsel accepted.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Allow/deny policy, copyleft triage, NOTICE, license CI gates | **This skill** | — |
| SBOM generate, CVE/SCA, pins, provenance | `sbom-and-supply-chain` | this for license policy on SBOM |
| Registry namespace / install-order confusion | `dependency-confusion` | — |
| Secrets in deps or CI | `secrets-management-hygiene` | — |
| CI stage graph, caches, fork PR trust | `ci-cd-pipeline-patterns` | this for gate content |
| Policy-as-code / scanner config quality | `code-quality-standards` | **always** on config/scripts |

- **`sbom-and-supply-chain`:** owns SBOM/SCA inventory; **this skill** owns license **policy**, attribution, and deny gates.
- Keep **this skill primary** for license compliance; switch when the ask is SBOM-only or vuln SLA only.

## Output Checklist

- [ ] Resolve path, lockfiles, and prod vs dev scopes identified
- [ ] Repo policy / scanner config followed (allow, deny, review, exceptions)
- [ ] Component table: package, version, SPDX, evidence, direct/transitive, ships?
- [ ] Deny-list hits blocked or exceptioned with owner + expiry
- [ ] Copyleft / dual-license / NOASSERTION items with distribution context
- [ ] NOTICE / third-party attribution pack present when distribution requires it
- [ ] CI: deny + missing license fail; scanner pinned; report artifact on release
- [ ] Explicit **not legal advice**; counsel path for residual risk
- [ ] Routed: SBOM/CVE → `sbom-and-supply-chain`; CI topology → `ci-cd-pipeline-patterns`
- [ ] CQS on license config and generator scripts; fail closed on unknown prod licenses
