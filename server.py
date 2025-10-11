#!/usr/bin/env python3
"""
Asked Tokens API 服务器
专门处理 asked tokens 相关的 API 端点
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import json
import os
import sys

# 添加backend路径到sys.path
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.join(CURRENT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# 导入 AskedTokensManager
from backend.data_managers.asked_tokens_manager import get_asked_tokens_manager

# 导入词汇API路由
from backend.api import vocab_router
from backend.api.vocab_routes_verbose import router as vocab_verbose_router

# 创建 FastAPI 应用
app = FastAPI(
    title="Language Learning API",
    description="语言学习系统 API 服务（包含 Asked Tokens 和 Vocab 管理）",
    version="2.0.0"
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册词汇API路由
app.include_router(vocab_router)
app.include_router(vocab_verbose_router)  # 详细日志版本

@app.get("/")
async def root():
    return {
        "message": "Language Learning API",
        "status": "running",
        "version": "2.0.0",
        "endpoints": {
            "asked_tokens": "/api/user/asked-tokens",
            "vocab_v2": "/api/v2/vocab",
            "vocab_verbose": "/api/v2/vocab-verbose (详细日志版本)",
            "docs": "/docs",
            "health": "/api/health"
        },
        "note": "使用 /api/v2/vocab-verbose 端点可以看到详细的数据转换日志"
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "Language Learning API is running",
        "services": {
            "asked_tokens": "active",
            "vocab_v2": "active (database)"
        }
    }

@app.get("/api/user/asked-tokens")
async def get_asked_tokens(user_id: str = Query(..., description="用户ID"), 
                          text_id: int = Query(..., description="文章ID")):
    """获取用户在指定文章下已提问的 token 键集合"""
    try:
        print(f" [AskedTokens] Getting asked tokens for user={user_id}, text_id={text_id}")
        
        # 使用 JSON 文件模式（测试阶段）
        manager = get_asked_tokens_manager(use_database=False)
        asked_tokens = manager.get_asked_tokens_for_article(user_id, text_id)
        
        print(f" [AskedTokens] Found {len(asked_tokens)} asked tokens")
        return {
            "success": True,
            "data": {
                "asked_tokens": list(asked_tokens),
                "count": len(asked_tokens)
            }
        }
    except Exception as e:
        print(f" [AskedTokens] Error getting asked tokens: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/user/asked-tokens")
async def mark_token_asked(payload: dict):
    """标记 token 为已提问"""
    try:
        user_id = payload.get("user_id", "default_user")  # 默认用户ID
        text_id = payload.get("text_id")
        sentence_id = payload.get("sentence_id")
        sentence_token_id = payload.get("sentence_token_id")
        
        print(f" [AskedTokens] Marking token as asked:")
        print(f"  - user_id: {user_id}")
        print(f"  - text_id: {text_id}")
        print(f"  - sentence_id: {sentence_id}")
        print(f"  - sentence_token_id: {sentence_token_id}")
        
        if not text_id or sentence_id is None or sentence_token_id is None:
            return {
                "success": False,
                "error": "text_id, sentence_id, sentence_token_id 都是必需的"
            }
        
        # 使用 JSON 文件模式（测试阶段）
        manager = get_asked_tokens_manager(use_database=False)
        success = manager.mark_token_asked(
            user_id=user_id,
            text_id=text_id,
            sentence_id=sentence_id,
            sentence_token_id=sentence_token_id
        )
        
        if success:
            print(f" [AskedTokens] Token marked as asked successfully")
            return {
                "success": True,
                "message": "Token 已标记为已提问",
                "data": {
                    "user_id": user_id,
                    "text_id": text_id,
                    "sentence_id": sentence_id,
                    "sentence_token_id": sentence_token_id
                }
            }
        else:
            return {
                "success": False,
                "error": "标记 token 为已提问失败"
            }
    except Exception as e:
        print(f" [AskedTokens] Error marking token as asked: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.delete("/api/user/asked-tokens")
async def unmark_token_asked(payload: dict):
    """取消标记 token 为已提问"""
    try:
        user_id = payload.get("user_id", "default_user")  # 默认用户ID
        token_key = payload.get("token_key")
        
        print(f" [AskedTokens] Unmarking token: user={user_id}, key={token_key}")
        
        if not token_key:
            return {
                "success": False,
                "error": "token_key 是必需的"
            }
        
        # 使用 JSON 文件模式（测试阶段）
        manager = get_asked_tokens_manager(use_database=False)
        success = manager.unmark_token_asked(user_id, token_key)
        
        if success:
            print(f" [AskedTokens] Token unmarked successfully")
            return {
                "success": True,
                "message": "Token 已取消标记",
                "data": {"token_key": token_key}
            }
        else:
            return {
                "success": False,
                "error": "取消标记 token 失败"
            }
    except Exception as e:
        print(f" [AskedTokens] Error unmarking token: {e}")
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("Starting FastAPI Server...")
    print("=" * 60)
    print("")
    print("Server Address: http://localhost:8001")
    print("API Documentation: http://localhost:8001/docs")
    print("Health Check: http://localhost:8001/api/health")
    print("")
    print("Press Ctrl+C to stop the server")
    print("")
    uvicorn.run(app, host="0.0.0.0", port=8001)

