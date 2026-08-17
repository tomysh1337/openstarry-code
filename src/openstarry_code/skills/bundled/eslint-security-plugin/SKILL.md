---
name: eslint-security-plugin
description: >
  Install, configure, and triage eslint-plugin-security for JavaScript and
  TypeScript: detectObjectInjection, detect-eval-with-expression, child_process
  and fs path patterns, legacy vs flat ESLint config, CI gates, and justified
  suppressions. Use when eslint-plugin-security, security/detect-*, ESLint
  security rules, Node injection lint, unsafe regex lint, or wiring security
  plugin rules into eslint.config.js / .eslintrc.
---

# ESLint Plugin Security

Own **eslint-plugin-security** as a static guardrail for JS/TS: enable the plugin,
match repo ESLint layout (flat or legacy), run targeted lint, triage true positives
vs framework noise, and gate CI without replacing deeper SAST or manual review.
Repo ESLint and CI scripts outrank generic presets below.

## When To Use

- Adding or tuning **`eslint-plugin-security`** in app, library, or monorepo packages
- Interpreting **`security/detect-*`** findings (object injection, `eval`, `exec`, paths)
- Wiring security rules into **flat** (`eslint.config.*`) or **legacy** (`.eslintrc*`) config
- Reducing false positives with scoped overrides, not blanket disables
- Keywords: eslint-plugin-security, `security/detect-object-injection`,
  `detect-non-literal-fs-filename`, `detect-child-process`, `detect-unsafe-regex`

Do **not** use as primary for: general TS style → `typescript-style-and-eslint`;
formatter fights → `prettier-eslint-editorconfig`; full injection testing →
class-specific security skills; SCA/CVE inventory → supply-chain skills;
implementation quality → `code-quality-standards`.

## Repo Config First

Repo and org ESLint **outrank** defaults below.

1. **Package manager & ESLint major** — `package.json`, ESLint 8 vs 9+
2. **Config shape** — `eslint.config.js|mjs|cjs` (flat) vs `.eslintrc.*` / `eslintConfig`
3. **Existing plugins** — `@typescript-eslint`, `import`, `n`/`node`, org presets
4. **Scripts & CI** — `lint`, path globs, required check names
5. **Ignores** — `ignores` / `.eslintignore`, generated, fixtures, `dist`
6. **Severity policy** — error vs warn; exception/expiry for legacy debt

Extend the real ESLint config and scripts; do not invent a parallel linter path.

## Workflow

### 1. Install and pin

```bash
npm i -D eslint-plugin-security
```

Pin via lockfile. Match the repo ESLint major. Prefer the workspace that already owns lint.

### 2. Enable in config

**Flat (ESLint 9+ typical):**

```js
import pluginSecurity from "eslint-plugin-security";
export default [
  { plugins: { security: pluginSecurity },
    rules: { ...pluginSecurity.configs.recommended.rules } },
];
```

**Legacy:** `plugins: ["security"]` and `extends: ["plugin:security/recommended"]`.

Prefer **recommended** first; tighten rules after baseline noise is known. Apply the
plugin on TS overrides too—not only `*.js`.

### 3. High-signal rules

| Rule family | Typical risk | Prefer |
| --- | --- | --- |
| `detect-eval-with-expression` / non-literal require | Dynamic code load | Static imports; gated loaders |
| `detect-child-process` | Command injection surface | Argv arrays; no shell concat |
| `detect-non-literal-fs-filename` | Path traversal / arbitrary I/O | Resolve + root check at boundary |
| `detect-object-injection` | `obj[key]` confusion | Allowlist keys or `Map` |
| `detect-unsafe-regex` | ReDoS | Bounded patterns / safer engines |
| Buffer / weak random / timing compare | Legacy crypto misuse | `Buffer.alloc`/`from`, `randomBytes`, `timingSafeEqual` |

Findings are **hypotheses**: confirm untrusted data flow before inflating severity.

### 4. Run, triage, suppress

```bash
npx eslint path/to/changed --max-warnings 0
npm run lint   # prefer repo script
```

Lint touched paths first; full tree when enabling repo-wide or when CI already does.

| Finding shape | Action |
| --- | --- |
| Untrusted key/path/cmd → sink | Fix with allowlist, path root, argv, structured APIs |
| Controlled `obj[key]` (enum/map) | Narrow keys; or one-line disable + reason |
| Tests/fixtures/generated | Path overrides; never blanket-disable `src/` |
| Deferred true positive | Ticket + owner + expiry; warn-only only with policy |

```js
// eslint-disable-next-line security/detect-object-injection -- key from fixed enum KEYS
const value = table[key];
```

### 5. CI gate

Install with lockfile; run the **same** ESLint config as local; fail on new
`security/*` errors per policy; keep the job required when the org treats it as a
gate. Record plugin + ESLint major on enablement PRs.

**Verify:** safe path clean; intentional `eval(user)` fails; JS and TS covered;
ignores do not drop app entrypoints.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| eslint-plugin-security setup, rules, triage, CI | **This skill** | — |
| TS style, `any`, `@typescript-eslint` | `typescript-style-and-eslint` | this for security plugin |
| Prettier vs ESLint format ownership | `prettier-eslint-editorconfig` | this after format stable |
| Injection class testing (SQLi, XSS, CMDi, …) | class-specific skill | this as early static signal |
| Secrets hygiene / scanners | `secrets-management-hygiene` | this is not a secret scanner |
| Fix quality, tests, review baseline | `code-quality-standards` | **always** on code/config changes |

Keep **this skill primary** until enablement, rule policy, and triage are correct.

## Output Checklist

- [ ] Repo ESLint major, flat vs legacy, scripts, and ignores read first
- [ ] `eslint-plugin-security` installed and lockfile-pinned
- [ ] Plugin enabled (recommended or explicit) on JS **and** TS overrides
- [ ] Lint run on changed paths (or full tree); findings listed by rule id
- [ ] True positives fixed safely; suppressions local and justified
- [ ] No blanket `security/*` disable in production sources
- [ ] Test/generated overrides do not weaken `src/` policy
- [ ] CI uses same config; severity and required-check status documented
- [ ] Hand-offs: `typescript-style-and-eslint`, `prettier-eslint-editorconfig`,
      class-specific vuln skills, `code-quality-standards`
- [ ] Rules: repo-first; evidence over fear; lint is signal, not full SAST
