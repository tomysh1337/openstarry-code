---
name: acr-content-trust
description: >
  Enable, operate, and enforce Azure Container Registry (ACR) content trust and
  image integrity: legacy Docker Content Trust / Notary, modern Notation (ORAS)
  or Cosign signatures on ACR, digest-only promote, and pull/deploy gates for
  signed digests. Use when ACR content trust, Docker Content Trust with ACR,
  Notary keys for Azure registry, notation sign/verify against ACR, Azure Policy
  or AKS admission requiring signed images, or hardening org-owned ACR so unsigned
  tags cannot reach production — not Dockerfile authorship alone, generic Cosign
  outside ACR, or third-party registry hunting.
---

# ACR Content Trust

Prove **which identity published** images in **Azure Container Registry** and
ensure consumers use only **trusted digests**. Cover legacy **DCT/Notary** and
modern **Notation** or **Cosign** on ACR. Digest pins + fail-closed verify.
Owned or authorized ACR only.

## When To Use

- Enable or audit **ACR content trust** (DCT/Notary) or migrate off it
- Sign/verify images on ACR with **Notation**, **Cosign**, or residual DCT
- CI promote or cluster gates that reject **unsigned** ACR digests
- Mentions: ACR content trust, Docker Content Trust, Notary, notation + ACR,
  signed images Azure, `DOCKER_CONTENT_TRUST`

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Cosign keyless OIDC / Fulcio / non-ACR admission | `container-image-signing` |
| Dockerfile multi-stage, non-root, layer secrets | `dockerfile-best-practices` |
| SBOM generate/publish / missing-SBOM gates | `sbom-ci-enforcement` |
| Registry token lifecycle, leak IR | `secrets-management-hygiene` |
| ACR pull/push managed identity | `azure-managed-identity-basics` |
| Key Vault custody of signing keys | `azure-keyvault-basics` |
| Pipeline topology, OIDC, required checks | `ci-cd-pipeline-patterns` |
| Workflow/policy quality baseline | `code-quality-standards` |

## Workflow

### 1. Inventory registry and trust mode

Record authorization, subscription, ACR name(s), SKU, prod images, and consumers
(AKS, App Service, ACI, geo-replicas). Detect mode: **legacy DCT**, **Notation**,
**Cosign**, or none. Prefer gates on digests, never `:latest` alone.

```bash
az acr show -n "$ACR" -g "$RG" --query "{loginServer:loginServer,sku:sku.name,adminUserEnabled:adminUserEnabled}"
az acr repository list -n "$ACR" -o table
az acr manifest list-metadata -r "$ACR" -n "$REPO" --query "[].{digest:digest,tags:tags}" -o table
```

### 2. Choose / document signing model

| Mode | Prefer when | Notes |
| --- | --- | --- |
| **Notation** (ORAS / Notary Project) | Azure-first OCI artifacts | Trust store + policy; ACR as store |
| **Cosign / Sigstore** | Existing Cosign pipeline | Deep keyless/admission → `container-image-signing`; this skill owns ACR placement/gates |
| **Legacy DCT / Notary v1** | Residual ACR content-trust | Prefer migrate; document key backup |
| **None (tag only)** | Finding | Gap until digest + signature path exists |

Keys in **Key Vault / KMS** (`azure-keyvault-basics`); never commit PEM. Prefer
Notation or Cosign over long-lived DCT roots.

### 3. Sign after push by digest

1. Build/push; resolve immutable `loginServer/repo@sha256:…`.
2. Sign that digest in the same trusted CI job (protected env as required).
3. Auth: prefer **managed identity / OIDC** over admin user or long-lived
   passwords (`azure-managed-identity-basics`, `secrets-management-hygiene`).
4. Pin notation/cosign/az versions; redact tokens from logs.

```bash
ACR_LOGIN_SERVER="$(az acr show -n "$ACR" -g "$RG" --query loginServer -o tsv)"
IMAGE="$ACR_LOGIN_SERVER/$REPO@$DIGEST"
# az acr login / workload identity, then: notation sign|verify "$IMAGE"
# or cosign sign|verify per org policy
```

### 4. Verify and enforce

1. **Promote job:** verify signature on ship digest; fail closed.
2. **Runtime:** AKS admission (Ratify/Gatekeeper/Kyverno/policy-controller),
   Azure Policy, or deploy-stage checks — match the platform already in use.
3. Trust policy: allowlist signing identities/certs; deny unknown signers.
4. Rollout audit → warn → **enforce** on prod; time-box unsigned exceptions
   with owner + expiry.
5. Multi-arch: verify index and/or platform digests. Geo-replicas: confirm
   signatures/referrers available at pull region.

### 5. Operate and migrate

Disable ACR **admin user** when identity auth works; rotate exposed passwords.
If still on DCT: inventory keys, backup, plan cutover to Notation/Cosign.
Compromise: revoke trust, re-sign clean digests, audit deploys. Wire CI via
`ci-cd-pipeline-patterns`; CQS on policy YAML; SBOM → `sbom-ci-enforcement`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| ACR content trust, DCT/Notary on ACR, Notation/Cosign on ACR, ACR signature gates | **This skill** | — |
| Cosign keyless OIDC, Fulcio/Rekor, generic admission | `container-image-signing` | this for ACR store/auth |
| Dockerfile / image contents | `dockerfile-best-practices` | this post-push |
| SBOM generate, publish, missing-SBOM gates | `sbom-ci-enforcement` | this if sig co-required |
| Registry password/token leak, rotation | `secrets-management-hygiene` | this for revoke/re-sign |
| ACR pull/push MI, federated credentials | `azure-managed-identity-basics` | this for sign identity |
| Signing keys in Key Vault | `azure-keyvault-basics` | this for trust policy |
| Pipeline graph, OIDC, required checks | `ci-cd-pipeline-patterns` | this for sign/verify steps |
| Workflow/policy quality | `code-quality-standards` | **always** on CI code |

**Hand-off:** Cosign/Sigstore depth → `container-image-signing`. SBOM gates →
`sbom-ci-enforcement`. Owns **ACR trust, sign-on-digest, Azure consumer enforce**.

## Output Checklist

- [ ] Authorization and ACR/subscription recorded; owned/authorized only
- [ ] Prod images inventoried; trust root is **digest**, not floating tag
- [ ] Trust mode: Notation / Cosign / legacy DCT / gap documented
- [ ] CI signs `loginServer/repo@sha256` after push; tools pinned
- [ ] Verify uses explicit trust policy / identity allowlist; fail closed
- [ ] AKS/Azure Policy/deploy enforces signatures in scope envs (not CI-only)
- [ ] Multi-arch and geo-replica signature availability checked
- [ ] Admin user minimized; MI/OIDC auth; keys in Key Vault/KMS; secrets not logged
- [ ] DCT migration path if legacy still on; exceptions owned with expiry
- [ ] SBOM → `sbom-ci-enforcement`; Cosign → `container-image-signing`; CI+CQS applied

## Scope And Authorization

- **In scope:** Org-owned ACR, staging/prod under written engagement, lab
  subscriptions, IaC/policy for trust and admission, sign/verify of authorized digests.
- **Out of scope:** Third-party ACR mutation; foreign private repo mass pull;
  trust bypasses into shared prod; unapproved key export or root overwrite.
- Prefer **metadata, manifests, signature status** before bulk image download.
  Gate deletes, quarantine clears, and enforce-mode flips. Redact passwords,
  tokens, signing keys, and customer image paths. Unsigned prod after enforce
  → incident: block pull/deploy, re-sign good digests, audit — never paste keys.

