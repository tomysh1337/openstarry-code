---
name: signed-commits-basics
description: >
  Configure and verify Git commit signing with GPG or SSH keys so hosts show a
  Verified badge and branch protection can require signed commits. Use when
  signed commits, commit signing, GPG sign, SSH signing key, git commit -S,
  Verified badge, required signed commits, gpg.program, user.signingkey, or
  commit signature hygiene. Not for container/image signatures—hand those off.
---

# Signed Commits Basics

Prove **who authored a commit** with a cryptographic signature (GPG or SSH)
that the forge maps to a trusted identity. Prefer the **host’s docs** and
**repo branch rules** over generic tutorials. Never paste private keys into
tickets, logs, or chat.

## When To Use

- Enabling **GPG** or **SSH** signing for `git commit` / `git tag`
- Fixing missing or failing **Verified** badges on a forge
- Enforcing **required signed commits** on protected branches
- Rotating, revoking, or documenting signing **key hygiene**
- Triggers: signed commits, `git commit -S`, `user.signingkey`, `gpg.format`,
  `commit.gpgsign`, SSH signing key, unverified commit, signature required

**Do not use as primary** for:

| Need | Skill instead |
| --- | --- |
| Commit message text | `commit-message-conventions` |
| Branch / PR process | `git-workflow-conventions` |
| Container/image provenance (cosign, sigstore) | `container-image-signing` |
| CI secrets / machine identity | `secrets-in-ci-pipelines` / `secrets-management-hygiene` |
| Code quality of the change | `code-quality-standards` |

## Repo Config First

Host and repository rules **outrank** this skill’s defaults.

1. **Contrib / security docs:** `CONTRIBUTING.md`, `SECURITY.md`, allowed key types
2. **Branch protection / rulesets:** “Require signed commits” and related checks
3. **Local git config:** `user.signingkey`, `commit.gpgsign`, `tag.gpgsign`,
   `gpg.format` (`openpgp` vs `ssh`), `gpg.ssh.program`
4. **Host account keys:** public GPG or SSH **signing** key uploaded; email verified
5. **Org policy:** hardware tokens, bot exceptions, squash/rebase signature rules
6. **CI bots:** org signing keys or explicit exemption—never commit bot private keys

**Precedence:** Fix identity mapping (email/UID, key on account) before disabling
signing when the host rejects a signature.

## Workflow

### 1. Choose signing backend

| Backend | Prefer when | Notes |
| --- | --- | --- |
| **SSH** | Simple setup; OpenSSH ≥ 8.0; host supports SSH signing | Less tooling friction |
| **GPG / OpenPGP** | Org already uses GPG, smartcards, or legacy docs | UID email must match forge |

Pick **one** primary method per machine identity.

### 2. Key hygiene

- Prefer a **dedicated signing** key/subkey; passphrase or hardware token
- Export only the **public** key to the forge; never share private material
- Record fingerprint, owner, creation date; keep a **revocation** path
- Compromised key: remove from host immediately, rotate, audit if required

### 3. Wire Git locally

```text
# SSH
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true

# GPG
git config --global user.signingkey <KEY_ID_OR_FPR>
git config --global commit.gpgsign true
```

- Align `user.name` / `user.email` with the forge-trusted identity
- Prefer non-global config when personal and work identities share a laptop
- Sign tags when release policy requires: `tag.gpgsign true` or `git tag -s`

### 4. Enroll, verify, require

1. Upload GPG public key or SSH key as a **signing** key (not auth-only)
2. Push a signed commit; confirm **Verified** (not Partial / Unverified)
3. Diagnose Unverified: wrong email, key missing/expired, auth-only SSH key,
   amend/rebase dropped the signature
4. Enable **Require signed commits** after contributors can sign; document
   bot/merge-queue exceptions so automation does not brick merges
5. Note squash-merge re-authorship: the merge actor must satisfy signature policy

### 5. Day-to-day checks

```text
git log --show-signature -1
git verify-commit HEAD
git commit -S -m "…"
```

After rotation: upload new public key, retire old; re-sign only if policy demands
(usually forward-only). Never force-push shared branches “to fix signatures”
without coordination.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| GPG/SSH commit signing, Verified badge, required signed commits | **This skill** | — |
| Commit subject/body wording | `commit-message-conventions` | this skill for `-S` / config |
| Branch protection / PR hygiene | `git-workflow-conventions` | this skill for signature requirement |
| Container/image signing (cosign, sigstore) | `container-image-signing` | not this skill |
| Private key storage / rotation process | `secrets-management-hygiene` | this skill for git wiring |
| CI bot signing / secret injection | `secrets-in-ci-pipelines` | `ci-cd-pipeline-patterns` |
| APK / mobile app signing | `apk-signing-and-integrity` | different artifact class |

**This skill** = Git commit/tag signatures and forge verification. Hand **image
and artifact signing** to `container-image-signing`.

## Output Checklist

- [ ] Repo/host signing policy and branch protection read first
- [ ] Backend chosen (SSH or GPG) for the identity used
- [ ] Public key enrolled; email/UID matches committer
- [ ] `user.signingkey` + `commit.gpgsign` (or explicit `-S`) set safely
- [ ] Sample push shows **Verified**; local `git log --show-signature` OK
- [ ] Required signed commits only after contributors can sign
- [ ] Bot/merge-queue path defined (sign or explicit exception)
- [ ] Passphrase/hardware protection; no private keys in repo or chat
- [ ] Rotation/revocation path known; compromised keys removed from host
- [ ] Container/image signing needs routed to `container-image-signing`
