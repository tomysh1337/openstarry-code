---
name: pypi-trusted-publishing
description: >
  Configure and review PyPI (and TestPyPI) Trusted Publishing so CI publishes
  Python packages via short-lived OIDC identity instead of long-lived API tokens.
  Use when designing or auditing PyPI OIDC publishers, GitHub Actions or GitLab
  publish jobs, pypa/gh-action-pypi-publish, pending publishers, environment-bound
  releases, retiring PYPI_API_TOKEN secrets, or hardening owned package release
  pipelines against token theft and fork-PR publish abuse.
---

# PyPI Trusted Publishing

Prove **which CI identity** may upload to **PyPI / TestPyPI** using **OIDC
Trusted Publishing** (no long-lived API token in secrets). Bind publish rights to
**forge + repo + workflow + environment**. Prefer over static `PYPI_API_TOKEN`.

## When To Use

- Adding or reviewing **Trusted Publishers** on PyPI/TestPyPI
- Wiring **GitHub Actions** / **GitLab CI** release jobs for OIDC publish
- Using or reviewing **`pypa/gh-action-pypi-publish`** (or equivalent OIDC upload)
- Migrating off long-lived **API tokens** / `__token__` secrets in CI
- Mentions: Trusted Publishing, PyPI OIDC, pending publisher, TestPyPI first,
  no `PYPI_API_TOKEN`

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| General CI stages, cache, fork isolation | `ci-cd-pipeline-patterns` |
| Secret inventory, rotation, leak IR | `secrets-management-hygiene` |
| CI secret scopes / multi-cloud OIDC | `secrets-in-ci-pipelines` |
| SBOM gates / dependency confusion | `sbom-ci-enforcement` / `dependency-confusion` |
| Workflow/script quality baseline | `code-quality-standards` |

## Repo Config First

Repo, org, and PyPI project settings **outrank** examples below.

1. Existing publish workflows (`.github/workflows/*`, GitLab release jobs)
2. PyPI / TestPyPI project name, owners, current publishers or tokens
3. Release trigger: tag, `workflow_dispatch`, GitHub Release, protected env
4. Build backend (`pyproject.toml`) and artifact dirs (sdist/wheel)
5. TestPyPI dry-run usage; branch protection and environment approvals
6. Neighbor jobs: signing, SBOM, provenance; org action-pin / OIDC policy

**Precedence:** Extend existing publisher allowlists. Surface org-wide or
any-workflow trust, token+OIDC dual publish without retirement, or publish from
untrusted PR contexts.

## Workflow

### 1. Inventory the ship path

1. List package names (PyPI project vs import), owners, indexes (prod vs TestPyPI).
2. Map who can cut a release (token holders, maintainers, bots).
3. Find jobs still injecting `__token__` / `TWINE_PASSWORD` / `PYPI_API_TOKEN`.
4. Record trust targets: **repository**, **workflow path**, **environment** (or GitLab claims).

### 2. Register the Trusted Publisher (PyPI side)

1. Prefer **TestPyPI** first for greenfield or migration proof.
2. Add publisher matching the forge: GitHub owner/repo + workflow file +
   environment; GitLab path/claims per current PyPI docs.
3. Use a **pending publisher** when the project does not exist yet; first
   successful OIDC upload claims the name under policy rules.
4. Bind **tightly**: one workflow + protected environment for prod — not
   any-workflow or org-wide for production indexes.
5. Document publisher rows (index, project, forge, workflow, env, owner).

### 3. Wire CI for OIDC publish

1. Publish only from **trusted refs** (tags and/or default branch + environment
   protection). Never grant OIDC publish to fork `pull_request` jobs.
2. Permissions: `id-token: write` plus least other rights (`contents: read`
   typical). No blanket `write-all`.
3. Build sdist/wheel in CI; publish the **same** artifacts (build once, upload once).
4. Prefer `pypa/gh-action-pypi-publish` or supported OIDC twine; **pin versions**.
5. Separate TestPyPI vs prod publishers/jobs; optional env reviewers for prod.

```yaml
# Sketch — pin action versions per org policy.
jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions: { contents: read, id-token: write }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install build && python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
        # repository-url: https://test.pypi.org/legacy/  # TestPyPI only
```

### 4. Migrate, operate, verify

1. Prove OIDC on TestPyPI; enable prod publisher; run one controlled release.
2. **Revoke** CI-only API tokens; remove secrets (`secrets-management-hygiene`).
3. Break-glass only if required: short-lived manual token, owner-held, time-boxed.
4. Re-check publishers after repo rename, workflow path change, or env rename.
5. Confirm uploads attribute to the OIDC publisher; fork/non-release paths cannot
   publish; tokens redacted. Apply CQS; topology → `ci-cd-pipeline-patterns`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| PyPI/TestPyPI Trusted Publishing, OIDC publisher, tokenless upload | **This skill** | — |
| CI stages, fork trust, general OIDC job shape | `ci-cd-pipeline-patterns` | this for publisher rows |
| Secret inventory, rotation, leak IR | `secrets-management-hygiene` | this to drop PyPI tokens |
| CI secret scopes / multi-cloud OIDC | `secrets-in-ci-pipelines` | this for PyPI binding |
| SBOM gates / namespace confusion | `sbom-ci-enforcement` / `dependency-confusion` | this for upload identity |
| Workflow/release script quality | `code-quality-standards` | **always** on code |

**Hand-off:** Token retirement / leak IR → **`secrets-management-hygiene`**.
This skill owns **publisher identity binding** and **OIDC publish wiring**.

## Output Checklist

- [ ] Package names, indexes (PyPI/TestPyPI), owners inventoried
- [ ] Publish workflows, envs, tokens/publishers read first
- [ ] Trusted Publisher bound to forge repo + workflow + environment
- [ ] No org-wide / any-workflow prod publisher without exception
- [ ] CI: `id-token: write`, least other perms, trusted-ref only
- [ ] Trusted-job artifacts; TestPyPI proven before prod when migrating
- [ ] Actions pinned; long-lived tokens removed after OIDC works
- [ ] Fork/PR and non-release workflows cannot publish; drift plan documented
- [ ] Secrets redacted; `ci-cd-pipeline-patterns` + CQS; SBOM → `sbom-ci-enforcement`

## Rules

- Prefer **OIDC Trusted Publishing** over long-lived PyPI API tokens in CI.
- Publisher claims are the trust boundary — loose workflow/env binding ≈ anyone
  who can change a workflow can ship your package name.
- Publish from **protected release paths** only; never from untrusted PR code.
- TestPyPI first when practical; revoke CI tokens once OIDC is proven.
- Owned or authorized projects only; never paste live tokens or OIDC assertions.
