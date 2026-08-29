"""协议处理器注册表

支持注册自定义协议处理器，用于扩展 starry:// 协议的功能。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .handler import StarryProtocolHandler
from .types import ProtocolResult


class BaseProtocolHandler(ABC):
    """协议处理器基类
    
    自定义处理器需要继承此类并实现 can_handle 和 handle 方法。
    """
    
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """判断是否可以处理此 URL
        
        Args:
            url: 协议 URL
            
        Returns:
            如果可以处理返回 True，否则返回 False
        """
        pass
    
    @abstractmethod
    async def handle(self, url: str) -> ProtocolResult:
        """处理协议 URL
        
        Args:
            url: 协议 URL
            
        Returns:
            处理结果
        """
        pass


class ProtocolHandlerRegistry:
    """协议处理器注册表"""
    
    def __init__(self):
        self._handlers: list[BaseProtocolHandler] = []
        self._default_handler = StarryProtocolHandler()
    
    def register(self, handler: BaseProtocolHandler) -> None:
        """注册自定义处理器
        
        Args:
            handler: 处理器实例
        """
        self._handlers.append(handler)
    
    def unregister(self, handler: BaseProtocolHandler) -> None:
        """注销处理器
        
        Args:
            handler: 处理器实例
        """
        if handler in self._handlers:
            self._handlers.remove(handler)
    
    def get_handler(self, url: str) -> BaseProtocolHandler | StarryProtocolHandler:
        """获取可以处理此 URL 的处理器
        
        Args:
            url: 协议 URL
            
        Returns:
            处理器实例，如果没有匹配的自定义处理器，返回默认处理器
        """
        for handler in self._handlers:
            if handler.can_handle(url):
                return handler
        
        return self._default_handler
    
    async def handle(self, url: str) -> ProtocolResult:
        """处理协议 URL
        
        Args:
            url: 协议 URL
            
        Returns:
            处理结果
        """
        handler = self.get_handler(url)
        return await handler.handle(url)


# 全局注册表实例
_registry = ProtocolHandlerRegistry()


def register_handler(handler: BaseProtocolHandler) -> None:
    """注册自定义协议处理器
    
    Args:
        handler: 处理器实例
        
    Example:
        >>> from openstarry_code.protocol import register_handler, BaseProtocolHandler
        >>> 
        >>> class MyHandler(BaseProtocolHandler):
        ...     def can_handle(self, url: str) -> bool:
        ...         return url.startswith("starry://custom/")
        ...     
        ...     async def handle(self, url: str) -> ProtocolResult:
        ...         # 自定义处理逻辑
        ...         pass
        >>> 
        >>> register_handler(MyHandler())
    """
    _registry.register(handler)


def unregister_handler(handler: BaseProtocolHandler) -> None:
    """注销协议处理器
    
    Args:
        handler: 处理器实例
    """
    _registry.unregister(handler)


def get_handler(url: str) -> BaseProtocolHandler | StarryProtocolHandler:
    """获取可以处理指定 URL 的处理器
    
    Args:
        url: 协议 URL
        
    Returns:
        处理器实例
    """
    return _registry.get_handler(url)


async def handle_url(url: str) -> ProtocolResult:
    """处理协议 URL（便捷函数）
    
    Args:
        url: 协议 URL
        
    Returns:
        处理结果
        
    Example:
        >>> from openstarry_code.protocol import handle_url
        >>> 
        >>> result = await handle_url("starry://api/import?provider=openai&key=env:OPENAI_API_KEY")
        >>> if result.success:
        ...     print(f"✅ {result.message}")
        ... else:
        ...     print(f"❌ {result.error}")
    """
    return await _registry.handle(url)
