#!/usr/bin/env python3
"""Search installed and cached Codex skills with high-precision domain routing."""

from __future__ import annotations

import argparse
import json
import os
import re
import unicodedata
from pathlib import Path


GROUP_ORDER = (
    "security-reverse",
    "cloud-ops",
    "frontend-creative",
    "science-data",
    "docs-research",
    "marketing-content",
    "planning-product",
    "engineering",
    "automation-catalog",
)

GROUP_QUERY_PATTERNS = {
    "security-reverse": (
        (r"\b(?:ctf|pwn|rop|exploit|pentest|malware|forensics?|reverse engineering)\b", 8),
        (r"\b(?:apk|ghidra|ida|frida|pcap|firmware|deobfuscation)\b", 7),
        (r"\b(?:vulnerability|security|xss|sqli|ssrf|csrf|jwt|oauth|auth bypass)\b", 5),
        (r"(?:安全|漏洞|渗透|逆向|取证|恶意软件|脱壳|反编译|抓包|利用链|二进制)", 8),
    ),
    "cloud-ops": (
        (r"\b(?:aws|azure|gcp|kubernetes|k8s|docker|terraform|helm|devops)\b", 8),
        (r"\b(?:container|cluster|pipeline|observability|prometheus|deployment|infra)\b", 5),
        (r"(?:云服务|云平台|运维|容器|集群|部署|基础设施|监控|可观测|流水线)", 7),
    ),
    "frontend-creative": (
        (r"\b(?:frontend|ui|ux|react|next\.js|vue|svelte|shadcn|a11y|wcag)\b", 7),
        (r"\b(?:dashboard|landing page|responsive|animation|design system|web design)\b", 6),
        (r"(?:前端|界面|网页|组件|仪表盘|数据看板|响应式|动效|动画|无障碍|设计系统)", 7),
    ),
    "science-data": (
        (r"\b(?:science|scientific|statistics?|statistical(?:ly)?|machine learning|data science|bioinformatics|genomics|chemistry|physics)\b", 8),
        (r"\b(?:analy[sz]e|design).*(?:experiment|study)\b", 7),
        (r"\b(?:pandas|polars|numpy|scipy|matplotlib|seaborn|sklearn|rdkit|biopython|pymc)\b", 7),
        (r"(?:科学计算|科研|统计分析|数据科学|机器学习|生物信息|基因组|化学信息|实验设计|假设检验)", 8),
    ),
    "docs-research": (
        (r"\b(?:docx|xlsx|pptx|pdf|spreadsheet|slides?|document|report|research|markdown)\b", 7),
        (r"\b(?:readme|changelog|runbook|citation|paper|presentation|diagram|ocr|transcription|speech.to.text)\b", 6),
        (r"\b(?:extract.*text|text.*image|image.*text)\b", 7),
        (r"(?:文档|表格|幻灯片|演示文稿|报告|研究|论文|引用|知识库|流程图|摘要|文字识别|图片.*提取|音频转写|语音转文字)", 7),
    ),
    "marketing-content": (
        (r"\b(?:marketing|seo|copywriting|content strategy|campaign|brand voice|conversion|cro|email sequence|social media)\b", 8),
        (r"\b(?:humanize|natural rewrite|sound.*natural|more natural)\b", 8),
        (r"\b(?:positioning|pricing|launch|growth|retention|customer research|competitor analysis)\b", 6),
        (r"(?:市场营销|营销|文案|内容策略|品牌语调|增长|转化率|用户留存|邮件营销|社交媒体|竞品分析)", 8),
    ),
    "planning-product": (
        (r"\b(?:project plan|task plan|planning|roadmap|product requirements?|prd|user stories|prioritization|requirements gathering)\b", 8),
        (r"\b(?:progress tracking|milestone|work breakdown|product management|discovery)\b", 6),
        (r"(?:任务规划|项目计划|制定计划|拆解任务|多步骤规划|进度跟踪|产品需求|产品路线图|需求分析|用户故事|优先级)", 8),
    ),
    "engineering": (
        (r"\b(?:python|typescript|javascript|golang|rust|java|csharp|\.net)\b", 6),
        (r"\b(?:code review|review code|code quality|unit tests?|integration tests?|debug|refactor|api design|api versioning|api documentation|json schema|git)\b", 6),
        (r"\b(?:implementation|coding|architecture|migration|package|dependency|lint)\b", 4),
        (r"(?:代码|编程|开发|调试|重构|单元测试|集成测试|架构|接口设计|依赖|迁移)", 6),
    ),
    "automation-catalog": (
        (r"\b(?:skillhub|skill sources?|skill cache|cached skills?|audit.*skills?|composio|mcp|browser automation|web scraping|crawler)\b", 8),
        (r"\b(?:automate|automation|publish|download|external app|saas integration)\b", 5),
        (r"(?:自动化|技能库|技能搜索|技能来源|技能缓存|技能审计|浏览器操作|网页抓取|网站抓取|抓取.*(?:网站|网页)|应用连接|外部应用|发布流程)", 7),
    ),
}

