---
name: npm-pack-ignore-hygiene
description: >
  Keep npm package publish contents intentional: package.json "files", .npmignore
  vs .gitignore, npm pack dry-runs, and exclusion of secrets, tests, and build
  junk from the tarball. Use when npm pack, npm publish, package tarball contents,
  .npmignore, package.json files field, accidental publish of source maps or
  credentials, shrinkwrap vs lockfile in packs, or "what ships on npm" audits
  are in scope.
---

# npm Pack / Ignore Hygiene

Own **what enters the published tarball**: `package.json` `files`, `.npmignore`,
default npm inclusion rules, and dry-run verification. Prefer the package’s
existing publish layout and monorepo tooling. Hand **lock/pin policy** to
`dependency-pinning-strategies` and **registry namespace confusion** to
`dependency-confusion`.

## When To Use

- Preparing or reviewing **`npm pack` / `npm publish`** for a library or CLI
- Editing **`package.json` `files`**, **`.npmignore`**, or publish-related scripts
- Investigating **oversized tarballs**, leaked **tests/fixtures**, **`.env`**,
  keys, source maps, or monorepo paths inside published packages
- Aligning **build output** (`dist/`, `lib/`) with what consumers actually import
- Keywords: npm pack, npm publish, .npmignore, files whitelist, tarball audit,
  accidental publish, package contents, prepublishOnly, bundledDependencies

Do **not** use as primary for: lockfile pins → `dependency-pinning-strategies`;
registry confusion → `dependency-confusion`; image context →
`dockerfile-best-practices`; secret IR → `secrets-management-hygiene`;
implementation quality → `code-quality-standards`.

## Repo Config First

Repository and package publish policy **outrank** defaults below.

1. **`package.json`:** `name`, `version`, `main`/`exports`/`types`, `files`,
   `bin`, lifecycle scripts (`prepack`/`prepare`/`prepublishOnly`), workspaces
2. **Ignore layers:** package `.npmignore`; note gitignore interaction (below)
3. **Build artifacts:** expected emit dirs, dual CJS/ESM, declaration layout
4. **Monorepo tools:** workspaces, Changesets, Lerna, Nx, Turborepo pack/publish
5. **CI publish:** provenance, OIDC/2FA, dry-run jobs, which roots publish
6. **Neighbors:** `.npmrc`, private registry, `bundledDependencies`

**Precedence:** Follow existing `files`/ignore conventions. Flag secrets or
whole-repo trees that would ship if packed today.

## Workflow

### 1. Inventory inclusion rules

For each package root that may publish:

1. **`files`** — explicit **allowlist** (npm always packs `package.json` and
   typically includes `README*`, `LICENSE*`, `CHANGELOG*` when present).
2. **`.npmignore` present** — denylist; it **replaces** `.gitignore` for packing
   (does not stack as a second layer on gitignore).
3. **No `.npmignore`** — npm applies **`.gitignore`** plus defaults; untracked
   files can still pack if not ignored.
4. **`main` / `exports` / `types` / `bin`** — every target must exist **in the
   tarball**, not only in the worktree.

Never assume “not in git” means “not in pack.” Always dry-run.

### 2. Prefer allowlist over denylist

| Approach | When | Risk if wrong |
| --- | --- | --- |
| **`files` allowlist** | Default for libraries | Missing `dist`/types breaks install |
| **`.npmignore` denylist** | Legacy / complex trees | New secret/test paths ship unnoticed |
| **Both** | `files` first; ignore trims inside | Over-trim drops needed assets |

Ship only runtime + types + license/docs consumers need. Keep tests, fixtures,
CI, editor config, and private scripts out of the allowlist.

### 3. Hard exclude (never ship)

- **Secrets / env:** `.env*`, `*.pem`, `*.key`, tokenized `.npmrc`, cloud creds
- **VCS / local:** `.git/`, IDE folders, OS junk
- **Dev-only:** tests, coverage, snapshots, large fixtures; raw `src/` when only
  `dist/` is consumed (unless intentional dual-publish)
- **Build junk:** caches, `node_modules/` (unless deliberate bundle), tsbuildinfo
- **Monorepo noise:** other packages’ sources, root-only tooling

Redact tokens in reports; rotate if dry-run or a published version already leaked.

### 4. Dry-run and inspect

```bash
npm pack --dry-run
npm pack --pack-destination /tmp
tar -tzf <name>-<version>.tgz | sort
```

Confirm `exports`/`bin` paths, no secrets, sane size, no surprise workspace roots.
Use the monorepo’s documented pack command when it differs from root `npm pack`.
Prefer CI that fails on forbidden globs or max tarball size.

### 5. Lifecycle, clean pack, smoke

Ensure `prepare`/`prepack`/`prepublishOnly` emit artifacts covered by `files`.
Publish from clean CI so local untracked files are not the only hygiene control.
Document whether source maps / `src/` ship. Smoke: `npm i ./pkg.tgz` and resolve
exports, `bin`, and types. Diff file list against the last publish when auditing.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Pack contents, `files`, `.npmignore`, tarball audit | **This skill** | — |
| Lockfiles, pin/range, frozen CI install | `dependency-pinning-strategies` | this for pack membership |
| Registry namespace / confusion | `dependency-confusion` | this for publish path hygiene |
| Docker build context ignore | `dockerfile-best-practices` | this for npm tarball only |
| Token leak / .npmrc secrets | `secrets-management-hygiene` | this for pack exclusion |
| Package source/script edits | `code-quality-standards` | **always** on implementation |

Keep **this skill primary** until allowlist/ignore and dry-run membership are correct.

## Output Checklist

- [ ] Package root(s), `files`, `.npmignore`/`.gitignore` interaction inventoried
- [ ] `main`/`exports`/`types`/`bin` paths exist inside the packed tarball
- [ ] Allowlist preferred; tests, secrets, caches, monorepo noise excluded
- [ ] `npm pack --dry-run` (or monorepo equivalent) run; file list reviewed
- [ ] Lifecycle produces shippable artifacts; clean CI pack path documented
- [ ] Size / forbidden globs OK; no credentials in archive
- [ ] Smoke install from tarball resolves exports/bin/types
- [ ] Hand-off: pins → `dependency-pinning-strategies`; leaks → `secrets-management-hygiene`
- [ ] `code-quality-standards` when package sources or scripts change

## Rules

- **Repo config first**; never claim cleanliness without a dry-run file list.
- Prefer **`files` allowlist**; re-audit when adding paths.
- **`.npmignore` replaces gitignore for packing** when present.
- Never publish tokens, keys, or `.env`; treat accidental inclusion as an incident.
- Own **tarball membership** only—locks, Docker context, and registry confusion
  are neighboring skills.
