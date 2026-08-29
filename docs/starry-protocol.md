# starry:// 协议规范

`starry://` 是 OpenStarry Code 的私有协议，用于快速导入 API 配置、安装 Skills 和加载扩展。

## 协议格式

### 1. API 配置导入

```
starry://api/import?url={config_url}&type={provider_type}
starry://api/import?provider={provider_id}&model={model_name}&key={api_key_or_env}
```

**参数说明：**

- `url`: API 配置文件的 URL（支持 HTTP/HTTPS/file://）
- `type`: 提供商类型（openai | anthropic | openrouter | azure | gemini | ollama | custom 等）
- `provider`: 直接指定提供商 ID
- `model`: 模型名称（可选）
- `key`: API 密钥或环境变量名称（格式：`env:VAR_NAME` 或直接传入密钥）

**示例：**

```bash
# 从 URL 导入 OpenAI 配置
starry://api/import?url=https://example.com/openai-config.json&type=openai

# 直接配置 OpenRouter
starry://api/import?provider=openrouter&key=env:OPENROUTER_API_KEY

# 配置 Anthropic 并指定模型
starry://api/import?provider=anthropic&model=claude-sonnet-4-5&key=env:ANTHROPIC_API_KEY

# 配置本地 Ollama
starry://api/import?provider=ollama&model=llama3.1
```

### 2. Skill 安装

```
starry://skill/install?source={source_type}&name={skill_reference}
starry://skill/install?github={owner/repo}&ref={branch_or_tag}&subpath={path}
starry://skill/install?clawhub={skill_id}
```

**参数说明：**

- `source`: 来源类型（github | clawhub | local）
- `name`: Skill 引用名称
- `github`: GitHub 仓库（格式：`owner/repo`）
- `ref`: Git 分支或标签（可选，默认为 main）
- `subpath`: 仓库内子路径（可选）
- `clawhub`: ClawHub Skill ID
- `local`: 本地路径

**示例：**

```bash
# 从 GitHub 安装
starry://skill/install?github=openstarry/awesome-skill

# 指定分支和子路径
starry://skill/install?github=myorg/skills&ref=v1.2.0&subpath=pdf-tools

# 从 ClawHub 安装
starry://skill/install?clawhub=deep-research-pro

# 从本地路径安装
starry://skill/install?local=file:///path/to/my-skill
```

### 3. 扩展加载

```
starry://extension/load?path={extension_path}&type={extension_type}
```

**参数说明：**

- `path`: 扩展文件路径（支持本地路径或 URL）
- `type`: 扩展类型（python | java | go | native）

**支持的扩展格式：**

- Python: `.py` 文件或包含 `__init__.py` 的目录
- Java: `.jar` 文件
- Go: `.so` (Linux/macOS) 或 `.dll` (Windows)
- Native: 编译后的本地库

**示例：**

```bash
# 加载 Python 扩展
starry://extension/load?path=file:///plugins/my_extension.py&type=python

# 加载 Java 扩展
starry://extension/load?path=file:///C:/plugins/code-analyzer.jar&type=java

# 从 URL 加载
starry://extension/load?path=https://example.com/extensions/analyzer.so&type=go
```

## 配置文件格式

### API 配置 JSON 格式

```json
{
  "version": "1.0",
  "provider": "openai",
  "config": {
    "api_key_env": "OPENAI_API_KEY",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4",
    "timeout": 60,
    "max_retries": 3
  },
  "router": {
    "mode": "recommended",
    "tiers": {
      "quick": "gpt-4-mini",
      "normal": "gpt-4",
      "advanced": "gpt-4-turbo"
    }
  }
}
```

### API 配置 TOML 格式

```toml
[llm]
provider = "openrouter"
model = "anthropic/claude-3.5-sonnet"
api_key_env = "OPENROUTER_API_KEY"
base_url = "https://openrouter.ai/api/v1"
timeout = 120

[router]
mode = "recommended"

[router.tier_models]
quick = "anthropic/claude-3-haiku"
normal = "anthropic/claude-3.5-sonnet"
advanced = "anthropic/claude-3-opus"
```

## 协议处理器实现

### CLI 使用

```bash
# 查看协议信息
openstarry-code protocol info

# 使用 openstarry-code CLI 处理协议
openstarry-code protocol handle "starry://api/import?provider=openrouter&key=env:OPENROUTER_API_KEY"

# 批量处理多个协议 URL
openstarry-code protocol batch urls.txt

# 验证协议 URL（不执行）
openstarry-code protocol validate "starry://skill/install?github=org/repo"

# 使用自定义配置文件
openstarry-code protocol handle "starry://api/import?provider=openai&key=env:OPENAI_API_KEY" --config ~/.config/openstarry/custom.toml

# JSON 输出格式
openstarry-code protocol handle "starry://api/import?provider=openai&key=env:OPENAI_API_KEY" --json
```

**可用命令：**

- `protocol info` - 显示协议信息和支持的操作
- `protocol handle <url>` - 处理单个协议 URL
- `protocol batch <file>` - 批量处理文件中的协议 URL（每行一个）
- `protocol validate <url>` - 验证协议 URL 格式（不执行）

