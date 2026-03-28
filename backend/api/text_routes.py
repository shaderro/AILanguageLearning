"""
文章 API 路由 - 使用数据库版本的 OriginalTextManager

提供文章和句子相关的 RESTful API 接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from database_system.business_logic.models import User, OriginalText

# 导入认证依赖
from backend.api.auth_routes import get_current_user
from backend.api.db_deps import get_db_session

# 导入数据库版本的 OriginalTextManager
from backend.data_managers import OriginalTextManagerDB
from backend.data_managers.preset_articles import get_preset_difficulty_for_text
from backend.preprocessing.language_classification import (
    get_language_code,
    is_non_whitespace_language,
)

# 导入 DTO（用于类型提示和响应）
from backend.data_managers.data_classes_new import (
    OriginalText as TextDTO,
    Sentence as SentenceDTO
)


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
        # 🔧 添加调试日志：记录当前用户ID
        print(f"🔍 [TextAPI] get_all_texts called - user_id: {current_user.user_id}, email: {current_user.email}")
        
        from database_system.business_logic.models import Sentence, Token, OriginalText
        from sqlalchemy import func
        
        # 直接使用数据库查询，支持语言过滤
        # 🔧 使用 LEFT JOIN 获取最后打开时间，按最后打开时间排序（最新的在前）
        from database_system.business_logic.models import UserArticleAccess
        
        # 构建查询：包含 LEFT JOIN 获取最后打开时间
        query = session.query(
            OriginalText,
            UserArticleAccess.last_opened_at.label('last_opened_at')
        ).outerjoin(
            UserArticleAccess,
            (UserArticleAccess.text_id == OriginalText.text_id) & 
            (UserArticleAccess.user_id == current_user.user_id)
        ).filter(OriginalText.user_id == current_user.user_id)
        
        # 语言过滤
        if language and language != 'all':
            query = query.filter(OriginalText.language == language)
        
        # 🔧 添加调试日志：记录查询结果数量
        total_count = query.count()
        print(f"🔍 [TextAPI] Found {total_count} articles for user_id: {current_user.user_id}, language={language}")
        
        # 🔧 按最后打开时间排序（最新的在前），如果从未打开过，则按创建时间排序（最新的在前）
        query = query.order_by(
            func.coalesce(UserArticleAccess.last_opened_at, OriginalText.created_at).desc()
        )
        
        results = query.all()
        
        # 为每篇文章计算句子数和token数
        texts_with_stats = []
        for result in results:
            # result 是 Row 对象，包含 (OriginalText, last_opened_at)
            # 使用索引访问：result[0] 是 OriginalText 对象，result[1] 是 last_opened_at
            t = result[0]  # OriginalText 对象
            last_opened_at = result[1] if len(result) > 1 else None
            # 使用SQL查询统计句子数（使用 try-except 防止查询失败）
            try:
                sentence_count = session.query(func.count(Sentence.id)).filter(
                    Sentence.text_id == t.text_id
                ).scalar() or 0
            except Exception as e:
                print(f"⚠️ [TextAPI] Error counting sentences for text_id={t.text_id}: {e}")
                sentence_count = 0
            
            # 使用SQL查询统计token数（使用 try-except 防止查询失败）
            try:
                token_count = session.query(func.count(Token.token_id)).filter(
                    Token.text_id == t.text_id
                ).scalar() or 0
            except Exception as e:
                print(f"⚠️ [TextAPI] Error counting tokens for text_id={t.text_id}: {e}")
                token_count = 0
            
            texts_with_stats.append({
                "text_id": t.text_id,
                "text_title": t.text_title,
                "language": t.language,
                "difficulty": get_preset_difficulty_for_text(t.language, t.text_title),
                "processing_status": t.processing_status,  # 添加处理状态
                "total_sentences": sentence_count,
                "total_tokens": token_count,
                "sentence_count": sentence_count,  # 保持向后兼容
                "last_opened_at": last_opened_at.isoformat() if last_opened_at else None,  # 🔧 添加最后打开时间
                "sentences": [
                    {
                        "sentence_id": s.sentence_id,
                        "sentence_body": s.sentence_body,
                        "difficulty_level": s.sentence_difficulty_level
                    }
                    for s in (t.sentences if hasattr(t, 'sentences') else [])
                ] if include_sentences and hasattr(t, 'sentences') else []
            })
        
        return {
            "success": True,
            "data": {
                "texts": texts_with_stats,
                "count": len(texts_with_stats)
            }
        }
    except Exception as e:
        print(f"[ERROR] Failed to get all texts: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{text_id}/access", summary="记录文章访问（更新最后打开时间）")
async def record_article_access(
    text_id: int,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    记录用户打开文章（更新最后打开时间，用于跨设备排序）
    
    - **text_id**: 文章ID
    
    需要认证：是
    """
    try:
        from database_system.business_logic.models import UserArticleAccess
        
        # 验证文章是否存在且属于当前用户
        text_model = session.query(OriginalText).filter(
            OriginalText.text_id == text_id,
            OriginalText.user_id == current_user.user_id
        ).first()
        
        if not text_model:
            raise HTTPException(status_code=404, detail=f"Text ID {text_id} not found")
        
        # 查找或创建访问记录
        access = session.query(UserArticleAccess).filter(
            UserArticleAccess.user_id == current_user.user_id,
            UserArticleAccess.text_id == text_id
        ).first()
        
        if access:
            # 更新最后打开时间
            access.last_opened_at = datetime.now()
            access.updated_at = datetime.now()
        else:
            # 创建新记录
            access = UserArticleAccess(
                user_id=current_user.user_id,
                text_id=text_id,
                last_opened_at=datetime.now()
            )
            session.add(access)
        
        session.commit()
        
        return {
            "success": True,
            "message": "Article access recorded",
            "data": {
                "text_id": text_id,
                "last_opened_at": access.last_opened_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
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
        
        # 🔧 记录文章访问（异步，不阻塞）
        try:
            from database_system.business_logic.models import UserArticleAccess
            
            access = session.query(UserArticleAccess).filter(
                UserArticleAccess.user_id == current_user.user_id,
                UserArticleAccess.text_id == text_id
            ).first()
            
            if access:
                access.last_opened_at = datetime.now()
                access.updated_at = datetime.now()
            else:
                access = UserArticleAccess(
                    user_id=current_user.user_id,
                    text_id=text_id,
                    last_opened_at=datetime.now()
                )
                session.add(access)
            session.commit()
        except Exception as e:
            print(f"⚠️ [API] 记录文章访问失败: {e}")
            session.rollback()
            # 不抛出异常，继续处理文章获取
        
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
        
        # 🔧 安全处理 sentences（可能为 None 或空列表）
        # 注意：TextDTO 的字段是 text_by_sentence，不是 sentences
        text_by_sentence = getattr(text, 'text_by_sentence', None) or getattr(text, 'sentences', None) or []
        sentence_count = len(text_by_sentence) if text_by_sentence else 0
        
        print(f"[API] Found text {text_id}: {text.text_title}, sentences: {sentence_count}")
        print(f"[API] Debug: text type={type(text)}, has text_by_sentence={hasattr(text, 'text_by_sentence')}, has sentences={hasattr(text, 'sentences')}")
        if text_by_sentence:
            print(f"[API] Debug: first sentence type={type(text_by_sentence[0])}, has sentence_body={hasattr(text_by_sentence[0], 'sentence_body')}")
        
        language_code = get_language_code(text.language) if text.language else None
        is_non_whitespace = is_non_whitespace_language(language_code) if language_code else None

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
                                    "difficulty_level": t.difficulty_level,
                                    "global_token_id": getattr(t, "global_token_id", None),
                                    "pos_tag": getattr(t, "pos_tag", None),
                                    "lemma": getattr(t, "lemma", None),
                                    "word_token_id": getattr(t, "word_token_id", None),
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
                        ),
                        "word_tokens": (
                            [
                                {
                                    "word_token_id": wt.word_token_id,
                                    "word_body": wt.word_body,
                                    "token_ids": list(wt.token_ids),
                                    "pos_tag": wt.pos_tag,
                                    "lemma": wt.lemma,
                                    "linked_vocab_id": wt.linked_vocab_id,
                                }
                                for wt in getattr(s, "word_tokens", []) or []
                            ]
                            if getattr(s, "word_tokens", None)
                            else []
                        ),
                        "language": text.language,
                        "language_code": language_code,
                        "is_non_whitespace": is_non_whitespace,
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
                "sentence_count": len(text.sentences) if hasattr(text, 'sentences') and text.sentences else 0
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


class TextUpdateRequest(BaseModel):
    """更新文章请求"""
    text_title: Optional[str] = Field(None, description="文章标题")
    language: Optional[str] = Field(None, description="语言")
    processing_status: Optional[str] = Field(None, description="处理状态")


@router.put("/{text_id}", summary="更新文章")
async def update_text(
    text_id: int,
    request: TextUpdateRequest,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    更新文章（仅限当前用户的文章）
    
    - **text_id**: 文章ID
    - **text_title**: 新标题（可选）
    - **language**: 新语言（可选）
    - **processing_status**: 新处理状态（可选）
    
    需要认证：是
    """
    try:
        print(f"[API] 更新文章 {text_id}, 请求数据: {request.dict()}")
        
        # 先验证文章是否存在且属于当前用户
        text_model = session.query(OriginalText).filter(
            OriginalText.text_id == text_id,
            OriginalText.user_id == current_user.user_id
        ).first()
        
        if not text_model:
            print(f"[API] 文章 {text_id} 不存在或不属于用户 {current_user.user_id}")
            raise HTTPException(status_code=404, detail=f"Text ID {text_id} not found")
        
        print(f"[API] 找到文章: {text_model.text_title}, 准备更新")
        
        text_manager = OriginalTextManagerDB(session)
        updated_text = text_manager.update_text(
            text_id, 
            request.text_title, 
            request.language, 
            request.processing_status
        )
        
        if not updated_text:
            print(f"[API] 更新失败，文章 {text_id} 不存在")
            raise HTTPException(status_code=404, detail=f"Text ID {text_id} not found")
        
        print(f"[API] 文章已更新: {updated_text.text_title}")
        
        return {
            "success": True,
            "message": "Text updated successfully",
            "data": {
                "text_id": updated_text.text_id,
                "text_title": updated_text.text_title,
                "language": updated_text.language,
                "processing_status": text_model.processing_status
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{text_id}", summary="删除文章")
async def delete_text(
    text_id: int,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    删除文章（仅限当前用户的文章）
    
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
        success = text_manager.delete_text(text_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Text ID {text_id} not found")
        
        return {
            "success": True,
            "message": "Text deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