ROUTER_NAMES = {
    "unified-skill-dispatcher",
    "skill-library-router",
    "security-reverse-router",
    "software-engineering-router",
    "cloud-ops-router",
    "frontend-creative-router",
    "docs-research-router",
    "automation-catalog-router",
    "science-data-router",
    "marketing-content-router",
    "planning-product-router",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "for",
    "from",
    "help",
    "in",
    "of",
    "on",
    "or",
    "please",
    "the",
    "to",
    "use",
    "using",
    "with",
    "我",
    "帮我",
    "需要",
    "一个",
    "一下",
    "如何",
    "怎么",
    "这个",
}

TOKEN_ALIASES = {
    "build": ("builder",),
    "create": ("creator", "generator"),
    "deploy": ("deployment",),
    "test": ("testing",),
    "write": ("writing", "writer"),
    "构建": ("builder",),
    "创建": ("creator", "generator"),
    "测试": ("testing",),
    "写": ("writing", "writer"),
    "前端": ("frontend", "web", "ui"),
    "网页": ("web", "frontend", "interface"),
    "界面": ("ui", "interface", "frontend"),
    "设计": ("design", "ui", "ux"),
    "组件": ("component", "composition", "react"),
    "响应": ("responsive", "design", "layout"),
    "仪表": ("dashboard", "ui", "interface"),
    "动效": ("animation", "motion", "transition"),
    "动画": ("animation", "motion", "transition"),
    "过渡": ("transition", "animation", "motion"),
    "性能": ("performance", "optimization"),
    "审查": ("review", "audit"),
    "重设": ("redesign", "design"),
    "重做": ("redesign", "design"),
    "极简": ("minimalist", "minimal", "ui"),
    "无障": ("accessibility", "a11y", "wcag"),
    "着陆": ("landing", "page", "frontend"),
    "落地": ("landing", "page", "frontend"),
    "截图": ("image", "code", "frontend"),
    "科研": ("science", "research", "scientific"),
    "统计": ("statistics", "analysis", "data"),
    "数据科学": ("data", "science", "analysis"),
    "机器学习": ("machine", "learning", "ml"),
    "营销": ("marketing", "campaign", "growth"),
    "文案": ("copywriting", "content", "writing"),
    "转化": ("conversion", "cro", "marketing"),
    "规划": ("planning", "plan", "roadmap"),
    "计划": ("planning", "plan", "project"),
    "需求": ("requirements", "product", "prd"),
}

