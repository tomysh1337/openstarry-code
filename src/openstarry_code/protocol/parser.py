"""协议 URL 解析器"""

from __future__ import annotations

import urllib.parse
from typing import Any

from .types import ParsedProtocolURL, ProtocolAction


class ProtocolParseError(Exception):
    """协议解析错误"""
    pass


def parse_starry_url(url: str) -> ParsedProtocolURL:
    """解析 starry:// 协议 URL
    
    Args:
        url: 协议 URL，例如 "starry://api/import?provider=openai&key=env:OPENAI_API_KEY"
        
    Returns:
        ParsedProtocolURL 对象
        
    Raises:
        ProtocolParseError: URL 格式不正确时抛出
        
    Examples:
        >>> parsed = parse_starry_url("starry://api/import?provider=openai")
        >>> parsed.action
        'api/import'
        >>> parsed.params['provider']
        'openai'
    """
    if not url.startswith("starry://"):
        raise ProtocolParseError(f"Invalid protocol scheme, expected 'starry://', got: {url}")
    
    try:
        # 解析 URL
        parsed = urllib.parse.urlparse(url)
        
        # 提取 action（host + path）
        action_parts = []
        if parsed.netloc:
            action_parts.append(parsed.netloc)
        if parsed.path and parsed.path != "/":
            # 移除开头的 /
            path = parsed.path.lstrip("/")
            if path:
                action_parts.append(path)
        
        if not action_parts:
            raise ProtocolParseError("Missing action in URL")
        
        action_str = "/".join(action_parts)
        
        # 验证 action 是否有效
        try:
            action = ProtocolAction(action_str)
        except ValueError:
            raise ProtocolParseError(
                f"Unknown action: {action_str}. Valid actions: {', '.join(ProtocolAction)}"
            )
        
        # 解析查询参数
        params = dict(urllib.parse.parse_qsl(parsed.query))
        
        return ParsedProtocolURL(
            scheme=parsed.scheme,
            action=action,
            params=params,
            raw_url=url,
        )
        
    except Exception as e:
        if isinstance(e, ProtocolParseError):
            raise
        raise ProtocolParseError(f"Failed to parse URL: {e}") from e


def validate_api_import_params(params: dict[str, str]) -> None:
    """验证 API 导入参数
    
    必须提供以下参数之一：
    - url + type
    - provider
    """
    has_url = "url" in params
    has_provider = "provider" in params
    
    if not has_url and not has_provider:
        raise ProtocolParseError(
            "API import requires either 'url' + 'type' or 'provider' parameter"
        )
    
    if has_url and "type" not in params:
        raise ProtocolParseError("When using 'url', 'type' parameter is required")


def validate_skill_install_params(params: dict[str, str]) -> None:
    """验证 Skill 安装参数
    
    必须提供以下参数之一：
    - source + name
    - github
    - clawhub
    - local
    """
    valid_sources = ["github", "clawhub", "local"]
    
    has_source = "source" in params and "name" in params
    has_direct = any(key in params for key in valid_sources)
    
    if not has_source and not has_direct:
        raise ProtocolParseError(
            f"Skill install requires either 'source' + 'name' or one of: {', '.join(valid_sources)}"
        )


def validate_extension_load_params(params: dict[str, str]) -> None:
    """验证扩展加载参数
    
    必须提供：
    - path
    """
    if "path" not in params:
        raise ProtocolParseError("Extension load requires 'path' parameter")


def validate_parsed_url(parsed: ParsedProtocolURL) -> None:
    """验证解析后的 URL 参数
    
    Args:
        parsed: 解析后的 URL 对象
        
    Raises:
        ProtocolParseError: 参数不合法时抛出
    """
    if parsed.action == ProtocolAction.API_IMPORT:
        validate_api_import_params(parsed.params)
    elif parsed.action == ProtocolAction.SKILL_INSTALL:
        validate_skill_install_params(parsed.params)
    elif parsed.action == ProtocolAction.EXTENSION_LOAD:
        validate_extension_load_params(parsed.params)
