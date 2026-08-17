---
name: automation-catalog-router
description: Select the right installed automation or discovery skill for SaaS integrations, Composio/MCP, browser automation, publishing, downloads, scraping, SkillHub, and community catalogs. Use for automate, MCP, Composio, SkillHub, browser automation, web scraping, 自动化, 技能库, 技能搜索, 浏览器操作, 网页抓取, 应用连接, 外部应用, or 发布流程 requests.
---

# Automation And Catalog Router

1. Search installed automation skills with `<python> <codex-home>/skills/skill-library-router/scripts/find_local_skill.py "<task>" --group automation-catalog --limit 12`.
2. If no concrete match exists, rerun with `--include-sources`.
3. Prefer a concrete installed automation skill when available.
4. For Composio/Rube apps, use `composio-app-automation-catalog`.
5. For SkillHub search, use `find-skill-skillhub`; for the Awesome source and external manifest, use `awesome-community-skill-catalog`; for `anbeime/skill`, use `anbeime-skill-catalog`; for CSDN discovery and distillation, use `csdn-skill-distiller`.
6. Search catalogs before installation. Install only a selected, licensed, validated skill whose repeated use justifies active registration.
7. Confirm current tool schemas, account connections, and user authorization before external state changes.
8. Do not route here merely because a skill name contains `automation`, `catalog`, `app`, or `workflow`.

Exact routes: browser automation/自动操作浏览器 -> `browser-automation`;
Composio/SaaS connection -> `composio-app-automation-catalog`; SkillHub or
searching for a skill -> `find-skill-skillhub`; Web crawling/scraping ->
`web-crawler`; broader community discovery -> `awesome-community-skill-catalog`.
