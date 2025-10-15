"""
适配器模块 - 负责 ORM Models ↔ DTO 的双向转换
"""
from .vocab_adapter import VocabAdapter, VocabExampleAdapter
from .grammar_adapter import GrammarAdapter, GrammarExampleAdapter
from .text_adapter import TextAdapter, SentenceAdapter

__all__ = [
    'VocabAdapter',
    'VocabExampleAdapter',
    'GrammarAdapter',
    'GrammarExampleAdapter',
    'TextAdapter',
    'SentenceAdapter',
]
