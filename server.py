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

# 导入API路由
from backend.api import vocab_router, grammar_router, text_router
from backend.api.vocab_routes_verbose import router as vocab_verbose_router
from backend.api.user_routes import router as user_router

# 创建 FastAPI 应用
app = FastAPI(
    title="Language Learning API",
    description="语言学习系统 API 服务（包含 Asked Tokens、Vocab、Grammar 和 Text 管理）",
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

# 注册API路由
app.include_router(vocab_router)
app.include_router(vocab_verbose_router)  # 详细日志版本
app.include_router(grammar_router)
app.include_router(text_router)
app.include_router(user_router)  # 用户管理路由

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
            "grammar_v2": "/api/v2/grammar",
            "texts_v2": "/api/v2/texts",
            "users_v2": "/api/v2/users",
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
            "vocab_v2": "active (database)",
            "grammar_v2": "active (database)",
            "texts_v2": "active (database)",
            "users_v2": "active (database)"
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
    """
    标记 token 或 sentence 为已提问
    
    支持两种类型的标记：
    1. type='token': 标记单词（需要 sentence_token_id）
    2. type='sentence': 标记句子（sentence_token_id 可选）
    
    向后兼容：如果 type 未指定但 sentence_token_id 存在，默认为 'token'
    """
    try:
        user_id = payload.get("user_id", "default_user")  # 默认用户ID
        text_id = payload.get("text_id")
        sentence_id = payload.get("sentence_id")
        sentence_token_id = payload.get("sentence_token_id")
        type_param = payload.get("type", None)  # 新增：标记类型
        
        # 向后兼容逻辑：如果 type 未指定但 sentence_token_id 不为空，默认为 'token'
        if type_param is None:
            if sentence_token_id is not None:
                type_param = "token"
            else:
                type_param = "sentence"
        
        print(f"🏷️ [AskedTokens] Marking as asked:")
        print(f"  - user_id: {user_id}")
        print(f"  - text_id: {text_id}")
        print(f"  - sentence_id: {sentence_id}")
        print(f"  - sentence_token_id: {sentence_token_id}")
        print(f"  - type: {type_param}")
        
        # 验证必需参数
        if not text_id or sentence_id is None:
            return {
                "success": False,
                "error": "text_id 和 sentence_id 是必需的"
            }
        
        # 如果是 token 类型，sentence_token_id 必须提供
        if type_param == "token" and sentence_token_id is None:
            return {
                "success": False,
                "error": "type='token' 时，sentence_token_id 是必需的"
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
            print(f"✅ [AskedTokens] Marked as asked successfully (type={type_param})")
            return {
                "success": True,
                "message": f"{'Token' if type_param == 'token' else 'Sentence'} 已标记为已提问",
                "data": {
                    "user_id": user_id,
                    "text_id": text_id,
                    "sentence_id": sentence_id,
                    "sentence_token_id": sentence_token_id,
                    "type": type_param
                }
            }
        else:
            return {
                "success": False,
                "error": "标记为已提问失败"
            }
    except Exception as e:
        print(f"❌ [AskedTokens] Error marking as asked: {e}")
        import traceback
        traceback.print_exc()
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
    print("Server Address: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/api/health")
    print("")
    print("Press Ctrl+C to stop the server")
    print("")
    uvicorn.run(app, host="0.0.0.0", port=8000)

