---
name: pip-audit-and-constraints
description: >
  Audit Python dependencies with pip-audit and enforce install integrity via
  constraints files and hash-checking mode (pip --require-hashes, hashed
  requirements). Use when Python CVE/SCA findings, pip-audit CI failures,
  requirements.txt/constraints.txt drift, unpinned transitive deps, or
  pip hash-mode installs need setup or remediation — hand multi-ecosystem
  lock/pin policy to dependency-pinning-strategies, SBOM/provenance to
  sbom-and-supply-chain, and registry confusion to dependency-confusion.
---

# pip-audit and Constraints / Hashes

Make **Python installs auditable and integrity-checked**: run **pip-audit**
on the resolved tree, pin with **constraints**, prefer **hash-checking mode**
for CI and prod. Owns **pip-audit + constraints/hashes** only—not cross-
ecosystem lock strategy or license policy.

## When To Use

- Running or wiring **pip-audit** on `requirements*.txt`, lock exports, or a venv
- Introducing or fixing **`constraints.txt`** so transitives do not float
- Enabling **hash-checking mode** (`--require-hashes`, `# sha256=…` lines)
- Fixing version drift between CI, Docker, and prod Python installs
- Mentions: pip-audit, OSV/PyPI vulns, constraints, require-hashes, pip-compile,
  hashed requirements, `PIP_REQUIRE_HASHES`

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Cross-ecosystem lock / Renovate pin policy | `dependency-pinning-strategies` |
| SBOM, multi-tool SCA, provenance | `sbom-and-supply-chain` |
| License allow/deny, NOTICE | `license-compliance-scan` |
| Private vs public PyPI resolve order | `dependency-confusion` |
| Dockerfile digests / CI topology | `dockerfile-best-practices` / `ci-cd-pipeline-patterns` |

## Repo Config First

Repo and org Python supply-chain policy **outrank** defaults below.

1. **Manifests:** `requirements*.txt`, `constraints.txt`, `pyproject.toml`, Poetry/`uv`/`Pipfile` exports used by install jobs
2. **Install command:** plain `pip install -r` vs `--require-hashes`, `-c constraints.txt`, frozen exports
3. **Audit gates:** `pip-audit` args, fail levels, ignore/vuln exceptions
4. **Index policy:** `index-url` / `extra-index-url` / private mirror → `dependency-confusion` if dual-index; never weaken allowlists to “fix” hashes
5. **Prod vs dev scopes:** separate requirement files so prod audit/hash sets stay intentional
6. **Neighbors:** Dependabot/Renovate Python groups, SBOM jobs, base-image pins

**Precedence:** Follow the repo’s resolver (pip-tools, uv, Poetry export). Do not hand-edit hashed lines—regenerate with the same tool. Flag floating prod installs or hashes skipped in release images.

## Workflow

### 1. Establish the resolve path

1. Identify **which file(s)** CI and production install from (not ad-hoc `pip install pkg`).
2. Prefer **one compile/export path**: `pip-compile` / `uv pip compile` → locked/hashed requirements (+ optional constraints).
3. Separate **runtime** vs **dev/test**; audit both if either lands in build or runtime images.

### 2. Constraints vs pins

| Mechanism | Role |
| --- | --- |
| **Direct pins** | Exact top-level versions the app declares |
| **`constraints.txt`** (`-c`) | Cap/pin versions without adding install targets; stabilize transitives |
| **Fully locked requirements** | Every package==version install will touch (often with hashes) |
| **Hash lines** | File integrity; **not** a substitute for version pins alone |

1. Apps/services: no floating prod resolve (`>=` without lock/constraints is debt).
2. Use constraints when several requirement files share one version ceiling.
3. Prefer **one generated locked file** for deploy over multi-hop manual pins.
4. After upgrades, **regenerate** constraints and hashes together.

### 3. Hash-checking mode

1. Generate hashes via project tool (`pip-compile --generate-hashes`, `uv pip compile --generate-hashes`, or `pip hash`).
2. Install: `pip install --require-hashes -r requirements.txt` (or `PIP_REQUIRE_HASHES=1`). Every package needs hashes; partial files fail.
3. Prefer **wheels** in CI; pin and hash remaining sdists consciously (trusted build toolchain).
4. Private indexes: hash generation and CI must resolve the **same** host/artifact policy.
5. Never disable hashes in prod images to unblock a pin—regenerate instead.

### 4. Run pip-audit

1. Pin `pip-audit` itself in CI.
2. Audit the **shipped tree**: `pip-audit -r requirements.txt` and/or post-install venv/image site-packages.
3. Fix: upgrade → regenerate lock/constraints/hashes → require-hashes install → re-audit.
4. Ignores (`--ignore-vuln` / policy file): **owner, reason, expiry**; prefer upgrade/replace.
5. Fail CI on unfixed **prod** vulns per org severity; do not scan only partial direct deps.

### 5. CI wiring and verify

1. Order: **export** → **install --require-hashes** → **pip-audit** → tests.
2. Cache key = hash of requirement/constraint files; do not restore unhashed site-packages over a hashed contract.
3. Docker: copy lock/constraints first; hashed install; audit on same artifact set.
4. Pipeline layout → `ci-cd-pipeline-patterns`; config quality → `code-quality-standards`.
5. Verify: clean env hashed install succeeds; float/tamper fails closed; audit clean or time-boxed exceptions only; document who regenerates hashes and bot cadence.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| pip-audit, constraints, require-hashes | **This skill** | — |
| Cross-ecosystem locks / Renovate policy | `dependency-pinning-strategies` | this for Python hashes |
| SBOM / multi-ecosystem SCA | `sbom-and-supply-chain` | this for Python audit gate |
| License / NOTICE | `license-compliance-scan` | tree versions from this |
| PyPI dual-index / namespace confusion | `dependency-confusion` | this after registry fixed |
| CI stages / Docker install flags | `ci-cd-pipeline-patterns` / `dockerfile-best-practices` | this for audit+hash steps |
| Workflow/script quality | `code-quality-standards` | **always** on config |

**Hand-offs:** multi-ecosystem pins → `dependency-pinning-strategies`; SBOM portfolio → `sbom-and-supply-chain`; licenses → `license-compliance-scan`. Keep **this skill primary** for Python pip-audit + constraints/hashes.

## Output Checklist

- [ ] Prod (and relevant dev) resolve path identified; single compile/export story
- [ ] Constraints and/or fully locked requirements; no silent transitive float in prod
- [ ] Hash-checking mode on CI/prod install; hashes tool-regenerated (not hand-edited)
- [ ] `pip-audit` on shipped tree; tool pinned; CI fails per severity policy
- [ ] Vuln fixes via upgrade + regenerate; ignores have owner, reason, expiry
- [ ] Order: export → require-hashes install → audit → tests; cache keyed on lock files
- [ ] Index policy intact; dual-index issues → `dependency-confusion`
- [ ] Hand-off: pins/bots → `dependency-pinning-strategies`; SBOM → `sbom-and-supply-chain`
- [ ] `code-quality-standards` + `ci-cd-pipeline-patterns` on workflow config
