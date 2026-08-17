---
name: python-packaging-modern
description: >-
  Modern Python packaging with pyproject.toml, hatch/poetry/uv, src layout,
  versioning, and wheels. Use when packaging a Python library or app, authoring
  or migrating setup.py/setup.cfg to PEP 517/518/621, choosing hatchling/setuptools/
  poetry-core, building sdist/wheel, version policy, entry points, or uv/pip
  publish workflows.
---

# Python Packaging Modern

Ship **installable, reproducible Python distributions** using declarative
`pyproject.toml`, a modern build backend, and clear layout. Prefer the repo’s
existing backend and tool chain over inventing a second stack.

## When To Use

- Creating or migrating a package to **PEP 517/518/621** `pyproject.toml`
- Choosing or configuring **hatchling**, **setuptools**, **poetry-core**, **flit**, or **pdm-backend**
- Adopting **src layout**, package discovery, data files, and console scripts
- Building **sdist/wheel**, checking metadata, and publishing (PyPI / private index)
- Versioning: static, dynamic (`__version__`, VCS, hatch-vcs, setuptools-scm)
- Dependency groups: runtime vs optional extras vs dev; lockfiles with **uv** / Poetry
- User mentions: pyproject.toml, wheel, sdist, hatch, poetry, uv, PEP 621, packaging

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| PEP 8, type hints, ruff/mypy/pyright | `python-style-and-typing` |
| Docstring content/templates | `docstring-and-typedoc` |
| CI publish job wiring | `ci-cd-pipeline-patterns` |
| App reliability/security/tests baseline | `code-quality-standards` |
| Dependency confusion / index abuse (authorized) | `dependency-confusion` |

## Repo Config First

Repository packaging config **outranks** generic preferences.

1. **Canonical manifest:** `pyproject.toml` (`[project]`, `[build-system]`, tool tables)
2. **Legacy only if still authoritative:** `setup.py`, `setup.cfg`, `MANIFEST.in` — migrate carefully; do not dual-define conflicting metadata
3. **Backend already chosen:** hatchling vs setuptools vs poetry-core — match it; do not force Poetry into a hatch repo
4. **Layout:** `src/<pkg>/` vs flat package; monorepo workspaces; namespace packages
5. **Lock / install UX:** `uv.lock`, `poetry.lock`, `requirements*.txt`, `pdm.lock` — keep the project’s installer
6. **Version source:** single source of truth (static in `[project]`, dynamic, or VCS plugin)
7. **CI publish:** trusted publishing / OIDC, test.pypi, private index URLs, artifact retention
8. **Tool tables nearby:** `[tool.ruff]`, `[tool.pytest.ini_options]`, `[tool.hatch.*]` — do not rewrite style config here

**Precedence:** Follow repo/backend when examples below conflict. Surface dual metadata, missing `requires-python`, or editable-install breakage.

## Workflow

1. **Classify the deliverable.** Library (importable, versioned API) vs app (CLI/service) vs namespace/plugin. Apps may still wheel for deploy; libraries must declare public package names and extras carefully.
2. **Establish `[build-system]`.** Pin a backend + minimum requires, e.g. hatchling, setuptools≥61, or poetry-core. Never rely on implicit setuptools from an old setuptools-only tree without `pyproject.toml`.
3. **Fill PEP 621 `[project]`.**
   - `name`, `version` or `dynamic = ["version"]`, `description`, `readme`, `requires-python`
   - `dependencies` for runtime only; use `[project.optional-dependencies]` for extras (`dev`, `test`, feature flags)
   - `authors`/`license`/`urls` as required by the org
   - `[project.scripts]` / `[project.entry-points.*]` for CLIs and plugins
4. **Choose layout.** Prefer **`src/<package_name>/`** so tests and accidental cwd imports cannot mask an uninstalled tree. Configure package discovery for the backend (`[tool.hatch.build.targets.wheel] packages`, setuptools `where = ["src"]`, etc.).
5. **Version policy.**
   - Prefer **one** source: static PEP 621, or dynamic from VCS (tag) / single module attribute
   - Follow SemVer or the repo’s scheme; tag releases that match the built wheel version
   - Avoid editing version in three places (toml + `__init__` + CI) without automation
