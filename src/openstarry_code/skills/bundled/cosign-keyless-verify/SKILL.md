---
name: cosign-keyless-verify
description: >
  Verify Cosign keyless (Sigstore/Fulcio/Rekor) signatures on images and
  artifacts with tight identity and OIDC issuer allowlists. Use when
  cosign verify, --certificate-identity, --certificate-oidc-issuer,
  keyless Sigstore check, Rekor transparency, signed digests in CI or
  admission, or offline/bundle verify — not for long-lived PEM key signing
  as the primary mode (see container-image-signing).
---

# Cosign Keyless Verify

Prove an artifact was signed by a **trusted OIDC identity** via **Sigstore**
(Fulcio short-lived cert + optional Rekor), not a shared PEM key. Always
verify by **digest**. Owned registries, CI, and clusters only.

## When To Use

- `cosign verify` on OCI images/blobs signed **keyless** (OIDC → Fulcio)
- Setting `--certificate-identity` / `--certificate-identity-regexp` and
  `--certificate-oidc-issuer` (or issuer-regexp) allowlists
- CI promote gates or admission that must fail closed on bad identity
- Offline/bundle verify when Rekor or public good is unreachable
- Mentions: keyless verify, Fulcio cert, Sigstore, cosign identity check

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| End-to-end sign + admission design | `container-image-signing` |
| SBOM generate / fail-if-missing gates | `sbom-ci-enforcement` |
| Git commit/tag signatures | `signed-commits-basics` |
| CI graph, OIDC job perms, fork trust | `ci-cd-pipeline-patterns` |
| Key/token storage, leak IR | `secrets-management-hygiene` |
| Policy/script quality | `code-quality-standards` |

## Repo Config First

Repo and platform policy **outrank** examples below.

1. Existing verify jobs, policy-controller / Kyverno verifyImages, scripts
2. Allowed **OIDC issuer** and **identity** (exact or documented regexp)
3. Registry; OCI referrers vs legacy signature attach
4. Cosign version pin; public good vs private Fulcio/Rekor
5. Envs that require verify; bundle/offline needs (air-gap, mirror)
6. Neighbors: sign job (`container-image-signing`), SBOM, deploy

**Precedence:** Extend issuer/identity allowlists. Surface tag-only pins,
“any Fulcio cert” verify, or CI-only checks with no deploy gate.

## Workflow

### 1. Pin the trust root (digest + identity)

1. Ship target = `name@sha256:…` (index or platform digest per org rule). Never
   treat a mutable tag alone as the verify target.
2. Allowlist expected OIDC issuer (GitHub Actions, GitLab, cloud WI) and
   certificate identity (repo, ref, workflow subject).
3. Prefer **exact** identity; regexp only with bounds (org/repo/workflow,
   protected refs) — not open `.*` on the whole subject.

### 2. Online keyless verify (default)

```bash
cosign verify \
  --certificate-identity 'https://github.com/ORG/REPO/.github/workflows/release.yml@refs/heads/main' \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
  "$REGISTRY/$IMAGE@$DIGEST"
```

| Flag / concern | Guidance |
| --- | --- |
| `--certificate-identity-regexp` | Bound to org/repo/workflow; review before expand |
| `--certificate-oidc-issuer-regexp` | Prefer exact issuer when one IdP |
| Rekor / multi-arch / Cosign pin | Public Rekor unless private; verify index/platforms per policy; pin Cosign with sign job |

Fail closed: non-zero exit; no soft-warn on prod promote paths.

### 3. Offline / bundle verify

Prefer a **signature bundle** from sign time when air-gapped or Rekor is down.
Use Cosign flags for your version; do not invent alternate roots without review.
Enforce the **same** issuer + identity constraints. Document TUF/root refresh
if using private or mirrored Sigstore.

### 4. Promote, admission, and failures

1. **CI promote:** verify the exact ship digest; block deploy on failure. Verifier
   job OIDC ≠ signer identity under test.
2. **Admission:** Kyverno / policy-controller / Gatekeeper strings must **match**
   CI allowlists (one source of truth). Update allowlists before enforce on
   workflow/IdP changes; re-verify known-good digests.
3. Break-glass: time-boxed, owner, expiry.

| Symptom | Typical cause |
| --- | --- |
| No signatures found | Wrong digest, unsigned, referrers/registry mismatch |
| Identity / issuer mismatch | Workflow path/ref change; wrong IdP URL; loose/tight regexp |
| Rekor / network errors | Need offline/mirror; transient public good |
| Passes with loose regexp | Policy gap — tighten before claiming assurance |

Evidence: command, Cosign version, digest, issuer, identity, exit code. Redact
creds/tokens. Apply `code-quality-standards` to verify scripts and policy YAML.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Keyless `cosign verify`, issuer/identity allowlists, bundle/offline | **This skill** | — |
| Sign flow, key vs keyless, full admission rollout | `container-image-signing` | this for verify steps |
| SBOM presence / format CI gates | `sbom-ci-enforcement` | this if sig + SBOM co-required |
| Git signing badges | `signed-commits-basics` | not image/artifact keyless |
| Pipeline OIDC perms, environments | `ci-cd-pipeline-patterns` | this for verify command/policy |
| Secrets, token leak IR | `secrets-management-hygiene` | this for identity config |
| Script/policy quality | `code-quality-standards` | **always** on code |

Keep **this skill primary** for keyless **verification**. Hand signing architecture
and admission product choice to `container-image-signing`.

## Output Checklist

- [ ] Target is digest (`@sha256:…`), not tag alone
- [ ] Repo verify jobs, allowlists, registry, Cosign pin read first
- [ ] Issuer + identity (or bounded regexp) match signer; no “any Fulcio”
- [ ] CI promote and/or admission fail closed; multi-arch rule documented
- [ ] Offline/bundle path when air-gap/Rekor constraints apply
- [ ] Failure triage noted; evidence captured; secrets redacted
- [ ] Routed: sign/admission → `container-image-signing`; SBOM →
      `sbom-ci-enforcement`; CI trust → `ci-cd-pipeline-patterns`; CQS on scripts

## Rules

- Keyless verify is only as strong as the **issuer + identity** allowlist.
- Digests are the integrity root; prefer exact identity over open regexps.
  Owned pipelines only; never paste OIDC tokens or private keys into logs.
