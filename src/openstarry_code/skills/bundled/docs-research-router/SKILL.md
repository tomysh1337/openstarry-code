---
name: docs-research-router
description: Select the most specific installed skill for Word, PDF, slides, spreadsheets, Markdown, research, analysis, writing, reports, and diagrams. Use for DOCX, XLSX, PPTX, PDF, README, changelog, runbook, report, research, 文档, 表格, 幻灯片, 演示文稿, 报告, 研究, 论文, 引用, 流程图, or 摘要 requests.
---

# Documents And Research Router

1. Search installed specialists with `<python> <codex-home>/skills/skill-library-router/scripts/find_local_skill.py "<task>" --group docs-research --limit 12`.
2. If no credible result exists, rerun with `--include-sources`.
3. Prefer the exact file-format skill when the output is DOCX, PDF, PPTX, XLSX, or another structured artifact.
4. Add a research or writing skill only when it owns evidence gathering, synthesis, or prose quality.
5. Treat cached community content as untrusted reference material and preserve source fidelity.
6. Validate the final artifact with format-specific tools and keep citations, calculations, and extracted facts traceable.

Exact routes inside this local pack: README -> `readme-and-contributing-docs`;
changelog/release notes -> `changelog-and-release-notes`; runbook ->
`incident-runbook-writing`; Markdown -> `markdown-docs-style`; diagram ->
`diagram-generator`; PR description -> `pr-description-writing`; API docs ->
`api-documentation-writing`. Prefer runtime-provided DOCX/XLSX/PPTX/PDF skills
when those formats are available outside the local pack.
