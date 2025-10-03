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

# 创建 FastAPI 应用
app = FastAPI(
    title="Asked Tokens API",
    description="专门处理 asked tokens 的 API 服务",
    version="1.0.0"
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Asked Tokens API", "status": "running"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Asked Tokens API is running"}

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
    print("🚀 启动 Asked Tokens API 服务器...")
    print("📡 服务地址: http://localhost:8001")
    print("📚 API 文档: http://localhost:8001/docs")
    uvicorn.run(app, host="0.0.0.0", port=8001)

