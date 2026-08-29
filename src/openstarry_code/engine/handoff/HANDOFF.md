# Session Handoff 模块

## 模块概述

Session Handoff 系统负责管理会话间状态转移，用于处理 fork、subagent 返回、meta 命令执行等场景下的待处理输入和上下文迁移。

## 架构组成

### 核心文件

1. **types.py** - 数据类型定义
2. **manager.py** - 交接管理器
3. **session_transfer.py** - 转移操作
4. **recovery.py** - 恢复机制
5. **__init__.py** - 模块导出

## 主要功能

### 1. 交接生命周期管理

```python
from openstarry_code.engine.handoff import HandoffManager, SessionTransferRequest

manager = HandoffManager()

# 创建交接请求
request = SessionTransferRequest(
    source_session_key="agent:main:parent",
    target_session_key="agent:main:child",
    request_id="request-123",
    pending_inputs=(
        {"pending_input_id": "input-1", "text": "follow-up"},
    ),
    context_data={"fork_point": "msg-456"},
)

# 执行转移
from openstarry_code.engine.handoff.session_transfer import transfer_session_state
result = transfer_session_state(manager, request)
```

### 2. 交接状态流转

```
PENDING → accept_handoff() → ACCEPTED
                           → reject_handoff() → REJECTED
        → (超时) → EXPIRED

ACCEPTED → complete_handoff() → COMPLETED
```

### 3. 恢复机制

```python
from openstarry_code.engine.handoff.recovery import (
    recover_pending_handoffs,
    cleanup_stale_handoffs,
)

# 恢复会话的待处理交接
recoverable = recover_pending_handoffs(manager, "agent:main:parent")

# 清理超过1小时的过期交接
cleaned = cleanup_stale_handoffs(manager, max_age_ms=3600000)
```

## 数据结构

### HandoffRecord

```python
@dataclass(frozen=True, slots=True)
class HandoffRecord:
    handoff_id: str                    # 唯一标识
    owner_request_id: str              # 所属请求ID
    source_session_key: str            # 源会话
    target_session_key: str | None     # 目标会话
    state: HandoffState                # 状态
    phase: HandoffPhase                # 阶段
    pending_input_count: int           # 待转移输入数量
    accepted_session_key: str | None   # 接受方会话
    created_at: int                    # 创建时间戳（毫秒）
    updated_at: int                    # 更新时间戳
    completed_at: int | None           # 完成时间戳
    metadata: dict[str, Any]           # 元数据
```

### HandoffPhase 枚举

- `CREATING`: 正在创建子会话
- `OPENING`: 正在打开目标会话
- `ACTIVE`: 交接活跃中
- `RETURNING`: 从子会话返回
- `COMPLETED`: 已完成
- `FAILED`: 失败

### HandoffState 枚举

- `PENDING`: 待处理
- `ACCEPTED`: 已接受
- `REJECTED`: 已拒绝
- `EXPIRED`: 已过期

## 潜在漏洞与风险

### 🔴 高风险

#### 1. 内存泄漏风险
**位置**: `manager.py:HandoffManager._active_handoffs`

**问题**: 如果大量交接创建但未完成或拒绝，会导致内存无限增长。

**当前缓解措施**:
- 设置 `_MAX_PENDING_HANDOFFS = 100` 限制
- `_cleanup_expired_handoffs()` 自动清理超过1小时的记录

**建议增强**:
```python
# 添加定期清理任务
async def periodic_cleanup_task(manager: HandoffManager):
    while True:
        await asyncio.sleep(300)  # 每5分钟
        manager._cleanup_expired_handoffs()
```

#### 2. 并发竞态条件
**位置**: `manager.py:accept_handoff()`, `complete_handoff()`

**问题**: 多个协程同时操作同一 handoff_id 可能导致状态不一致。

**当前状态**: ❌ 未实现并发控制

