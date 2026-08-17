---
name: readme-and-contributing-docs
description: >
  Structure and write project README, CONTRIBUTING, and quickstart docs that
  get users running and contributors shipping safely. Use when README,
  CONTRIBUTING, quickstart, 写说明文档, project overview, onboarding docs,
  setup instructions, or polishing the repository entrypoint for developers.
---

# README And Contributing Docs

Make the repository entrypoint answer three jobs fast: **what this is**, **how
to run it**, and **how to contribute without breaking the house rules**. Prefer
existing project voice, section order, and tooling over a generic template dump.

## Use When

- Creating or rewriting `README.md` (or root `README.rst` / docs landing that
  serves as the entrypoint)
- Writing or updating `CONTRIBUTING.md`, `CONTRIBUTING.zh-CN.md`, or
  `docs/contributing*`
- Adding a **quickstart** that gets a new developer to a first successful run
- User mentions: README, CONTRIBUTING, quickstart, 写说明文档, 项目说明,
  onboarding, setup docs, developer guide entry

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Markdown fences, tables, link hygiene only | `markdown-docs-style` |
| OpenAPI operation descriptions | `api-documentation-writing` |
| In-code docstrings / TSDoc | `docstring-and-typedoc` |
| Security assessment writeups | domain security skill |

## Repo Config First

Repo layout and existing docs **outrank** this skill’s section template.

1. **Entrypoints already present:** root `README*`, `CONTRIBUTING*`,
   `docs/README`, monorepo package READMEs, `AGENTS.md` / `Agents.md`
2. **Tooling truth:** package managers and scripts in `package.json`,
   `pyproject.toml`, `go.mod`, `Makefile`, `Taskfile`, `cargo` workspace,
   `docker-compose*`, `.nvmrc` / `.python-version` / `rust-toolchain`
3. **CI as source of truth:** required checks, lint/test/format commands in
   `.github/workflows` (or equivalent)—document what CI actually runs
4. **House rules:** code of conduct, DCO/CLA, commit/PR templates
   (`.github/PULL_REQUEST_TEMPLATE*`), branch naming, release process
5. **Audience split:** library consumers vs application operators vs internal
   monorepo contributors; do not mash all three into one wall of text
6. **Language policy:** EN-only, 中文, or bilingual (`README.md` +
   `README.zh-CN.md`); match the product’s public language

**Precedence:** Follow the repo’s established README shape. When empty or
chaotic, use the structure below. Never invent install commands that are not
in scripts/CI—verify by reading config or running the documented path.

## Workflow

1. **Name the audience and job.** e.g. “App developer wants local API in 10
   minutes” vs “OSS library user wants install + minimal example.”
2. **Load repo config** (section above). Extract real prerequisites, versions,
   and script names.
3. **Outline before prose.** Prefer the section order in **README structure**
   / **CONTRIBUTING structure** below; drop sections that do not apply; do not
   pad with empty badges or aspirational features.
4. **Write the quickstart last among discovery, first among verification.**
   Draft install/run after you know the real commands; then put quickstart
   high in the README so scanners hit it early.
5. **Make every command copy-pasteable.** From repo root unless stated.
   Separate “you type this” from expected output. Mark OS-specific steps.
6. **Link deeper docs; don’t duplicate.** Architecture, full API reference,
   ADRs, and runbooks live under `docs/` or the portal—README points to them.
7. **Align CONTRIBUTING with README.** Same install baseline; CONTRIBUTING
   adds branch/PR/test/lint/review norms and “how to propose changes.”
8. **Verify.** Run the quickstart on a clean mental path (or real clean
   checkout when practical). Fix broken links; run markdownlint/link check if
   the repo has them. Redact secrets and internal-only hostnames.

## README Structure (default)

Use this order when the repo has no stronger convention. Omit N/A sections.

1. **Title + one-paragraph pitch** — what it is, who it is for, one outcome
2. **Badges (optional)** — only if CI/package badges exist and stay truthful
3. **Features / non-goals (short)** — bullets; explicit non-goals prevent wrong
   expectations
4. **Quickstart** — prerequisites → install → configure → run → verify
   (e.g. hit health endpoint or run one test). Aim for the shortest happy path
5. **Configuration** — required env vars table; point to full config reference
6. **Usage examples** — minimal library import or CLI invocation
7. **Project layout (optional)** — only if monorepo or non-obvious structure
8. **Documentation map** — links to API docs, design docs, runbooks
9. **Development** — one-liner to CONTRIBUTING or short “lint / test / build”
10. **License / security contact** — `LICENSE`, `SECURITY.md` if present

**Monorepos:** Root README explains the workspace and points to package
READMEs. Each publishable package keeps its own install + API quickstart.

