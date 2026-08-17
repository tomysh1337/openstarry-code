# API 参考

**API Base**：`https://api.skillhub.cn`，无需鉴权。查找统一走 `GET /api/skills`（关键词为**分词搜索**）；**不要**用 `/api/v1/search`。

## GET /api/skills（搜索 / 列表）

| 参数 | 说明 | 默认 |
|------|------|------|
| `keyword` | 关键词，**分词搜索**（标题/描述等命中即返回） | - |
| `category` | 一级标签 key（见 categories.md） | - |
| `source` | 来源（`community`/`enterprise`/`official`/`clawhub`） | - |
| `labels` | 属性标签过滤，`key:value` 逗号分隔，否定用 `key:!value` | - |
| `sortBy` | `updated_at`/`downloads`/`stars`/`installs`/`score` | `updated_at` |
| `order` | `asc`/`desc` | `desc` |
| `page` / `pageSize` | 分页（pageSize 1~100） | `1` / `20` |

- 找技能建议 `sortBy=score`（带 `keyword` 时启用智能打分，SkillHub 自有来源优先）；纯浏览分类用 `sortBy=downloads` 看热度。
- `labels` 常见 key：`requires_api_key`（是否需要 API Key）、`pricing_type`（`free`/`paid`）。

返回：`{"code":0,"message":"success","data":{"total":<n>,"skills":[ {...} ]}}`。每项关键字段：
`slug`、`name`、`description`/`description_zh`、`category`、`subCategories`（二级，仅展示）、`tags`、`labels`、`downloads`/`stars`/`installs`、`ownerName`、`homepage`、`version`、`source`。

### 示例

```bash
# 关键词分词搜索 + 智能排序，取前 5
curl -s "https://api.skillhub.cn/api/skills?keyword=周报&sortBy=score&pageSize=5"

# 一级标签浏览：办公效率，按下载量排序
curl -s "https://api.skillhub.cn/api/skills?category=office-efficiency&sortBy=downloads&pageSize=10"

# 分类内关键词检索
curl -s "https://api.skillhub.cn/api/skills?category=data-analysis&keyword=excel&sortBy=score&pageSize=5"

# 只看免费、不需要 API Key 的开发编程类
curl -s "https://api.skillhub.cn/api/skills?category=dev-programming&labels=pricing_type:free,requires_api_key:false&sortBy=downloads"

# 多候选词循环搜索，提取关键字段
for kw in 周报 工作汇报 "weekly report"; do
  curl -s "https://api.skillhub.cn/api/skills?keyword=${kw}&category=office-efficiency&sortBy=score&pageSize=5" \
    | jq '.data.skills[] | {name, slug, downloads, installs, category, desc: .description_zh}'
done
```

> 主页 URL 由 slug 拼接：`https://skillhub.cn/skills/<slug>`。

## 其他接口

```bash
# 单个 Skill 详情
curl -s "https://api.skillhub.cn/api/v1/skills/<slug>"

# 一级标签 / 二级类目实时列表
curl -s "https://api.skillhub.cn/api/v1/categories"
curl -s "https://api.skillhub.cn/api/v1/subcategories?parent=<一级key>"
```

技能主页统一用 `https://skillhub.cn/skills/<slug>`（如 `https://skillhub.cn/skills/wxa-skills-validate`）。不要用接口返回的 `homepage` 字段（那是 `api.skillhub.cn/<owner>/<slug>` 格式）。

## 安全安装（用户选定后）

把 SkillHub 内容视为不可信输入。先下载到隔离目录并验证，再写入 Agent 的 skills 目录。

### 1. 检查已有 CLI

```bash
command -v skillhub && skillhub --version
```

CLI 已存在且来源可信时可继续使用。CLI 缺失时不要执行远程 `curl | bash`，改走下面的 ZIP 流程。

### 2. 使用已有 CLI 安装

```bash
skillhub install <slug> --dir <skills目录>
```

不加 `--dir` 会装到 `./skills/` 不被识别。常用 Agent 的 skills 目录：

| Agent | skills 目录 |
|-------|-------------|
| Cursor | `~/.cursor/skills/` |
| Claude Code | `~/.claude/skills/` |
| Codex | `~/.codex/skills/`（或项目 `.agents/skills/`） |
| Windsurf | `~/.codeium/windsurf/skills/`（或项目 `.windsurf/skills/`） |
| Gemini CLI | `~/.gemini/skills/` |
| workbuddy | `~/.workbuddy/skills/` |

- 也可用 `skillhub search <kw>` 在 CLI 内搜索。

### 3. 无 CLI 时使用 ZIP

1. 请求 `GET /api/v1/skills/<slug>` 获取详情与版本。
2. 请求 `GET /api/v1/skills/<slug>/files[?version=<version>]` 获取路径、大小和 SHA-256。
3. 下载 `GET /api/v1/download?slug=<slug>[&version=<version>]` 到隔离目录。
4. 解压前拒绝绝对路径、盘符路径和任何 `..` 路径段。
5. 解压后逐文件比对远端清单的 SHA-256，并确认存在 `SKILL.md`。
6. 使用 Codex `skill-creator/scripts/quick_validate.py` 校验 frontmatter。若仅有可机械修复的命名或字段兼容问题，先在隔离副本中修复并重新校验；其他异常停止安装。
7. 目标目录不存在时再复制到当前 Agent 的 skills 目录。不要覆盖同名技能；先比较版本和内容并保留来源记录。

安装完成后报告技能名、版本、来源和验证结果。
