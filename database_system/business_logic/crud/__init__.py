"""
CRUD 模块 - 按功能拆分的数据库操作
"""
from .vocab_crud import VocabCRUD
from .grammar_crud import GrammarCRUD
from .text_crud import TextCRUD
from .token_crud import TokenCRUD
from .asked_token_crud import AskedTokenCRUD
from .stats_crud import StatsCRUD

__all__ = [
    'VocabCRUD',
    'GrammarCRUD', 
    'TextCRUD',
    'TokenCRUD',
    'AskedTokenCRUD',
    'StatsCRUD'
]
