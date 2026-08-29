"""Headroom-style 提示词压缩器

在提示词发送给 LLM 前进行智能压缩，减少 token 消耗。
参考 Headroom 项目的压缩策略。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class CompressionLevel(str, Enum):
    """压缩级别"""
    LIGHT = "light"
    MEDIUM = "medium"
    DEEP = "deep"


@dataclass(frozen=True)
class CompressionResult:
    """压缩结果"""
    
    original: str
    compressed: str
    original_length: int
    compressed_length: int
    compression_ratio: float
    tokens_saved_estimate: int
    strategies_applied: tuple[str, ...] = field(default_factory=tuple)


class HeadroomCompressor:
    """提示词压缩器"""
    
    REDUNDANT_WORDS = frozenset({
        "please", "kindly", "could you", "would you",
        "i want", "i need", "i would like",
        "basically", "actually", "literally",
        "请", "麻烦", "能否", "可以吗",
        "我想", "我需要", "我希望"
    })
    
    FILLER_PHRASES = (
        r"\b(please note that|it should be noted that|it is important to)\b",
        r"\b(as you (?:know|can see)|as mentioned)\b",
        r"\b(in order to|for the purpose of)\b",
        r"(?:^|\. )(?:So|Well|Now|Also),?\s+",
        r"（请注意|需要注意的是|重要的是）",
        r"（如你所知|如前所述）"
    )
    
    PHRASE_REPLACEMENTS = {
        "in order to": "to",
        "due to the fact that": "because",
        "at this point in time": "now",
        "for the purpose of": "for",
        "in the event that": "if",
        "with regard to": "about",
        "in spite of the fact that": "although",
        "on the basis of": "based on",
        "is able to": "can",
        "in order for": "for",
        "as a result of": "from",
        "in the process of": "during",
    }
    
    TECHNICAL_ABBREVIATIONS = {
        "function": "fn",
        "parameter": "param",
        "parameters": "params",
        "argument": "arg",
        "arguments": "args",
        "variable": "var",
        "variables": "vars",
        "implementation": "impl",
        "configuration": "config",
        "initialize": "init",
        "repository": "repo",
        "directory": "dir",
        "documentation": "docs",
        "application": "app",
        "database": "db",
        "environment": "env",
        "authentication": "auth",
        "authorization": "authz",
    }
    
    __slots__ = ("level",)
    
    def __init__(self, level: CompressionLevel = CompressionLevel.MEDIUM):
        self.level = level
    
    def compress(self, prompt: str) -> CompressionResult:
        """压缩提示词"""
        if not prompt:
            return CompressionResult(
                original="",
                compressed="",
                original_length=0,
                compressed_length=0,
                compression_ratio=0.0,
                tokens_saved_estimate=0,
                strategies_applied=()
            )
        
        original = prompt
        original_length = len(prompt)
        compressed = prompt
        strategies = []
        
        # 根据压缩级别应用不同策略
        is_light = self.level == CompressionLevel.LIGHT
        is_medium = self.level == CompressionLevel.MEDIUM
        is_deep = self.level == CompressionLevel.DEEP
        
        # 策略 1：删除冗余词汇（所有级别）
        compressed = self._remove_redundant_words(compressed)
        strategies.append("remove_redundant_words")
        
        # 策略 2：删除客套话（Medium 及以上）
        if is_medium or is_deep:
            compressed = self._remove_filler_phrases(compressed)
            strategies.append("remove_filler_phrases")
        
        # 策略 3：短语替换（所有级别）
        compressed = self._replace_phrases(compressed)
        strategies.append("phrase_replacement")
        
        # 策略 4：简化句式（Medium 及以上）
        if is_medium or is_deep:
            compressed = self._simplify_syntax(compressed)
            strategies.append("simplify_syntax")
        
        # 策略 5-7：Deep 级别专属
        if is_deep:
            compressed = self._compress_examples(compressed)
            strategies.append("compress_examples")
            
            compressed = self._apply_abbreviations(compressed)
            strategies.append("apply_abbreviations")
            
            compressed = self._aggressive_compression(compressed)
            strategies.append("aggressive_compression")
        
        # 清理多余空格和换行
        compressed = self._cleanup_whitespace(compressed)
        strategies.append("cleanup_whitespace")
        
        compressed_length = len(compressed)
        compression_ratio = 1 - (compressed_length / original_length) if original_length > 0 else 0.0
        tokens_saved = (original_length - compressed_length) // 4
        
        return CompressionResult(
            original=original,
            compressed=compressed,
            original_length=original_length,
            compressed_length=compressed_length,
            compression_ratio=compression_ratio,
            tokens_saved_estimate=tokens_saved,
            strategies_applied=tuple(strategies)
        )
    
    def _remove_redundant_words(self, text: str) -> str:
        """删除冗余词汇"""
        for word in self.REDUNDANT_WORDS:
            pattern = r'\b' + re.escape(word) + r'\b'
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        return text
    
    def _remove_filler_phrases(self, text: str) -> str:
        """删除客套话"""
        for pattern in self.FILLER_PHRASES:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        return text
    
    def _replace_phrases(self, text: str) -> str:
        """短语替换"""
        for long_phrase, short_phrase in self.PHRASE_REPLACEMENTS.items():
            pattern = r'\b' + re.escape(long_phrase) + r'\b'
            text = re.sub(pattern, short_phrase, text, flags=re.IGNORECASE)
        return text
    
    def _simplify_syntax(self, text: str) -> str:
        """简化句式"""
        text = re.sub(r'\b(so|such)\s+that\b', r'\1', text, flags=re.IGNORECASE)
        text = re.sub(r'\bThere\s+(?:is|are)\s+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(?:a|an|the)\s+(?:very|really|quite)\b', '', text, flags=re.IGNORECASE)
        return text
    
    def _compress_examples(self, text: str) -> str:
        """压缩示例：'For example: A, B, C' -> 'e.g. A,B,C'"""
        text = re.sub(r'\bFor example:\s*', 'e.g. ', text, flags=re.IGNORECASE)
        text = re.sub(r'\b例如[:：]\s*', '如 ', text)
        text = re.sub(r',\s+', ',', text)
        return text
    
    def _apply_abbreviations(self, text: str) -> str:
        """应用技术缩写"""
        for full, abbr in self.TECHNICAL_ABBREVIATIONS.items():
            pattern = r'\b' + re.escape(full) + r'\b'
            text = re.sub(pattern, abbr, text, flags=re.IGNORECASE)
        return text
    
    def _aggressive_compression(self, text: str) -> str:
        """激进压缩策略"""
        text = re.sub(r'\n{3,}', '\n\n', text)
        lines = [line.strip() for line in text.split('\n')]
        return '\n'.join(lines)
    
    def _cleanup_whitespace(self, text: str) -> str:
        """清理多余空格和换行"""
        text = re.sub(r' {2,}', ' ', text)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()


def should_compress_prompt(
    prompt: str,
    *,
    min_length: int = 1000,
    auto_compress: bool = True
) -> bool:
    """判断是否应该压缩提示词
    
    Args:
        prompt: 原始提示词
        min_length: 最小长度阈值
        auto_compress: 是否自动压缩
    
    Returns:
        是否应该压缩
    """
    if not auto_compress:
        return False
    
    return len(prompt) >= min_length


def compress_prompt(
    prompt: str,
    level: CompressionLevel = CompressionLevel.MEDIUM,
    *,
    auto_compress: bool = True,
    min_length: int = 1000
) -> str:
    """压缩提示词（便捷函数）
    
    Args:
        prompt: 原始提示词
        level: 压缩级别
        auto_compress: 是否自动压缩
        min_length: 最小长度阈值
    
    Returns:
        压缩后的提示词（如果不需要压缩则返回原文）
    """
    if not should_compress_prompt(prompt, min_length=min_length, auto_compress=auto_compress):
        return prompt
    
    compressor = HeadroomCompressor(level=level)
    result = compressor.compress(prompt)
    return result.compressed
