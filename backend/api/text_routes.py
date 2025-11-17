"""
文章 API 路由 - 使用数据库版本的 OriginalTextManager

提供文章和句子相关的 RESTful API 接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

# 导入数据库管理器
from database_system.database_manager import DatabaseManager
from database_system.business_logic.models import User, OriginalText

# 导入认证依赖
from backend.api.auth_routes import get_current_user

# 导入数据库版本的 OriginalTextManager
from backend.data_managers import OriginalTextManagerDB

# 导入 DTO（用于类型提示和响应）
from backend.data_managers.data_classes_new import (
    OriginalText as TextDTO,
    Sentence as SentenceDTO
)


# ==================== 依赖注入：数据库 Session ====================

def get_db_session():
    """
    依赖注入：提供数据库 Session
    
    特点：
    - 每个请求获取一个新的 Session
    - 成功时自动 commit
    - 失败时自动 rollback
    - 请求结束时自动 close
    """
    db_manager = DatabaseManager('development')
    session = db_manager.get_session()
    try:
        yield session
        session.commit()  # 成功时提交事务
    except Exception as e:
        session.rollback()  # 失败时回滚事务
        raise e
    finally:
        session.close()  # 总是关闭 Session


# ==================== Pydantic 模型（请求/响应） ====================

class TextCreateRequest(BaseModel):
    """创建文章请求"""
    text_title: str = Field(..., description="文章标题", example="德语阅读材料")


class SentenceCreateRequest(BaseModel):
    """创建句子请求"""
    text_id: int = Field(..., description="文章ID")
    sentence_body: str = Field(..., description="句子内容")
    difficulty_level: Optional[str] = Field(None, description="难度等级：easy/hard")


class TextResponse(BaseModel):
    """文章响应"""
    text_id: int
    text_title: str
    sentence_count: int = 0

    class Config:
        from_attributes = True


class SentenceResponse(BaseModel):
    """句子响应"""
    text_id: int
    sentence_id: int
    sentence_body: str
    sentence_difficulty_level: Optional[str] = None
    grammar_annotations: List[int] = []
    vocab_annotations: List[int] = []

    class Config:
        from_attributes = True


class ApiResponse(BaseModel):
    """统一 API 响应格式"""
    success: bool
    message: str = ""
    data: Optional[dict] = None
    error: Optional[str] = None


# ==================== 创建路由器 ====================

router = APIRouter(
    prefix="/api/v2/texts",
    tags=["texts-db"],
    responses={404: {"description": "Not found"}},
)


# ==================== API 端点 ====================

@router.get("/", summary="获取所有文章")
async def get_all_texts(
    include_sentences: bool = Query(default=False, description="是否包含句子列表"),
    language: Optional[str] = Query(default=None, description="语言过滤：中文、英文、德文"),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的所有文章
    
    - **include_sentences**: 是否包含句子（默认不包含，提升性能）
    - **language**: 语言过滤（中文、英文、德文），None表示不过滤
    
    需要认证：是
    """
    try:
        from database_system.business_logic.models import Sentence, Token, OriginalText
        from sqlalchemy import func
        
        # 直接使用数据库查询，支持语言过滤
        query = session.query(OriginalText).filter(OriginalText.user_id == current_user.user_id)
        
        # 语言过滤
        if language and language != 'all':
            query = query.filter(OriginalText.language == language)
        
        text_models = query.all()
        
        # 为每篇文章计算句子数和token数
        texts_with_stats = []
        for t in text_models:
            # 使用SQL查询统计句子数
            sentence_count = session.query(func.count(Sentence.id)).filter(
                Sentence.text_id == t.text_id
            ).scalar() or 0
            
            # 使用SQL查询统计token数
            token_count = session.query(func.count(Token.token_id)).filter(
                Token.text_id == t.text_id
            ).scalar() or 0
            
            texts_with_stats.append({
                "text_id": t.text_id,
                "text_title": t.text_title,
                "language": t.language,
                "total_sentences": sentence_count,
                "total_tokens": token_count,
                "sentence_count": sentence_count,  # 保持向后兼容
                "sentences": [
                    {
                        "sentence_id": s.sentence_id,
                        "sentence_body": s.sentence_body,
                        "difficulty_level": s.sentence_difficulty_level
                    }
                    for s in t.text_by_sentence
                ] if include_sentences and hasattr(t, 'text_by_sentence') else []
            })
        
        return {
            "success": True,
            "data": {
                "texts": texts_with_stats,
                "count": len(texts_with_stats)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{text_id}", summary="获取单个文章")
async def get_text(
    text_id: int,
    include_sentences: bool = Query(default=True, description="是否包含句子列表"),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    根据 ID 获取文章（仅限当前用户）
    
    - **text_id**: 文章ID
    - **include_sentences**: 是否包含句子
    
    需要认证：是
    """
    try:
        print(f"[API] Getting text {text_id}, include_sentences={include_sentences}, user_id={current_user.user_id}")
        
        # 先验证文章是否存在且属于当前用户
        text_model = session.query(OriginalText).filter(
            OriginalText.text_id == text_id,
            OriginalText.user_id == current_user.user_id
        ).first()
        
        if not text_model:
            print(f"[API] Text {text_id} not found for user {current_user.user_id}")
            raise HTTPException(status_code=404, detail=f"Text ID {text_id} not found")
        
        text_manager = OriginalTextManagerDB(session)
        text = text_manager.get_text_by_id(text_id, include_sentences=include_sentences)
        
        if not text:
            print(f"[API] Text {text_id} not found")
            raise HTTPException(status_code=404, detail=f"Text ID {text_id} not found")
        
        # 🔧 安全处理 text_by_sentence（可能为 None 或空列表）
        text_by_sentence = text.text_by_sentence if text.text_by_sentence else []
        sentence_count = len(text_by_sentence) if text_by_sentence else 0
        
        print(f"[API] Found text {text_id}: {text.text_title}, sentences: {sentence_count}")
        
        result = {
            "success": True,
            "data": {
                "text_id": text.text_id,
                "text_title": text.text_title,
                "language": text.language,
                "sentence_count": sentence_count,
                "sentences": [
                    {
                        "sentence_id": s.sentence_id,
                        "sentence_body": s.sentence_body,
                        "difficulty_level": s.sentence_difficulty_level,
                        "grammar_annotations": list(s.grammar_annotations) if s.grammar_annotations else [],
                        "vocab_annotations": list(s.vocab_annotations) if s.vocab_annotations else [],
                        # tokens：优先使用 DTO 自带的 tokens；如果为空，则按空格简单切分 sentence_body 生成 fallback tokens
                        "tokens": (
                            [
                                {
                                    # 与前端 TokenSpan 预期字段对齐
                                    "token_body": t.token_body,
                                    "sentence_token_id": t.sentence_token_id,
                                    # 统一使用小写的 'text'，便于前端判断
                                    "token_type": (
                                        str(t.token_type).lower()
                                        if t.token_type is not None
                                        else "text"
                                    ),
                                    # 标记为可选择 token
                                    "selectable": True,
                                }
                                for t in getattr(s, "tokens", []) or []
                            ]
                            if getattr(s, "tokens", None)
                            else [
                                {
                                    "token_body": word,
                                    "sentence_token_id": idx,
                                    "token_type": "text",
                                    "selectable": True,
                                }
                                for idx, word in enumerate((s.sentence_body or "").split())
                            ]
                        )
                    }
                    for s in text_by_sentence
                ] if include_sentences else []
            }
        }
        print(f"[API] Returning {len(result['data']['sentences'])} sentences")
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to get text {text_id}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", summary="创建新文章", status_code=201)
async def create_text(
    request: TextCreateRequest,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    创建新文章（属于当前用户）
    
    - **text_title**: 文章标题
    
    需要认证：是
    """
    try:
        text_manager = OriginalTextManagerDB(session)
        
        # 创建文章（关联到当前用户）
        text = text_manager.add_text(request.text_title, user_id=current_user.user_id)
        
        return {
            "success": True,
            "message": "Text created successfully",
            "data": {
                "text_id": text.text_id,
                "text_title": text.text_title,
                "language": text.language,
                "sentence_count": len(text.text_by_sentence)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/", summary="搜索文章")
async def search_texts(
    keyword: str = Query(..., description="搜索关键词"),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    搜索文章（根据标题，仅限当前用户）
    
    - **keyword**: 搜索关键词
    
    需要认证：是
    """
    try:
        text_manager = OriginalTextManagerDB(session)
        # 只搜索当前用户的文章
        texts = text_manager.search_texts(keyword, user_id=current_user.user_id)
        
        return {
            "success": True,
            "data": {
                "texts": [
                    {
                        "text_id": t.text_id,
                        "text_title": t.text_title,
                        "sentence_count": 0  # 搜索结果不包含句子数
                    }
                    for t in texts
                ],
                "count": len(texts),
                "keyword": keyword
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{text_id}/sentences", summary="为文章添加句子", status_code=201)
async def add_sentence_to_text(
    text_id: int,
    sentence_body: str = Query(..., description="句子内容"),
    difficulty_level: Optional[str] = Query(None, description="难度等级：easy/hard"),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    为文章添加句子（仅限当前用户的文章）
    
    - **text_id**: 文章ID
    - **sentence_body**: 句子内容
    - **difficulty_level**: 难度等级（可选）
    
    需要认证：是
    """
    try:
        # 先验证文章是否存在且属于当前用户
        text_model = session.query(OriginalText).filter(
            OriginalText.text_id == text_id,
            OriginalText.user_id == current_user.user_id
        ).first()
        
        if not text_model:
            raise HTTPException(status_code=404, detail=f"Text ID {text_id} not found")
        
        text_manager = OriginalTextManagerDB(session)
        
        # 检查文章是否存在
        text = text_manager.get_text_by_id(text_id, include_sentences=False)
        if not text:
            raise HTTPException(status_code=404, detail=f"Text ID {text_id} not found")
        
        # 添加句子
        sentence = text_manager.add_sentence_to_text(
            text_id=text_id,
            sentence_text=sentence_body,
            difficulty_level=difficulty_level
        )
        
        return {
            "success": True,
            "message": "Sentence added successfully",
            "data": {
                "text_id": sentence.text_id,
                "sentence_id": sentence.sentence_id,
                "sentence_body": sentence.sentence_body,
                "difficulty_level": sentence.sentence_difficulty_level
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{text_id}/sentences", summary="获取文章的所有句子")
async def get_text_sentences(
    text_id: int,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    获取文章的所有句子（仅限当前用户的文章）
    
    - **text_id**: 文章ID
    
    需要认证：是
    """
    try:
        # 先验证文章是否存在且属于当前用户
        text_model = session.query(OriginalText).filter(
            OriginalText.text_id == text_id,
            OriginalText.user_id == current_user.user_id
        ).first()
        
        if not text_model:
            raise HTTPException(status_code=404, detail=f"Text ID {text_id} not found")
        
        text_manager = OriginalTextManagerDB(session)
        
        # 检查文章是否存在
        text = text_manager.get_text_by_id(text_id, include_sentences=False)
        if not text:
            raise HTTPException(status_code=404, detail=f"Text ID {text_id} not found")
        
        # 获取句子
        sentences = text_manager.get_sentences_by_text(text_id)
        
        return {
            "success": True,
            "data": {
                "text_id": text_id,
                "sentences": [
                    {
                        "sentence_id": s.sentence_id,
                        "sentence_body": s.sentence_body,
                        "difficulty_level": s.sentence_difficulty_level,
                        "grammar_annotations": list(s.grammar_annotations) if s.grammar_annotations else [],
                        "vocab_annotations": list(s.vocab_annotations) if s.vocab_annotations else []
                    }
                    for s in sentences
                ],
                "count": len(sentences)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{text_id}/sentences/{sentence_id}", summary="获取指定句子")
async def get_sentence(
    text_id: int,
    sentence_id: int,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定句子（仅限当前用户的文章）
    
    - **text_id**: 文章ID
    - **sentence_id**: 句子ID
    
    需要认证：是
    """
    try:
        # 先验证文章是否存在且属于当前用户
        text_model = session.query(OriginalText).filter(
            OriginalText.text_id == text_id,
            OriginalText.user_id == current_user.user_id
        ).first()
        
        if not text_model:
            raise HTTPException(status_code=404, detail=f"Text ID {text_id} not found")
        
        text_manager = OriginalTextManagerDB(session)
        sentence = text_manager.get_sentence(text_id, sentence_id)
        
        if not sentence:
            raise HTTPException(
                status_code=404, 
                detail=f"Sentence (text_id={text_id}, sentence_id={sentence_id}) not found"
            )
        
        return {
            "success": True,
            "data": {
                "text_id": sentence.text_id,
                "sentence_id": sentence.sentence_id,
                "sentence_body": sentence.sentence_body,
                "difficulty_level": sentence.sentence_difficulty_level,
                "grammar_annotations": list(sentence.grammar_annotations) if sentence.grammar_annotations else [],
                "vocab_annotations": list(sentence.vocab_annotations) if sentence.vocab_annotations else []
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary", summary="获取文章统计")
async def get_text_stats(
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    获取文章统计信息（仅限当前用户）
    
    返回：
    - total_texts: 总文章数
    - total_sentences: 总句子数
    
    需要认证：是
    """
    try:
        text_manager = OriginalTextManagerDB(session)
        stats = text_manager.get_text_stats(user_id=current_user.user_id)
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

