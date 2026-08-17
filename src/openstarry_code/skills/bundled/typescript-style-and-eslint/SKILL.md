---
name: typescript-style-and-eslint
description: >
  Apply TypeScript strictness, ESLint/Prettier interplay, any-ban patterns, and
  import-order discipline while editing or reviewing TS/TSX code. Use when
  TypeScript style, ESLint, TS 风格, @typescript-eslint, no-explicit-any,
  import order, tsconfig strict, or eslint-config conflicts with prettier.
---

# TypeScript Style And ESLint

## Use When

| Situation | Direction |
| --- | --- |
| TS/TSX style, strictness, typing hygiene | **This skill** (primary) |
| ESLint for TypeScript (`@typescript-eslint/*`) | This skill |
| `any` / unsafe casts / assertion sprawl | This skill |
| Import order, path aliases, barrels | This skill |
| Formatter-only fights (quotes, semis, width) | `prettier-eslint-editorconfig` |
| Design, errors, tests, security | Baseline: `code-quality-standards` |

Triggers: TypeScript style, ESLint, TS 风格, 严格模式, any 禁用, import 顺序.

## Repo Config First

Repo config **outranks** this skill. Before changing style, read:

1. `tsconfig.json` / `tsconfig.*.json` (`strict`, `noImplicitAny`, paths)
2. ESLint: `eslint.config.*`, `.eslintrc.*`, package `eslintConfig`
3. Prettier / EditorConfig (do not re-litigate format in ESLint if Prettier owns it)
4. Nearby modules: types, import style, aliases (`@/`, `~/`)
5. CI scripts: `typecheck`, `lint` — match what CI enforces

Follow the repo on conflicts. Propose config changes only when asked or when config is broken.

## Workflow

1. **Discover** — load TS + ESLint + Prettier; note `strict` and `@typescript-eslint` rules.
2. **Align types** — real types/interfaces; prefer `unknown` + narrowing over `any`.
3. **Lint scope** — fix rules on **touched** files; avoid unrelated drive-by rewrites.
4. **Separate concerns** — correctness in TS/ESLint; pure formatting via Prettier.
5. **Verify** — repo `typecheck` / `tsc --noEmit` and `eslint` on changed paths.
6. **Report** — document suppressions (`eslint-disable`, `@ts-expect-error`) and why.

### Strictness (when repo is silent)

- Keep `strict: true` if already on; do not flip strictness in a drive-by PR.
- No `// @ts-nocheck` or blanket `any` to silence errors.
- Prefer `@ts-expect-error` + one-line reason over `@ts-ignore`.
- Prefer `satisfies` / discriminated unions over assertion chains.

### `any` ban patterns

| Pattern | Prefer |
| --- | --- |
| `x: any` | Concrete type, generics, or `unknown` |
| `as any` | Narrowing, type guards, or fix the source type |
| `Record<string, any>` | `Record<string, unknown>` or a named type |
| `Function` / bare `object` | Explicit signatures / typed objects |
| Catch `e: any` | `unknown`, then narrow |

Suppressions must be **local** and **justified**:

```ts
// eslint-disable-next-line @typescript-eslint/no-explicit-any -- vendor SDK lacks types
const payload = sdk.raw() as any;
```

### Import order

Match the repo plugin (`import/order`, `simple-import-sort`, Perfectionist). Typical groups when unspecified:

1. Node/builtin → external → internal aliases → relative parent → relative sibling
2. Side-effect imports per existing file pattern
3. `import type` when the project already uses it
4. One alias scheme; do not invent a second mid-change

Reorder whole files only when lint requires it for your change, or the file is already in the diff.

## Good / Bad Examples

**Bad — silence typing with `any`:**

```ts
export function parseUser(data: any): any {
  return { id: data.id, name: data.name };
}
```

**Good — unknown boundary + narrow:**

```ts
type User = { id: string; name: string };

export function parseUser(data: unknown): User {
  if (!data || typeof data !== "object") throw new Error("invalid user");
  const rec = data as Record<string, unknown>;
  if (typeof rec.id !== "string" || typeof rec.name !== "string") {
    throw new Error("invalid user");
  }
  return { id: rec.id, name: rec.name };
}
```

**Bad:** ESLint stylistic rules (`indent`, `quotes`, `semi`, `max-len`) while Prettier also formats.

**Good:** `eslint-config-prettier` (or flat equivalent); keep rules like `no-floating-promises`, `no-explicit-any`.

**Bad:** chaotic import order mixing builtin/external/relative.

**Good:** stable groups — `node:` → packages → `@/` → `./`.

## Routing

| Need | Skill |
| --- | --- |
| TS style, ESLint typing, `any`, imports | **This skill** (primary) |
| Prettier vs ESLint vs EditorConfig, fix pipeline | `prettier-eslint-editorconfig` |
| Design, errors, tests, security, lifecycle | `code-quality-standards` (always baseline) |
| Generic quality, no TS focus | `code-quality-standards` |

Keep this skill primary for TS/ESLint style; apply `code-quality-standards` for non-style quality. Do not invent a third personal style guide.

## Checklist

- [ ] Read `tsconfig` + ESLint (+ Prettier) before editing style
- [ ] No new `any` / unjustified `as any` / bare `@ts-ignore`
- [ ] Runtime boundaries validated even when types look sound
- [ ] Import order matches repo plugin; no alias proliferation
- [ ] ESLint not reformatting what Prettier owns
- [ ] Scope limited to touched files unless CI requires more
- [ ] `typecheck` + `eslint` run on changed paths
- [ ] Suppressions documented and minimal
- [ ] `code-quality-standards` applied for behavior, errors, tests, security
