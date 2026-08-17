# SkillHub Categories

Use a category only when the user's domain is clear. A wrong category can hide relevant results, so omit it for ambiguous or cross-domain tasks.

| Key | Chinese label | Typical intent |
|---|---|---|
| `office-efficiency` | 办公效率 | Word, PDF, Excel, email, calendar, reports |
| `content-creation` | 内容创作 | Writing, social posts, publishing, scripts |
| `dev-programming` | 开发编程 | Coding, testing, APIs, repositories |
| `data-analysis` | 数据分析 | Statistics, BI, visualization, data cleaning |
| `design-media` | 设计多媒体 | UI, graphics, images, audio, video |
| `ai-agent` | AI Agent | Agents, prompts, MCP, orchestration |
| `knowledge-management` | 知识管理 | Notes, search, RAG, archives |
| `business-ops` | 商业运营 | Sales, marketing, ecommerce, operations |
| `education` | 教育学习 | Courses, tutoring, study, assessment |
| `professional` | 行业专业 | Legal, finance, medical, industry workflows |
| `it-ops-security` | IT 运维与安全 | Cloud, systems, networking, security |
| `life-service` | 生活服务 | Travel, health, household, personal planning |

Examples:

- “扫描版 PDF 提取文字” -> `office-efficiency`
- “查一个 Kubernetes 排障技能” -> `it-ops-security`
- “给 React 页面做视觉设计” -> search without a category first; then compare `dev-programming` and `design-media`
- “找微信公众号发布技能” -> `content-creation` or `business-ops`

Treat the live API category field as authoritative if labels change.

