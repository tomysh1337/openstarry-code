---
name: rust-cargo-vet-basics
description: >
  Set up and gate Rust supply-chain audits with cargo-vet: supply-chain/
  config.toml and audits.toml, exemptions, peer audit imports, certify
  criteria (safe-to-run / safe-to-deploy), inspect/diff workflow, and CI
  fail-closed checks for owned Cargo workspaces. Use when cargo-vet,
  cargo vet, supply-chain audits.toml, config.toml exemptions, Mozilla
  cargo-vet, trusted audits import, safe-to-deploy criteria, unaudited
  crates gate, or wiring cargo-vet into GitHub Actions/GitLab CI.
---
# Rust Cargo Vet Basics
Own **local and CI `cargo-vet`** for Rust crates and workspaces: init the
`supply-chain/` store, import trusted peer audits, shrink exemptions, certify
with explicit criteria, and fail pipelines when the locked graph is not fully
vetted. Prefer the repo toolchain and existing cargo jobs. Hand **CVE/RustSec**
to `cargo-audit-workflow`; lock/pin policy to `dependency-pinning-strategies`;
license/ban/source policy to cargo-deny workflows when present.

## When To Use
- Adding or fixing **`cargo-vet`** (init, check, certify, CI gate)
- Managing **`supply-chain/config.toml`** and **`supply-chain/audits.toml`**
- Importing peer audits (Mozilla, Bytecode Alliance, Google, etc.)
- Reducing **exemptions** / unaudited crates; certifying `safe-to-run` or
  `safe-to-deploy`
- Keywords: cargo-vet, supply-chain audits, exemption table, trusted audits,
  `cargo vet check`, certify criteria
Do **not** use as primary for: RustSec/CVE → `cargo-audit-workflow`; lockfile
pins → `dependency-pinning-strategies`; multi-lang SBOM/SCA →
`sbom-and-supply-chain`; SBOM presence → `sbom-ci-enforcement`; CVE clocks →
`vulnerability-sla-process`; pipeline layout → `ci-cd-pipeline-patterns`; Rust
style → `rust-style-and-clippy`; code quality → `code-quality-standards`.

## Repo Config First
Repo and org policy **outrank** defaults below.
1. **`Cargo.toml` / workspace:** members; optional `[package.metadata.vet]` /
   `[workspace.metadata.vet]` store path
2. **`Cargo.lock`:** committed for apps/binaries; vet the **locked** graph
3. **Existing `supply-chain/`:** `config.toml`, `audits.toml`, imports,
   exemptions—extend, do not rewrite without review
4. **CI:** cargo setup, cache keys, required check names
5. **Tool pin:** fixed `cargo-vet` version; no floating latest on gates
6. **Criteria policy:** which crates need `safe-to-deploy` vs `safe-to-run`
7. **Network:** crates.io / private registries; remote audit import URLs
8. **Neighbors:** `cargo-audit`, cargo-deny, Dependabot/Renovate, SBOM, branch
   protection
Extend the real lockfile root; do not invent a divergent store path unless
metadata already sets one.

## Workflow
### 1. Install, init, check
```bash
cargo install cargo-vet --version 0.10.0 --locked   # org-approved pin
cargo vet --version
cargo vet init          # once: creates supply-chain/
cargo vet               # check unpaid audit debt
cargo vet --locked      # prefer in CI when lock must not change
```
Match CI Rust toolchain (`rust-toolchain.toml`). Document the pin in workflow
or Makefile. Default store: `supply-chain/` next to `Cargo.lock` (`audits.toml`
+ `config.toml`). First init typically records third-party deps as
**exemptions** (unaudited debt). Goal: shrink exemptions via imports and
first-party certifies—not grow them silently.
### 2. Imports, exemptions, and policy
| Concern | Practice |
| --- | --- |
| Peer audits | `[imports.<name>]` URL to trusted `audits.toml` (e.g. Mozilla) |
| Exemptions | Explicit crate/version + reason; **time-boxed debt** |
| Criteria | `safe-to-run` (dev/CI) vs `safe-to-deploy` (shipped/prod) |
| Policy / fmt | Tune `[policy.<crate>]` if required; `cargo vet fmt` after edits |
Never mass-exempt new deps without owner + expiry. Prefer importing reputable
audits before re-auditing popular crates from scratch.
### 3. Inspect, certify, maintain
```bash
cargo vet suggest
cargo vet inspect <crate> <version>
cargo vet diff <crate> <from> <to>
cargo vet certify <crate> <version>   # after real review; pick criteria
cargo vet prune                       # drop unused entries carefully
```
| Situation | Action |
| --- | --- |
| Covered by imported audit | Rely on import unless policy criteria differ |
| New/unaudited dep | Inspect; certify after review; or temporary exemption |
| Version bump | `diff` old→new; re-certify or confirm import covers |
| Dev-only vs prod path | `safe-to-run` if never shipped; else prefer `safe-to-deploy` |
Certification is a **human assurance record**, not a CVE scan—pair with
`cargo-audit-workflow` for RustSec.
### 4. CI gate and verify
1. Install Rust from repo toolchain; restore cargo cache.
2. Ensure **`Cargo.lock`** present; fetch with `--locked` as appropriate.
3. Install **pinned** `cargo-vet`; run `cargo vet --locked` at each shippable
   lockfile root (matrix monorepos).
4. **Fail closed** on unpaid audit debt (unless staged rollout with owner/expiry).
5. Commit `supply-chain/` with dep PRs; required check on main.
6. Never print registry tokens; redact private audit URL credentials.
```yaml
- uses: dtolnay/rust-toolchain@stable
- run: cargo install cargo-vet --version 0.10.0 --locked
- run: cargo vet --locked
```
**Verify:** same pin/command as CI green; intentional unaudited dep fails gate;
every independent lock/store covered; secrets redacted.

## Routing
| Situation | Primary | Helper |
| --- | --- | --- |
| cargo-vet init/check/certify, supply-chain store, CI gate | **This skill** | — |
| RustSec / cargo-audit CVE advisories | `cargo-audit-workflow` | this for criteria gate |
| Cargo.lock pin/update bots, frozen installs | `dependency-pinning-strategies` | this after lock exists |
| Multi-lang SBOM / SCA or SBOM presence gate | `sbom-and-supply-chain` / `sbom-ci-enforcement` | this for Rust vet |
| CVE clocks, exception tickets | `vulnerability-sla-process` | this for exemption evidence |
| Workflow YAML, caches, required checks | `ci-cd-pipeline-patterns` | this for job body |
| Rust style / Clippy | `rust-style-and-clippy` | after dep bumps compile |
| Fix quality, tests, review baseline | `code-quality-standards` | **always** on code/CI changes |
Keep **this skill primary** until store layout, imports, and gate are correct.

## Output Checklist
- [ ] Workspace roots, `Cargo.lock`, existing `supply-chain/`, CI cargo job read first
- [ ] `cargo-vet` pinned; store path correct; TOML committed
- [ ] Peer imports where trusted; exemptions owner+expiry, not mass-blind
- [ ] Criteria clear (`safe-to-run` vs `safe-to-deploy`); certify after inspect/diff
- [ ] CI: `cargo vet --locked` fail-closed; monorepo matrix complete
- [ ] Dep bumps update store + lock; tests pass; secrets redacted; same pin as CI
- [ ] Hand-offs: `cargo-audit-workflow`, `dependency-pinning-strategies`,
      `vulnerability-sla-process`, `sbom-and-supply-chain` / `sbom-ci-enforcement`,
      `code-quality-standards`
- [ ] Rules: repo-first store; imports before re-audit; no silent exemption growth
