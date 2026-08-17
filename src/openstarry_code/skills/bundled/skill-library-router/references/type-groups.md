# 类型分组 / Skill Type Groups

这是一个**虚拟分组**索引。技能目录继续保持 Codex 可发现的顶层结构，分组只由路由器的精确规则计算，因此不会因为移动目录而破坏现有技能路径。

## 领域

| 分组 | 中文 | 覆盖范围 | 路由器 |
| --- | --- | --- | --- |
| `security-reverse` | 安全与逆向 | 安全、CTF、漏洞、认证、逆向、移动、二进制、取证 | `security-reverse-router` |
| `engineering` | 软件工程 | 编程、测试、调试、代码审查、API、Git、语言规范、架构 | `software-engineering-router` |
| `cloud-ops` | 云与运维 | AWS/Azure/GCP、容器、Kubernetes、CI/CD、数据库、网络、可观测性 | `cloud-ops-router` |
| `frontend-creative` | 前端与创意 | React/Vue、UI/UX、响应式、无障碍、浏览器、图像、视频、动效 | `frontend-creative-router` |
| `science-data` | 科学与数据 | 科学计算、统计、实验、机器学习、生物信息、数据分析 | `science-data-router` |
| `docs-research` | 文档与研究 | DOCX/XLSX/PPTX/PDF、Markdown、报告、论文、OCR、转写 | `docs-research-router` |
| `marketing-content` | 营销与内容 | SEO、营销、文案、内容策略、邮件、增长、转化、品牌 | `marketing-content-router` |
| `planning-product` | 规划与产品 | 任务计划、项目拆解、PRD、需求、路线图、优先级 | `planning-product-router` |
| `automation-catalog` | 自动化与目录 | SkillHub、技能搜索、MCP、SaaS 集成、浏览器自动化、来源审计 | `automation-catalog-router` |

## 查看分组

Windows：

```powershell
py -3 "$HOME\.codex\skills\skill-library-router\scripts\list_groups.py"
py -3 "$HOME\.codex\skills\skill-library-router\scripts\list_groups.py" --group frontend-creative
py -3 "$HOME\.codex\skills\skill-library-router\scripts\list_groups.py" --markdown > skill-groups.md
py -3 "$HOME\.codex\skills\skill-library-router\scripts\list_groups.py" --json
```

中英文关键词仍由统一调度器自动识别领域：

```powershell
py -3 "$HOME\.codex\skills\unified-skill-dispatcher\scripts\dispatch.py" "做一次 SEO 审计" --json
py -3 "$HOME\.codex\skills\unified-skill-dispatcher\scripts\dispatch.py" "analyze this experiment statistically" --json
```

分组计数允许重叠：例如云安全技能同时属于 `cloud-ops` 和 `security-reverse`，精确任务关键词决定最终主路由。