RULES = {
    "security-reverse": {
        "names": {
            "account-lockout-design",
            "account-takeover-methodology",
            "api-sec",
            "api-security",
            "apk-reverse",
            "attack-chain",
            "auth-sec",
            "binary-re",
            "bug-bounty-methodology",
            "captcha-bypass-research",
            "deep-analysis",
            "hack",
            "hello-js-reverse-skill",
            "llm-security",
            "mobile-reverse",
            "network-protocol-analysis-skill",
            "pentest-tools",
            "reverse-engineering",
            "reverse-skill",
        },
        "prefixes": (
            "active-directory-",
            "android-pentesting-",
            "binary-re-",
            "competition-",
            "ctf-",
            "firmware-",
            "frida-",
            "ghidra-",
            "ida-",
            "ios-pentesting-",
            "malware-",
            "pwn-",
            "reverse-",
        ),
        "terms": {
            "anti-debugging",
            "attack",
            "attacks",
            "authentication",
            "authorization",
            "authn",
            "authz",
            "bola",
            "bypass",
            "codeql",
            "cors",
            "credential",
            "credentials",
            "csrf",
            "csp",
            "ctf",
            "dast",
            "deobfuscation",
            "exploit",
            "exploitation",
            "forensic",
            "forensics",
            "hardening",
            "iam",
            "idor",
            "injection",
            "integrity",
            "jwt",
            "lateral-movement",
            "malware",
            "mtls",
            "oauth",
            "obfuscation",
            "oidc",
            "pentest",
            "pentesting",
            "pki",
            "privilege-escalation",
            "pwn",
            "rbac",
            "reverse-engineering",
            "saml",
            "sast",
            "sbom",
            "secret",
            "secrets",
            "secure",
            "security",
            "semgrep",
            "ssrf",
            "threat",
            "tls",
            "traversal",
            "vulnerability",
            "vulnerabilities",
            "vuln",
            "xss",
            "xxe",
            "yara",
            "安全",
            "漏洞",
            "逆向",
            "取证",
        },
    },
    "engineering": {
        "names": {
            "async-concurrency-patterns",
            "backpressure-patterns",
            "caching-strategies",
            "circuit-breaker-patterns",
            "code-quality-standards",
            "debugger-integration",
            "feature-flag-patterns",
            "load-shedding-patterns",
            "mocking-and-test-doubles",
            "mutation-testing-basics",
            "property-based-testing",
            "retry-backoff-patterns",
        },
        "prefixes": (
            "bun-",
            "composer-",
            "csharp-",
            "eslint-",
            "git-",
            "go-",
            "gradle-",
            "java-",
            "maven-",
            "npm-",
            "nuget-",
            "openapi-",
            "pip-",
            "pnpm-",
            "prettier-",
            "protobuf-",
            "pypi-",
            "python-",
            "react-component-",
            "rust-",
        ),
        "terms": {
            "api-design",
            "api-documentation",
            "api-versioning",
            "architecture",
            "async",
            "backpressure",
            "branch-protection",
            "caching",
            "circuit-breaker",
            "code-quality",
            "code-review",
            "coding",
            "commit-message",
            "concurrency",
            "contract-testing",
            "debugging",
            "dependency",
            "development",
            "docstring",
            "editorconfig",
            "eslint",
            "git-workflow",
            "graphql",
            "grpc",
            "integration-test",
            "lint",
            "lockfile",
            "migration",
            "mocking",
            "naming-conventions",
            "openapi",
            "packaging",
            "prettier",
            "property-based-testing",
            "protobuf",
            "schema-design",
            "style-conventions",
            "test-strategy",
            "testing",
            "typing",
            "工程",
            "代码",
            "测试",
            "架构",
        },
    },
    "cloud-ops": {
        "names": {
            "backpressure-patterns",
            "bulkhead-isolation",
            "caching-strategies",
            "chaos-engineering-basics",
            "circuit-breaker-patterns",
            "load-shedding-patterns",
            "observability-metrics-tracing",
            "performance-testing-basics",
            "retry-backoff-patterns",
        },
        "prefixes": (
            "acr-",
            "ansible-",
            "argo-",
            "artifact-registry-",
            "aws-",
            "azure-",
            "cert-manager-",
            "cloudformation-",
            "docker-",
            "ecr-",
            "envoy-",
            "external-secrets-",
            "flux-",
            "gcp-",
            "gcr-",
            "github-actions-",
            "gitlab-ci-",
            "haproxy-",
            "helm-",
            "istio-",
            "jenkins-",
            "kubernetes-",
            "nginx-",
            "opa-",
            "podman-",
            "pulumi-",
            "terraform-",
        ),
        "terms": {
            "admission-webhook",
            "certificate",
            "ci-cd",
            "container-image",
            "container-runtime",
            "database",
            "devops",
            "dnssec",
            "dockerfile",
            "firewall-rule",
            "gitops",
            "load-shedding",
            "networking",
            "observability",
            "pipeline",
            "registry",
            "reliability",
            "retry-backoff",
            "rootless",
            "service-mesh",
            "secrets-operator",
            "运维",
            "容器",
            "数据库",
            "网络",
        },
    },
    "frontend-creative": {
        "names": {
            "accessibility-a11y-checklist",
            "angular-security-basics",
            "apple-ui-design",
            "artifacts-builder",
            "brand-guidelines",
            "browser-extension-security",
            "canvas-design",
            "electron-app-security",
            "error-message-ux-writing",
            "frontend-design",
            "design-taste-frontend",
            "full-output-enforcement",
            "i18n-l10n-guidelines",
            "image-to-code",
            "image-enhancer",
            "impeccable",
            "minimalist-ui",
            "nextjs-security-checklist",
            "pptx",
            "pwa-security-checklist",
            "react-component-patterns",
            "react-hooks-security",
            "redesign-existing-projects",
            "shadcn",
            "slack-gif-creator",
            "state-management-guidelines",
            "theme-factory",
            "top-design",
            "ui-ux-pro-max",
            "vercel-composition-patterns",
            "vercel-react-best-practices",
            "vercel-react-view-transitions",
            "web-design-guidelines",
            "webapp-testing",
        },
        "prefixes": (),
        "terms": {
            "a11y",
            "accessibility",
            "frontend",
            "animation",
            "component",
            "dashboard",
            "design-system",
            "landing-page",
            "motion",
            "react",
            "responsive-design",
            "shadcn",
            "transition",
            "ui",
            "ux",
            "user-experience",
            "user-interface",
            "visual-design",
            "wcag",
            "前端",
            "动效",
            "动画",
            "响应式",
            "界面",
            "组件",
            "无障碍",
            "视觉设计",
        },
    },
    "science-data": {
        "names": {
            "biopython",
            "citation-management",
            "experimental-design",
            "exploratory-data-analysis",
            "literature-review",
            "matplotlib",
            "networkx",
            "numpy",
            "pandas",
            "polars",
            "pymc",
            "rdkit",
            "scientific-critical-thinking",
            "scientific-visualization",
            "scientific-writing",
            "scikit-learn",
            "seaborn",
            "statistical-analysis",
            "statistical-power",
            "statsmodels",
            "sympy",
        },
        "prefixes": (
            "bio-",
            "chem-",
            "genomic-",
            "molecular-",
            "scientific-",
            "statistical-",
        ),
        "terms": {
            "bioinformatics",
            "chemistry",
            "data-science",
            "experimental-design",
            "genomics",
            "machine-learning",
            "scientific-computing",
            "statistics",
            "科研",
            "科学计算",
            "数据科学",
            "机器学习",
            "统计分析",
        },
    },
    "docs-research": {
        "names": {
            "binary-re-synthesis",
            "changelog-and-release-notes",
            "content-research-writer",
            "csdn-skill-distiller",
            "data-storytelling",
            "diagram-generator",
            "docx",
            "internal-comms",
            "incident-runbook-writing",
            "lead-research-assistant",
            "meeting-insights-analyzer",
            "markdown-docs-style",
            "markdown-converter",
            "ocr-local",
            "openai-whisper",
            "pdf",
            "pptx",
            "pr-description-writing",
            "presentations",
            "readme-and-contributing-docs",
            "tailored-resume-generator",
            "xlsx",
            "gemini-deep-research",
        },
        "prefixes": (),
        "terms": {
            "analysis-report",
            "changelog",
            "content-research",
            "csv",
            "data-analysis",
            "documentation",
            "docstring",
            "internal-communications",
            "knowledge-management",
            "markdown",
            "meeting-insights",
            "pr-description",
            "readme",
            "release-notes",
            "report-writing",
            "research",
            "resume",
            "runbook",
            "spreadsheet",
            "technical-writing",
            "文档",
            "写作",
            "研究",
            "报告",
            "表格",
            "演示",
        },
    },
    "marketing-content": {
        "names": {
            "ab-test-setup",
            "ad-creative",
            "analytics-tracking",
            "brand-voice",
            "churn-prevention",
            "competitor-alternatives",
            "content-strategy",
            "copy-editing",
            "copywriting",
            "emails",
            "form-cro",
            "free-tool-strategy",
            "humanizer",
            "launch-strategy",
            "marketing-ideas",
            "marketing-psychology",
            "onboarding-cro",
            "cro",
            "paid-ads",
            "pricing-strategy",
            "product-marketing-context",
            "product-marketing",
            "programmatic-seo",
            "schema-markup",
            "seo-audit",
            "signup-flow-cro",
            "social-content",
        },
        "prefixes": ("marketing-", "seo-"),
        "terms": {
            "brand-voice",
            "campaign",
            "content-strategy",
            "conversion",
            "copywriting",
            "cro",
            "growth",
            "marketing",
            "positioning",
            "retention",
            "seo",
            "social-media",
            "市场营销",
            "品牌",
            "增长",
            "文案",
            "营销",
            "转化率",
        },
    },
    "planning-product": {
        "names": {
            "brainstorming",
            "planning-with-files",
            "planning-with-files-zh",
            "product-manager-toolkit",
            "requirements-clarification",
            "roadmap-planning",
            "writing-plans",
        },
        "prefixes": ("planning-", "product-management-", "requirements-", "roadmap-"),
        "terms": {
            "milestone",
            "planning",
            "prd",
            "prioritization",
            "product-management",
            "product-requirements",
            "progress-tracking",
            "project-plan",
            "roadmap",
            "task-plan",
            "user-stories",
            "产品需求",
            "任务规划",
            "优先级",
            "产品路线图",
            "项目计划",
            "进度跟踪",
            "需求分析",
        },
    },
    "automation-catalog": {
        "names": {
            "anbeime-skill-catalog",
            "awesome-community-skill-catalog",
            "browser-automation",
            "composio-app-automation-catalog",
            "connect",
            "connect-apps",
            "csdn-skill-distiller",
            "find-skill-skillhub",
            "langsmith-fetch",
            "mcp-builder",
            "skill-share",
            "skill-source-manager",
            "web-crawler",
        },
        "prefixes": (),
        "terms": {
            "app-connection",
            "external-app",
            "mcp-server",
            "saas-integration",
            "skill-discovery",
            "tool-integration",
            "应用连接",
            "技能发现",
        },
    },
}

