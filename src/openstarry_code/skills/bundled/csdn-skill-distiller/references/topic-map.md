# CSDN Topic Map for Skill Coverage

Use this map when a user asks to learn broadly from CSDN and add the result to Codex skills. The map comes from visible CSDN navigation and homepage sections, and should be refreshed before large updates because categories and featured topics change.

## Current Top-Level Topics

- `csdn-news-research`: 资讯, vendor news, ecosystem shifts, release notes, trend tracking.
- `csdn-openclaw-research`: OpenClaw-specific articles, tools, platform notes, ecosystem updates.
- `csdn-deepseek-research`: DeepSeek models, deployment notes, prompt/application patterns, benchmark claims.
- `csdn-mcp-research`: MCP protocol, tools, server/client implementation, workflow integration.
- `csdn-devops-research`: 运维, SRE, Linux service operations, deployment, observability, incident triage.
- `csdn-cann-research`: CANN, Ascend, AI accelerator toolchains, operator/runtime troubleshooting.
- `csdn-os-research`: 操作系统, Linux/Windows internals, kernel/userland debugging, environment setup.
- `csdn-ai-research`: 人工智能, LLM applications, model serving, agents, RAG, evaluation, AI engineering.
- `csdn-java-research`: Java language, JVM, Spring, Maven/Gradle, concurrency, backend troubleshooting.
- `csdn-cpp-research`: C/C++, toolchains, STL, memory, build systems, native debugging.
- `csdn-python-research`: Python language, packaging, data tooling, automation, web/backend, native extensions.
- `csdn-algorithms-research`: 数据结构与算法, sorting, graphs, dynamic programming, interview patterns.
- `csdn-frontend-research`: 前端, HTML/CSS/JS/TS, Vue/React, browser APIs, build tools.
- `csdn-backend-research`: 后端, APIs, databases, middleware, auth, queues, distributed systems.
- `csdn-opensource-research`: 开源项目, project evaluation, installation, usage, integration notes.
- `csdn-mobile-research`: Android, HarmonyOS, mobile publishing, app store policy, mobile debugging.
- `csdn-database-research`: MySQL, Redis, SQL design, indexes, constraints, query troubleshooting.
- `csdn-git-tooling-research`: Git, GitHub, IDEs, local developer environment, Windows build tools.

## Skill Creation Pattern

For each domain skill:

1. Name the skill with a stable action, not a source name, when possible. Example: prefer `debug-gradle-builds` over `csdn-java-gradle-posts`.
2. Put CSDN and similar sources in references as leads, with links and verification status.
3. Keep `SKILL.md` focused on the reusable workflow.
4. Add scripts only for repeated deterministic checks, such as log classifiers or environment probes.
5. Validate with local tests, official docs, or live sandbox behavior before trusting a blog claim.

## Source Queue Format

Use this compact format in topic references:

```markdown
## Sources

- URL: <link>
  Title: <title>
  Topic: <domain>
  Claim used: <one-sentence paraphrase>
  Verification: reproduced | official-doc-confirmed | weak-lead | rejected
```

Never paste full article bodies into the queue.
