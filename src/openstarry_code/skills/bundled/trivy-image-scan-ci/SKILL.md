---
name: trivy-image-scan-ci
description: >
  Wire Trivy container image scans into CI with severity exit gates, ignore
  policy, DB freshness, and SARIF upload to code scanning. Use when Trivy image
  CI, trivy image --severity, --exit-code, SARIF upload, GitHub code scanning
  container CVE gate, .trivyignore, or blocking HIGH/CRITICAL image vulns on
  PR/main — not Dockerfile authorship, SBOM publish, or image signing.
---

# Trivy Image Scan CI

Make **container image CVE gates** real in CI: scan the **ship digest**, fail on
policy severities, export **SARIF**, and keep ignores time-boxed. Prefer the
repo’s existing Trivy job, org reusable workflow, and scanner policy over a
parallel greenfield gate.

## When To Use

- Add or fix `trivy image` (or aquasecurity/trivy-action) in GitHub Actions,
  GitLab CI, or equivalent after build/push
- Severity gates (`--severity`, `--exit-code`), ignore files, or fail-closed vs
  report-only rollout
- SARIF / JSON artifacts and upload to code scanning or org finding systems
- Mentions: Trivy CI, image CVE gate, SARIF, `.trivyignore`, HIGH/CRITICAL block

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Dockerfile multi-stage, non-root, layer secrets | `dockerfile-best-practices` |
| Pipeline stages, OIDC, fork PR trust, caches | `ci-cd-pipeline-patterns` |
| SBOM generate/publish / fail-if-missing SBOM | `sbom-ci-enforcement` |
| Cosign/Sigstore sign-verify / admission | `container-image-signing` |
| License allow/deny on deps | `license-compliance-scan` |
| Broad SCA/SAST tool choice outside Trivy image gate | `sast-dast-tooling-usage` |
| Workflow/script quality baseline | `code-quality-standards` |

## Repo Config First

Repo and org scanner policy **outrank** examples below.

1. Existing Trivy/Grype/Scout jobs, composite actions, and required check names
2. Org severity policy (block CRITICAL only vs HIGH+CRITICAL; OS vs app pkgs)
3. Registry and image refs already built in CI (prefer digest, not `:latest`)
4. `.trivyignore`, `trivy.yaml`, ignore file in reusable workflows
5. Code scanning / SARIF upload permissions and branch protection required checks
6. DB mirror / offline air-gap cache if runners cannot hit default Trivy DB
7. Neighbor gates: SBOM (`sbom-ci-enforcement`), sign (`container-image-signing`)

**Precedence:** Extend the existing job. Surface `continue-on-error` on the
security job, scan-only-on-PR-skip-main, or tag-only refs without digest.

## Workflow

### 1. Inventory the image under gate

List images that ship to prod; resolve **immutable digest** from build-push
output. Gate the same digest that deploy will use. Multi-arch: scan index and/or
platform digests per org rule.

### 2. Place the job in the pipeline

- Run **after** image build (and push if registry pull is required)
- PR: scan local load or CI registry tag; main/tag/release: required fail-closed
- Do not skip scan on protected branches; report-only only as a time-boxed rollout
- Least privilege: `contents: read`; add `security-events: write` only if uploading SARIF to GitHub code scanning

### 3. Severity gate (fail closed)

1. Pin Trivy version (action SHA/tag or binary pin).
2. Refresh DB (`trivy image --download-db-only` or action default) unless offline cache is policy.
3. Scan: `trivy image --severity HIGH,CRITICAL --exit-code 1 --ignore-unfixed` (tune to org; document if unfixed ignored).
4. Optional: `--scanners vuln` (default focus); add secret/misconfig only if org owns those signals here.
5. Never `|| true` / `continue-on-error: true` on the gate job without a separate required follow-up.

```bash
trivy image --format sarif --output trivy-image.sarif \
  --severity HIGH,CRITICAL --exit-code 1 \
  "$REGISTRY/$IMAGE@$DIGEST"
```

### 4. SARIF and artifacts

1. Emit SARIF (and optionally JSON table for humans).
2. Upload SARIF to code scanning when on GitHub; else retain artifact for the org tool.
3. Upload even on failure (`if: always()`) so findings remain visible.
4. Redact registry credentials from logs; do not print pull secrets.

### 5. Ignores and exceptions

- Prefer `.trivyignore` / `trivy.yaml` with **CVE id + expiry + owner** comments
- No permanent blank ignore of whole packages without justification
- Re-review expired ignores; fix base image or app deps rather than growing ignore lists
- Align exception process with security/product owners

### 6. Verify the gate

Break a known HIGH/CRITICAL in a throwaway image or temporarily lower threshold
in a draft PR and confirm the required check fails. Confirm check name matches
branch protection. Apply `code-quality-standards` to workflow YAML.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Trivy image CI, severity exit codes, SARIF upload, .trivyignore | **This skill** | — |
| Pipeline graph, secrets, fork PR, required checks wiring | `ci-cd-pipeline-patterns` | this for scan step |
| Dockerfile / image contents hardening | `dockerfile-best-practices` | this post-build |
| SBOM generate, publish, missing-SBOM gates | `sbom-ci-enforcement` | this for CVE gate |
| Image sign/verify admission | `container-image-signing` | this for vuln gate |
| License compliance scan | `license-compliance-scan` | not CVE severity |
| Multi-tool SAST/DAST program shape | `sast-dast-tooling-usage` | this for Trivy image |
| Workflow quality, pins, tests | `code-quality-standards` | **always** on CI code |

**Hand-off:** SBOM presence/format → `sbom-ci-enforcement`. Signatures →
`container-image-signing`. This skill owns **image vuln severity gates + SARIF**.

## Output Checklist

- [ ] Ship images/digests inventoried; gate uses digest not floating tag alone
- [ ] Repo Trivy job, org severity policy, ignore files, SARIF path read first
- [ ] Trivy version pinned; DB refresh or approved offline cache
- [ ] `--severity` + `--exit-code 1` (or equivalent) on protected refs; no silent continue
- [ ] SARIF (and optional JSON) produced; uploaded/retained with failure visibility
- [ ] Code scanning / required check names match branch protection
- [ ] `.trivyignore` / exceptions have owner + expiry; no unbounded ignores
- [ ] Multi-arch scan rule documented; registry auth not logged
- [ ] SBOM → `sbom-ci-enforcement`; sign → `container-image-signing`
- [ ] `ci-cd-pipeline-patterns` + `code-quality-standards` applied to workflow
