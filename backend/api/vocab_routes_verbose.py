"""
词汇 API 路由 - 详细日志版本

用于学习和调试，展示完整的数据转换过程
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
import logging

from backend.api.db_deps import get_db_session

# 导入详细日志版本的 VocabManager
from backend.data_managers.vocab_manager_db_verbose import VocabManager as VocabManagerDB

# 导入 DTO
from backend.data_managers.data_classes_new import (
    VocabExpression as VocabDTO,
    VocabExpressionExample as VocabExampleDTO
)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


# ==================== Pydantic 模型 ====================

class VocabCreateRequest(BaseModel):
    vocab_body: str = Field(..., description="词汇内容")
    explanation: str = Field(..., description="词汇解释")
    source: str = Field(default="manual", description="来源：auto/qa/manual")
    is_starred: bool = Field(default=False, description="是否收藏")


class VocabUpdateRequest(BaseModel):
    vocab_body: Optional[str] = Field(None, description="词汇内容")
    explanation: Optional[str] = Field(None, description="词汇解释")
    source: Optional[str] = Field(None, description="来源")
    is_starred: Optional[bool] = Field(None, description="是否收藏")


# ==================== 创建路由器 ====================

router = APIRouter(
    prefix="/api/v2/vocab-verbose",
    tags=["vocab-verbose"],
    responses={404: {"description": "Not found"}},
)


# ==================== API 端点 ====================

@router.get("/", summary="获取所有词汇（详细日志）")
async def get_all_vocabs(
    skip: int = Query(default=0, ge=0, description="跳过的记录数"),
    limit: int = Query(default=100, ge=1, le=1000, description="返回的最大记录数"),
    starred_only: bool = Query(default=False, description="是否只返回收藏的词汇"),
    session: Session = Depends(get_db_session)
):
    """
    获取所有词汇（分页）- 带详细日志
    """
    try:
        logger.info("\n" + "🟢" * 35)
        logger.info("[API] 端点: GET /api/v2/vocab-verbose/")
        logger.info(f"[API] 参数: skip={skip}, limit={limit}, starred_only={starred_only}")
        logger.info("🟢" * 35)
        
        logger.info("\n[API] 创建 VocabManagerDB...")
        vocab_manager = VocabManagerDB(session, verbose=True)
        
        logger.info("\n[API] 调用 vocab_manager.get_all_vocabs()...")
        vocabs = vocab_manager.get_all_vocabs(skip=skip, limit=limit, starred_only=starred_only)
        
        logger.info("\n[API] 构建响应 JSON...")
        response = {
            "success": True,
            "data": {
                "vocabs": [
                    {
                        "vocab_id": v.vocab_id,
                        "vocab_body": v.vocab_body,
                        "explanation": v.explanation,
                        "source": v.source,  # ← 已经是字符串
                        "is_starred": v.is_starred
                    }
                    for v in vocabs
                ],
                "count": len(vocabs),
                "skip": skip,
                "limit": limit
            }
        }
        
        logger.info(f"[API] 响应包含 {len(vocabs)} 个词汇")
        logger.info("[API] FastAPI 自动序列化为 JSON 返回给前端")
        logger.info("🟢" * 35 + "\n")
        
        return response
    except Exception as e:
        logger.error(f"[API] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{vocab_id}", summary="获取单个词汇（详细日志）")
async def get_vocab(
    vocab_id: int,
    include_examples: bool = Query(default=True, description="是否包含例句"),
    session: Session = Depends(get_db_session)
):
    """
    根据 ID 获取词汇 - 带详细日志
    """
    try:
        logger.info("\n" + "🟢" * 35)
        logger.info(f"[API] 端点: GET /api/v2/vocab-verbose/{vocab_id}")
        logger.info(f"[API] 参数: include_examples={include_examples}")
        logger.info("🟢" * 35)
        
        logger.info("\n[API] 创建 VocabManagerDB...")
        vocab_manager = VocabManagerDB(session, verbose=True)
        
        logger.info(f"\n[API] 调用 vocab_manager.get_vocab_by_id({vocab_id})...")
        vocab = vocab_manager.get_vocab_by_id(vocab_id)
        
        if not vocab:
            logger.warning(f"[API] 未找到 ID={vocab_id} 的词汇")
            raise HTTPException(status_code=404, detail=f"Vocab ID {vocab_id} not found")
        
        logger.info("\n[API] 构建响应 JSON...")
        response = {
            "success": True,
            "data": {
                "vocab_id": vocab.vocab_id,
                "vocab_body": vocab.vocab_body,
                "explanation": vocab.explanation,
                "source": vocab.source,  # ← 已经是字符串，无需转换
                "is_starred": vocab.is_starred,
                "examples": [
                    {
                        "vocab_id": ex.vocab_id,
                        "text_id": ex.text_id,
                        "sentence_id": ex.sentence_id,
                        "context_explanation": ex.context_explanation,
                        "token_indices": ex.token_indices
                    }
                    for ex in vocab.examples
                ] if include_examples else []
            }
        }
        
        logger.info("[API] 响应已构建")
        logger.info("[API] FastAPI 自动序列化为 JSON")
        logger.info("🟢" * 35 + "\n")
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", summary="创建新词汇（详细日志）", status_code=201)
async def create_vocab(
    request: VocabCreateRequest,
    session: Session = Depends(get_db_session)
):
    """
    创建新词汇 - 带详细日志
    """
    try:
        logger.info("\n" + "🟢" * 35)
        logger.info("[API] 端点: POST /api/v2/vocab-verbose/")
        logger.info(f"[API] 请求体:")
        logger.info(f"  vocab_body: '{request.vocab_body}'")
        logger.info(f"  explanation: '{request.explanation}'")
        logger.info(f"  source: '{request.source}'")
        logger.info(f"  is_starred: {request.is_starred}")
        logger.info("🟢" * 35)
        
        logger.info("\n[API] 创建 VocabManagerDB...")
        vocab_manager = VocabManagerDB(session, verbose=True)
        
        # 检查是否已存在
        logger.info(f"\n[API] 检查词汇是否已存在...")
        existing = vocab_manager.get_vocab_by_body(request.vocab_body)
        if existing:
            logger.warning(f"[API] 词汇已存在: ID={existing.vocab_id}")
            raise HTTPException(
                status_code=400, 
                detail=f"Vocab '{request.vocab_body}' already exists with ID {existing.vocab_id}"
            )
        
        logger.info("[API] 词汇不存在，可以创建")
        
        # 创建词汇
        logger.info(f"\n[API] 调用 vocab_manager.add_new_vocab()...")
        vocab = vocab_manager.add_new_vocab(
            vocab_body=request.vocab_body,
            explanation=request.explanation,
            source=request.source,
            is_starred=request.is_starred
        )
        
        logger.info("\n[API] 构建响应 JSON...")
        response = {
            "success": True,
            "message": "Vocab created successfully",
            "data": {
                "vocab_id": vocab.vocab_id,
                "vocab_body": vocab.vocab_body,
                "explanation": vocab.explanation,
                "source": vocab.source,  # ← 已经是字符串
                "is_starred": vocab.is_starred
            }
        }
        
        logger.info(f"[API] 词汇创建成功: ID={vocab.vocab_id}")
        logger.info("🟢" * 35 + "\n")
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary", summary="获取词汇统计（详细日志）")
async def get_vocab_stats(
    session: Session = Depends(get_db_session)
):
    """
    获取词汇统计信息 - 带详细日志
    """
    try:
        logger.info("\n" + "🟢" * 35)
        logger.info("[API] 端点: GET /api/v2/vocab-verbose/stats/summary")
        logger.info("🟢" * 35)
        
        vocab_manager = VocabManagerDB(session, verbose=False)  # 统计不需要详细日志
        stats = vocab_manager.get_vocab_stats()
        
        logger.info(f"[API] 统计结果: {stats}")
        logger.info("🟢" * 35 + "\n")
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"[API] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

