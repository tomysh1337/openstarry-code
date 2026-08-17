---
name: cargo-audit-workflow
description: >
  Run and gate Rust dependency vulnerability checks with cargo-audit locally
  and in CI: RustSec advisory DB, Cargo.lock scans, JSON outputs, ignore
  policy, version pins, and actionable upgrade paths for owned crates. Use
  when cargo-audit, RustSec, RUSTSEC-*, Cargo CVE scanning, rustsec advisory
  database, cargo audit CI gate, yanked crate warnings, or wiring cargo-audit
  into GitHub Actions/GitLab CI for Rust workspaces.
---

# Cargo Audit Workflow

Own **local and CI `cargo-audit`** for Rust crates: pin the tool, require a
committed **`Cargo.lock`**, interpret RustSec advisories, fail pipelines on
policy findings, and fix-then-recheck. Prefer repo toolchain and CI jobs.
Hand multi-lang SCA/SBOM to supply-chain skills; lock/pin policy to
`dependency-pinning-strategies`.

## When To Use

- Adding or fixing **`cargo-audit`** in developer workflow or CI
- Interpreting **RustSec** findings (`RUSTSEC-YYYY-NNNN`), patched versions,
  yanked crate warnings
- Scanning workspace trees from a committed **`Cargo.lock`**
- Failing PRs/main on known Rust crate vulns; JSON artifacts for triage
- Keywords: cargo-audit, RustSec, rustsec.org, Cargo CVE gate, advisory DB

Do **not** use as primary for: lockfile pins → `dependency-pinning-strategies`;
SBOM/SCA → `sbom-and-supply-chain` / `sbom-ci-enforcement`; CVE clocks →
`vulnerability-sla-process`; pipeline layout → `ci-cd-pipeline-patterns`;
Rust style → `rust-style-and-clippy`; quality → `code-quality-standards`.

## Repo Config First

Repo and org policy **outrank** defaults below.

1. **`Cargo.toml` / workspace:** package roots, `[workspace].members`
2. **`Cargo.lock`:** committed for apps; lock CI for library repos
3. **CI workflows:** cargo setup, cache keys, required check names
4. **Tool version:** pin `cargo-audit`—not floating latest on gates
5. **Config:** `.cargo/audit.toml`—ignores, DB URL, thresholds if used
6. **Gate policy:** all advisories vs severity floor; exception/expiry
7. **Network:** crates.io / private registries; optional advisory DB mirror
8. **Neighbors:** Dependabot/Renovate, SBOM, cargo-deny, branch protection

Extend the real build job’s workspace root; do not invent a divergent path.

## Workflow

### 1. Install and pin

```bash
cargo install cargo-audit --version 0.21.2 --locked   # org-approved pin
cargo audit --version
```

Match CI Rust (`rust-toolchain.toml` / rustup) to the project. Document the
pin in the workflow or Makefile. Avoid unpinned installs on release gates.

### 2. Local scan

From the workspace root that owns **`Cargo.lock`**:

```bash
cargo fetch --locked
cargo audit
cargo audit --json > cargo-audit.json
```

Audits the **locked dependency graph**. Without a lockfile, results are weak
or blocked—commit per app policy (`dependency-pinning-strategies`). Record
command, path, tool version, DB freshness. Optional: `--db <path>` for a
mirrored RustSec DB in air-gapped CI.

### 3. Config and ignores

Prefer **repo-local** `.cargo/audit.toml` over ad-hoc flags. Ignore only with
explicit `RUSTSEC-…` id plus **owner + expiry**. Treat yanked/unmaintained as
signals—never mass-ignore (`vulnerability-sla-process`).

### 4. CI gate

1. Install Rust from toolchain file; restore cargo cache.
2. Ensure **`Cargo.lock`** present; prefer `--locked` on builds.
3. Install **pinned** `cargo-audit`; run at each independent lockfile root.
4. **Fail closed** per policy; upload JSON as artifact—not log-only.
5. Required checks via `ci-cd-pipeline-patterns`; never print registry tokens.

```yaml
- uses: dtolnay/rust-toolchain@stable
- run: cargo install cargo-audit --version 0.21.2 --locked
- run: cargo audit
```

### 5. Triage, fix, verify

| Finding shape | Action |
| --- | --- |
| Direct dep, fix published | Bump; `cargo update -p <crate>`; test |
| Transitive only | Upgrade intermediate; avoid eternal `[patch]` |
| Yanked / no fix / N/A | Upgrade, owner+expiry ignore, or document proof |

After bumps: `cargo check` / `cargo test` with `--locked` as appropriate.
**Verify:** same pin as CI green; intentional old vuln fails gate; all
shippable lockfile roots in matrix; redact private URLs/creds.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| cargo-audit local/CI, RustSec gate | **This skill** | — |
| Cargo.lock pin/update bots | `dependency-pinning-strategies` | this after lock exists |
| Multi-lang SBOM / SCA | `sbom-and-supply-chain` | this for Rust audit gate |
| SBOM presence/attest gate | `sbom-ci-enforcement` | this for vuln content |
| CVE clocks, exceptions | `vulnerability-sla-process` | this for detection evidence |
| Workflow YAML, required checks | `ci-cd-pipeline-patterns` | this for job body |
| Rust style / Clippy | `rust-style-and-clippy` | after vuln fix compiles |
| Fix quality, tests, review | `code-quality-standards` | **always** on code/CI changes |

Keep **this skill primary** until pin, lockfile, and gate behavior are correct.

## Output Checklist

- [ ] Repo toolchain, workspace roots, `Cargo.lock`, existing CI cargo job read first
- [ ] `cargo-audit` version pinned (not floating latest on gates)
- [ ] Scan from lockfile root(s); JSON uploaded; tool + DB context recorded
- [ ] `.cargo/audit.toml` documents ignores with owner/expiry
- [ ] Gate policy clear; required check enforced; monorepo matrix complete
- [ ] Locked updates + tests pass; secrets redacted; CI pin/command verified
- [ ] Hand-offs: `dependency-pinning-strategies`, `vulnerability-sla-process`,
      `sbom-and-supply-chain` / `sbom-ci-enforcement`, `code-quality-standards`
- [ ] Rules: repo-first pin; no silent mass-ignore; authorized crates only