### Python API

```python
from openstarry_code.protocol import StarryProtocolHandler

# 创建处理器
handler = StarryProtocolHandler()

# 处理协议 URL
result = await handler.handle("starry://api/import?provider=openrouter&key=env:OPENROUTER_API_KEY")

if result.success:
    print(f"✅ {result.message}")
else:
    print(f"❌ {result.error}")

# 批量处理
urls = [
    "starry://api/import?provider=openai&key=env:OPENAI_API_KEY",
    "starry://skill/install?github=openstarry/deep-research",
]

results = await handler.handle_batch(urls)
```

### Web UI 集成

在 Web UI 的设置面板中，可以直接粘贴 starry:// URL：

1. 打开设置 → API 配置
2. 点击"从 URL 导入"
3. 粘贴 `starry://api/import?...`
4. 点击"导入"按钮

## 安全注意事项

1. **API 密钥安全**：
   - 优先使用 `env:` 前缀引用环境变量
   - 避免在 URL 中直接包含密钥明文
   - 配置文件中使用 `api_key_env` 而非 `api_key`

2. **来源验证**：
   - 从 GitHub 安装时会验证仓库签名
   - ClawHub 安装会进行安全扫描
   - 本地扩展需要手动确认

3. **权限控制**：
   - 安装 Skill 时会显示所需权限
   - 扩展加载需要管理员确认
   - 可以在配置中设置白名单

## 与 IDE 插件系统对比

| 特性 | VS Code | JetBrains IDEA | OpenStarry Code |
|------|---------|----------------|-----------------|
| 安装来源 | Marketplace | Plugin Repository | GitHub + ClawHub |
| 配置导入 | JSON | XML/Properties | TOML + JSON + starry:// |
| 扩展语言 | TypeScript/JS | Java/Kotlin | Python/Java/Go |
| 动态加载 | ✅ | ✅ | ✅ |
| 沙箱隔离 | ✅ | ✅ | ✅ (Sandbox) |
| 协议支持 | vscode:// | ❌ | starry:// |

## 常见问题

### Q: starry:// 协议与普通 CLI 命令有什么区别？

A: starry:// 协议是一种快速配置的方式，适合：
- 分享配置链接
- 一键安装脚本
- Web UI 集成
- 自动化部署

等价关系：
```bash
# 协议方式
starry://api/import?provider=openai&key=env:OPENAI_API_KEY

# CLI 命令方式
openstarry-code configure provider --provider openai --api-key-env OPENAI_API_KEY
```

### Q: 如何自定义协议处理行为？

A: 可以通过配置文件设置：

```toml
[protocol]
# 是否自动确认安装
auto_confirm_install = false

# 允许的来源
allowed_sources = ["github", "clawhub"]

# 禁止的域名（用于 URL 导入）
blocked_domains = ["untrusted.com"]

# 扩展加载需要管理员权限
extension_require_admin = true
```

### Q: 能否创建自定义协议处理器？

A: 可以，参考 `src/openstarry_code/protocol/handlers.py` 创建自定义处理器：

```python
from openstarry_code.protocol.base import ProtocolHandler

class MyCustomHandler(ProtocolHandler):
    def can_handle(self, url: str) -> bool:
        return url.startswith("starry://custom/")
    
    async def handle(self, url: str) -> ProtocolResult:
        # 自定义处理逻辑
        pass

# 注册处理器
register_protocol_handler(MyCustomHandler())
```

## 快速开始

### 1. 配置第一个 API Provider

```bash
# 配置 OpenRouter（推荐，支持多个模型）
openstarry-code protocol handle "starry://api/import?provider=openrouter&key=env:OPENROUTER_API_KEY"

# 配置 Anthropic Claude
openstarry-code protocol handle "starry://api/import?provider=anthropic&model=claude-sonnet-4-5&key=env:ANTHROPIC_API_KEY"

# 配置本地 Ollama（无需 API key）
openstarry-code protocol handle "starry://api/import?provider=ollama&model=llama3.1"
```

### 2. 安装 Skills

```bash
# 查看可用的 Skills
openstarry-code skills search

# 从 GitHub 安装 Skill
openstarry-code protocol handle "starry://skill/install?github=openstarry/deep-research"
```

### 3. 批量配置

创建 `setup.txt`：
```
starry://api/import?provider=openrouter&key=env:OPENROUTER_API_KEY
starry://skill/install?github=openstarry/deep-research
```

执行批量配置：
```bash
openstarry-code protocol batch setup.txt
```

## 示例文件

项目提供了示例文件供参考：

- `examples/api-config-example.json` - JSON 格式的 API 配置示例
- `examples/api-config-example.toml` - TOML 格式的 API 配置示例
- `examples/protocol-examples.txt` - 完整的协议 URL 示例集合

## 参考资料

- [Configuration Guide](configuration.md)
- [Skills Documentation](features/skills.md)
- [Provider Configuration](providers-and-models.md)
- [CLI Reference](cli.md)

---

[Docs index](README.md) · [Product guide](../README.product.md) · [Report an issue](https://github.com/tomysh1337/openstarry/issues)
