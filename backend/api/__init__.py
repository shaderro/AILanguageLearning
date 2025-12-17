"""
Backend API 模块
"""
from .vocab_routes import router as vocab_router
from .grammar_routes import router as grammar_router
from .text_routes import router as text_router
from .chat_history_routes import router as chat_history_router

__all__ = ['vocab_router', 'grammar_router', 'text_router', 'chat_history_router']
