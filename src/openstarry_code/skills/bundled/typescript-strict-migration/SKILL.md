---
name: typescript-strict-migration
description: >
  Migrate a TypeScript codebase toward compiler strict mode: inventory current
  flags, enable checks incrementally (strictNullChecks, noImplicitAny, and the
  rest of strict), use per-package or path-scoped tsconfigs, ts-migrate/codemod
  patterns, and temporary suppressions with a burn-down plan. Use when turning
  on strict, fixing mass tsc errors after strictNullChecks/noImplicitAny, or
  planning an incremental TS strict rollout without a big-bang rewrite.
---

# TypeScript Strict Migration

Move a TS/TSX codebase to **compiler strictness** safely: measure error volume,
enable flags in a controlled order, fix or quarantine debt, and keep CI green.
This skill owns **migration mechanics and flag sequencing**. Day-to-day typing
hygiene and ESLint rules stay with `typescript-style-and-eslint`; reliability,
tests, and security stay with `code-quality-standards`.

## When To Use

- Enabling `strict`, `strictNullChecks`, `noImplicitAny`, or sibling flags on an existing app/lib
- `tsc` error floods after a strict flip; need incremental path or package-by-package rollout
- Adopting `ts-migrate`, codemods, or path-scoped tsconfigs / project references for strict
- Burning down `// @ts-nocheck`, blanket `any`, or unchecked JS allowlists
- Mentions: TypeScript strict mode, strictNullChecks migration, noImplicitAny backlog, ts-migrate, incremental strict enablement

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Everyday TS style, ESLint `no-explicit-any`, import order | `typescript-style-and-eslint` |
| Prettier vs ESLint format ownership | `prettier-eslint-editorconfig` |
| Behavior, errors, tests, security of fixed code | `code-quality-standards` |
| New greenfield TS with strict already on | `typescript-style-and-eslint` + CQS |

## Repo Config First

Repo compiler and CI settings **outrank** defaults below.

1. **tsconfig graph:** root `tsconfig.json`, `tsconfig.app/build/test.json`, project references, `extends` chains
2. **Current flags:** `strict` and each sub-flag; `allowJs`, `checkJs`, `skipLibCheck`, `noEmit` / build mode
3. **CI typecheck:** which config CI runs (`tsc -b`, `tsc --noEmit`, Nx/Turbo target) — migrate that path first
4. **Monorepo boundaries:** packages that can go strict independently; shared types packages first when feasible
5. **Existing suppressions:** `@ts-nocheck`, `@ts-ignore` / `@ts-expect-error`, `any` density, `// @ts-check` JS
6. **Tooling:** ESLint `@typescript-eslint`, `ts-migrate`, `typescript-eslint` type-aware rules already on
7. **Neighbor patterns:** prior migrations, path-mapped strict overlays, exclude globs

**Precedence:** Follow the repo’s package manager, composite projects, and CI. Propose flag flips only with a measured error budget and exit criteria.

## Workflow

1. **Baseline.** Run the repo typecheck command; capture error count by code (`TS7006`, `TS2322`, `TS2345`, `TS2531`/`TS2532`, `TS18048`, etc.) and by directory/package. Record current `strict*` flags. Do not flip everything in one PR on a large dirty tree without a quarantine plan.

2. **Choose a rollout shape.**

   | Shape | When | Notes |
   | --- | --- | --- |
   | Package-by-package | Monorepo / clear package boundaries | Strict in leaf libs first, then apps |
   | Path-scoped overlay | One app, hot dirs first | Extra `tsconfig.strict.json` `include`/`files` or project ref |
   | Flag-by-flag | Single package, moderate errors | Enable one sub-flag per milestone |
   | Codemod + fix | Huge implicit-any / null noise | `ts-migrate` / scripted inserts, then human fix |
   | Big-bang | Small repo or already near-clean | Only if baseline is low and CI can absorb |