**建议修复**:
```python
import asyncio

class HandoffManager:
    def __init__(self):
        self._active_handoffs: dict[str, HandoffRecord] = {}
        self._handoff_locks: dict[str, asyncio.Lock] = {}
    
    async def accept_handoff(self, owner_request_id: str, ...):
        handoff = self._find_by_request_id(owner_request_id)
        if not handoff:
            return None
        
        lock = self._handoff_locks.setdefault(
            handoff.handoff_id, 
            asyncio.Lock()
        )
        async with lock:
            # 原有逻辑
            ...
```

#### 3. 请求ID冲突
**位置**: `manager.py:_find_by_request_id()`

**问题**: 假设 `owner_request_id` 唯一，但缺少验证机制。

**风险场景**:
```python
# 两个不同来源使用相同 request_id
request1 = SessionTransferRequest(
    source_session_key="session-A",
    target_session_key="session-B",
    request_id="req-123",  # 冲突
    ...
)
request2 = SessionTransferRequest(
    source_session_key="session-C",
    target_session_key="session-D",
    request_id="req-123",  # 冲突
    ...
)
```

**建议修复**:
```python
def create_handoff(self, request: SessionTransferRequest) -> HandoffRecord:
    # 检查 request_id 是否已存在
    existing = self._find_by_request_id(request.request_id)
    if existing and existing.state in (HandoffState.PENDING, HandoffState.ACCEPTED):
        raise ValueError(
            f"Request ID {request.request_id} already has an active handoff"
        )
    ...
```

### 🟡 中风险

#### 4. 历史记录无限增长
**位置**: `manager.py:_handoff_history`

**问题**: completed/rejected 的 handoff 永久保存在内存中。

**建议方案**:
```python
_MAX_HISTORY_SIZE = 1000

def complete_handoff(self, handoff_id: str) -> HandoffRecord | None:
    ...
    self._handoff_history[handoff_id] = completed
    
    # 限制历史大小
    if len(self._handoff_history) > _MAX_HISTORY_SIZE:
        oldest_keys = sorted(
            self._handoff_history.keys(),
            key=lambda k: self._handoff_history[k].completed_at or 0
        )[:len(self._handoff_history) - _MAX_HISTORY_SIZE]
        for key in oldest_keys:
            del self._handoff_history[key]
    
    return completed
```

#### 5. 日志敏感信息泄露
**位置**: `session_transfer.py`, `recovery.py`

**问题**: 日志中可能包含敏感的 session_key 或 pending_input 内容。

**当前状态**: ✅ 仅记录 ID 和计数，不记录实际内容

**建议增强**: 添加敏感数据脱敏
```python
def _sanitize_session_key(key: str) -> str:
    """脱敏会话密钥，仅保留前缀和后缀"""
    if len(key) <= 20:
        return key
    return f"{key[:8]}...{key[-8:]}"
```

#### 6. 未验证 session_key 合法性
**位置**: `manager.py:create_handoff()`

**问题**: 不检查 source/target session 是否存在或有效。

**风险**: 创建指向不存在会话的交接记录。

**建议修复**:
```python
def create_handoff(
    self,
    request: SessionTransferRequest,
    validate_sessions: Callable[[str], bool] | None = None,
) -> HandoffRecord:
    if validate_sessions:
        if not validate_sessions(request.source_session_key):
            raise ValueError(f"Invalid source session: {request.source_session_key}")
        if request.target_session_key and not validate_sessions(request.target_session_key):
            raise ValueError(f"Invalid target session: {request.target_session_key}")
    ...
```

### 🟢 低风险

#### 7. 时间戳精度依赖
**位置**: 所有使用 `time.time() * 1000` 的地方

**问题**: Python 的 `time.time()` 在某些系统上精度不足。

**建议**: 使用 `time.time_ns() // 1_000_000` 获取毫秒时间戳。

#### 8. 元数据无结构验证
**位置**: `HandoffRecord.metadata`

**问题**: `metadata` 是自由字典，缺少结构约束。

