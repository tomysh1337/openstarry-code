"""Hermes-style 工作流自动学习系统

对话完成后自动分析工作流模式，提取可复用的技能。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class WorkflowPattern:
    """工作流模式"""
    
    task_type: str  # 任务类型
    intent: str  # 用户意图
    tool_sequence: tuple[str, ...] = field(default_factory=tuple)  # 工具调用序列
    file_patterns: tuple[str, ...] = field(default_factory=tuple)  # 涉及的文件模式
    key_steps: tuple[str, ...] = field(default_factory=tuple)  # 关键步骤描述
    reusability_score: float = 0.0  # 可复用性评分 0-1
    


@dataclass(frozen=True)
class SkillDraft:
    """Skill 草稿"""
    
    name: str
    description: str
    trigger_patterns: tuple[str, ...] = field(default_factory=tuple)
    workflow_steps: tuple[str, ...] = field(default_factory=tuple)
    example_usage: str = ""
    estimated_complexity: str = "medium"  # low/medium/high


async def analyze_turn_for_learning(
    user_message: str,
    tool_calls: list[dict[str, Any]],
    turn_segments: list[dict[str, Any]],
    *,
    success: bool = True
) -> WorkflowPattern | None:
    """分析 Turn 是否值得学习
    
    Args:
        user_message: 用户消息
        tool_calls: 工具调用列表
        turn_segments: Turn 片段
        success: 任务是否成功完成
    
    Returns:
        WorkflowPattern 如果值得学习，否则 None
    """
    if not success or len(tool_calls) < 5:
        return None
    
    tool_sequence = tuple(call.get("tool_name", "") for call in tool_calls)
    task_type = _identify_task_type(user_message, tool_sequence)
    file_patterns = _extract_file_patterns(tool_calls)
    key_steps = _generate_key_steps(tool_calls, turn_segments)
    
    reusability_score = _calculate_reusability(
        tool_sequence=tool_sequence,
        file_patterns=file_patterns,
        task_type=task_type
    )
    
    if reusability_score < 0.6:
        return None
    
    return WorkflowPattern(
        task_type=task_type,
        intent=user_message[:200],
        tool_sequence=tool_sequence,
        file_patterns=file_patterns,
        key_steps=key_steps,
        reusability_score=reusability_score
    )


_BUG_KEYWORDS = frozenset({"bug", "fix", "error", "修复", "错误"})
_TEST_KEYWORDS = frozenset({"test", "测试"})
_REFACTOR_KEYWORDS = frozenset({"refactor", "重构"})
_API_KEYWORDS = frozenset({"api", "endpoint", "接口"})
_UI_KEYWORDS = frozenset({"ui", "frontend", "页面"})
_DB_KEYWORDS = frozenset({"database", "数据库", "schema"})
_DEPLOY_KEYWORDS = frozenset({"deploy", "部署", "ci/cd"})


def _identify_task_type(user_message: str, tool_sequence: tuple[str, ...]) -> str:
    """识别任务类型"""
    message_lower = user_message.lower()
    
    if any(kw in message_lower for kw in _BUG_KEYWORDS):
        return "bug_fix"
    elif any(kw in message_lower for kw in _TEST_KEYWORDS):
        return "testing"
    elif any(kw in message_lower for kw in _REFACTOR_KEYWORDS):
        return "refactoring"
    elif any(kw in message_lower for kw in _API_KEYWORDS):
        return "api_development"
    elif any(kw in message_lower for kw in _UI_KEYWORDS):
        return "frontend_development"
    elif any(kw in message_lower for kw in _DB_KEYWORDS):
        return "database_work"
    elif any(kw in message_lower for kw in _DEPLOY_KEYWORDS):
        return "deployment"
    
    return "general_development"


def _extract_file_patterns(tool_calls: list[dict[str, Any]]) -> tuple[str, ...]:
    """提取文件模式"""
    patterns = set()
    
    for call in tool_calls:
        args = call.get("arguments", {})
        
        path = args.get("file_path")
        if isinstance(path, str):
            if "." in path:
                ext = path.split(".")[-1]
                patterns.add(f"*.{ext}")
            
            parts = path.split("/")
            if len(parts) >= 2:
                patterns.add(f"{parts[-2]}/*")
        
        pattern = args.get("pattern")
        if isinstance(pattern, str):
            patterns.add(pattern)
    
    return tuple(sorted(patterns)[:5])


def _generate_key_steps(tool_calls: list[dict[str, Any]], turn_segments: list[dict[str, Any]]) -> tuple[str, ...]:
    """生成关键步骤描述"""
    steps = []
    groups = _group_tool_calls(tool_calls)
    
    for group_type, calls in groups.items():
        count = len(calls)
        if group_type == "read":
            steps.append(f"读取 {count} 个文件进行分析")
        elif group_type == "search":
            steps.append(f"执行 {count} 次代码搜索定位目标")
        elif group_type == "write":
            steps.append(f"修改 {count} 个文件")
        elif group_type == "command":
            steps.append(f"执行 {count} 条命令")
        elif group_type == "verify":
            steps.append(f"验证 {count} 项检查")
    
    return tuple(steps[:6])


_READ_TOOLS = frozenset({"read", "cat"})
_SEARCH_TOOLS = frozenset({"search", "grep", "glob"})
_WRITE_TOOLS = frozenset({"write", "edit", "replace"})
_COMMAND_TOOLS = frozenset({"command", "run"})
_VERIFY_TOOLS = frozenset({"verify", "check", "test"})


def _group_tool_calls(tool_calls: list[dict[str, Any]]) -> dict[str, list[dict]]:
    """按类型分组工具调用"""
    groups: dict[str, list[dict]] = {
        "read": [],
        "search": [],
        "write": [],
        "command": [],
        "verify": []
    }
    
    for call in tool_calls:
        tool_name = call.get("tool_name", "").lower()
        
        if any(kw in tool_name for kw in _READ_TOOLS):
            groups["read"].append(call)
        elif any(kw in tool_name for kw in _SEARCH_TOOLS):
            groups["search"].append(call)
        elif any(kw in tool_name for kw in _WRITE_TOOLS):
            groups["write"].append(call)
        elif any(kw in tool_name for kw in _COMMAND_TOOLS):
            groups["command"].append(call)
        elif any(kw in tool_name for kw in _VERIFY_TOOLS):
            groups["verify"].append(call)
    
    return {k: v for k, v in groups.items() if v}


def _calculate_reusability(
    tool_sequence: tuple[str, ...],
    file_patterns: tuple[str, ...],
    task_type: str
) -> float:
    """计算可复用性评分"""
    score = 0.5
    
    unique_tools = len(frozenset(tool_sequence))
    if unique_tools >= 4:
        score += 0.2
    
    if file_patterns:
        score += 0.15
    
    if task_type != "general_development":
        score += 0.15
    
    return min(score, 1.0)


def generate_skill_draft(pattern: WorkflowPattern) -> SkillDraft:
    """根据工作流模式生成 Skill 草稿"""
    name = _generate_skill_name(pattern.task_type)
    description = f"自动化 {pattern.task_type} 相关任务的工作流"
    
    trigger_patterns = (
        pattern.intent[:100],
        f"涉及 {', '.join(pattern.file_patterns[:2])} 文件的 {pattern.task_type} 任务"
    )
    
    seq_len = len(pattern.tool_sequence)
    if seq_len < 8:
        complexity = "low"
    elif seq_len < 15:
        complexity = "medium"
    else:
        complexity = "high"
    
    return SkillDraft(
        name=name,
        description=description,
        trigger_patterns=trigger_patterns,
        workflow_steps=pattern.key_steps,
        example_usage=pattern.intent,
        estimated_complexity=complexity
    )


_TASK_TYPE_NAMES = {
    "bug_fix": "auto-bug-fixer",
    "testing": "test-generator",
    "refactoring": "code-refactorer",
    "api_development": "api-scaffolder",
    "frontend_development": "ui-builder",
    "database_work": "db-schema-manager",
    "deployment": "deploy-automator",
    "general_development": "dev-workflow"
}


def _generate_skill_name(task_type: str) -> str:
    """生成 Skill 名称"""
    return _TASK_TYPE_NAMES.get(task_type, "custom-workflow")