3. **Prefer explicit sub-flags before or with `strict`.** `strict: true` turns on the family together. On dirty codebases, enable high-value flags in order (adjust to measured top codes):

   1. `noImplicitAny` — forces parameter/return annotation debt into the open  
   2. `strictNullChecks` — usually the largest semantic win and the largest diff  
   3. `strictFunctionTypes`, `strictBindCallApply`, `strictPropertyInitialization`  
   4. `noImplicitThis`, `useUnknownInCatchVariables`, `alwaysStrict`  
   5. Related non-`strict` companions when ready: `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitReturns`, `noFallthroughCasesInSwitch`, `noPropertyAccessFromIndexSignature`

4. **Quarantine without lying forever.** Temporary tactics (always with burn-down):
   - Path/`exclude` or a loose tsconfig for legacy folders; shrink include over time
   - Per-file `// @ts-nocheck` only as last resort; track in a list to delete
   - Prefer `// @ts-expect-error` + one-line reason over `@ts-ignore` (error must still exist)
   - `ts-migrate` / codemods that insert `$TSFixMe` / `any` / expect-error as **markers**, not the end state
   - Do not set `strict: false` again after a clean package is green

5. **Fix patterns (common).**

   | Symptom | Prefer |
   | --- | --- |
   | Implicit `any` params | Real types, generics, or `unknown` + narrow |
   | Possibly undefined | Optional chaining, early return, narrowing, defaults |
   | `null` / `undefined` mismatch | Normalize API types; avoid non-null `!` except proven invariants |
   | Uninitialized class fields | Definite assignment only when ctor/init guarantees it; else optional or defaults |
   | Index access `T | undefined` (if `noUncheckedIndexedAccess`) | Guard, `.at` + check, or typed maps |
   | Catch clause | `unknown` then narrow (`useUnknownInCatchVariables`) |
   | Third-party untyped | Minimal `.d.ts` / `declare module`; local wrapper types; avoid app-wide `any` |

6. **PR hygiene.** One package or one flag family per PR when possible. Keep behavior changes out of pure typing PRs, or isolate them and test. Re-run full typecheck + unit tests for touched packages. Never “green” CI by disabling typecheck or adding repo-wide `skipLibCheck` flips without need (`skipLibCheck` is orthogonal; do not use it to hide app errors).

7. **Exit criteria.** Target package has agreed flags on; error count zero under CI config; suppression inventory reduced or ticketed; docs/ADR note the new default for new code.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Strict rollout, flag order, ts-migrate, error burn-down | **This skill** | — |
| Style, ESLint typing rules, import order after types settle | `typescript-style-and-eslint` | this during migration |
| Format pipeline only | `prettier-eslint-editorconfig` | — |
| Implementation quality of runtime fixes/tests | `code-quality-standards` | **always** on code changes |
| JSDoc/TSDoc for public APIs touched in migration | `docstring-and-typedoc` | this for compiler flags |

- **`typescript-style-and-eslint`:** hand off once flags are decided and bulk errors are under control; that skill owns ongoing `any` bans, assertion hygiene, and ESLint interplay. Keep **this skill primary** while sequencing flags and quarantine.
- **`code-quality-standards`:** apply whenever migration edits runtime behavior (null guards, API normalization, init order): explicit errors, tests for boundary null/undefined, no secrets in logs, no silent catch.

## Output Checklist

- [ ] Current tsconfig graph, CI typecheck command, and baseline error counts recorded
- [ ] Rollout shape chosen (package / path overlay / flag-by-flag / codemod / small big-bang)
- [ ] Flag sequence documented; high-value checks not skipped without reason
- [ ] Temporary suppressions are local, justified, and on a burn-down list
- [ ] No new repo-wide `@ts-nocheck` or permanent `$TSFixMe` without owners
- [ ] Null/any fixes prefer narrowing and real types over `!` / `as any`
- [ ] Typecheck green under the same config CI uses; tests run for behavioral edits
- [ ] New code defaults to strict; legacy quarantine shrink plan noted
- [ ] Hand off day-to-day style to `typescript-style-and-eslint`
- [ ] `code-quality-standards` applied for behavior, errors, tests, and security
