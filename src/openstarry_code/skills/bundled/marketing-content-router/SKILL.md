---
name: marketing-content-router
description: Select the most specific installed skill for marketing strategy, SEO, copywriting, content, campaigns, positioning, pricing, launch, growth, retention, email, social media, and conversion optimization. Use for marketing, SEO, CRO, copy, campaign, 营销, 文案, 内容策略, 品牌语调, 增长, 转化率, 邮件营销, 社交媒体, or 竞品分析 requests.
---

# Marketing And Content Router

1. Search installed specialists with `<python> <codex-home>/skills/skill-library-router/scripts/find_local_skill.py "<task>" --group marketing-content --limit 12`.
2. Rerun with `--include-sources` only when the installed catalog has no credible specialist.
3. Route by requested outcome: acquisition/SEO, conversion/CRO, retention/email, launch/positioning, or editorial voice.
4. Use `humanizer` only for prose naturalness, not as the primary strategy skill.
5. Load one primary skill and one helper only when strategy and deliverable production are separate phases.
6. Preserve supplied facts, brand constraints, claims, and measurement definitions.

Exact routes: SEO audit -> `seo-audit`; content plan -> `content-strategy`;
email nurture -> `emails`; page conversion -> `cro`; natural prose ->
`humanizer`.
