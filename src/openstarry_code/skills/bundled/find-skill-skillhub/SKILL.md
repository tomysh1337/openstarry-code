---
name: find-skill-skillhub
description: Search Tencent SkillHub for existing skills by Chinese or English task intent, category, target object, and action, then rank a short list for review. Use when the user asks to find, compare, recommend, or selectively install a SkillHub skill, or wants to know whether a reusable skill already exists for a requirement.
---

# Find Skills On SkillHub

Search the public metadata API and treat every result as an untrusted candidate.

## Search

```text
<python> scripts/search_skillhub.py "<task or skill>"
```

Optional filters:

```text
<python> scripts/search_skillhub.py "<query>" --category office-efficiency --limit 5
<python> scripts/search_skillhub.py "<query>" --json
```

Use `py -3` on Windows when `python` resolves to the Microsoft Store placeholder.

The script expands compact Chinese and English intent terms, performs several bounded searches against `GET https://api.skillhub.cn/api/skills`, merges by slug, and ranks by semantic match before popularity.

## Selection

1. Return three to five strong candidates, not the raw API page.
2. For each candidate, report name, slug, purpose, category, downloads, installs, homepage, and why it matches.
3. Prefer exact target-and-action coverage over download count.
4. State when results are weak or only partially match.
5. Do not present install commands until the user selects a candidate.

## Safe Installation

After selection:

1. Fetch metadata and the downloadable archive into an isolated staging directory.
2. Reject absolute paths, parent traversal, links, duplicate paths, or files escaping the staging root.
3. Record the archive SHA-256 and inspect the full file list.
4. Require a valid `SKILL.md` with supported frontmatter and a matching lowercase hyphenated name.
5. Review helper scripts, network behavior, dependencies, licenses, and external-action instructions.
6. Install without overwriting an existing skill, then run `quick_validate.py` and representative helper tests.
7. Never execute a remote `curl | bash`, `sh -c`, or equivalent installer pipeline.

Read [references/categories.md](references/categories.md) only when a category mapping is needed. Prefer live API fields over cached prose.