## CONTRIBUTING Structure (default)

1. **Welcome + expectations** — code of conduct link; “discuss large changes
   first” if that is policy
2. **Prerequisites** — toolchain versions (link to README quickstart rather
   than forking install steps when identical)
3. **Local setup** — clone, deps, env file templates (`.env.example`), DB/redis
   if required, how to run the app and tests
4. **Development workflow** — branch naming, commit message norms (if any),
   format/lint/typecheck/test commands **exactly as CI**
5. **PR checklist** — what reviewers expect (tests, docs, changelog)
6. **Architecture pointers** — where to read before large changes
7. **Release / versioning (if contributors participate)** — semver, changeset,
   changelog ownership
8. **Getting help** — issues, discussions, chat—only real channels

## Style Rules (defaults when repo is silent)

- **Scannable:** short paragraphs; headings as navigation; quickstart within
  the first screen when practical
- **Commands from root:** `npm ci`, `pnpm install`, `uv sync`, `make test`—
  match the lockfile and Makefile that exist
- **Placeholders consistent:** `<project-id>`, `YOUR_API_KEY`, or ALL_CAPS env
  names; never paste live keys
- **Versions explicit:** “Node 20+”, “Python 3.12”, not “recent Node”
- **Truth over marketing:** do not list features that are half-merged; mark
  experimental clearly
- **Single H1** on the page; follow `markdown-docs-style` for fences and links
- **Bilingual:** keep section parity or clearly mark which language is
  canonical when docs diverge

## Good / Bad Examples

### Pitch

**Good**

```markdown
# Invoice Worker

Async worker that finalizes draft invoices and pushes PDF renders to object
storage. Aimed at backend engineers running the billing stack locally or in
staging.
```

**Bad**

```markdown
# invoice-worker
The best next-gen AI-powered synergy platform for all your needs!!!
```

### Quickstart

**Good**

```markdown
## Quickstart

**Prerequisites:** Node 20+, Docker (Postgres 16).

```bash
cp .env.example .env
docker compose up -d postgres
npm ci
npm run db:migrate
npm run dev
```

Verify:

```bash
curl -s http://localhost:3000/health
# {"status":"ok"}
```
```

**Bad**

```markdown
## Setup
Install dependencies and run the app somehow.
Also configure the database (ask Bob).
Use the production API key from 1Password.
```

### Configuration table

**Good**

```markdown
| Variable | Required | Description |
| --- | --- | --- |
| `DATABASE_URL` | yes | Postgres connection string |
| `LOG_LEVEL` | no | Default `info` |
```

**Bad**

```markdown
Set the usual env vars. See source for names.
```

### CONTRIBUTING test gate

**Good**

```markdown
## Before you push

```bash
npm run lint
npm run typecheck
npm test
```

CI runs the same three scripts; PRs that skip them will fail checks.
```

**Bad**

```markdown
Please test your code. We use various linters.
```

### README vs deep docs

**Good** — README links out:

```markdown
## Documentation

- [HTTP API (OpenAPI)](./docs/api/openapi.yaml)
- [Architecture](./docs/architecture.md)
- [Contributing](./CONTRIBUTING.md)
```

**Bad** — pastes the entire OpenAPI file into README, or duplicates CONTRIBUTING
install steps that immediately rot.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| README, CONTRIBUTING, quickstart, 写说明文档 | **This skill** | — |
| Markdown structure, fences, tables, anchors | `markdown-docs-style` | apply for form |
| OpenAPI endpoint descriptions inside linked specs | `api-documentation-writing` | README only links |
| Code comment / docstring quality | `comment-writing-standards` / `docstring-and-typedoc` | — |
| Implementation quality of sample code in README | `code-quality-standards` | keep samples minimal |
| AGENTS.md / skill library routing docs | match local Agents conventions | this skill for onboarding shape |

## Checklist

- [ ] Audience and primary job stated in the opening pitch
- [ ] Repo scripts, toolchain versions, and CI commands used as source of truth
- [ ] Quickstart is copy-pasteable from repo root with verify step
- [ ] Prerequisites and required env vars documented (table or `.env.example`)
- [ ] No live secrets, internal-only URLs, or “ask Bob” gaps
- [ ] Features/non-goals truthful; experimental marked
- [ ] Deep topics linked (`docs/`, API portal), not dumped into README
- [ ] CONTRIBUTING aligns with README install; adds PR/lint/test/review norms
- [ ] Monorepo: root map + per-package entrypoints as needed
- [ ] Language policy respected (EN / 中文 / bilingual)
- [ ] Links and markdown lint/build checked when available
- [ ] Diff limited to intended docs; no drive-by reformat of unrelated pages
