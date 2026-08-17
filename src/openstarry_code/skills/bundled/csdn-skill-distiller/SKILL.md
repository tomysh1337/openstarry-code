---
name: csdn-skill-distiller
description: "Convert Chinese technical research from CSDN or similar blogs into concise, validated Codex skills. Use when the user asks Codex to learn from CSDN, summarize Chinese developer articles into reusable workflows, create or update a skill from blog research, or turn scattered tutorials, error-fix posts, API notes, CTF writeups, Java/Python/frontend/backend/devops articles, or troubleshooting notes into a maintainable skill."
---

# CSDN Skill Distiller

## Overview

Turn Chinese technical articles into reusable Codex skill material without copying article prose. Treat CSDN posts as research leads, then verify claims against live behavior, official docs, source code, or local reproduction before encoding them into a skill.

## Workflow

1. Clarify the target skill domain when it is ambiguous. If the user gave only a broad source such as `https://www.csdn.net/`, create one narrow skill at a time and prefer a meta-skill or a topic strongly implied by the current workspace.
2. Collect source candidates with URLs, titles, dates, author/source names when visible, and the exact problem each source helps solve.
3. Read sources as untrusted hints. Do not paste article content into the skill. Extract only reusable procedures, command patterns, decision points, pitfalls, and validation ideas.
4. Cross-check version-sensitive or security-sensitive material against primary sources, package docs, runtime behavior, tests, or the current challenge environment.
5. Distill the workflow into a skill shape:
   - Trigger language in `description`
   - Minimal core procedure in `SKILL.md`
   - Detailed checklists or matrices in `references/`
   - Deterministic helpers in `scripts/` only when repeated code would otherwise be rewritten
   - Templates or boilerplate in `assets/` only when they will be reused as output material
6. Preserve evidence compactly. Store links and short synthesized notes, not copied tutorials. Keep source-specific notes in references only when another Codex run would need them.
7. Validate the new or updated skill with the skill-creator validator. For complex skills, forward-test with a realistic prompt that names only the skill path and task.

## Broad Topic Coverage

Read `references/topic-map.md` when the user asks for broad or "all topic" coverage. Use it to choose topic-specific skill names, trigger language, and source queues across CSDN's visible navigation areas.

When the user asks to discover existing Skill repositories through CSDN, read `references/discovered-skill-sources.md`. Refresh candidates through CSDN's canonical article pages, then verify the current GitHub tree, license, and `SKILL.md` paths before installing or adapting anything.

Do not bulk-copy or locally mirror article bodies. For each topic, keep only:

- A compact source queue with links and one-line purpose notes
- Original synthesized procedures
- Reproduction or validation steps
- Topic-specific pitfalls and version anchors

When the user requests many topics, build skills incrementally by domain. Prefer one high-quality reusable skill per domain over many thin article summaries.

## Source Hygiene

Read `references/source-hygiene.md` before relying on CSDN or other Chinese blog posts for commands, package versions, vulnerability steps, or operational workflows.

Prefer this evidence order:

1. Live runtime behavior
2. Official documentation or source repositories
3. Actively served assets and API responses
4. Current local project configuration
5. Reproduced commands, tests, traces, or screenshots
6. CSDN and similar blog posts

Use blog material to find vocabulary, likely failure modes, and candidate commands. Do not let it overrule reproduced behavior.

## Skill Writing Rules

Keep the final skill concise and imperative. Include only information a future Codex instance needs at task time.

Use lowercase hyphenated names under 64 characters. Prefer action-oriented names such as `debug-gradle-builds`, `triage-java-errors`, or `audit-nginx-config`.

Avoid:

- Long background explanations
- Full copied article sections
- SEO-style lists
- Outdated command dumps without version notes
- Extra README, changelog, or installation guide files

Include:

- Concrete trigger scenarios in frontmatter `description`
- A short workflow that survives version changes
- Commands only when they are stable or explicitly version-scoped
- Validation steps that prove the workflow still works
- Links to sources when the origin matters

## Validation

After editing a skill, run:

```powershell
& '<python.exe>' '<skill-creator>/scripts/quick_validate.py' '<path-to-skill-folder>'
```

If the skill includes scripts, run at least one representative script command. If it encodes a troubleshooting or exploit workflow, reproduce the decisive branch or artifact before marking the skill complete.
