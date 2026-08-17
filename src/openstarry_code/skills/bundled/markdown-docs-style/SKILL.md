---
name: markdown-docs-style
description: >
  Write and edit Markdown documentation with consistent headings, links, tables,
  code fences, and docs-site hygiene. Use when markdown style, docs markdown,
  README polish, CONTRIBUTING, ADRs, MkDocs/Docusaurus/VitePress content, or
  fixing broken docs structure, anchors, or fence languages.
---

# Markdown Docs Style

Produce Markdown that is scannable, link-stable, and friendly to common docs
toolchains (GitHub, MkDocs, Docusaurus, VitePress, Sphinx/MyST). Prefer the
repository’s existing docs conventions over generic preference.

## Use When

- Authoring or rewriting `README`, `CONTRIBUTING`, `docs/**`, ADRs, runbooks, or skill docs
- User asks for markdown style, docs markdown, heading hierarchy, or fence hygiene
- Fixing broken internal links, inconsistent tables, or unlabelled code blocks
- Preparing docs for a static site generator or GitHub rendering
- Reviewing a docs-only PR for structure and readability (not product UI design)

Do **not** use this as primary for visual product UI (`frontend-design`,
`apple-ui-design`, `top-design`) or for security assessment writeups that need
a domain skill first.

## Repo Config First

Before inventing style rules, read what the repo already enforces:

1. **Style / lint config:** `.markdownlint.json(c)`, `.markdownlint.yaml`,
   `markdownlint-cli2` config, `.prettierrc*` (prose wrap), `remarkrc*`,
   `vale.ini` / `.vale.ini`, `lychee.toml`, `mlc_config.json`
2. **Docs toolchain:** `mkdocs.yml`, `docusaurus.config.*`, `vitepress` config,
   `sidebars.*`, `docs.json`, Sphinx `conf.py`, Mintlify / Nextra config
3. **Project rules:** `CONTRIBUTING.md`, `docs/README`, style guides under
   `docs/`, `AGENTS.md` / `Agents.md`, PR templates that prescribe docs layout
4. **Local examples:** 2–3 recently edited pages in the same docs tree; match
   heading depth, link style, callout syntax, and frontmatter keys
5. **CI checks:** workflows that run markdownlint, link checkers, or spellcheck

**Precedence:** repo config and neighboring docs **outrank** this skill’s defaults.
If repo rules conflict with a default below, follow the repo and note the conflict
only when it causes broken anchors, inaccessible tables, or unrenderable fences.

## Workflow

1. **Scope the doc.** Audience (contributor, operator, end user), one primary
   job, and whether the file is entrypoint (`README`) or deep reference.
2. **Load repo config** (section above). Note required frontmatter, admonition
   syntax, and max line length / prose wrap.
3. **Outline headings first.** One H1 per page (title). Sections as H2; subsections
   H3. Avoid skipping levels (`##` → `####`). Prefer parallel phrasing among siblings.
4. **Write for scan.** Lead each section with the answer or action; put background
   after. Prefer short paragraphs and tight lists over walls of text.
5. **Links and anchors.** Prefer relative paths inside the repo. Use descriptive
   link text (not “click here”). Keep heading text stable if others deep-link;
   when renaming headings, fix inbound anchors and sidebar entries.
6. **Tables.** Header row + separator; align columns for source readability when
   practical; avoid tables for long prose or nested lists (use headings/lists).
7. **Code fences.** Always set a language tag when known (`bash`, `json`, `ts`,
   `text`). Prefer copy-pasteable commands; separate interactive shell prompts
   from script bodies when readers might copy them.
8. **Docs-site hygiene.** Update nav/sidebar/index when adding pages; avoid orphan
   pages; keep frontmatter (`title`, `description`, `sidebar_position`) consistent;
   do not commit secrets, tokens, or live credentials in examples—use placeholders.
9. **Verify.** Run the repo’s markdownlint / link check / docs build when available.
   Spot-check GitHub preview or local docs dev server for tables, anchors, and fences.

## Style Rules (defaults when repo is silent)

### Headings

- Exactly one `#` title per file (unless the toolchain forbids H1 in body).
- Use sentence case or the repo’s established case; do not mix Title Case and
  sentence case randomly in the same tree.
- Headings are navigation labels: specific (`## Install from source`), not vague
  (`## Stuff`).
- Do not end headings with punctuation except `?` when truly a FAQ item.
- Keep heading-derived anchors unique on the page (avoid duplicate section titles).

