---
name: reproducible-builds-basics
description: >
  Achieve bit-for-bit or policy-defined equivalent rebuilds: hermetic inputs,
  SOURCE_DATE_EPOCH, pinned toolchains, and binary equivalence checks. Use when
  reproducible builds, rebuild verification, deterministic builds, SOURCE_DATE_EPOCH,
  build nondeterminism, diffoscope, or verifying that release artifacts match a
  clean rebuild from the same commit. Hand image signing to container-image-signing
  and SBOM/SCA inventory to sbom-and-supply-chain.
---

# Reproducible Builds Basics

A **reproducible build** yields the **same artifact bits** (or a documented
equivalence class) from the **same inputs**. Pin inputs, kill host/time leakage,
and **prove** with a second rebuild—not only a green CI job. Prefer the repo path.

## When To Use

- Library/app/binary releases **rebuild-identical** across machines or CI
- **`SOURCE_DATE_EPOCH`**, timestamp clamp, embed-path strip, hermetic pins
- **Binary equivalence**: hash/`cmp`, `diffoscope`, rebuild gates
- Debugging nondeterminism (timestamps, paths, archive order, gzip mtime)
- Triggers: reproducible builds, deterministic build, SOURCE_DATE_EPOCH,
  bit-identical, rebuild verify, diffoscope, hermetic build

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| SBOM / SCA / dep inventory | `sbom-and-supply-chain` |
| Image/cosign/Sigstore signing | `container-image-signing` |
| CI layout, caches, fork trust | `ci-cd-pipeline-patterns` |
| Dockerfile runtime hygiene | `dockerfile-best-practices` |
| Index / namespace confusion | `dependency-confusion` |
| Git commit Verified signatures | `signed-commits-basics` |
| Implementation quality baseline | `code-quality-standards` |

## Repo Config First

Existing build and release config **outranks** generic recipes below.

1. **Canonical build entry:** Makefile, Gradle, Cargo, Go, `pyproject`, npm,
   Bazel/Nix/Guix, msbuild—**one** official release path
2. **CI rebuild job:** workflows that already pin tools, containers, or epoch
3. **Lock / pin files:** language locks, `.tool-versions`, `rust-toolchain.toml`,
   action SHAs, base image **digests**
4. **Release packaging:** how wheel/jar/binary/installer is produced today
5. **Org bar:** bit-identical required vs normalized after agreed strip
6. **Repro helpers present:** `reprotest`, Nix, Bazel, diffoscope in CI
7. **Neighbor artifacts:** SBOM/sign via `sbom-and-supply-chain` /
   `container-image-signing`—do not reimplement those pipelines here

**Precedence:** Follow repo pins. Surface dual build paths, unpinned “latest”
toolchains, or release jobs that build once with no compare step.

## Workflow

### 1. Define artifact and success bar

1. Name **exact outputs** (path + format: ELF, wheel, jar, zip, …).
2. Choose bar: **bit-identical** (`cmp`/equal digests) or **normalized-identical**
   (after agreed strip of signatures, debug links, or known-volatile fields).
3. Record git commit/tag and the **official** release command.

### 2. Hermetic inputs inventory

| Input class | Pin / freeze |
| --- | --- |
| Source | Single clean commit; no dirty tree; no uncommitted codegen |
| Dependencies | Lockfiles + integrity; offline or allowlisted registry only |
| Toolchain | Compiler/JDK/Go/Rust/Node pins; container image **digest** |
| Environment | Fixed locale (e.g. `C.UTF-8`), `TZ=UTC`, stable `umask`/`PATH` |
| Build flags | Same feature flags and required env; document them |
| Parallelism | Deterministic schedule or fewer jobs when order leaks into output |

No network mid-build unless fetch is content-addressed and verified.

### 3. Neutralize common nondeterminism

1. Set **`SOURCE_DATE_EPOCH`** to a fixed Unix time (tagged commit or changelog
   timestamp). Propagate into compilers, archivers, and docs generators.
2. Avoid embedding **clocks**, **hostname**, **username**, **absolute cwd**, or
   random build-ids unless replaced with stable values.
3. Normalize **archive member order** and zip/gzip mtimes (`SOURCE_DATE_EPOCH`
   or explicit `--mtime`).
4. Prefer **path remapping** (`-ffile-prefix-map` or equivalent) so workspace
   roots do not differ by builder.
5. Stabilize custom packers’ **map/readdir order**. Treat PGO, download-latest,
   and “dirty `git describe`” embeds as repro hazards.

### 4. Rebuild twice and compare

1. Build A on clean tree → artifact A; record command, env, tool versions.
2. Build B in a **second** environment (other runner/container/path) with the
   **same pins** and `SOURCE_DATE_EPOCH`.
3. Compare: `sha256sum` / `cmp`; on mismatch run `diffoscope`.
4. Classify: timestamp → epoch/mtime; path → prefix-map; content → input drift.
   Fix **one cause per iteration**. Gate release on match (or strip + match).

### 5. Wire CI without redefining supply chain

- Tag/release: full rebuild + compare; optional PR smoke on changed packages.
- Hash-keyed caches; never silently mutate lockfiles (`ci-cd-pipeline-patterns`).
- Publish digests. **SBOM** → `sbom-and-supply-chain`; **sign** →
  `container-image-signing`. Apply `code-quality-standards` on build-script changes.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Determinism, SOURCE_DATE_EPOCH, hermetic pins, cmp/diffoscope | **This skill** | — |
| SBOM, SCA, lockfile inventory | `sbom-and-supply-chain` | this for rebuild proof |
| Cosign/Sigstore image or artifact signing | `container-image-signing` | this for what is signed |
| CI stages, caches, OIDC publish | `ci-cd-pipeline-patterns` | this for repro job content |
| Image multi-stage / runtime surface | `dockerfile-best-practices` | this for in-image determinism |
| Malicious index / resolve confusion | `dependency-confusion` | this for pin/offline builds |
| Git commit Verified signatures | `signed-commits-basics` | different trust layer |
| Build script quality / gate tests | `code-quality-standards` | **always** on code changes |

**This skill** = same-inputs → same-bits (or documented equivalence). Hand SBOM/SCA
to `sbom-and-supply-chain` and signature/provenance to `container-image-signing`.

## Output Checklist

- [ ] Official artifact paths and bit-identical vs normalized bar documented
- [ ] Repo build entry, locks, toolchain pins, and CI path inventoried first
- [ ] Hermetic inputs: clean commit, lockfiles, toolchain/image digests, fixed locale/TZ
- [ ] `SOURCE_DATE_EPOCH` (or equivalent) set and consumed by packers/compilers
- [ ] Path/host/time leakage addressed (prefix-map, no hostname, stable archive order)
- [ ] Two independent rebuilds compared (`sha256`/`cmp`; `diffoscope` on mismatch)
- [ ] Nondeterminism fixed iteratively; residual exceptions have owner + review date
- [ ] CI/release records digests; caches cannot change inputs silently
- [ ] SBOM → `sbom-and-supply-chain`; signing → `container-image-signing`
- [ ] `code-quality-standards` applied when build/CI scripts change
