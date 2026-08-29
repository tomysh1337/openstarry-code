"""starry:// 协议处理器

用于处理 OpenStarry Code 的私有协议 URL，支持：
- API 配置导入
- Skill 安装
- 扩展加载
"""

from __future__ import annotations

from .handler import StarryProtocolHandler, ProtocolHandlerError
from .parser import ProtocolParseError, parse_starry_url, validate_parsed_url
from .registry import (
    BaseProtocolHandler,
    register_handler,
    unregister_handler,
    get_handler,
    handle_url,
)
from .types import (
    ParsedProtocolURL,
    ProtocolAction,
    ProtocolResult,
    ProtocolStatus,
)

__all__ = [
    # Handler
    "StarryProtocolHandler",
    "ProtocolHandlerError",
    # Parser
    "ProtocolParseError",
    "parse_starry_url",
    "validate_parsed_url",
    # Registry
    "BaseProtocolHandler",
    "register_handler",
    "unregister_handler",
    "get_handler",
    "handle_url",
    # Types
    "ParsedProtocolURL",
    "ProtocolAction",
    "ProtocolResult",
    "ProtocolStatus",
]
