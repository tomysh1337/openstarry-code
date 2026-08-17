---
name: container-image-signing
description: >
  Sign and verify container images with Cosign and Sigstore: keyless OIDC,
  long-lived keys, and admission or policy enforcement by digest. Use when
  cosign sign/verify, Fulcio/Rekor, keyless OIDC image signing, Kyverno or
  Gatekeeper or Sigstore policy-controller image checks, or OCI signature
  enforcement on deploy — hand SBOM generate/publish/CI gates to
  sbom-ci-enforcement; hand Git commit signatures to signed-commits-basics.
---

# Container Image Signing

Prove **which identity built and published** a container image so registries and
clusters **reject unsigned or wrong-identity digests**. Primary tools: **Cosign**
+ **Sigstore** (Fulcio, Rekor). Prefer **keyless OIDC** from trusted CI. Owned
registries and clusters only.

## When To Use

- Sign images after build (`cosign sign`) by **digest**, not floating tags
- **Keyless OIDC** (GitHub Actions / GitLab / cloud WI → Fulcio) or **KMS/key**
- **Verify** before promote; wire **admission/policy** (Kyverno, Gatekeeper,
  Sigstore policy-controller, cloud deploy gates)
- Mentions: cosign, Sigstore, Fulcio, Rekor, keyless signing, signed OCI image

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| SBOM generate, upload, missing-SBOM CI gates, SBOM attest body | `sbom-ci-enforcement` |
| Broad dep hygiene / SCA | `sbom-and-supply-chain` |
| Git commit/tag Verified badge | `signed-commits-basics` |
| Dockerfile multi-stage / non-root | `dockerfile-best-practices` |
| Pipeline topology, fork PR trust | `ci-cd-pipeline-patterns` |
| Key/token storage, leak IR | `secrets-management-hygiene` |
| Workflow/script quality | `code-quality-standards` |

## Repo Config First

Repo and platform policy **outrank** examples below.

1. Existing signer jobs (Cosign, GitHub Attestations, Notation, cloud signer)
2. Allowed OIDC issuer/subject (repo, ref, workflow) or key IDs
3. Registry (GHCR/ECR/GCR/ACR/Harbor) and OCI referrers support
4. CI OIDC (`id-token: write`, WI) and protected environments
5. Admission stack already in GitOps (Kyverno, Gatekeeper, policy-controller)
6. Which envs require signatures; monorepo image matrix; tag/digest conventions
7. Neighbor jobs: SBOM (`sbom-ci-enforcement`), scan, deploy

**Precedence:** Extend existing identity allowlists. Surface tag-only prod pins,
verify-in-CI-only (no cluster gate), or unrotated shared keys.

## Workflow

### 1. Inventory ship path

List prod images, build jobs, registry, and final **runtime** digests (multi-arch
settled). Prefer trust root `image@sha256:…` only — never `:latest` alone.

### 2. Choose signing mode

| Mode | Prefer when | Notes |
| --- | --- | --- |
| **Keyless OIDC** | CI can OIDC to Fulcio | Identity = issuer + subject/regex; Rekor |
| **KMS / HSM** | Regulated key custody | Key refs in config, not PEM in git |
| **Cosign key pair** | Lab/bootstrap only | High risk; restrict and rotate |

Prefer keyless. Tighten verify: exact `certificate-identity` /
`certificate-oidc-issuer` (or documented regex), not any Fulcio cert.

### 3. Sign in CI (after push by digest)

1. Build/push; resolve immutable digest from build output.
2. Sign that digest in the same trusted workflow (protected env as required).
3. Keyless: enable OIDC; pin Cosign version.
4. Optional provenance attest — **SBOM generate/format/upload and fail-if-missing
   gates → `sbom-ci-enforcement`** (this skill only co-wires signature identity).
5. No signing material in logs; short-lived registry creds
   (`secrets-management-hygiene`, `ci-cd-pipeline-patterns`).

```bash
cosign sign --yes "$REGISTRY/$IMAGE@$DIGEST"
cosign verify \
  --certificate-identity-regexp 'https://github.com/ORG/REPO/.*' \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
  "$REGISTRY/$IMAGE@$DIGEST"
```

### 4. Verify and enforce

1. **Promote job:** `cosign verify` on the ship digest; fail closed.
2. **Admission:** policy-controller / Kyverno verifyImages / Gatekeeper / cloud
   “signed only” — match platform in use. Inputs: registry allowlist, digest
   required, issuer/subject, optional Rekor.
3. Rollout audit → warn → **enforce** on prod namespaces; document break-glass.
4. GitOps must not bypass admission with controllers that pull unsigned digests.
5. Multi-arch: verify index and/or platform digests per org rule. Unsigned legacy:
   time-boxed exception with owner/expiry.

### 5. Operate

Pin Cosign/policy versions. On workflow/repo rename, update identity regex before
enforce. Key mode: rotate KMS/keys and verify roots. Compromise: revoke trust,
re-sign clean digests, audit deploys. Apply `code-quality-standards` to policy YAML.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Cosign/Sigstore sign, keyless OIDC, verify, admission image policy | **This skill** | — |
| SBOM generate, publish, empty/missing CI gates, SBOM attest content | `sbom-ci-enforcement` | this if image sig co-required |
| Broad SBOM/SCA outside CI gate shape | `sbom-and-supply-chain` | this for signatures |
| Git commit signing | `signed-commits-basics` | not image provenance |
| Dockerfile/image contents | `dockerfile-best-practices` | this post-build |
| CI graph, OIDC job perms | `ci-cd-pipeline-patterns` | this for cosign steps |
| Keys/tokens, leak IR | `secrets-management-hygiene` | this for identity config |
| Policy/workflow quality | `code-quality-standards` | **always** on code |

**Required hand-off:** SBOM artifacts and **fail-if-missing-SBOM** →
**`sbom-ci-enforcement`**. This skill owns **image signature identity**, verify,
and admission; share digests as joint evidence.

## Output Checklist

- [ ] Prod images/digests inventoried; trust root is digest not tag
- [ ] Repo signer, OIDC/key policy, registry, admission stack read first
- [ ] Mode: keyless OIDC (preferred) or KMS/key with custody
- [ ] CI signs `image@sha256` after push; Cosign version pinned
- [ ] Verify uses explicit issuer + identity; fail closed
- [ ] Admission/deploy enforces signatures in scope envs (not CI-only)
- [ ] Multi-arch verify rule and time-boxed exceptions documented
- [ ] SBOM gates → `sbom-ci-enforcement`; Git signing → `signed-commits-basics`
- [ ] Secrets redacted; `ci-cd-pipeline-patterns` + CQS applied

## Rules

- Sign/verify **digests**; tags are not integrity. Prefer **keyless OIDC** with
  tight allowlists over long-lived PEM. Unsigned must not reach prod once enforce
  is on. Owned targets only; never paste keys or OIDC tokens. SBOM presence gates
  live in **`sbom-ci-enforcement`** — do not reinvent them here.
