---
name: planning-product-router
description: Select the most specific installed skill for project planning, task decomposition, persistent progress tracking, product requirements, PRDs, roadmaps, user stories, discovery, and prioritization. Use for project plan, task plan, roadmap, PRD, requirements, 任务规划, 项目计划, 制定计划, 拆解任务, 多步骤规划, 进度跟踪, 产品需求, 产品路线图, 需求分析, 用户故事, or 优先级 requests.
---

# Planning And Product Router

1. Search installed specialists with `<python> <codex-home>/skills/skill-library-router/scripts/find_local_skill.py "<task>" --group planning-product --limit 12`.
2. Rerun with `--include-sources` only when no installed workflow matches.
3. Use `planning-with-files` for durable multi-step execution state; use a requirements or roadmap specialist for product artifacts.
4. Separate discovery assumptions from confirmed requirements and keep decisions traceable.
5. Load one primary skill and at most one helper for implementation or documentation.
6. Do not activate planning overhead for a small, single-file, or quick lookup task.

Exact routes: persistent multi-step plan -> `planning-with-files`; ambiguous
requirements -> `requirements-clarification`; roadmap -> `roadmap-planning`.