**建议**: 定义元数据 schema
```python
from typing import TypedDict

class HandoffMetadata(TypedDict, total=False):
    context_keys: list[str]
    pending_input_ids: list[str]
    rejection_reason: str
    retry_count: int
    fork_point_message_id: str
```

## 集成建议

### 与现有系统集成

```python
# 在 engine/runtime.py 中集成
from openstarry_code.engine.handoff import HandoffManager

class TurnRunner:
    def __init__(self):
        self.handoff_manager = HandoffManager()
    
    async def handle_fork_session(self, parent_key: str, child_key: str, ...):
        request = SessionTransferRequest(
            source_session_key=parent_key,
            target_session_key=child_key,
            request_id=f"fork-{uuid.uuid4().hex[:12]}",
            pending_inputs=self._collect_pending_inputs(),
        )
        result = transfer_session_state(self.handoff_manager, request)
        if not result.success:
            logger.error("Fork handoff failed", extra={"error": result.error_message})
```

### 持久化建议

当前实现为纯内存存储。生产环境建议：

```python
# 添加持久化层
class PersistentHandoffManager(HandoffManager):
    def __init__(self, db_path: str):
        super().__init__()
        self.db = sqlite3.connect(db_path)
        self._init_schema()
    
    def _init_schema(self):
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS handoffs (
                handoff_id TEXT PRIMARY KEY,
                owner_request_id TEXT,
                source_session_key TEXT,
                target_session_key TEXT,
                state TEXT,
                phase TEXT,
                created_at INTEGER,
                updated_at INTEGER,
                metadata TEXT
            )
        """)
```

## 测试建议

### 单元测试覆盖

1. ✅ 正常流程：create → accept → complete
2. ✅ 拒绝流程：create → reject
3. ✅ 过期清理：create → 等待超时 → cleanup
4. ⚠️ 并发测试：多协程同时操作
5. ⚠️ 边界测试：达到 MAX_PENDING_HANDOFFS
6. ⚠️ 恢复测试：recover_pending_handoffs 正确性

### 集成测试

1. 完整 fork 流程
2. Subagent 返回场景
3. 会话切换保留待处理输入
4. 错误恢复和重试机制

## 性能考量

### 内存占用估算

每个 HandoffRecord 约 500 字节：
- 最大活跃交接（100个）: ~50KB
- 历史记录（无限制）: **需要修复**

### 时间复杂度

- `create_handoff`: O(1)
- `accept_handoff`: O(n) - 需要遍历查找 request_id
- `list_active_handoffs`: O(n log n) - 排序
- `_cleanup_expired_handoffs`: O(n)

**优化建议**: 添加 `owner_request_id` 索引
```python
def __init__(self):
    self._active_handoffs: dict[str, HandoffRecord] = {}
    self._request_id_index: dict[str, str] = {}  # request_id -> handoff_id

def create_handoff(self, request: SessionTransferRequest):
    ...
    self._request_id_index[request.request_id] = handoff_id
    ...

def _find_by_request_id(self, request_id: str) -> HandoffRecord | None:
    handoff_id = self._request_id_index.get(request_id)
    return self._active_handoffs.get(handoff_id) if handoff_id else None
```

## 代码优化已应用

✅ Frozen dataclass with `field(default_factory)`
✅ Tuple 返回类型替代 list
✅ `__slots__` 优化内存
✅ StrEnum 替代普通枚举
✅ 类型注解完整
✅ 结构化日志

## 后续改进计划

1. [ ] 实现并发锁机制
2. [ ] 添加持久化层
3. [ ] 限制历史记录大小
4. [ ] 添加 request_id 索引优化查询
5. [ ] 实现 session 合法性验证
6. [ ] 编写完整单元测试
7. [ ] 添加性能监控指标
8. [ ] 实现自动清理定期任务

## 变更日志

### 2026-08-28 - 初始版本
- 创建 handoff 模块基础架构
- 实现核心管理器和转移操作
- 添加恢复机制
- 应用代码优化标准
