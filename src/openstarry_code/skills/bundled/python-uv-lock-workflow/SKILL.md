---
name: python-uv-lock-workflow
description: >
  Own Astral uv lockfiles and install gates: uv.lock generation, upgrade, check,
  frozen sync, dependency groups/extras, index policy, and CI reproducibility for
  Python projects. Use when uv.lock, uv lock, uv sync --frozen, uv lock --check,
  uv lock --upgrade, pyproject dependency resolution with uv, locked installs,
  uv workspace members, or regenerating/resolving uv locks are in scope.
---

# Python uv Lock Workflow

Own **`uv.lock` lifecycle and reproducible installs** with Astral **uv**: resolve,
commit, check, and sync from lock without silent rewrite. Prefer the repo’s
`pyproject.toml`, indexes, and CI flags. Packaging layout → `python-packaging-modern`;
multi-ecosystem pin policy → `dependency-pinning-strategies`.

## When To Use

- Creating, reviewing, or fixing **`uv.lock`** next to `pyproject.toml`
- **`uv lock`**, **`uv lock --upgrade`**, **`uv lock --check`**, **`uv sync --frozen`/`--locked`**
- Dependency/group changes that must keep lock and manifest in sync
- CI lock drift, divergent trees, or non-reproducible installs
- uv **workspaces**, platform markers, optional extras
- Keywords: uv.lock, uv lock, frozen sync, locked install, uv resolve, Astral uv

Do **not** use as primary for: packaging/layout → `python-packaging-modern`;
cross-ecosystem pins → `dependency-pinning-strategies`; pip-tools/`pip-audit` →
`pip-audit-and-constraints`; style → `python-style-and-typing`; SBOM →
`sbom-and-supply-chain`; registry confusion → `dependency-confusion`.

## Repo Config First

Repository and org Python policy **outrank** defaults below.

1. **`pyproject.toml`:** `[project]` deps, optional-dependencies, dependency-groups,
   `[tool.uv]` (indexes, sources, package flags), Python version / requires-python
2. **`uv.lock`:** present for apps/services; commit policy; workspace members
3. **Install story:** single tool path (uv vs Poetry vs pip-tools)—do not mix generators
4. **CI jobs:** exact `uv lock --check` / `uv sync --frozen` (or project equivalents)
5. **Indexes:** default PyPI, private indexes, `[[tool.uv.index]]`, credentials via env/CI secrets
6. **Neighbors:** Renovate/Dependabot for Python, SCA/audit job, Docker base image Python pin

**Precedence:** Follow existing uv major and CI flags. Flag local-only index URLs,
hand-edited lock chaos, or installs that rewrite lock on every CI run.

## Workflow

### 1. Inventory

Read `pyproject.toml` and `uv.lock` (workspace roots too). Note Python constraint,
direct deps, groups/extras, path/git sources, and custom indexes. Record the **uv**
version used locally vs CI. List whether the artifact is an **app** (must lock) or
published **library** (may float consumer ranges but still lock CI/dev).

### 2. Resolve and commit

After any dependency or constraint edit:

```bash
uv lock
uv lock --check          # CI / pre-commit: fail if lock would change
uv sync --frozen         # or --locked per repo docs; no resolve rewrite
```

- Commit **`pyproject.toml` and `uv.lock` together**.
- Prefer `uv add` / `uv remove` / `uv lock` over hand-editing the lock.
- Do not delete `uv.lock` to “fix conflicts”—regenerate with the team’s uv major.
- One resolver story: do not regenerate with Poetry/pip-tools into a uv project.

### 3. Upgrade safely

| Goal | Command posture | Notes |
| --- | --- | --- |
| Full tree refresh | `uv lock --upgrade` | Review large diffs; run tests |
| One package | `uv lock --upgrade-package PKG` | Prefer over blanket upgrade for hotfixes |
| Pin / floor | Edit `pyproject` constraint then `uv lock` | Ranges state intent; lock freezes ship |
| Platform markers | Keep markers in manifest; re-lock | Verify multi-OS CI if markers matter |

Review lock diffs for new packages, major jumps, unexpected indexes/URLs, and
yanked versions. Record intentional pins with owner and exit criteria.

### 4. Groups, extras, workspaces

1. **Dependency groups** (dev, lint, docs): lock includes them; sync only what
   CI/runtime needs (`--group` / `--no-dev` as documented).
2. **Extras / optional-dependencies:** resolve extras that ship or are CI-tested.
3. **Workspaces:** lock from the workspace root; avoid divergent per-member locks
   unless the repo already does and CI matches.
4. **Path / git sources:** pin commits or tags; avoid floating branches on release.

### 5. Indexes and private packages

Configure indexes in `pyproject` / uv config—not ad-hoc one-off CLI that only one
developer runs. Authenticate private indexes via CI secrets and local env
(netrc/keyring as org standard). Never commit tokens. Registry namespace risks
→ `dependency-confusion`. Hashed requirements export for non-uv consumers →
`pip-audit-and-constraints` / `uv export` when the repo already uses that path.

### 6. CI gate and verify

1. Install pinned **uv** (or `astral-sh/setup-uv` with version pin)—not floating latest on gates.
2. **`uv lock --check`** (or fail if `uv lock` would rewrite) on every PR.
3. **`uv sync --frozen`** (or `--locked`) before test/lint/build.
4. Cache keyed on `uv.lock` (+ uv version) per `ci-cd-pipeline-patterns`.
5. After dep bumps: tests + typecheck per project; regenerate SBOM if release policy requires.

**Verify:** clean runner install matches lock; deliberate dep bump updates lock
coherently; `--check` fails when lock is stale; no secrets in lock or logs.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| uv.lock, uv lock/sync/check, frozen installs | **This skill** | — |
| pyproject packaging, wheels, src layout, publish | `python-packaging-modern` | this for lock after manifest |
| Cross-ecosystem lock/bot pin strategy | `dependency-pinning-strategies` | this for uv-specific commands |
| pip-compile hashes, pip-audit, constraints.txt | `pip-audit-and-constraints` | this when source of truth is uv |
| Python style / types | `python-style-and-typing` | after env is locked |
| SBOM / SCA inventory | `sbom-and-supply-chain` | this for exact tree |
| Private index / namespace confusion | `dependency-confusion` | this for uv index config |
| CI layout, caches, required checks | `ci-cd-pipeline-patterns` | this for job body |
| Implementation quality | `code-quality-standards` | **always** on app/tooling changes |

Keep **this skill primary** until lock, sync flags, and CI check behavior are correct.

## Output Checklist

- [ ] `pyproject.toml`, `[tool.uv]`, indexes, and existing `uv.lock` inventoried
- [ ] uv version aligned between local and CI (pinned on gates)
- [ ] After dep edits: `uv lock` run; `pyproject.toml` + `uv.lock` committed together
- [ ] CI: `uv lock --check` (or equivalent) + `uv sync --frozen`/`--locked`
- [ ] Upgrades scoped (`--upgrade-package` vs full); lock diffs reviewed
- [ ] Groups/extras/workspaces resolved consistently with runtime and CI
- [ ] Private index auth via secrets; no tokens in git; single installer story
- [ ] Tests (and export/SBOM if required) after lock change
- [ ] Hand-offs: packaging, pins, audit, style, `code-quality-standards`
