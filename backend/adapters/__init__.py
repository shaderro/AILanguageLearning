"""
适配器模块 - 负责 ORM Models ↔ DTO 的双向转换
"""
from .vocab_adapter import VocabAdapter, VocabExampleAdapter

__all__ = [
    'VocabAdapter',
    'VocabExampleAdapter',
]
