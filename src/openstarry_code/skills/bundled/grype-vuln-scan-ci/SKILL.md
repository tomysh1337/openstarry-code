---
name: grype-vuln-scan-ci
description: >
  Wire Anchore Grype vulnerability scans into CI with severity fail-on gates,
  config and ignore policy, DB freshness, and SARIF/JSON artifacts. Use when
  Grype CI, anchore/scan-action, grype image/dir/sbom, --fail-on, .grype.yaml,
  grype ignore matches, SARIF upload, or blocking HIGH/CRITICAL image or SBOM
  vulns on PR/main — not Dockerfile authorship, SBOM publish-only, or signing.
---

# Grype Vuln Scan CI

Make **Grype CVE gates** real in CI: scan the **ship digest**, directory tree,
or **SBOM**, fail on policy severities, export **SARIF/JSON**, and keep ignores
time-boxed. Prefer the repo’s existing Grype job, org reusable workflow, and
scanner policy over a parallel greenfield gate.

## When To Use

- Add or fix `grype` (or `anchore/scan-action`) in GitHub Actions, GitLab CI, or
  equivalent for images, dirs, or SBOMs after build
- Severity gates (`--fail-on`, `.grype.yaml`), match ignores, fail-closed vs
  report-only rollout
- SARIF / JSON artifacts and upload to code scanning or org finding systems
- Mentions: Grype CI, Anchore scan, image/dir/SBOM CVE gate, SARIF, `.grype.yaml`

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Dockerfile multi-stage, non-root, layer secrets | `dockerfile-best-practices` |
| Pipeline stages, OIDC, fork PR trust, caches | `ci-cd-pipeline-patterns` |
| SBOM generate/publish / fail-if-missing SBOM | `sbom-ci-enforcement` |
| Cosign/Sigstore sign-verify / admission | `container-image-signing` |
| Trivy image flags / `.trivyignore` | `trivy-image-scan-ci` |
| License allow/deny; broad SAST/DAST choice | `license-compliance-scan` / `sast-dast-tooling-usage` |
| Workflow/script quality baseline | `code-quality-standards` |

## Repo Config First

Repo and org scanner policy **outrank** examples below.

1. Existing Grype/Trivy/Scout jobs, composite actions, and required check names
2. Org severity policy (block CRITICAL only vs high+; OS vs language packages)
3. Targets already built in CI: image digests, workspace paths, SBOM artifact paths
4. `.grype.yaml`, `.grype/config.yaml`, ignore rules, VEX inputs if used
5. Code scanning / SARIF upload permissions and branch protection required checks
6. DB mirror / offline air-gap cache if runners cannot refresh the Grype DB
7. Neighbor gates: SBOM (`sbom-ci-enforcement`), sign (`container-image-signing`),
   alternate scanner (`trivy-image-scan-ci`)

**Precedence:** Extend the existing job. Surface `continue-on-error` on the
security job, scan-only-on-PR-skip-main, or tag-only refs without digest.

## Workflow

### 1. Inventory the scan target

| Target | Prefer when | Gate artifact |
| --- | --- | --- |
| `grype image …` | Ship container | Same **digest** deploy uses |
| `grype dir:.` / path | App deps without image | Locked tree from CI install |
| `grype sbom:…` | Syft/CI already emits SBOM | Same SBOM release/attests |

Multi-arch: scan index and/or platform digests per org rule. Prefer digest refs
over floating tags (`:latest`).

### 2. Place the job in the pipeline

- Run **after** image build (and push if registry pull is required) or after
  SBOM/dir install is ready
- PR: scan local load, CI registry tag, or workspace; main/tag/release: required
  fail-closed; no skip on protected branches; report-only only as time-boxed rollout
- Least privilege: `contents: read`; `security-events: write` only for GitHub SARIF upload

### 3. Severity gate (fail closed)

1. Pin Grype version (action SHA/tag, binary release, or container digest).
2. Refresh DB (`grype db update` or action default) unless offline cache is policy.
3. Scan with fail-on: `grype … --fail-on high` (tune to org: `critical` vs `high`+;
   document fixed-only policy if configured).
4. Scope via in-repo `.grype.yaml` (matching, auth, excludes); keep reviewed.
5. Never `|| true` / `continue-on-error: true` on the gate without a required follow-up.

```bash
grype "registry/$IMAGE@$DIGEST" \
  --fail-on high \
  -o sarif --file grype.sarif
# or: grype sbom:./sbom.cdx.json --fail-on high -o json --file grype.json
```

### 4. SARIF and artifacts

1. Emit SARIF (and optionally table/JSON for humans).
2. Upload SARIF to code scanning when on GitHub; else retain for the org tool.
3. Upload even on failure (`if: always()`); redact registry credentials from logs.

### 5. Ignores and exceptions

- Prefer Grype ignore rules / VEX with **CVE or match id + expiry + owner**
- No permanent blank ignore of whole packages; re-review expired ignores
- Fix base image or app deps rather than growing ignore lists
- Exception clocks → `vulnerability-sla-process` when the org uses it

### 6. Verify the gate

Break a known high/critical in a throwaway image or temporarily tighten
`--fail-on` in a draft PR; confirm the required check fails and its name matches
branch protection. Apply `code-quality-standards` to workflow YAML.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Grype CI, fail-on, .grype.yaml, SARIF, image/dir/SBOM scan | **This skill** | — |
| Trivy image flags, `.trivyignore`, trivy-action only | `trivy-image-scan-ci` | this if both required |
| Pipeline graph, secrets, fork PR, required checks | `ci-cd-pipeline-patterns` | this for scan step |
| Dockerfile / image contents hardening | `dockerfile-best-practices` | this post-build |
| SBOM generate, publish, missing-SBOM gates | `sbom-ci-enforcement` | this for CVE on SBOM |
| Image sign/verify; license scan; CVE SLA clocks | `container-image-signing` / `license-compliance-scan` / `vulnerability-sla-process` | this for detection |
| Multi-tool SAST/DAST program shape | `sast-dast-tooling-usage` | this for Grype gate |
| Workflow quality, pins, tests | `code-quality-standards` | **always** on CI code |

**Hand-off:** SBOM → `sbom-ci-enforcement`. Signatures → `container-image-signing`.
Trivy-only → `trivy-image-scan-ci`. This skill owns **Grype severity gates +
artifacts** for authorized owned/CI targets.

## Output Checklist

- [ ] Ship images/digests, dirs, or SBOMs inventoried; gate uses digest/SBOM not floating tag alone
- [ ] Repo Grype job, org severity policy, `.grype.yaml`/ignores, SARIF path read first
- [ ] Grype version pinned; DB refresh or approved offline cache
- [ ] `--fail-on` (or config equivalent) on protected refs; no silent continue
- [ ] SARIF and/or JSON produced; uploaded/retained with failure visibility
- [ ] Code scanning / required check names match branch protection
- [ ] Ignores/VEX have owner + expiry; no unbounded package-wide ignores
- [ ] Multi-arch / multi-target rule documented; registry auth not logged
- [ ] SBOM → `sbom-ci-enforcement`; sign → `container-image-signing`; Trivy twin → `trivy-image-scan-ci`
- [ ] `ci-cd-pipeline-patterns` + `code-quality-standards` applied to workflow