GROUP_EXCLUDES = {
    "security-reverse": {
        "code-quality-standards",
        "csdn-skill-distiller",
        "database-migration-safety",
        "error-message-ux-writing",
        "logging-message-style",
    },
    "automation-catalog": {
        "acme-dns01-automation",
        "ctf-sandbox-orchestrator",
        "ssrf-filter-bypass-catalog",
    },
    "science-data": set(),
    "marketing-content": set(),
    "planning-product": set(),
}

AUTOMATION_SUFFIXES = (
    "-analyzer",
    "-automation",
    "-downloader",
    "-extractor",
    "-generator",
    "-organizer",
    "-optimizer",
    "-picker",
    "-publisher",
)

INTENT_BOOSTS = (
    (
        (r"\bapk\b", r"android.*(?:reverse|decompil)", r"(?:安卓|android).*(?:逆向|反编译)"),
        {"apk-reverse": 120, "android-reverse-engineering": 90},
    ),
    ((r"\bghidra\b",), {"ghidra-reverse": 120}),
    ((r"\bida(?: pro)?\b",), {"ida-reverse": 120}),
    ((r"\bfrida\b",), {"frida-17": 120, "frida-hooking-playbook": 100}),
    (
        (r"binary.*static", r"static.*binary", r"二进制.*静态", r"静态分析"),
        {"binary-re-static-analysis": 110},
    ),
    (
        (r"binary.*dynamic", r"dynamic.*binary", r"二进制.*动态", r"动态分析"),
        {"binary-re-dynamic-analysis": 110},
    ),
    ((r"\bmalware\b", r"恶意软件", r"样本分析"), {"malware-analysis": 110}),
    ((r"\bforensics?\b", r"数字取证", r"日志取证"), {"digital-forensics": 110}),
    ((r"\b(?:pcap|packet capture)\b", r"流量分析", r"协议抓包"), {"network-protocol-analysis-skill": 220}),
    ((r"\b(?:pwn|rop)\b", r"栈溢出", r"利用链"), {"pwn-chain": 110}),
    ((r"\bweb pentest\b", r"web 渗透", r"网站渗透"), {"web-pentest": 110}),
    ((r"\bctf\b", r"夺旗赛", r"竞赛题"), {"ctf-sandbox-orchestrator": 90}),
    (
        (r"\bcode review\b", r"review.*code quality", r"代码审查", r"审查代码"),
        {"code-quality-standards": 130, "code-review-comments-style": 70},
    ),
    ((r"\bunit tests?\b", r"单元测试"), {"unit-testing-style": 110}),
    ((r"\bintegration tests?\b", r"集成测试"), {"integration-test-strategy": 110}),
    ((r"\bdebug(?:ging)?\b", r"调试", r"定位 bug"), {"debugger-integration": 100}),
    ((r"\bpython\b.*(?:style|typing)", r"python.*(?:规范|类型)"), {"python-style-and-typing": 110}),
    ((r"\btypescript\b.*(?:strict|migration)", r"typescript.*(?:严格|迁移)"), {"typescript-strict-migration": 110}),
    ((r"\bgit\b.*(?:workflow|branch|commit)", r"git.*(?:工作流|分支|提交)"), {"git-workflow-conventions": 100}),
    ((r"\bapi documentation\b", r"接口文档", r"api 文档"), {"api-documentation-writing": 110}),
    ((r"\bapi version", r"接口版本", r"api 版本"), {"api-versioning-design": 110}),
    ((r"json schema", r"json 模式", r"json 架构"), {"json-schema-design": 110}),
    ((r"async.*concurr", r"concurr.*async", r"异步并发"), {"async-concurrency-patterns": 110}),
    ((r"database migration", r"数据库迁移"), {"database-migration-safety": 110}),
    ((r"\baws\b.*\bs3\b", r"s3.*(?:bucket|桶)"), {"aws-s3-bucket-hardening": 120}),
    ((r"\baws\b.*\biam\b", r"aws.*身份权限"), {"aws-iam-least-privilege": 120}),
    ((r"\baws\b.*\blambda\b", r"lambda.*权限"), {"aws-lambda-least-privilege": 110}),
    ((r"azure.*key ?vault", r"azure.*密钥库"), {"azure-keyvault-basics": 120}),
    ((r"gcp.*\biam\b", r"gcp.*身份权限"), {"gcp-iam-basics": 120}),
    ((r"kubernetes.*\brbac\b", r"k8s.*\brbac\b", r"集群.*角色权限"), {"kubernetes-rbac-least-privilege": 120}),
    ((r"kubernetes.*network polic", r"k8s.*网络策略"), {"kubernetes-network-policy": 120}),
    ((r"dockerfile", r"docker 镜像构建"), {"dockerfile-best-practices": 110}),
    ((r"terraform.*state", r"terraform.*状态"), {"terraform-state-locking": 110}),
    ((r"terraform.*provider", r"terraform.*提供商"), {"terraform-provider-pinning": 110}),
    ((r"\bci/?cd\b", r"持续集成", r"持续部署"), {"ci-cd-pipeline-patterns": 100}),
    ((r"observability", r"metrics.*tracing", r"可观测", r"指标.*链路"), {"observability-metrics-tracing": 110}),
    ((r"\breadme\b", r"项目说明"), {"readme-and-contributing-docs": 110}),
    ((r"\bchangelog\b", r"变更日志"), {"changelog-and-release-notes": 110}),
    ((r"\brunbook\b", r"运维手册", r"故障手册"), {"incident-runbook-writing": 110}),
    ((r"\bmarkdown\b", r"markdown 文档"), {"markdown-docs-style": 100}),
    ((r"\bdiagram\b", r"流程图", r"架构图"), {"diagram-generator": 100}),
    ((r"\bpr description\b", r"pr 描述", r"合并请求说明"), {"pr-description-writing": 110}),
    ((r"browser automation", r"自动操作浏览器", r"浏览器自动化"), {"browser-automation": 120}),
    ((r"\bcomposio\b", r"saas integration", r"应用连接"), {"composio-app-automation-catalog": 120}),
    ((r"\bskillhub\b", r"查找技能", r"搜索技能"), {"find-skill-skillhub": 120}),
    ((r"skill source", r"skill cache", r"audit skills", r"技能来源", r"技能缓存", r"技能审计", r"更新技能库"), {"skill-source-manager": 140}),
    ((r"web crawl", r"crawler", r"网页抓取", r"网站抓取", r"网站爬取", r"抓取.*(?:网站|网页)"), {"web-crawler": 110}),
    (
        (r"\bshadcn\b", r"components\.json", r"组件注册表", r"预设码"),
        {"shadcn": 120},
    ),
    (
        (
            r"(?:react|next(?:\.js|js)?).*(?:performance|bundle|waterfall|rerender)",
            r"(?:performance|bundle|waterfall|rerender).*(?:react|next(?:\.js|js)?)",
            r"(?:react|next(?:\.js|js)?).*(?:性能|包体|瀑布流|重渲染)",
            r"(?:性能|包体|瀑布流|重渲染).*(?:react|next(?:\.js|js)?)",
        ),
        {"vercel-react-best-practices": 100},
    ),
    (
        (r"boolean prop", r"compound component", r"render prop", r"布尔属性", r"复合组件"),
        {"vercel-composition-patterns": 100},
    ),
    (
        (r"view transition", r"shared element", r"页面过渡", r"路由过渡", r"共享元素"),
        {"vercel-react-view-transitions": 100},
    ),
    (
        (r"(?:existing|current).*(?:redesign|restyle)", r"(?:redesign|restyle).*(?:existing|current)", r"(?:现有|当前).*(?:重做|重设|重构|改版|重新设计|重设计)", r"(?:重做|重设|改版|重新设计|重设计).*(?:现有|当前)"),
        {"redesign-existing-projects": 110},
    ),
    (
        (r"screenshot.*(?:code|web|page|ui)", r"(?:截图|设计图).*(?:还原|网页|界面|代码)"),
        {"image-to-code": 110},
    ),
    (
        (r"dashboard", r"仪表盘", r"数据看板", r"后台界面"),
        {"ui-ux-pro-max": 90},
    ),
    (
        (r"(?:ui|ux).*(?:review|audit)", r"(?:review|audit).*(?:ui|ux)", r"(?:界面|网页).*(?:审查|检查|审核)"),
        {"web-design-guidelines": 90},
    ),
    (
        (r"accessibility", r"\ba11y\b", r"\bwcag\b", r"无障碍"),
        {"accessibility-a11y-checklist": 100, "web-design-guidelines": 60},
    ),
    (
        (r"minimalist", r"editorial minimal", r"极简", r"编辑风"),
        {"minimalist-ui": 100},
    ),
    (
        (r"landing page", r"portfolio", r"着陆页", r"落地页", r"作品集"),
        {"design-taste-frontend": 80},
    ),
    (
        (r"no omissions", r"complete files?", r"full output", r"不要省略", r"完整输出", r"全部文件"),
        {"full-output-enforcement": 80},
    ),
    ((r"\bocr\b", r"extract.*text.*image", r"text.*from.*image", r"图片.*(?:文字|识别|提取)", r"(?:文字|内容).*图片.*提取", r"文字识别"), {"ocr-local": 130}),
    ((r"speech.to.text", r"transcrib", r"语音转文字", r"音频转写"), {"openai-whisper": 130}),
    ((r"convert.*markdown", r"转.*markdown", r"转换.*markdown"), {"markdown-converter": 130}),
    ((r"deep research", r"深度研究", r"多源研究"), {"gemini-deep-research": 120}),
    ((r"literature review", r"文献综述"), {"literature-review": 130}),
    ((r"experimental design", r"实验设计"), {"experimental-design": 130}),
    ((r"statistical analysis", r"statistically", r"统计分析"), {"statistical-analysis": 150}),
    ((r"scientific writing", r"科研写作", r"科学写作"), {"scientific-writing": 130}),
    ((r"data visuali[sz]ation", r"数据可视化"), {"scientific-visualization": 120, "data-storytelling": 80}),
    ((r"humanize", r"remove ai writing", r"sound.*natural", r"more natural", r"去除.*ai.*味", r"润色得更自然", r"自然润色"), {"humanizer": 130}),
    ((r"seo audit", r"seo 审计", r"seo 检查"), {"seo-audit": 130}),
    ((r"content strategy", r"内容策略"), {"content-strategy": 130}),
    ((r"email sequence", r"邮件序列", r"邮件营销"), {"emails": 130}),
    ((r"conversion rate", r"\bcro\b", r"转化率优化"), {"cro": 130}),
    ((r"task plan", r"project plan", r"任务规划", r"项目计划", r"文件规划"), {"planning-with-files": 140, "planning-with-files-zh": 140}),
    ((r"product requirements?", r"\bprd\b", r"产品需求"), {"requirements-clarification": 120}),
)


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).lower().replace("_", "-")
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", value).strip("-")


