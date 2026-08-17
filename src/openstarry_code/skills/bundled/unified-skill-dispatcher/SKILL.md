---
name: unified-skill-dispatcher
description: Single automatic entry point for selecting installed Codex skills by bilingual task keywords and exact intent. Use for broad, ambiguous, or multi-domain requests spanning engineering, frontend, security, cloud operations, science and data, documents and research, marketing and content, product planning, or automation, and whenever the user asks to find, choose, coordinate, audit, install, or dispatch skills.
---

# Unified Skill Dispatcher

Use this skill as the first routing step for requests that do not explicitly
name a concrete skill.

## Dispatch Procedure

1. If the user explicitly names an installed skill, load that skill directly.
2. Otherwise search the installed library before considering any cached source.
   The wrapper automatically infers one of nine domains from English and Chinese
   keywords before ranking concrete skills:

   ```powershell
   py -3 "$env:USERPROFILE\.codex\skills\unified-skill-dispatcher\scripts\dispatch.py" "<task>" --json
   ```

3. Select the highest-scoring concrete skill. Do not select a router as the
   final implementation skill. Load at most one primary and one helper unless
   the request has clearly independent deliverables.
4. Resolve ties by the earliest unresolved concern:
   - security, CTF, binary, mobile, protocol, malware, or forensics:
     `security-reverse-router`
   - application implementation, tests, API, language, quality, or Git:
     `software-engineering-router`
   - infrastructure, cloud, containers, CI/CD, database, network, or
     observability: `cloud-ops-router`
   - frontend, browser UI, accessibility, image, video, or visual design:
     `frontend-creative-router`
   - document, spreadsheet, slide, PDF, report, or research output:
     `docs-research-router`
   - scientific computing, statistics, machine learning, experiments, or data:
     `science-data-router`
   - marketing, SEO, copywriting, campaigns, growth, or conversion:
     `marketing-content-router`
   - project plans, task breakdowns, PRDs, roadmaps, or requirements:
     `planning-product-router`
   - external app connection, publishing, automation, or catalog discovery:
     `automation-catalog-router`
5. Read the selected concrete skill completely before changing files or running
   task-specific commands. Add one helper only when it owns a distinct phase.
6. Use `-IncludeSources` only when installed candidates do not cover the task.
   Source-cached material remains reference material until separately installed.

Use `--no-auto-group` only to diagnose cross-domain ranking. Normal requests
must keep automatic domain inference enabled. An explicitly named installed
skill always outranks inferred-domain routing.

## Frontend Exact Routes

Use these deterministic routes before generic score ordering:

| Request signal | Primary skill |
|---|---|
| `components.json`, shadcn registry, preset, add a shadcn component | `shadcn` |
| React/Next.js performance, waterfall, bundle, rerender | `vercel-react-best-practices` |
| Boolean prop sprawl, compound component, render props, reusable React API | `vercel-composition-patterns` |
| View Transition API, route/shared-element/enter-exit transition | `vercel-react-view-transitions` |
| Review UI, UX audit, accessibility or interface-guideline check | `web-design-guidelines` |
| New dashboard, product UI, design system, chart, responsive app shell | `ui-ux-pro-max` |
| Broad frontend polish, critique, hierarchy, interaction or edge states | `impeccable` |
| Landing page, portfolio, anti-template or anti-slop visual direction | `design-taste-frontend` |
| Upgrade an existing page without changing its stack or behavior | `redesign-existing-projects` |
| Explicit editorial/minimal/flat visual direction | `minimalist-ui` |
| Rebuild a web UI from a screenshot or visual reference | `image-to-code` |
| User explicitly requires every file/component with no omissions | `full-output-enforcement` as helper |

When two rows match, choose the row describing the requested outcome as primary
and the narrower implementation constraint as helper. Existing repository rules,
design systems, and neighboring components remain authoritative.

## Command Interface

`scripts/dispatch.py` wraps the maintained local index at
`skill-library-router/scripts/find_local_skill.py`.

```powershell
# Show the best installed candidates.
py -3 "$env:USERPROFILE\.codex\skills\unified-skill-dispatcher\scripts\dispatch.py" "analyze an Android APK" --json

# Limit a search to a known domain.
py -3 "$env:USERPROFILE\.codex\skills\unified-skill-dispatcher\scripts\dispatch.py" "review Kubernetes RBAC" --group cloud-ops

# Print inventory counts for a routing health check.
py -3 "$env:USERPROFILE\.codex\skills\skill-library-router\scripts\find_local_skill.py" --summary
```

The wrapper reports ranked candidates with their resolved `SKILL.md` paths.
It does not execute helpers from the returned skills. `dispatch.ps1` is retained
for PowerShell callers and can be run with `-ExecutionPolicy Bypass` where
required by the local execution policy.
