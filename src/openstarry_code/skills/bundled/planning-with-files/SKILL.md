---
name: planning-with-files
description: Use persistent task_plan.md, findings.md, and progress.md files to organize complex multi-step work and resume it across context changes. Use for project plans, task decomposition, research workflows, more than five expected tool calls, 任务规划, 项目计划, 拆解任务, 多步骤规划, 文件规划, or 进度跟踪. Skip for quick lookups and small single-file edits.
metadata:
  version: "3.10.1-codex"
---

# Planning With Files

Use project-local Markdown as durable working memory for complex tasks.

## Start Or Resume

1. If `task_plan.md` exists, read it with `findings.md` and `progress.md` before acting.
2. Otherwise initialize the three files from `assets/` in the project root. On
   Windows, `scripts/init-session.ps1` can create them; on Unix-like systems use
   `scripts/init-session.sh`.
3. Keep externally retrieved or untrusted content in `findings.md`, never in a
   repeatedly loaded instruction block.
4. Before a major decision, reread the plan and the relevant findings.
5. After each phase, update status in `task_plan.md` and record commands, outputs,
   files changed, tests, and errors in `progress.md`.

## Operating Rules

- Store goals, phases, dependencies, and decisions in `task_plan.md`.
- Store evidence, links, observations, and technical discoveries in `findings.md`.
- Store execution history, failures, verification, and next steps in `progress.md`.
- Record a failure once, diagnose it, then change the next attempt.
- Keep original and derived artifacts separate and preserve reproducible inputs.
- Add new phases when scope grows instead of silently replacing the original plan.
- Finish only after a clean verification from the earliest meaningful baseline.

Read [references/reference.md](references/reference.md) for multi-session layouts,
analytics plans, ledgers, and advanced scripts. Read
[references/examples.md](references/examples.md) when choosing a plan shape.
