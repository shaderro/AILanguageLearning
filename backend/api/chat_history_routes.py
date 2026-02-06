from typing import Optional, Any, Dict, List

from fastapi import APIRouter, Query, Depends, HTTPException

from backend.data_managers.chat_message_manager_db import ChatMessageManagerDB

# 延迟导入以避免启动时初始化失败
try:
    from backend.api.auth_routes import get_current_user
    from database_system.business_logic.models import User
except ImportError:
    # 如果认证模块不可用，提供占位符
    def get_current_user():
        raise HTTPException(status_code=500, detail="认证系统未加载")
    User = None

router = APIRouter(prefix="/api/chat", tags=["chat"])

# 延迟初始化 ChatMessageManagerDB（避免启动时失败）
_chat_manager = None

def get_chat_manager():
    """延迟初始化 ChatMessageManagerDB，避免启动时失败"""
    global _chat_manager
    if _chat_manager is None:
        try:
            _chat_manager = ChatMessageManagerDB()
        except Exception as e:
            # 如果初始化失败（例如在 PostgreSQL 环境中），返回 None
            print(f"⚠️ [ChatHistory] ChatMessageManagerDB 初始化失败: {e}")
            return None
    return _chat_manager


@router.get("/history")
def get_chat_history(
    text_id: Optional[int] = Query(None, description="文章 ID（可选）"),
    sentence_id: Optional[int] = Query(None, description="句子 ID（可选）"),
    limit: int = Query(100, ge=1, le=500, description="最大返回条数，默认 100，上限 500"),
    offset: int = Query(0, ge=0, description="偏移量，用于分页"),
    current_user: User = Depends(get_current_user),  # 🔒 强制认证，确保用户隔离
) -> Dict[str, Any]:
    """
    获取聊天历史记录（跨设备，仅当前用户）。

    - ✅ 强制认证：必须登录
    - ✅ 用户隔离：只能查看自己的聊天记录
    - 按 `created_at` 升序返回（旧 → 新）
    - 可按 `text_id` / `sentence_id` 过滤
    """
    # 🔒 强制使用当前登录用户的 user_id（忽略任何查询参数中的 user_id）
    user_id = str(current_user.user_id)
    print(f"🔍 [ChatHistory] 获取历史记录请求: text_id={text_id}, sentence_id={sentence_id}, user_id={user_id}, limit={limit}, offset={offset}")
    
    # 获取 ChatMessageManagerDB 实例
    chat_manager = get_chat_manager()
    if chat_manager is None:
        # 如果 ChatMessageManagerDB 不可用（例如在 PostgreSQL 环境中尚未迁移），返回空结果
        print("⚠️ [ChatHistory] ChatMessageManagerDB 不可用，返回空结果")
        return {
            "success": True,
            "data": {
                "items": [],
                "count": 0,
                "limit": limit,
                "offset": offset,
            },
        }
    
    # 🔒 强制使用当前用户的 user_id 查询（确保用户隔离）
    messages: List[Dict[str, Any]] = chat_manager.list_messages(
        user_id=user_id,  # ✅ 强制使用当前用户的 ID
        text_id=text_id,
        sentence_id=sentence_id,
        limit=limit,
        offset=offset,
    )

    # 规范化为前端更容易消费的字段命名
    normalized = [
        {
            "id": m["id"],
            "user_id": m["user_id"],
            "text_id": m["text_id"],
            "sentence_id": m["sentence_id"],
            "is_user": m["is_user"],
            "text": m["content"],
            "quote_sentence_id": m["quote_sentence_id"],
            "quote_text": m["quote_text"],
            "selected_token": m["selected_token"],
            "created_at": m["created_at"],
        }
        for m in messages
    ]

    return {
        "success": True,
        "data": {
            "items": normalized,
            "count": len(normalized),
            "limit": limit,
            "offset": offset,
        },
    }


