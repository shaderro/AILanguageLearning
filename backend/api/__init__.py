"""
Backend API 模块
"""
from .vocab_routes import router as vocab_router
from .grammar_routes import router as grammar_router
from .text_routes import router as text_router

__all__ = ['vocab_router', 'grammar_router', 'text_router']
