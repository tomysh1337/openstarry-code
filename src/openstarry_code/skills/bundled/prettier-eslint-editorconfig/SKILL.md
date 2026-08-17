---
name: prettier-eslint-editorconfig
description: >
  Resolve formatter/linter/EditorConfig hierarchy, avoid tool fights, and run a
  reliable format-then-lint fix pipeline. Use when prettier, eslint, editorconfig,
  格式化, format-on-save conflicts, eslint-config-prettier, or CI format checks fail.
---

# Prettier, ESLint, And EditorConfig

## Use When

| Situation | Direction |
| --- | --- |
| Prettier / format-on-save / CI format check | **This skill** (primary) |
| ESLint vs Prettier rule collisions | This skill |
| EditorConfig (charset, indent, EOL, final newline) | This skill |
| “Don’t fight the tools” / ownership of concerns | This skill |
| TS `any`, strictness, semantic import rules | `typescript-style-and-eslint` |
| Broader maintainability, tests, security | Baseline: `code-quality-standards` |

Triggers: prettier, eslint, editorconfig, 格式化, format pipeline, lint-staged, eslint --fix.

## Repo Config First

Never impose personal formatter prefs. Discover and obey:

1. **EditorConfig** — `.editorconfig` (indent, EOL, charset, final newline, trim)
2. **Prettier** — `.prettierrc*`, `prettier.config.*`, package `prettier`, `.prettierignore`
3. **ESLint** — flat/legacy; note `eslint-config-prettier` / `eslint-plugin-prettier`
4. **Globs** — Prettier plugins and ESLint overrides per path
5. **Automation** — package scripts, lint-staged, husky, CI format/lint jobs

For pure presentation when tools disagree: **repo Prettier** wins for languages it formats; EditorConfig fills editor defaults and non-Prettier files; ESLint should not re-assert formatting if Prettier is adopted. If configs are missing, **match neighboring files**. Do not add a full tool stack unless asked.

## Tool Hierarchy (Do Not Fight Tools)

| Concern | Owner | Examples |
| --- | --- | --- |
| Indent, quotes, semis, width, trailing commas | **Prettier** | `printWidth`, `singleQuote` |
| Charset, EOL, final newline, basic indent defaults | **EditorConfig** | `end_of_line`, `indent_size` |
| Correctness, bugs, TS safety | **ESLint** | `no-unused-vars`, `no-floating-promises` |
| Import **sorting** | Repo choice | One of: ESLint plugin **or** Prettier plugin |
| Typechecking | **`tsc` / vue-tsc** | Not ESLint alone |

### Anti-patterns

- ESLint stylistic rules (`indent`, `quotes`, `semi`, `max-len`) **while** Prettier formats the same files
- `eslint --fix` and Prettier in orders that undo each other
- Mixed tabs/spaces or CRLF/LF in the same package
- Hand-reformatting huge unrelated diffs
- Checking in caches/settings that contradict repo config

### Integration (good)

1. **Prettier + eslint-config-prettier** — Prettier formats; ESLint drops conflicting style rules.
2. **`eslint-plugin-prettier` only if already present** — do not add by default.
3. **EditorConfig aligned with Prettier** (`indent_size` == `tabWidth`, consistent EOL).
4. **Single import sorter** — not two mechanisms fighting.

## Workflow (Fix Pipeline)

Prefer repository scripts. Safe default order:

1. **Read configs** — EditorConfig → Prettier → ESLint → CI commands.
2. **Change behavior first** — format only files needed for the task.
3. **Format** — Prettier on touched paths (`npm run format` / equivalent).
4. **Lint fix** — ESLint `--fix` for non-format auto-fixes.
5. **Typecheck** — if the package defines it.
6. **Re-format** if a codemod/ESLint rewrite changed structure.
7. **Verify** as CI does (`prettier --check`, `eslint`).

```bash
prettier --write path/to/file.ts
eslint path/to/file.ts --fix
# Full suite only when CI or user requires
npm run format && npm run lint && npm run typecheck
```

**lint-staged / CI:** format + lint staged files in pre-commit; full check in CI. Fail on `prettier --check` (or equivalent)—do not rely on review-only fixes.

## Good / Bad Examples

**Bad — two owners of quotes/semis:**

```text
ESLint: quotes double, semi required
Prettier: singleQuote true, semi false
→ save-loop / CI thrash
```

**Good:** Prettier is the style source; `eslint-config-prettier` last (or flat equiv).

**Bad pipeline:** `eslint --fix` then Prettier undoes import/layout every run.

**Good pipeline:** one sorter; Prettier write → ESLint fix with no stylistic overlap.

**Bad:** reformat entire monorepo to tabs while `.editorconfig`/Prettier specify 2 spaces.

**Good:** touch feature files only; run package format script; leave unrelated packages alone.

**Bad:** `/* eslint-disable */` whole file because tools disagree.

**Good:** fix ownership with `eslint-config-prettier`; reserve disable for true exceptions.

## Routing

| Need | Skill |
| --- | --- |
| Prettier / EditorConfig / format pipeline / hierarchy | **This skill** (primary) |
| TS strictness, `any` ban, semantic imports | `typescript-style-and-eslint` |
| Implementation quality beyond format/lint | `code-quality-standards` (always baseline) |
| “Only make it pretty” | This skill; still honor `code-quality-standards` contracts |

Route formatting fights here; TypeScript correctness style to `typescript-style-and-eslint`; always keep `code-quality-standards` for behavior, errors, tests, and security.

## Checklist

- [ ] Read `.editorconfig`, Prettier, and ESLint configs before changing format
- [ ] One owner per concern (Prettier format vs ESLint correctness)
- [ ] `eslint-config-prettier` (or equivalent) when both tools are present
- [ ] EditorConfig indent/EOL aligned with Prettier
- [ ] Only one import-sort mechanism active
- [ ] Pipeline: format → lint --fix → typecheck → recheck
- [ ] No whole-repo reformat unless requested or required by CI
- [ ] No blanket `eslint-disable` to hide tool conflicts
- [ ] CI `format:check` / `lint` would pass on touched paths
- [ ] `code-quality-standards` applied for non-format quality
