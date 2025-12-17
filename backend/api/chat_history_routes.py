from typing import Optional, Any, Dict, List

from fastapi import APIRouter, Query

from backend.data_managers.chat_message_manager_db import ChatMessageManagerDB

router = APIRouter(prefix="/api/chat", tags=["chat"])

_chat_manager = ChatMessageManagerDB()


@router.get("/history")
def get_chat_history(
    text_id: Optional[int] = Query(None, description="文章 ID（可选）"),
    sentence_id: Optional[int] = Query(None, description="句子 ID（可选）"),
    user_id: Optional[str] = Query(None, description="用户 ID（可选，预留字段）"),
    limit: int = Query(100, ge=1, le=500, description="最大返回条数，默认 100，上限 500"),
    offset: int = Query(0, ge=0, description="偏移量，用于分页"),
) -> Dict[str, Any]:
    """
    获取聊天历史记录（跨设备）。

    - 按 `created_at` 升序返回（旧 → 新）
    - 可按 `text_id` / `sentence_id` / `user_id` 过滤
    """
    messages: List[Dict[str, Any]] = _chat_manager.list_messages(
        user_id=user_id,
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