### Links

- Internal: relative paths (`../api/auth.md`, `./images/flow.png`). Avoid machine-specific absolute paths.
- External: full `https://` URLs; consider whether a version-pinned docs URL is required.
- Reference-style links are fine for repeated URLs; keep the definition block tidy at the bottom or near the section.
- Images: meaningful alt text; store assets next to docs or in the repo’s conventional `static/` / `img/` path.

### Tables

- Use tables for comparisons, parameters, and matrices—not for multi-paragraph cells.
- Escape pipes in cells (`\|`) or rephrase.
- First column ideally the “key” (name, flag, field); keep column count small (≤5 when possible).

### Code fences

- Fenced blocks with language; indent code blocks only when nested inside lists requires it (4 spaces / tight list rules per renderer).
- For CLI: show a realistic invocation; mark placeholders with `<>` or ALL_CAPS consistently.
- For diffs, use `diff` language when illustrating changes.
- Do not fence ordinary prose. Do not use triple backticks for inline code—use single backticks.
- Avoid tabs in fences unless the language requires them; prefer spaces to match project style.

### Lists and emphasis

- One idea per bullet; keep nesting shallow (one sub-level when possible).
- Use numbered lists only for ordered procedures.
- Bold for UI labels or critical warnings sparingly; italics for introducing terms once.

### Docs site hygiene

- New page → nav/sidebar + optional index mention in the same change when the site uses explicit navigation.
- Prefer stable filenames (`install.md`) over frequent renames; when renaming, add redirects if the toolchain supports them.
- Callouts/admonitions: use the site’s native syntax (`!!! note`, `:::tip`, etc.), not invent a third style.
- Frontmatter titles should match or closely track the H1 to avoid double-title glitches.

## Examples

### Headings

**Good**

```markdown
# Deploy the worker

## Prerequisites
## Configure environment
### Required variables
## Roll back
```

**Bad**

```markdown
# Deploy the worker
### Configure environment
# Another H1 on the same page
## prerequisites
## Configure Environment!!!
```

### Links

**Good**

```markdown
See [authentication overview](../security/auth.md#tokens).
Full reference: [OpenAPI 3.1](https://spec.openapis.org/oas/v3.1.0).
![Request flow](./images/request-flow.png)
```

**Bad**

```markdown
Click [here](../security/auth.md).
Details: https://spec.openapis.org/oas/v3.1.0 (raw URL as the only cue).
![](./images/request-flow.png)
```

### Tables

**Good**

```markdown
| Variable | Required | Description |
| --- | --- | --- |
| `API_URL` | yes | Base URL for the API |
| `LOG_LEVEL` | no | Default `info` |
```

**Bad**

```markdown
| Variable | Notes |
| --- | --- |
| API_URL | You must set this or nothing works and also see the wiki for history... |
| | missing header alignment / incomplete row |
```

### Code fences

**Good**

````markdown
Install dependencies:

```bash
npm ci
npm run build
```

Config shape:

```json
{
  "port": 8080
}
```
````

**Bad**

````markdown
```
npm ci
```

```javascript
{ "port": 8080 }
```
(wrong language tag; JSON is not JavaScript)
````

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Markdown / docs structure, fences, tables, links | **This skill** | — |
| Implementation code quality inside fenced samples | `code-quality-standards` | keep samples minimal and correct |
| Product UI / visual page design (not docs Markdown) | `frontend-design` | `apple-ui-design` / `top-design` |
| API inventory or OpenAPI discovery (assessment) | `api-recon-and-docs` | not a prose-style skill |
| Security procedure content | domain security skill | this skill for Markdown form only |
| Code review comment wording on a docs PR | `code-review-comments-style` | this skill for docs criteria |

## Checklist

- [ ] Repo markdown/docs config and neighboring page style checked first
- [ ] Single clear H1; heading levels do not skip
- [ ] Sections scannable; procedures numbered where order matters
- [ ] Internal links relative and descriptive; images have alt text
- [ ] Tables reserved for structured data; columns consistent
- [ ] Code fences have correct language tags; placeholders obvious
- [ ] No secrets in examples; placeholders documented
- [ ] Sidebar/nav/index updated if the docs site requires it
- [ ] Frontmatter matches toolchain conventions
- [ ] Lint / link check / docs build run when available
- [ ] Diff limited to intended docs; no drive-by reformat of unrelated pages
