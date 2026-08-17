---
name: codeql-query-pack-basics
description: >
  CodeQL packs: qlpack.yml layout, query vs library packs, dependencies,
  lock files, custom queries, suite selection, and analyze/CI wiring for
  org-owned codebases. Use when creating or packing CodeQL query packs,
  qlpack.yml / codeql-pack.yml, pack dependencies, codeql pack resolve,
  custom .ql queries, query suites, database analyze with packs, or
  GitHub code-scanning pack configuration.
---

# CodeQL Query Pack Basics

Own **CodeQL pack** structure for authorized/org-owned codebases: declare packs,
pin deps, author queries/suites, resolve, and run `database analyze` (or Actions)
reproducibly. CI topology → `ci-cd-pipeline-patterns`; fixes → language skills +
`code-quality-standards`.

## When To Use

- Creating/refactoring a **query pack** or **library pack** (`qlpack.yml`)
- Declaring **dependencies**, versions, and `codeql-pack.lock.yml` resolution
- Writing custom `.ql` / `.qll` and **query suites** (`.qls`)
- Running `codeql pack` / `codeql database analyze` with pack specs
- Wiring org packs into GitHub code scanning / Advanced Security
- Keywords: CodeQL pack, qlpack.yml, query pack, library pack, pack resolve,
  suite, `queries:`, `packs:`

Do **not** use as primary for: CI graphs → `ci-cd-pipeline-patterns`; SCA/SBOM →
`sbom-and-supply-chain`; Go vulndb → `go-govulncheck-workflow`; secrets →
`secrets-management-hygiene`; binary RE → `binary-re/static-analysis`; app
quality → `code-quality-standards`.

## Repo Config First

Repo and org CodeQL wiring **outrank** samples below.

1. **Existing packs:** `qlpack.yml` / `codeql-pack.yml` under `.github/codeql`,
   `codeql/`, or monorepo security trees — **extend**
2. **CLI / Actions pin:** CodeQL CLI or `github/codeql-action` version
3. **Languages & DB:** `codeql-config.yml`, init languages, paths/paths-ignore
4. **Default packs:** GitHub `codeql/*-queries` vs private org packs/registry
5. **Suites:** security-extended, security-and-quality, or custom `.qls`
6. **Auth / neighbors:** GHAS; registry tokens never committed; SARIF gates

**Precedence:** Match pack names, pins, and analyze command. Surface floating
`@latest` deps, missing locks on release packs, unpublished local libs.

## Workflow

### 1. Pack kind and layout

| Kind | Role | Contents |
| --- | --- | --- |
| **Query pack** | Runnable queries/suites | `.ql`, `.qls`, `qlpack.yml` |
| **Library pack** | Shared predicates/models | `.qll`; consumed as deps |
| **Model pack** | Framework/dataflow models | Language-specific models |

```yaml
# qlpack.yml
name: my-org/java-security-queries
version: 0.1.0
groups: [queries]
dependencies:
  codeql/java-all: "*"
  codeql/java-queries: "*"
extractor: java
```

Use scoped `org/name` names. Split shared helpers into a library pack when
multiple query packs need them.

### 2. Dependencies and lock

```bash
codeql pack install
codeql pack resolve deps
codeql pack download codeql/java-queries
```

Pin major (or exact) versions for CI. Commit `codeql-pack.lock.yml` when the org
requires reproducible packs. Private registry auth via CI secrets only.

### 3. Queries and suites

- One main query per `.ql`; shared logic in `.qll`.
- Set `@id`, `@name`, `@severity`, `@tags`, `@precision`, `@problem.severity`.
- Prefer library dataflow/path-problem patterns over ad-hoc AST greps.
- Select/exclude via `.qls` suites.

```yaml
# example.qls
- description: Org Java security extras
- queries: .
- exclude:
    id: [java/example-noisy-id]
```

### 4. Database, analyze, CI, verify

```bash
codeql database create db --language=java --command='./gradlew -q assemble'
codeql database analyze db my-org/java-security-queries:suite.qls \
  --format=sarif-latest --output=results.sarif
```

Same pack version/suite locally and in CI. Multi-language: one DB (or matrix)
per language. Prefer `codeql-config.yml` / workflow `packs`+`queries`; pin
`github/codeql-action/*`; upload SARIF; gate severity (`ci-cd-pipeline-patterns`).
Compile pack; analyze a small known DB; diff SARIF. Bump pack `version` on
publish. FPs: tighten query or suite exclude with owner — never silently drop
high severity.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| qlpack.yml, pack deps, custom .ql/.qls, analyze with packs | **This skill** | — |
| Workflow YAML, required checks, caches | `ci-cd-pipeline-patterns` | this for pack body |
| Private registry tokens / secret process | `secrets-management-hygiene` | this for pack layout |
| App fixes from findings | language skills + `code-quality-standards` | this for evidence |
| Multi-lang SCA/SBOM | `sbom-and-supply-chain` | this for CodeQL SAST |
| Go vulndb gate only | `go-govulncheck-workflow` | optional parallel |

Keep **this skill primary** until pack identity, deps, suite, and analyze
command are correct; apply **`code-quality-standards`** on code changes.

## Output Checklist

- [ ] Repo packs, config, Actions pins, and language matrix read first
- [ ] Pack kind clear (query/library/model); `name`/`version` set
- [ ] Dependencies declared; lock committed if org requires it
- [ ] Queries have stable `@id`/severity metadata; shared logic in `.qll`
- [ ] Suite selects intended queries; noisy IDs excluded with rationale
- [ ] DB create matches real build; analyze uses same pack/suite as CI
- [ ] SARIF produced; CLI/action pinned; tokens not logged; version bumped
- [ ] Routed: CI → `ci-cd-pipeline-patterns`; fixes → CQS; authorized scope only

## Rules

- **Authorized** codebases/org packs only; prefer **pack + suite** over ad-hoc `.ql` in CI.
- Treat pack/CLI pins as toolchain inventory; redact registry tokens and sensitive paths.
