---
name: python-style-and-typing
description: >-
  Apply PEP 8 style, modern type hints, and repo-aligned pyright/mypy plus
  black/ruff tooling when writing or reviewing Python. Use when Python style,
  typing, type hints, 类型注解, PEP 8, mypy, pyright, ruff, black, annotations,
  or Python formatting/linting conventions are the focus.
---

# Python Style And Typing

## When To Use

- Adding or changing Python modules, packages, scripts, or tests.
- Introducing or tightening type hints (`typing`, `collections.abc`, PEP 604 unions).
- Configuring or reconciling **black/ruff** format-lint and **mypy/pyright** check.
- Reviewing PRs for style drift, untyped public APIs, or `Any`/`# type: ignore` abuse.
- User mentions: Python style, typing, 类型注解, PEP 8, annotations.

Prefer this skill for **style and types**. Use `docstring-and-typedoc` when the main ask is docstring content/templates. Use `code-quality-standards` for architecture, errors, security, and tests beyond style.

## Repo Config First

Repository conventions **outrank** generic PEP 8 defaults when they conflict on pure style.

1. Read `pyproject.toml`, `setup.cfg`, `tox.ini`, `.ruff.toml`, `ruff.toml`, `.flake8`, `mypy.ini`, `pyrightconfig.json` / `pyrightconfig.toml`, and CI lint jobs.
2. Match nearby modules: import style, line length, quote policy, `from __future__ import annotations`, package layout.
3. Prefer the **project’s** formatter and type checker. Common stacks:
   - Format: **Black** or **Ruff format** (`ruff format`)
   - Lint: **Ruff** (often replaces flake8/isort/pyupgrade)
   - Types: **Pyright** / Pylance and/or **mypy**
4. Do not invent a second style (e.g. force 79-col if the repo uses 88/100/120).
5. Surface real conflicts (correctness vs style config) instead of silent dual conventions.

## Workflow

1. **Scope the change.** Public API vs internal helper; sync vs async; library vs app script.
2. **Align layout (PEP 8, high-level).**
   - `snake_case` functions/vars; `PascalCase` classes; `UPPER_SNAKE` module constants.
   - 4-space indent; no tabs mixed with spaces.
   - Imports: stdlib → third party → local; avoid wildcard imports; prefer absolute or established relative style.
   - One statement per line; blank lines between top-level defs; two between major sections when local code does so.
   - Names express domain meaning; avoid single-letter names outside short scopes.
3. **Type the contract.**
   - Annotate public functions, methods, and module-level constants that are part of a contract.
   - Prefer precise types: `list[str]`, `dict[str, int]`, `X | None` (3.10+) or `Optional[X]` if the repo is older.
   - Use `collections.abc` (`Mapping`, `Sequence`, `Iterable`, `Callable`) at boundaries when mutation is not required.
   - Prefer `TypeAlias` / `type` statements for repeated shapes; dataclasses/TypedDict/Pydantic when dicts hide invariants.
   - Avoid bare `Any`. If unavoidable, localize and comment why.
   - Prefer `Protocol` / structural typing over deep inheritance when matching local patterns.
   - Keep runtime validation for untrusted input; types alone are not a trust boundary.
4. **Tooling pass.**
   - Format with the repo command (often `ruff format` or `black`).
   - Lint with Ruff (or project equivalent); fix unused imports, bare excepts Ruff flags, pyupgrade issues.
   - Run pyright and/or mypy at the **configured** strictness; do not weaken `pyproject` to silence one file without discussion.
   - Prefer fixing types over blanket `# type: ignore`. If ignore is required: narrowest code, specific error code, short reason.
5. **Docstrings (high-level, PEP 257).**
   - Public modules/classes/functions: one-line summary; expand only when behavior is non-obvious.
   - Do not restate types already in annotations. Point to `docstring-and-typedoc` for full templates.
6. **Verify.** Run the repo’s format → lint → typecheck → focused tests for touched code.

## Good Vs Bad Examples

**Good — typed public API, clear names**

```python
def fetch_user(user_id: str, *, timeout_s: float = 5.0) -> User | None:
    """Return the user or None if missing. Raises on transport failure."""
    ...
```

**Bad — untyped, mutable default, broad except**

```python
def fetch_user(user_id, opts={}):
    try:
        return do_fetch(user_id, opts)
    except Exception:
        return None
```

**Good — narrow ignore with code**

```python
result = legacy_api()  # type: ignore[no-untyped-call]
```

**Bad — file-wide silence**

```python
# mypy: ignore-errors
# or repeated bare `# type: ignore` without codes
```

**Good — formatter/linter ownership**

- Let Black/Ruff own whitespace and import order; do not hand-fight diffs after format.

**Bad — dual style**

- Manually reflow to 79 columns in a Black-88 codebase; mix isort profile with Ruff `isort` settings.

## Routing

| Need | Skill |
| --- | --- |
| Python PEP 8 / type hints / ruff / mypy / pyright | **This skill** (primary) |
| Docstring / JSDoc / TSDoc content and templates | `docstring-and-typedoc` |
| Architecture, errors, security, tests, multi-language baseline | `code-quality-standards` (always as helper on production changes) |
| Security defect in Python web/API | Domain vuln skill + this for clean fixes |

Always apply **`code-quality-standards`** as the implementation baseline when changing production behavior; this skill specializes style and typing.

## Output Checklist

- [ ] Repo formatter/linter/type-checker config identified and followed
- [ ] Naming, imports, and layout match nearby modules (PEP 8 where not overridden)
- [ ] Public APIs annotated; no new unjustified `Any`
- [ ] Unions/Optional/collections.abc used appropriately for the language version
- [ ] Format + lint + typecheck commands run (or explicitly noted if unavailable)
- [ ] `# type: ignore` / suppressions are narrow, coded, and justified
- [ ] Docstrings not used as a substitute for types; PEP 257 summaries where public
- [ ] Behavioral risks (errors, resources, security) covered under `code-quality-standards`

## Rules

- Aesthetics never outrank correctness, security, or data integrity.
- Do not “fix types” by deleting annotations or casting everything to `Any`.
- Do not reformat unrelated files; keep diffs focused.
- Match the project’s Python version: avoid syntax the CI interpreter rejects.
- Ruff is a linter/formatter, not a full type checker — still run mypy/pyright when configured.
- Prefer evidence from tool output and tests over style opinions in review comments.
