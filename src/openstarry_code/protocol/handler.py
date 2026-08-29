"""starry:// 协议处理器主逻辑"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from openstarry_code.onboarding.config_store import (
    default_config_path,
    load_config,
    persist_config,
)
from openstarry_code.onboarding.mutations import upsert_llm_provider
from openstarry_code.onboarding.provider_specs import get_provider_setup_spec

from .parser import (
    ProtocolParseError,
    parse_starry_url,
    validate_parsed_url,
)
from .types import ParsedProtocolURL, ProtocolAction, ProtocolResult, ProtocolStatus


class ProtocolHandlerError(Exception):
    """协议处理器错误"""
    pass


class StarryProtocolHandler:
    """starry:// 协议处理器
    
    负责处理 starry:// 协议 URL，包括：
    - API 配置导入
    - Skill 安装
    - 扩展加载
    """
    
    def __init__(self, config_path: Path | None = None):
        """初始化处理器
        
        Args:
            config_path: 配置文件路径，默认使用系统配置路径
        """
        self.config_path = config_path or default_config_path()
    
    async def handle(self, url: str) -> ProtocolResult:
        """处理协议 URL
        
        Args:
            url: starry:// 协议 URL
            
        Returns:
            ProtocolResult 对象，包含处理结果
        """
        try:
            # 解析 URL
            parsed = parse_starry_url(url)
            
            # 验证参数
            validate_parsed_url(parsed)
            
            # 根据 action 分发处理
            if parsed.action == ProtocolAction.API_IMPORT:
                return await self._handle_api_import(parsed)
            elif parsed.action == ProtocolAction.SKILL_INSTALL:
                return await self._handle_skill_install(parsed)
            elif parsed.action == ProtocolAction.EXTENSION_LOAD:
                return await self._handle_extension_load(parsed)
            elif parsed.action == ProtocolAction.CONFIG_IMPORT:
                return await self._handle_config_import(parsed)
            else:
                return ProtocolResult(
                    status=ProtocolStatus.FAILED,
                    message=f"Unknown action: {parsed.action}",
                    action=parsed.action,
                    error=f"Unsupported protocol action: {parsed.action}",
                )
        
        except ProtocolParseError as e:
            return ProtocolResult(
                status=ProtocolStatus.FAILED,
                message=f"Failed to parse URL: {e}",
                action=ProtocolAction.API_IMPORT,  # 默认值
                error=str(e),
            )
        except Exception as e:
            return ProtocolResult(
                status=ProtocolStatus.FAILED,
                message=f"Unexpected error: {e}",
                action=ProtocolAction.API_IMPORT,  # 默认值
                error=str(e),
            )
    
    async def _handle_api_import(self, parsed: ParsedProtocolURL) -> ProtocolResult:
        """处理 API 配置导入"""
        try:
            # 方式 1: 从 URL 导入配置文件
            if "url" in parsed.params:
                config_url = parsed.require_param("url")
                provider_type = parsed.require_param("type")
                
                # 下载并解析配置文件
                config_data = await self._fetch_config_file(config_url)
                
                # 应用配置
                result = await self._apply_provider_config(provider_type, config_data)
                
                return ProtocolResult(
                    status=ProtocolStatus.SUCCESS,
                    message=f"✅ Successfully imported API configuration from {config_url}",
                    action=ProtocolAction.API_IMPORT,
                    data={"provider": provider_type, "source": config_url},
                )
            
            # 方式 2: 直接配置 provider
            elif "provider" in parsed.params:
                provider_id = parsed.require_param("provider")
                api_key = parsed.get_param("key")
                model = parsed.get_param("model")
                base_url = parsed.get_param("base_url")
                
                # 验证 provider 是否支持
                spec = get_provider_setup_spec(provider_id)
                if not spec:
                    return ProtocolResult(
                        status=ProtocolStatus.FAILED,
                        message=f"❌ Unknown provider: {provider_id}",
                        action=ProtocolAction.API_IMPORT,
                        error=f"Provider '{provider_id}' is not supported",
                    )
                
                # 构建配置
                config = load_config(self.config_path)
                
                provider_config: dict[str, Any] = {
                    "provider": provider_id,
                }
                
                # 处理 API key（支持 env: 前缀）
                if api_key:
                    if api_key.startswith("env:"):
                        provider_config["api_key_env"] = api_key[4:]
                    else:
                        provider_config["api_key"] = api_key
                
                if model:
                    provider_config["model"] = model
                
                if base_url:
                    provider_config["base_url"] = base_url
                
                # 使用 mutations 更新配置
                upsert_llm_provider(config, provider_config)
                
                # 持久化配置
                persist_config(self.config_path, config)
                
                return ProtocolResult(
                    status=ProtocolStatus.SUCCESS,
                    message=f"✅ Successfully configured provider: {provider_id}",
                    action=ProtocolAction.API_IMPORT,
                    data={
                        "provider": provider_id,
                        "model": model,
                        "has_key": bool(api_key),
                    },
                )
            
            else:
                return ProtocolResult(
                    status=ProtocolStatus.FAILED,
                    message="❌ Missing required parameters",
                    action=ProtocolAction.API_IMPORT,
                    error="Either 'url' or 'provider' parameter is required",
                )
        
        except Exception as e:
            return ProtocolResult(
                status=ProtocolStatus.FAILED,
                message=f"❌ Failed to import API configuration: {e}",
                action=ProtocolAction.API_IMPORT,
                error=str(e),
            )
    
    async def _handle_skill_install(self, parsed: ParsedProtocolURL) -> ProtocolResult:
        """处理 Skill 安装"""
        try:
            # 从 GitHub 安装
            if "github" in parsed.params:
                repo = parsed.require_param("github")
                ref = parsed.get_param("ref", "main")
                subpath = parsed.get_param("subpath")
                
                return ProtocolResult(
                    status=ProtocolStatus.REQUIRES_CONFIRMATION,
                    message=f"Ready to install skill from GitHub: {repo}",
                    action=ProtocolAction.SKILL_INSTALL,
                    data={
                        "source": "github",
                        "repo": repo,
                        "ref": ref,
                        "subpath": subpath,
                    },
                    confirmation_token=f"github:{repo}@{ref}",
                )
            
            # 从 ClawHub 安装
            elif "clawhub" in parsed.params:
                skill_id = parsed.require_param("clawhub")
                
                return ProtocolResult(
                    status=ProtocolStatus.REQUIRES_CONFIRMATION,
                    message=f"Ready to install skill from ClawHub: {skill_id}",
                    action=ProtocolAction.SKILL_INSTALL,
                    data={
                        "source": "clawhub",
                        "skill_id": skill_id,
                    },
                    confirmation_token=f"clawhub:{skill_id}",
                )
            
            # 从本地路径安装
            elif "local" in parsed.params:
                local_path = parsed.require_param("local")
                
                # 处理 file:// 协议
                if local_path.startswith("file://"):
                    local_path = urlparse(local_path).path
                
                return ProtocolResult(
                    status=ProtocolStatus.REQUIRES_CONFIRMATION,
                    message=f"Ready to install skill from local path: {local_path}",
                    action=ProtocolAction.SKILL_INSTALL,
                    data={
                        "source": "local",
                        "path": local_path,
                    },
                    confirmation_token=f"local:{local_path}",
                )
            
            else:
                return ProtocolResult(
                    status=ProtocolStatus.FAILED,
                    message="❌ Missing skill source parameter",
                    action=ProtocolAction.SKILL_INSTALL,
                    error="One of 'github', 'clawhub', or 'local' parameter is required",
                )
        
        except Exception as e:
            return ProtocolResult(
                status=ProtocolStatus.FAILED,
                message=f"❌ Failed to prepare skill installation: {e}",
                action=ProtocolAction.SKILL_INSTALL,
                error=str(e),
            )
    
    async def _handle_extension_load(self, parsed: ParsedProtocolURL) -> ProtocolResult:
        """处理扩展加载"""
        try:
            ext_path = parsed.require_param("path")
            ext_type = parsed.get_param("type", "python")
            
            # 处理 file:// 协议
            if ext_path.startswith("file://"):
                ext_path = urlparse(ext_path).path
            
            return ProtocolResult(
                status=ProtocolStatus.REQUIRES_CONFIRMATION,
                message=f"Ready to load extension: {ext_path} (type: {ext_type})",
                action=ProtocolAction.EXTENSION_LOAD,
                data={
                    "path": ext_path,
                    "type": ext_type,
                },
                confirmation_token=f"extension:{ext_type}:{ext_path}",
            )
        
        except Exception as e:
            return ProtocolResult(
                status=ProtocolStatus.FAILED,
                message=f"❌ Failed to prepare extension loading: {e}",
                action=ProtocolAction.EXTENSION_LOAD,
                error=str(e),
            )
    
    async def _handle_config_import(self, parsed: ParsedProtocolURL) -> ProtocolResult:
        """处理完整配置导入"""
        try:
            config_url = parsed.require_param("url")
            
            # 下载配置文件
            config_data = await self._fetch_config_file(config_url)
            
            return ProtocolResult(
                status=ProtocolStatus.REQUIRES_CONFIRMATION,
                message=f"Ready to import full configuration from: {config_url}",
                action=ProtocolAction.CONFIG_IMPORT,
                data={
                    "url": config_url,
                    "preview": config_data,
                },
                confirmation_token=f"config:{config_url}",
            )
        
        except Exception as e:
            return ProtocolResult(
                status=ProtocolStatus.FAILED,
                message=f"❌ Failed to fetch configuration: {e}",
                action=ProtocolAction.CONFIG_IMPORT,
                error=str(e),
            )
    
    async def _fetch_config_file(self, url: str) -> dict[str, Any]:
        """从 URL 获取配置文件
        
        支持 HTTP/HTTPS 和 file:// 协议
        """
        if url.startswith("file://"):
            # 本地文件
            file_path = Path(urlparse(url).path)
            if not file_path.exists():
                raise FileNotFoundError(f"Config file not found: {file_path}")
            
            content = file_path.read_text(encoding="utf-8")
            
            # 根据文件扩展名解析
            if file_path.suffix == ".json":
                return json.loads(content)
            elif file_path.suffix == ".toml":
                import tomli
                return tomli.loads(content)
            else:
                raise ValueError(f"Unsupported config file format: {file_path.suffix}")
        
        else:
            # HTTP/HTTPS
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                
                # 根据 Content-Type 解析
                content_type = response.headers.get("content-type", "")
                
                if "json" in content_type:
                    return response.json()
                elif "toml" in content_type:
                    import tomli
                    return tomli.loads(response.text)
                else:
                    # 尝试 JSON
                    try:
                        return response.json()
                    except Exception:
                        # 尝试 TOML
                        import tomli
                        return tomli.loads(response.text)
    
    async def _apply_provider_config(
        self, 
        provider_type: str, 
        config_data: dict[str, Any]
    ) -> None:
        """应用 provider 配置到系统配置文件"""
        config = load_config(self.config_path)
        
        # 提取 provider 配置
        provider_config = config_data.get("config", {})
        provider_config["provider"] = provider_type
        
        # 使用 mutations 更新配置
        upsert_llm_provider(config, provider_config)
        
        # 持久化配置
        persist_config(self.config_path, config)
    
    async def handle_batch(self, urls: list[str]) -> list[ProtocolResult]:
        """批量处理协议 URL
        
        Args:
            urls: 协议 URL 列表
            
        Returns:
            处理结果列表
        """
        tasks = [self.handle(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=False)