def contains_term(value: str, term: str) -> bool:
    normalized_value = normalize(value)
    normalized_term = normalize(term)
    return bool(normalized_term) and f"-{normalized_term}-" in f"-{normalized_value}-"


def query_tokens(value: str) -> list[str]:
    tokens: list[str] = []
    for part in normalize(value).split("-"):
        if not part or part in STOPWORDS:
            continue
        if re.fullmatch(r"[a-z0-9]+", part) and len(part) < 2:
            continue
        tokens.append(part)
        if re.fullmatch(r"[\u4e00-\u9fff]+", part) and len(part) > 2:
            tokens.extend(part[index : index + 2] for index in range(len(part) - 1))
    expanded = list(token for token in tokens if token not in STOPWORDS)
    for token in list(expanded):
        expanded.extend(TOKEN_ALIASES.get(token, ()))
    return list(dict.fromkeys(expanded))


def infer_group(query: str) -> str | None:
    """Return the strongest bilingual domain match for an unscoped query."""
    value = unicodedata.normalize("NFKC", query).lower()
    scores = {
        group: sum(weight for pattern, weight in patterns if re.search(pattern, value))
        for group, patterns in GROUP_QUERY_PATTERNS.items()
    }
    best_score = max(scores.values(), default=0)
    if best_score <= 0:
        return None
    return next(group for group in GROUP_ORDER if scores.get(group, 0) == best_score)


