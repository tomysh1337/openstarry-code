---
name: yarn-berry-constraints
description: >
  Author, fix, and enforce Yarn Berry (Yarn 2+) workspace constraints for
  dependency consistency, banned packages, field rules, and CI gates. Use when
  yarn constraints, constraints.pro, yarn.config.cjs constraints, monorepo
  dependency alignment, workspace: protocol rules, yarn constraints --fix,
  or Berry package graph policy are in scope — hand lockfile pin strategy to
  dependency-pinning-strategies and SBOM/CVE inventory to sbom-and-supply-chain.
---

# Yarn Berry Constraints

Own **Yarn Berry workspace constraints**: declarative rules over the package
graph (versions, fields, bans, peers, `workspace:`) and CI enforcement. Prefer
the repo’s Yarn major and existing rules. Not pin/float policy, SBOM, or npm/pnpm-only.

## When To Use

- Adding, reviewing, or debugging **`yarn constraints`** / **`yarn constraints --fix`**
- Yarn 2–3 **Prolog** (`.yarn/constraints.pro`) or Yarn 4+ **JS**
  (`yarn.config.cjs` / `defineConfig` + `constraints` callback)
- Monorepo **version drift** (same package, different ranges across workspaces)
- Enforcing **`workspace:`** for internals, banning deps, or package.json field
  policy (`engines`, `license`, `private`)
- CI failing on constraints; local tree green but policy still violated
- Mentions: Yarn Berry constraints, constraints.pro, yarn.config.cjs, monorepo alignment

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Lockfiles, exact vs range, Renovate/Dependabot | `dependency-pinning-strategies` |
| SBOM, SCA/CVE, provenance | `sbom-and-supply-chain` / `sbom-ci-enforcement` |
| Registry namespace confusion | `dependency-confusion` |
| npm/pnpm-only (no Berry) | pin/hygiene skills for that installer |
| Secrets in Yarn/CI config | `secrets-management-hygiene` |
| App implementation quality | `code-quality-standards` |

## Repo Config First

Repo and org Yarn policy **outrank** defaults below.

1. **Yarn major + installer:** `.yarnrc.yml` (`nodeLinker`, `yarnPath`, plugins),
   committed binary under `.yarn/releases` when used
2. **Constraint source:** `.yarn/constraints.pro` (Prolog) **or** `yarn.config.cjs`
   / TS config with `constraints` (Yarn 4+)
3. **Workspaces:** root `package.json` `workspaces` and nested packages
4. **Lock + CI:** `yarn.lock`, immutable install, existing constraint job
5. **Catalogs / linker:** dependency catalogs, PnP vs node-modules
6. **Neighbors:** Renovate/Dependabot, CODEOWNERS on constraint files, private registry

**Precedence:** Extend existing rules; no Prolog↔JS rewrite without a plan. Never
“fix” by deleting constraints or skipping CI.

## Workflow

### 1. Detect engine and baseline

1. Confirm Berry (Yarn ≥2): `yarn --version`, `.yarnrc.yml` (not classic-only).
2. Locate constraints: JS `yarn.config.cjs` → `constraints({ Yarn })` **or**
   Prolog `.yarn/constraints.pro` (+ plugin if required by major).
3. Run without fix: `yarn constraints` (or repo script). Capture all violations.
4. Note `nodeLinker`; constraints still target workspace manifests.

### 2. Inventory policy intent

| Intent | Typical rule |
| --- | --- |
| Align versions | Same ident → same range/version across workspaces |
| Internal linking | Internals use `workspace:^` / `workspace:*` |
| Ban / allowlist | Forbid idents or require scoped internals |
| Manifest fields | Enforce `engines`, `license`, `private`, repo URL |
| Peers | Peer ranges coherent with direct deps |
| Dev vs prod | No build-only tools as runtime deps on publishables |

Prefer **few high-signal rules** over one-off exception sprawl.

### 3. Author or fix rules
**Yarn 4+ JS (illustrative—match repo Yarn API docs):**

```js
// yarn.config.cjs
module.exports = {
  async constraints({ Yarn }) {
    for (const dep of Yarn.dependencies({ ident: 'lodash' })) {
      dep.update('^4.17.21');
    }
    for (const workspace of Yarn.workspaces()) {
      // fields / workspace: protocol per org standards
    }
  },
};
```

**Prolog (Yarn 2/3):** keep predicates readable; comment non-obvious
`gen_enforced_dependency` / field rules; parameterize by workspace type.

1. Constraints enforce **manifests** (Yarn model), not lock-only hand edits.
2. `yarn constraints --fix` only when safe; then install per immutable policy;
   re-run constraints until clean.
3. Exceptions: **named allowlists** or documented owner + expiry—not silent disables.
4. Prefer a **catalog** or single shared range over per-workspace drift.

### 4. CI gates and verify

1. CI **fails** on nonzero `yarn constraints`; pair with `yarn install --immutable`
   (or repo equivalent).
2. Optional: require the job when `package.json`, constraint files, or `.yarnrc.yml` change.
3. No auto-merge of bot PRs that skip the constraints step.
4. Verify: clean exit 0; deliberate skew fails; `--fix` restores policy; review
   lock diffs. Document how new workspaces inherit rules.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Berry constraints, constraints.pro, yarn.config.cjs | **This skill** | — |
| Lock pins, Renovate/Dependabot, exact vs range | `dependency-pinning-strategies` | this for enforcement |
| SBOM / CVE / provenance | `sbom-and-supply-chain` | this for tree consistency |
| SBOM CI gates | `sbom-ci-enforcement` | constraints + immutable install |
| Registry namespace confusion | `dependency-confusion` | this for allow/ban idents |
| CI layout / caches | `ci-cd-pipeline-patterns` | constraint step wiring |
| Tokens in Yarn/CI | `secrets-management-hygiene` | this for non-secret policy |
| Shipped config/scripts quality | `code-quality-standards` | **always** |

**Hand-offs:** pins → `dependency-pinning-strategies`; SCA → `sbom-and-supply-chain`.
Keep **this skill primary** until constraint files and CI gate are correct.

## Output Checklist

- [ ] Yarn major, `.yarnrc.yml`, and engine (Prolog vs JS) identified
- [ ] `yarn constraints` baseline run; violations classified by intent
- [ ] Rules cover alignment, bans, fields, peers, and/or `workspace:` as needed
- [ ] Fixes via `--fix` + install—not deleted rules or lock-only hacks
- [ ] Exceptions have owner/expiry or explicit allowlist
- [ ] CI fail-closed on constraints + immutable install
- [ ] Deliberate violation proves the gate; clean run exits 0
- [ ] Hand-off: pins/bots → `dependency-pinning-strategies`; CVE → SBOM skills
- [ ] `code-quality-standards` on config/scripts touched
