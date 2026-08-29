# 插件开发指南

本文档介绍如何为 OpenStarry Code 开发自定义插件，包括 Skills、扩展（Extensions）以及如何使用 starry:// 协议进行分发。

## 目录

- [插件类型概述](#插件类型概述)
- [开发 Skill 插件](#开发-skill-插件)
- [开发扩展（Extensions）](#开发扩展extensions)
- [使用 starry:// 协议分发](#使用-starry-协议分发)
- [最佳实践](#最佳实践)
- [发布与分享](#发布与分享)

---

## 插件类型概述

OpenStarry Code 支持三种主要的插件类型：

| 类型 | 描述 | 语言 | 分发方式 |
|------|------|------|----------|
| **Skill** | 任务特定的指令包和脚本 | Markdown + YAML | GitHub / ClawHub / Local |
| **Meta-Skill** | 多步骤工作流协议 | Markdown + YAML | GitHub / ClawHub / Local |
| **Extension** | 原生代码扩展 | Python / Java / Go | starry:// 协议 |

### 插件架构层级

Skills 遵循六层优先级架构（从低到高）：

1. **Extra**: 配置文件指定的额外目录
2. **Bundled**: 随 OpenStarry Code 发布的内置技能
3. **Managed**: 本地安装目录 (`~/.openstarry-code/skills/`)
4. **Personal**: 用户个人目录 (`~/.agents/skills/`)
5. **Project**: 项目级目录 (`{workspace}/.agents/skills/`)
6. **Workspace**: 工作区目录 (`{workspace}/skills/`)

---

## 开发 Skill 插件

### 1. Skill 基本结构

每个 Skill 是一个包含 `SKILL.md` 文件的目录：

```
my-awesome-skill/
├── SKILL.md          # 必需：Skill 定义文件
├── README.md         # 可选：使用说明
├── scripts/          # 可选：辅助脚本
│   └── helper.py
└── resources/        # 可选：资源文件
    └── templates/
```

### 2. SKILL.md 格式

#### 基础 Skill 示例

```yaml
---
name: my-awesome-skill
description: "A clear one-sentence description of what this skill does"
description_zh: "该技能功能的中文描述"
triggers:
  - "keyword or phrase that activates this skill"
  - "another trigger phrase"
homepage: https://github.com/yourname/my-awesome-skill
provenance:
  origin: community
  license: MIT
  upstream_url: https://github.com/yourname/my-awesome-skill
  maintained_by: Your Name
requires:
  - python>=3.10
  - pip:pandas
metadata:
  risk: low
  capabilities:
    - filesystem-read
---

# My Awesome Skill

## Purpose

Explain what this skill does and when to use it.

## Instructions

Detailed instructions for the AI agent on how to use this skill.

### Step 1: Understand the Request

Guidelines for interpreting user input...

### Step 2: Execute the Task

Specific implementation steps...

### Step 3: Deliver the Result

How to format and present the output...

## Examples

### Example 1: Basic Usage

User request: "Do something awesome"

Expected behavior:
1. Analyze the request
2. Execute the task
3. Return the result

## Constraints

- Do not perform action X
- Always validate input Y
- Respect user preferences for Z

## Error Handling

How to handle common error scenarios...
```

#### Meta-Skill 示例

```yaml
---
name: research-report-workflow
kind: meta
description: "Automated research report generation with citation management"
triggers:
  - "research report"
  - "academic paper"
meta_priority: 50
provenance:
  origin: bundled
  license: MIT
metadata:
  risk: medium
  capabilities:
    - filesystem-write
    - network-read
    - artifact-write
composition:
  inputs:
    topic:
      type: string
      required: true
    depth:
      type: string
      default: "comprehensive"
  
  steps:
    - id: research
      kind: agent
      skill: deep-research
      with:
        query: "{{ inputs.topic }}"
        depth: "{{ inputs.depth }}"
    
    - id: analyze
      kind: llm_chat
      depends_on: [research]
      with:
        system: "Analyze the research findings and extract key points"
        task: "{{ outputs.research.content }}"
    
    - id: draft
      kind: agent
      skill: document-writer
      depends_on: [analyze]
      with:
        content: "{{ outputs.analyze.result }}"
        format: "markdown"
    
    - id: export
      kind: agent
      skill: pdf-export
      depends_on: [draft]
      with:
        source: "{{ outputs.draft.document }}"
  
  output: "{{ outputs.export.file_path }}"
---

# Research Report Workflow

This Meta-Skill automates the process of creating research reports...

[详细说明...]
```

### 3. Skill 开发工作流

#### 创建新 Skill

```bash
# 1. 创建 Skill 目录
mkdir -p ~/.openstarry-code/skills/my-awesome-skill
cd ~/.openstarry-code/skills/my-awesome-skill

# 2. 创建 SKILL.md
cat > SKILL.md << 'EOF'
---
name: my-awesome-skill
description: "Your skill description"
---

# My Awesome Skill

[Your skill content...]
EOF

# 3. 测试 Skill
openstarry-code skills list
openstarry-code skills view my-awesome-skill
openstarry-code skills doctor my-awesome-skill
```

#### 验证 Skill

```bash
# 检查 Skill 是否被正确识别
openstarry-code skills doctor my-awesome-skill --json

# 查看 Skill 内容
openstarry-code skills view my-awesome-skill

# 测试 Skill 触发
# 在聊天中使用相关触发词，观察是否正确激活
```

### 4. Skill 最佳实践

#### ✅ 应该做的：

- **清晰的描述**：一句话说明 Skill 的用途
- **具体的触发词**：使用用户自然会说的短语
- **详细的指令**：为 AI 提供清晰的执行步骤
- **错误处理**：说明如何处理常见错误
- **示例**：提供具体的使用案例
- **约束条件**：明确说明不应该做什么
- **依赖声明**：在 `requires` 中声明所有依赖

#### ❌ 不应该做的：

- 不要在 `description` 中使用多句话
- 不要使用过于宽泛的触发词（如 "help", "do"）
- 不要在指令中使用模糊的语言
- 不要忘记声明风险级别和所需权限
- 不要在 Skill 中硬编码路径或凭据

---

## 开发扩展（Extensions）

扩展是用 Python、Java 或 Go 编写的原生代码模块，可以扩展 OpenStarry Code 的核心功能。

### 1. Python 扩展

#### 扩展结构

```python
# my_extension.py
"""
OpenStarry Code Python Extension
"""

from typing import Dict, Any

class MyExtension:
    """扩展主类"""
    
    def __init__(self):
        self.name = "my-extension"
        self.version = "1.0.0"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        初始化扩展
        
        Args:
            config: 配置字典
        
        Returns:
            初始化成功返回 True
        """
        print(f"Initializing {self.name} v{self.version}")
        return True
    
    def execute(self, command: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行扩展命令
        
        Args:
            command: 命令名称
            args: 命令参数
        
        Returns:
            执行结果字典
        """
        if command == "analyze":
            return self.analyze(args)
        elif command == "transform":
            return self.transform(args)
        else:
            return {"error": f"Unknown command: {command}"}
    
    def analyze(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """分析功能实现"""
        data = args.get("data", "")
        result = {
            "status": "success",
            "length": len(data),
            "analysis": "Sample analysis result"
        }
        return result
    
    def transform(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """转换功能实现"""
        data = args.get("data", "")
        transformed = data.upper()  # 示例转换
        return {
            "status": "success",
            "result": transformed
        }
    
    def cleanup(self) -> None:
        """清理资源"""
        print(f"Cleaning up {self.name}")


# 扩展入口点
def get_extension():
    """返回扩展实例"""
    return MyExtension()


# 元数据
EXTENSION_METADATA = {
    "name": "my-extension",
    "version": "1.0.0",
    "description": "A sample Python extension for OpenStarry Code",
    "author": "Your Name",
    "license": "MIT",
    "requires": {
        "python": ">=3.10",
        "packages": []
    }
}
```

#### 安装 Python 扩展

```bash
# 方式 1: 从本地文件安装
starry://extension/load?path=file:///path/to/my_extension.py&type=python

# 方式 2: 从 URL 安装
starry://extension/load?path=https://example.com/extensions/my_extension.py&type=python

# 方式 3: 使用 CLI
openstarry-code protocol handle "starry://extension/load?path=file:///path/to/my_extension.py&type=python"
```

### 2. Java 扩展

#### 扩展接口

```java
// OpenStarryExtension.java
package com.openstarry.extensions;

import java.util.Map;

/**
 * OpenStarry Code Java 扩展接口
 */
public interface OpenStarryExtension {
    
    /**
     * 获取扩展名称
     */
    String getName();
    
    /**
     * 获取扩展版本
     */
    String getVersion();
    
    /**
     * 初始化扩展
     * 
     * @param config 配置参数
     * @return 初始化成功返回 true
     */
    boolean initialize(Map<String, Object> config);
    
    /**
     * 执行扩展命令
     * 
     * @param command 命令名称
     * @param args 命令参数
     * @return 执行结果
     */
    Map<String, Object> execute(String command, Map<String, Object> args);
    
    /**
     * 清理资源
     */
    void cleanup();
}
```

#### 实现示例

```java
// MyExtension.java
package com.example.openstarry;

import com.openstarry.extensions.OpenStarryExtension;
import java.util.HashMap;
import java.util.Map;

public class MyExtension implements OpenStarryExtension {
    
    private static final String NAME = "my-java-extension";
    private static final String VERSION = "1.0.0";
    
    @Override
    public String getName() {
        return NAME;
    }
    
    @Override
    public String getVersion() {
        return VERSION;
    }
    
    @Override
    public boolean initialize(Map<String, Object> config) {
        System.out.println("Initializing " + NAME + " v" + VERSION);
        // 初始化逻辑
        return true;
    }
    
    @Override
    public Map<String, Object> execute(String command, Map<String, Object> args) {
        Map<String, Object> result = new HashMap<>();
        
        switch (command) {
            case "analyze":
                return analyze(args);
            case "process":
                return process(args);
            default:
                result.put("error", "Unknown command: " + command);
                return result;
        }
    }
    
    private Map<String, Object> analyze(Map<String, Object> args) {
        Map<String, Object> result = new HashMap<>();
        result.put("status", "success");
        result.put("message", "Analysis completed");
        return result;
    }
    
    private Map<String, Object> process(Map<String, Object> args) {
        Map<String, Object> result = new HashMap<>();
        String data = (String) args.get("data");
        result.put("status", "success");
        result.put("result", data.toUpperCase());
        return result;
    }
    
    @Override
    public void cleanup() {
        System.out.println("Cleaning up " + NAME);
    }
}
```

#### 构建和安装

```bash
# 1. 编译为 JAR
mvn clean package

# 2. 安装扩展
starry://extension/load?path=file:///path/to/my-extension.jar&type=java

# 3. 或使用 CLI
openstarry-code protocol handle "starry://extension/load?path=file:///C:/plugins/my-extension.jar&type=java"
```

### 3. Go 扩展

#### 扩展接口

```go
// extension.go
package main

import "C"
import (
	"encoding/json"
	"fmt"
)

// Extension 扩展主结构
type Extension struct {
	Name    string
	Version string
}

// Initialize 初始化扩展
//export Initialize
func Initialize(configJSON *C.char) C.int {
	config := C.GoString(configJSON)
	fmt.Printf("Initializing extension with config: %s\n", config)
	return 1 // 成功返回 1
}

// Execute 执行命令
//export Execute
func Execute(command *C.char, argsJSON *C.char) *C.char {
	cmd := C.GoString(command)
	args := C.GoString(argsJSON)
	
	var argsMap map[string]interface{}
	json.Unmarshal([]byte(args), &argsMap)
	
	var result map[string]interface{}
	
	switch cmd {
	case "analyze":
		result = analyze(argsMap)
	case "transform":
		result = transform(argsMap)
	default:
		result = map[string]interface{}{
			"error": fmt.Sprintf("Unknown command: %s", cmd),
		}
	}
	
	resultJSON, _ := json.Marshal(result)
	return C.CString(string(resultJSON))
}

// Cleanup 清理资源
//export Cleanup
func Cleanup() {
	fmt.Println("Cleaning up extension")
}

func analyze(args map[string]interface{}) map[string]interface{} {
	data, _ := args["data"].(string)
	return map[string]interface{}{
		"status": "success",
		"length": len(data),
	}
}

func transform(args map[string]interface) map[string]interface{} {
	data, _ := args["data"].(string)
	return map[string]interface{}{
		"status": "success",
		"result": data,
	}
}

// GetMetadata 获取元数据
//export GetMetadata
func GetMetadata() *C.char {
	metadata := map[string]interface{}{
		"name":        "my-go-extension",
		"version":     "1.0.0",
		"description": "A sample Go extension for OpenStarry Code",
		"author":      "Your Name",
		"license":     "MIT",
	}
	metadataJSON, _ := json.Marshal(metadata)
	return C.CString(string(metadataJSON))
}

func main() {}
```

#### 构建和安装

```bash
# 1. 构建共享库
# Linux/macOS
go build -buildmode=c-shared -o my_extension.so extension.go

# Windows
go build -buildmode=c-shared -o my_extension.dll extension.go

# 2. 安装扩展
starry://extension/load?path=file:///path/to/my_extension.so&type=go

# 3. 或使用 CLI
openstarry-code protocol handle "starry://extension/load?path=file:///usr/local/lib/my_extension.so&type=go"
```

---

## 使用 starry:// 协议分发

### 1. 创建插件分发包

#### Skill 分发

**GitHub 仓库结构：**

```
my-awesome-skill/
├── SKILL.md          # Skill 定义
├── README.md         # 文档
├── LICENSE           # 许可证
├── .gitignore
└── examples/         # 示例
    └── demo.md
```

**分发 URL：**

```bash
# 从 GitHub 安装（默认 main 分支）
starry://skill/install?github=yourname/my-awesome-skill

# 指定版本标签
starry://skill/install?github=yourname/my-awesome-skill&ref=v1.0.0

# 指定子路径
starry://skill/install?github=yourorg/skills-repo&ref=main&subpath=my-awesome-skill
```

#### 扩展分发

**创建扩展发布：**

```bash
# 1. 构建扩展
python setup.py bdist_wheel  # Python
mvn package                   # Java
go build -buildmode=c-shared  # Go

# 2. 上传到服务器或 GitHub Releases

# 3. 创建分发 URL
starry://extension/load?path=https://github.com/yourname/my-extension/releases/download/v1.0.0/my_extension.so&type=go
```

### 2. 创建一键安装脚本

**setup.txt 示例：**

```
# OpenStarry Code 插件包安装脚本
# 使用方式: openstarry-code protocol batch setup.txt

# API 配置
starry://api/import?provider=openrouter&key=env:OPENROUTER_API_KEY

# 安装 Skills
starry://skill/install?github=yourname/awesome-skill
starry://skill/install?github=yourname/another-skill&ref=v2.0.0

# 加载扩展
starry://extension/load?path=https://example.com/extensions/analyzer.so&type=go
starry://extension/load?path=file:///opt/plugins/custom.jar&type=java
```

**执行安装：**

```bash
# 批量安装
openstarry-code protocol batch setup.txt

# JSON 输出格式
openstarry-code protocol batch setup.txt --json
```

### 3. 创建插件市场链接

**在网页或文档中使用：**

```html
<!-- 一键安装按钮 -->
<a href="starry://skill/install?github=yourname/my-awesome-skill">
  📦 一键安装 My Awesome Skill
</a>

<!-- 配置导入 -->
<a href="starry://api/import?provider=openrouter&key=env:OPENROUTER_API_KEY">
  ⚙️ 配置 OpenRouter
</a>
```

---

## 最佳实践

### 1. 安全性

#### ✅ 推荐做法

```yaml
# 使用环境变量存储密钥
starry://api/import?provider=openai&key=env:OPENAI_API_KEY

# 在 SKILL.md 中声明风险
metadata:
  risk: medium
  capabilities:
    - filesystem-write
    - network-read

# 验证用户输入
requires:
  - python>=3.10
  - pip:requests>=2.28.0
```

#### ❌ 避免的做法

```yaml
# ❌ 不要在 URL 中硬编码密钥
starry://api/import?provider=openai&key=sk-abc123...

# ❌ 不要省略风险声明
# 缺少 metadata.risk 和 capabilities

# ❌ 不要忽略依赖版本
requires:
  - python  # 应该指定版本
```

### 2. 文档

#### 必需的文档

- **README.md**: 插件概述、安装说明、使用示例
- **SKILL.md**: 完整的 AI 指令和元数据
- **LICENSE**: 开源许可证
- **CHANGELOG.md**: 版本更新记录

#### README.md 模板

```markdown
# My Awesome Skill

简短描述您的 Skill 功能。

## 功能特性

- 特性 1
- 特性 2
- 特性 3

## 安装

### 使用 starry:// 协议（推荐）

```bash
starry://skill/install?github=yourname/my-awesome-skill
```

### 使用 CLI

```bash
openstarry-code skills install yourname/my-awesome-skill --source github
```

## 使用方法

### 基础用法

```
[使用示例]
```

### 高级用法

```
[高级示例]
```

## 配置

如果需要配置，说明配置方法。

## 依赖

- Python >= 3.10
- pandas >= 2.0.0

## 许可证

MIT License
```

### 3. 版本管理

#### 语义化版本

```
v<major>.<minor>.<patch>

v1.0.0 - 初始发布
v1.1.0 - 新增功能
v1.1.1 - 修复 bug
v2.0.0 - 破坏性更新
```

#### Git 标签

```bash
# 创建版本标签
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# 用户可以安装特定版本
starry://skill/install?github=yourname/my-skill&ref=v1.0.0
```

### 4. 测试

#### Skill 测试清单

- [ ] `openstarry-code skills list` 能够列出该 Skill
- [ ] `openstarry-code skills view <name>` 能够查看内容
- [ ] `openstarry-code skills doctor <name>` 通过所有检查
- [ ] 触发词能够正确激活 Skill
- [ ] 所有示例场景都能正常工作
- [ ] 错误处理能够正确响应

#### 扩展测试清单

- [ ] 扩展能够成功加载
- [ ] `initialize()` 方法正常执行
- [ ] 所有命令能够正确响应
- [ ] 错误情况能够正确处理
- [ ] `cleanup()` 方法正常执行
- [ ] 无内存泄漏

---

## 发布与分享

### 1. 发布到 GitHub

```bash
# 1. 创建仓库
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourname/my-awesome-skill.git
git push -u origin main

# 2. 创建 Release
git tag -a v1.0.0 -m "Version 1.0.0"
git push origin v1.0.0

# 3. 在 GitHub 上创建 Release，上传构建产物
```

### 2. 发布到 ClawHub

```bash
# 发布到 ClawHub（如果支持）
openstarry-code skills publish /path/to/my-awesome-skill
```

### 3. 分享安装链接

**创建安装文档：**

```markdown
# 安装 My Awesome Skill

## 方式 1: 一键安装（推荐）

点击下方链接或复制到浏览器：

```
starry://skill/install?github=yourname/my-awesome-skill
```

## 方式 2: CLI 安装

```bash
openstarry-code skills install yourname/my-awesome-skill --source github
```

## 方式 3: 批量安装

创建 `setup.txt`:

```
starry://skill/install?github=yourname/my-awesome-skill
```

执行:

```bash
openstarry-code protocol batch setup.txt
```
```

### 4. 社区推广

- 在 GitHub 上添加主题标签: `openstarry-code`, `openstarry-skill`
- 在 README 中添加徽章
- 在社区论坛分享
- 创建使用教程视频或博客

---

## 参考资料

### 官方文档

- [Skills 文档](features/skills.md) - Skills 系统概述
- [Meta-Skills 文档](features/meta-skills.md) - Meta-Skills 概述
- [Meta-Skill 开发指南](authoring/meta-skills.md) - 详细开发规范
- [starry:// 协议规范](starry-protocol.md) - 协议完整文档
- [配置指南](configuration.md) - 配置文件格式

### 示例代码

- `examples/api-config-example.json` - API 配置示例
- `examples/protocol-examples.txt` - 协议 URL 示例
- `src/openstarry_code/skills/bundled/` - 内置 Skills 源代码

### 社区资源

- GitHub 仓库: https://github.com/tomysh1337/openstarry
- 问题追踪: https://github.com/tomysh1337/openstarry/issues
- 讨论区: https://github.com/tomysh1337/openstarry/discussions

---

[文档索引](README.md) · [产品指南](../README.product.md) · [报告问题](https://github.com/tomysh1337/openstarry/issues)