def default_codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))


def default_roots() -> list[Path]:
    codex_home = default_codex_home()
    candidates = [
        codex_home / "skills",
        Path.home() / ".agents" / "skills",
        codex_home / "plugins" / "cache" / "openai-bundled",
        codex_home / "plugins" / "cache" / "openai-primary-runtime",
    ]
    return [path for path in candidates if path.is_dir()]


def default_source_roots() -> list[tuple[Path, str]]:
    source_home = default_codex_home() / "skill-sources"
    if not source_home.is_dir():
        return []
    origin_aliases = {
        "anbeime-skill": "anbeime-cache",
        "composiohq-awesome-claude-skills": "awesome-cache",
        "hello-js-reverse-skill": "csdn-cache",
        "skillhub-cn": "skillhub-cache",
    }
    return [
        (path, origin_aliases.get(path.name, f"cache:{path.name}"))
        for path in sorted(source_home.iterdir(), key=lambda item: item.name.lower())
        if path.is_dir() and not path.name.startswith(".")
    ]


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    return value.replace(r'\"', '"')


def parse_metadata(text: str, fallback: str) -> tuple[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return fallback, ""
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration:
        return fallback, ""

    values: dict[str, str] = {}
    frontmatter = lines[1:end]
    index = 0
    while index < len(frontmatter):
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", frontmatter[index])
        if not match:
            index += 1
            continue
        key, raw = match.groups()
        if raw.strip() in {"|", ">", "|-", ">-"}:
            block: list[str] = []
            index += 1
            while index < len(frontmatter) and (
                not frontmatter[index].strip() or frontmatter[index][0].isspace()
            ):
                block.append(frontmatter[index].strip())
                index += 1
            values[key] = " ".join(part for part in block if part)
            continue
        values[key] = strip_quotes(raw)
        index += 1
    return values.get("name") or fallback, values.get("description", "")


def rule_matches(group: str, name: str, description: str) -> bool:
    normalized_name = normalize(name)
    if normalized_name in GROUP_EXCLUDES.get(group, set()):
        return False
    rule = RULES[group]
    if normalized_name in rule["names"]:
        return True
    if any(normalized_name.startswith(prefix) for prefix in rule["prefixes"]):
        return True
    haystack = f"{normalized_name}-{normalize(description)}"
    return any(contains_term(haystack, term) for term in rule["terms"])


def classify(name: str, description: str, origin: str) -> list[str]:
    normalized_name = normalize(name)
    if origin == "awesome-composio-cache":
        return ["automation-catalog"]
    if normalized_name.startswith("competition-"):
        return ["security-reverse"]

    groups = [group for group in GROUP_ORDER if rule_matches(group, name, description)]
    if (
        normalized_name not in GROUP_EXCLUDES["automation-catalog"]
        and normalized_name.endswith(AUTOMATION_SUFFIXES)
        and "automation-catalog" not in groups
    ):
        groups.append("automation-catalog")
    return groups or ["engineering"]


def score(query: str, name: str, description: str, installed: bool) -> int:
    normalized_query = normalize(query)
    normalized_name = normalize(name)
    normalized_description = normalize(description)
    tokens = query_tokens(query)
    token_set = set(tokens)
    name_parts = {
        part for part in normalized_name.split("-") if part and part not in STOPWORDS
    }
    result = 0
    if normalized_query == normalized_name:
        result += 100
    if normalized_query and normalized_name.startswith(normalized_query):
        result += 30
    if normalized_query and contains_term(normalized_name, normalized_query):
        result += 20
    if name_parts and name_parts.issubset(token_set):
        result += 35
    result += sum(12 for token in tokens if contains_term(normalized_name, token))
    result += sum(3 for token in tokens if contains_term(normalized_description, token))
    query_lower = unicodedata.normalize("NFKC", query).lower()
    for patterns, boosts in INTENT_BOOSTS:
        if any(re.search(pattern, query_lower) for pattern in patterns):
            result += boosts.get(normalized_name, 0)
    if result and installed:
        result += 6
    return result


def iter_skill_files(root: Path):
    for skill_file in root.rglob("SKILL.md"):
        relative = skill_file.relative_to(root)
        if any(
            part.lower()
            in {
                ".git",
                ".system",
                ".venv",
                "__pycache__",
                "node_modules",
                "test",
                "tests",
                "template",
                "templates",
            }
            for part in relative.parts
        ):
            continue
        yield skill_file, relative


def item_from_file(
    skill_file: Path,
    origin: str,
    installed: bool,
) -> dict[str, object]:
    text = skill_file.read_text(encoding="utf-8", errors="replace")
    name, description = parse_metadata(text, skill_file.parent.name)
    return {
        "name": name,
        "description": description,
        "groups": classify(name, description, origin),
        "path": str(skill_file.resolve()),
        "origin": origin,
        "installed": installed,
    }


def load_skills(roots: list[Path], include_sources: bool) -> list[dict[str, object]]:
    selected: dict[str, dict[str, object]] = {}
    for root_index, root in enumerate(roots):
        for skill_file, _ in iter_skill_files(root):
            item = item_from_file(skill_file, f"installed:{root_index}", True)
            key = normalize(str(item["name"]))
            if not key or key in ROUTER_NAMES or key.startswith("competition-"):
                continue
            previous = selected.get(key)
            if previous is None or len(str(item["path"])) < len(str(previous["path"])):
                selected[key] = item

    if include_sources:
        for source_root, base_origin in default_source_roots():
            for skill_file, relative in iter_skill_files(source_root):
                origin = base_origin
                if base_origin == "awesome-cache" and relative.parts[:1] == ("composio-skills",):
                    origin = "awesome-composio-cache"
                item = item_from_file(skill_file, origin, False)
                key = normalize(str(item["name"]))
                if not key or key in ROUTER_NAMES or key in selected:
                    continue
                selected[key] = item
    return list(selected.values())


def print_summary(skills: list[dict[str, object]], as_json: bool) -> None:
    group_counts = {
        group: sum(group in item["groups"] for item in skills)
        for group in GROUP_ORDER
    }
    origin_counts: dict[str, int] = {}
    for item in skills:
        origin = str(item["origin"])
        origin_counts[origin] = origin_counts.get(origin, 0) + 1
    payload = {
        "unique_skills": len(skills),
        "installed": sum(bool(item["installed"]) for item in skills),
        "cached_only": sum(not bool(item["installed"]) for item in skills),
        "groups": group_counts,
        "origins": dict(sorted(origin_counts.items())),
        "note": "Group counts overlap because one skill may serve multiple domains.",
    }
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"unique_skills={payload['unique_skills']}")
    print(f"installed={payload['installed']} cached_only={payload['cached_only']}")
    for group, count in group_counts.items():
        print(f"{group}={count}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", help="Task description or skill name")
    parser.add_argument("--group", choices=GROUP_ORDER)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--min-score", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--include-sources", action="store_true")
    parser.add_argument(
        "--auto-group",
        action="store_true",
        help="Infer one domain from bilingual task keywords before ranking.",
    )
    parser.add_argument(
        "--root",
        action="append",
        type=Path,
        dest="roots",
        help="Installed skill root. Repeat to search multiple roots.",
    )
    args = parser.parse_args()

    roots = args.roots or default_roots()
    if not roots:
        parser.error("No installed skill roots were found")
    missing = [str(root) for root in roots if not root.is_dir()]
    if missing:
        parser.error(f"Skill roots not found: {', '.join(missing)}")

    skills = load_skills(roots, args.include_sources)
    if args.summary:
        print_summary(skills, args.json)
        return 0
    if not args.query:
        parser.error("query is required unless --summary is used")

    effective_group = args.group or (infer_group(args.query) if args.auto_group else None)
    rows: list[dict[str, object]] = []
    for item in skills:
        if effective_group and effective_group not in item["groups"]:
            continue
        if effective_group:
            item["routing_group"] = effective_group
        item["score"] = score(
            args.query,
            str(item["name"]),
            str(item["description"]),
            bool(item["installed"]),
        )
        if int(item["score"]) >= args.min_score:
            rows.append(item)

    rows.sort(
        key=lambda item: (
            -int(item["score"]),
            not bool(item["installed"]),
            str(item["name"]),
        )
    )
    rows = rows[: max(1, args.limit)]
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for item in rows:
            print(
                f"{item['score']:>3}  {item['name']}"
                f"  groups={','.join(item['groups'])}"
                f"  origin={item['origin']}\n"
                f"     {item['path']}\n"
                f"     {item['description']}"
            )
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
