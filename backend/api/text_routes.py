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
    session: Session = Depends(get_db_session)
):
    """
    获取所有文章
    
    - **include_sentences**: 是否包含句子（默认不包含，提升性能）
    """
    try:
        text_manager = OriginalTextManagerDB(session)
        texts = text_manager.get_all_texts(include_sentences=include_sentences)
        
        return {
            "success": True,
            "data": {
                "texts": [
                    {
                        "text_id": t.text_id,
                        "text_title": t.text_title,
                        "sentence_count": len(t.text_by_sentence) if include_sentences else 0,
                        "sentences": [
                            {
                                "sentence_id": s.sentence_id,
                                "sentence_body": s.sentence_body,
                                "difficulty_level": s.sentence_difficulty_level
                            }
                            for s in t.text_by_sentence
                        ] if include_sentences else []
                    }
                    for t in texts
                ],
                "count": len(texts)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{text_id}", summary="获取单个文章")
async def get_text(
    text_id: int,
    include_sentences: bool = Query(default=True, description="是否包含句子列表"),
    session: Session = Depends(get_db_session)
):
    """
    根据 ID 获取文章
    
    - **text_id**: 文章ID
    - **include_sentences**: 是否包含句子
    """
    try:
        text_manager = OriginalTextManagerDB(session)
        text = text_manager.get_text_by_id(text_id, include_sentences=include_sentences)
        
        if not text:
            raise HTTPException(status_code=404, detail=f"Text ID {text_id} not found")
        
        return {
            "success": True,
            "data": {
                "text_id": text.text_id,
                "text_title": text.text_title,
                "sentence_count": len(text.text_by_sentence),
                "sentences": [
                    {
                        "sentence_id": s.sentence_id,
                        "sentence_body": s.sentence_body,
                        "difficulty_level": s.sentence_difficulty_level,
                        "grammar_annotations": list(s.grammar_annotations) if s.grammar_annotations else [],
                        "vocab_annotations": list(s.vocab_annotations) if s.vocab_annotations else []
                    }
                    for s in text.text_by_sentence
                ] if include_sentences else []
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", summary="创建新文章", status_code=201)
async def create_text(
    request: TextCreateRequest,
    session: Session = Depends(get_db_session)
):
    """
    创建新文章
    
    - **text_title**: 文章标题
    """
    try:
        text_manager = OriginalTextManagerDB(session)
        
        # 创建文章
        text = text_manager.add_text(request.text_title)
        
        return {
            "success": True,
            "message": "Text created successfully",
            "data": {
                "text_id": text.text_id,
                "text_title": text.text_title,
                "sentence_count": len(text.text_by_sentence)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/", summary="搜索文章")
async def search_texts(
    keyword: str = Query(..., description="搜索关键词"),
    session: Session = Depends(get_db_session)
):
    """
    搜索文章（根据标题）
    
    - **keyword**: 搜索关键词
    """
    try:
        text_manager = OriginalTextManagerDB(session)
        texts = text_manager.search_texts(keyword)
        
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
    session: Session = Depends(get_db_session)
):
    """
    为文章添加句子
    
    - **text_id**: 文章ID
    - **sentence_body**: 句子内容
    - **difficulty_level**: 难度等级（可选）
    """
    try:
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
    session: Session = Depends(get_db_session)
):
    """
    获取文章的所有句子
    
    - **text_id**: 文章ID
    """
    try:
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
    session: Session = Depends(get_db_session)
):
    """
    获取指定句子
    
    - **text_id**: 文章ID
    - **sentence_id**: 句子ID
    """
    try:
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
    session: Session = Depends(get_db_session)
):
    """
    获取文章统计信息
    
    返回：
    - total_texts: 总文章数
    - total_sentences: 总句子数
    """
    try:
        text_manager = OriginalTextManagerDB(session)
        stats = text_manager.get_text_stats()
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

