"""协议处理器类型定义"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class ProtocolAction(StrEnum):
    """协议操作类型"""
    
    API_IMPORT = "api/import"
    SKILL_INSTALL = "skill/install"
    EXTENSION_LOAD = "extension/load"
    CONFIG_IMPORT = "config/import"


class ProtocolStatus(StrEnum):
    """协议处理状态"""
    
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    REQUIRES_CONFIRMATION = "requires_confirmation"


@dataclass
class ProtocolResult:
    """协议处理结果"""
    
    status: ProtocolStatus
    message: str
    action: ProtocolAction
    data: dict[str, Any] | None = None
    error: str | None = None
    confirmation_token: str | None = None
    
    @property
    def success(self) -> bool:
        return self.status == ProtocolStatus.SUCCESS
    
    @property
    def requires_confirmation(self) -> bool:
        return self.status == ProtocolStatus.REQUIRES_CONFIRMATION


@dataclass
class ParsedProtocolURL:
    """解析后的协议 URL"""
    
    scheme: str  # starry
    action: ProtocolAction
    params: dict[str, str]
    raw_url: str
    
    def get_param(self, key: str, default: str | None = None) -> str | None:
        """获取参数值"""
        return self.params.get(key, default)
    
    def require_param(self, key: str) -> str:
        """获取必需参数，如果不存在则抛出异常"""
        if key not in self.params:
            raise ValueError(f"Missing required parameter: {key}")
        return self.params[key]