6. **Build and inspect.**
   - `python -m build` or `uv build` / `hatch build` / `poetry build`
   - Produce both **sdist** and **wheel** unless policy says otherwise
   - Check metadata and contents: `twine check dist/*`; open the wheel (zip) for expected modules only — no tests, secrets, or local `.env`
7. **Install sanity.** Editable install (`pip install -e .` / `uv sync`) from a clean venv; import the package; run console scripts; exercise extras.
8. **Publish path.** Test index first when new; use trusted publishing or scoped tokens; never commit API tokens. Record requires-python and classifiers that match CI interpreters.

## Core Practices

### pyproject.toml shape (minimal mental model)

| Table | Owns |
| --- | --- |
| `[build-system]` | Backend + build deps (PEP 517/518) |
| `[project]` | Name, version, deps, scripts, requires-python (PEP 621) |
| `[project.optional-dependencies]` | Extras; keep `dev`/`test` out of runtime installs |
| `[tool.*]` | Hatch/ruff/pytest/mypy — not a substitute for `[project]` metadata |

### Backend notes

- **Hatch / hatchling:** strong default for new libs; matrix envs optional; version plugins common
- **setuptools:** fine for mature repos; use `package-dir` / discovery; avoid legacy `setup.py` logic unless custom build steps require it
- **Poetry:** if the repo is Poetry-first, keep `poetry-core` and Poetry lock workflow; do not half-migrate to hatch mid-PR
- **uv:** excellent resolver/installer and build/publish UX; still honor the declared build backend in `pyproject.toml`

### Wheels and sdists

- Wheel = install artifact (pure or platform tags); sdist = source for rebuilds
- Pure Python: aim for `py3-none-any.whl` with correct package data
- Include package data explicitly (`*.pyi`, `py.typed`, templates) — do not rely on accidental filesystem copies
- Exclude caches, tests (unless intentional), virtualenvs, and secrets from both artifacts

### Versioning pitfalls

- Dynamic version must resolve at build time in clean CI (full git history for VCS schemes, or `setuptools-scm`/`hatch-vcs` config)
- Yank/re-release policy: never reuse a published version number with different bits

## Routing

| Need | Skill |
| --- | --- |
| pyproject, hatch/poetry/uv, src layout, wheels, versioning | **This skill** (primary) |
| PEP 8, typing, ruff/black, mypy/pyright | `python-style-and-typing` |
| Docstrings / Typedoc | `docstring-and-typedoc` |
| CI build/publish jobs, OIDC, artifacts | `ci-cd-pipeline-patterns` |
| Dockerfile that installs the package | `dockerfile-best-practices` |
| Changelog / release notes prose | `changelog-and-release-notes` |
| Production code quality | `code-quality-standards` (always as helper on behavior changes) |
| Malicious index / dependency confusion research | `dependency-confusion` |

Hand off **style and type-checker config** to `python-style-and-typing`. Keep packaging metadata and build layout decisions here.

## Output Checklist

- [ ] Existing backend, layout, and lock/install tool identified and preserved
- [ ] `[build-system]` and PEP 621 `[project]` complete; no conflicting setup.py/cfg dual source
- [ ] `requires-python` and runtime deps correct; extras separated from runtime
- [ ] Src (or deliberate flat) layout with working package discovery
- [ ] Single version source; wheel version matches tag/release policy
- [ ] Scripts/entry points declared and smoke-tested via install
- [ ] sdist + wheel build clean; `twine check` (or equivalent) OK; no secrets/tests junk in wheel
- [ ] Editable/clean venv install imports successfully
- [ ] Style/typing tool tables left to `python-style-and-typing`; CQS applied if code changed
- [ ] Publish path uses scoped/trusted credentials; versions not reused
