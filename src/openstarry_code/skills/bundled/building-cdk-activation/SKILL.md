---
name: building-cdk-activation
description: Use when building, adapting, reviewing, or testing CDK/license-key activation and signed online updates in Windows desktop applications, especially Qt/QML, WPF/WinUI, or Electron projects.
---

# Windows CDK Activation and Update Engineering

## Overview

Build or audit a complete activation and update path without mixing UI, trust decisions, and installer execution. Treat runtime evidence and executable tests as the acceptance source of truth.

## ACTION REQUIRED（读完后立刻执行）

1. `NOW`: Read `../field-journal/precedent-reverse.md` and confirm the target is user-provided software development or authorized analysis.
2. `NOW`: Run `scripts/inspect-activation.ps1 -Path <target>` to identify the stack and current activation/update surface.
3. `NEXT`: Read `references/license-contract.md`, then the matching section of `references/windows-ui-adapters.md`.
4. `NEXT`: If online updates are in scope, read `references/signed-update-contract.md`.
5. `ACT`: Implement from the first failing behavior test; finish with `references/verification-matrix.md`.

## 语言行为契约

- 内部推理、工具选择和阶段控制使用 English。
- 用户可见消息、报告和下一步菜单默认使用中文，除非用户要求其他语言。
- 双语标签使用“中文 / English”格式。

## 适用范围

- Windows Qt/QML、WPF/WinUI 或 Electron 应用的激活页与授权状态适配。
- Ed25519 离线 CDK 验签、试用/永久许可、缓存重验和时钟回拨处理。
- HTTPS 静态更新清单、完整安装包、自动检查和用户确认安装。
- 已有激活/更新实现的功能、安全和升级路径审计。

不用于破解第三方授权、生成未授权密钥、增量更新、静默强制安装、设备指纹、在线撤销或重型 DRM。

## 工具依赖

| 工具 | 必需 | 用途 | 缺失处理 |
|---|---:|---|---|
| PowerShell 7 或 Windows PowerShell 5.1 | 是 | 勘察、清单验证、安装 Skill | Windows 内置；不可用时停止并报告 |
| 目标项目原生测试工具 | 是 | 运行真实行为测试 | 先读 `../tool-index.md`；已登记能力缺失时调用 bootstrap |
| Python/.NET/Node | 按技术栈 | 构建和测试目标应用 | 不猜路径，不在本 Skill 注册新工具 |

本 Skill 没有独立第三方工具，因此不修改 bootstrap manifest。目标项目工具缺失时，唯一动作是使用项目已有 bootstrap；bootstrap 失败后立即给出手动配置步骤。

## 不可变安全边界

- CDK 签发私钥、更新签名私钥 `MUST NOT` 进入客户端、源码、日志、测试夹具或公开服务器目录。
- CDK 与更新 `MUST` 使用不同密钥。
- UI/Renderer `MUST NOT` 决定验签结果、写激活缓存或启动安装程序。
- 更新 `MUST` 独立于授权状态；未激活、过期或缓存损坏时仍可更新。
- 安装前 `MUST` 验证最终 HTTPS 域名、产品/渠道/版本、Ed25519、大小、SHA-256 和 Authenticode 发布者。
- 所有失败 `MUST` 保持当前可运行版本，不得留下被信任的部分下载文件。

## 工作流

### 1. 勘察与建模

1. 运行勘察脚本并核对其证据路径；静态命中不是最终结论。
2. 确认 UI 入口、授权服务、缓存、更新服务、安装技术和进程边界。
3. 建立两个正交状态机：
   - Activation: `idle`, `validating`, `active`, `invalid`, `expired`, `clock_rollback`, `storage_error`。
   - Update: `idle`, `checking`, `up_to_date`, `available`, `downloading`, `ready`, `installing`, `cancelled`, `failed`。
4. 先写失败测试，证明缺失行为或现有缺陷。

### 2. CDK 核心与界面

1. 按 `references/license-contract.md` 实现规范化载荷和 Ed25519 公钥验签。
2. 将验证和缓存放在服务层；UI 只提交 CDK、展示状态和触发导航。
3. 每次读取缓存时重新验签；试用期以首次激活时间为准，持久化最后可信时间。
4. UI 必须覆盖验证中禁用、就地错误、成功、过期、回拨、存储失败和重试。
5. 按 `references/windows-ui-adapters.md` 落到目标技术栈。

### 3. 签名在线更新

1. 后台异步检查 `stable` 渠道，不阻塞激活和主界面。
2. 按 `references/signed-update-contract.md` 验证静态清单与完整安装包。
3. 下载到应用数据目录下的随机临时文件；支持进度、取消、断网清理和重试。
4. 仅在所有校验通过后进入 `ready`；用户确认后由受信任后台层启动安装程序并退出当前进程。
5. 更新失败回到可操作状态，保留当前版本并输出可复现证据。

### 4. 验证与报告

1. 执行 `references/verification-matrix.md` 中适用的全部案例。
2. 运行目标项目完整测试和构建；不要用源码字符串断言替代状态流测试。
3. 对每个结论记录命令、输入、输出、证据路径和置信度。
4. 若用户要求实现，未通过安全与失败恢复测试不得宣称完成。

## 建议下一步（每个阶段结束时提供）

1. 继续实现当前阶段的下一条失败测试。
2. 用另一技术栈适配规则交叉检查边界。
3. 运行完整验证矩阵并修复失败项。
4. 导出阶段性实施或审计报告。
5. 暂停，先确认当前证据和产品决策。

## 脚本速查

```powershell
# 只读勘察
./scripts/inspect-activation.ps1 -Path C:\src\app -Format markdown

# 校验本地或 HTTPS 更新清单；提供 -Package 时同时校验安装包
./scripts/validate-update-manifest.ps1 -Manifest C:\release\manifest.json `
  -PublicKey C:\keys\update-public.pem -ExpectedProduct example-product `
  -CurrentVersion 1.0.0 -Package C:\release\setup.exe `
  -ExpectedPublisher 'CN=Example Software Ltd, O=Example Software Ltd, C=CN'

# 从项目源码安装到个人 Codex Skills
./scripts/install-personal.ps1 -Force
```

## 任务完成自检（声称完成前 MUST 通过）

- [ ] 已执行勘察并人工核对关键证据。
- [ ] 已确认私钥不在客户端或公开产物中，CDK/更新密钥相互独立。
- [ ] 已验证两个状态机及授权与更新解耦。
- [ ] 已验证重定向域、Ed25519、SHA-256、大小和 Authenticode。
- [ ] 已覆盖取消、断网、磁盘/存储失败、安装启动失败和重启恢复。
- [ ] 已运行目标项目测试、构建和适用验证矩阵。
- [ ] 已产出可复现命令、日志和报告，并完成 RULES 要求的 Checklist。
