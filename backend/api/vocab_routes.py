"""
词汇 API 路由 - 使用数据库版本的 VocabManager

提供词汇相关的 RESTful API 接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

# 导入数据库管理器
from database_system.database_manager import DatabaseManager
from database_system.business_logic.models import User, VocabExpression

# 导入认证依赖
from backend.api.auth_routes import get_current_user

# 导入数据库版本的 VocabManager
from backend.data_managers import VocabManagerDB

# 导入 DTO（用于类型提示和响应）
from backend.data_managers.data_classes_new import (
    VocabExpression as VocabDTO,
    VocabExpressionExample as VocabExampleDTO
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

class VocabCreateRequest(BaseModel):
    """创建词汇请求"""
    vocab_body: str = Field(..., description="词汇内容", example="challenging")
    explanation: str = Field(..., description="词汇解释", example="具有挑战性的")
    source: str = Field(default="manual", description="来源：auto/qa/manual")
    is_starred: bool = Field(default=False, description="是否收藏")


class VocabUpdateRequest(BaseModel):
    """更新词汇请求"""
    vocab_body: Optional[str] = Field(None, description="词汇内容")
    explanation: Optional[str] = Field(None, description="词汇解释")
    source: Optional[str] = Field(None, description="来源")
    is_starred: Optional[bool] = Field(None, description="是否收藏")


class VocabExampleCreateRequest(BaseModel):
    """创建词汇例句请求"""
    vocab_id: int = Field(..., description="词汇ID")
    text_id: int = Field(..., description="文章ID")
    sentence_id: int = Field(..., description="句子ID")
    context_explanation: str = Field(..., description="上下文解释")
    token_indices: List[int] = Field(default_factory=list, description="关联的token索引")


class VocabResponse(BaseModel):
    """词汇响应（基于 DTO）"""
    vocab_id: int
    vocab_body: str
    explanation: str
    source: str
    is_starred: bool
    examples: List[dict] = []

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
    prefix="/api/v2/vocab",
    tags=["vocab-db"],
    responses={404: {"description": "Not found"}},
)


# ==================== API 端点 ====================

@router.get("/", summary="获取所有词汇")
async def get_all_vocabs(
    skip: int = Query(default=0, ge=0, description="跳过的记录数"),
    limit: int = Query(default=100, ge=1, le=1000, description="返回的最大记录数"),
    starred_only: bool = Query(default=False, description="是否只返回收藏的词汇"),
    session: Session = Depends(get_db_session),
    current_user: 'User' = Depends(get_current_user)
):
    """
    获取当前用户的所有词汇（分页）
    
    - **skip**: 跳过的记录数（用于分页）
    - **limit**: 返回的最大记录数
    - **starred_only**: 是否只返回收藏的词汇
    
    需要认证：是
    """
    try:
        from database_system.business_logic.models import VocabExpression
        
        # 查询当前用户的词汇
        query = session.query(VocabExpression).filter(VocabExpression.user_id == current_user.user_id)
        
        if starred_only:
            query = query.filter(VocabExpression.is_starred == True)
        
        vocabs = query.offset(skip).limit(limit).all()
        
        return {
            "success": True,
            "data": {
                "vocabs": [
                    {
                        "vocab_id": v.vocab_id,
                        "vocab_body": v.vocab_body,
                        "explanation": v.explanation,
                        "source": v.source,
                        "is_starred": v.is_starred
                    }
                    for v in vocabs
                ],
                "count": len(vocabs),
                "skip": skip,
                "limit": limit
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{vocab_id}", summary="获取单个词汇")
async def get_vocab(
    vocab_id: int,
    include_examples: bool = Query(default=True, description="是否包含例句"),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    根据 ID 获取词汇
    
    - **vocab_id**: 词汇ID
    - **include_examples**: 是否包含例句
    
    需要认证：是
    """
    try:
        print(f"[API] Getting vocab {vocab_id}, include_examples={include_examples}, user_id={current_user.user_id}")
        
        # 验证词汇属于当前用户
        vocab_model = session.query(VocabExpression).filter(
            VocabExpression.vocab_id == vocab_id,
            VocabExpression.user_id == current_user.user_id
        ).first()
        
        if not vocab_model:
            print(f"[API] Vocab {vocab_id} not found for user {current_user.user_id}")
            raise HTTPException(status_code=404, detail=f"Vocab ID {vocab_id} not found")
        
        print(f"[API] Found vocab: {vocab_model.vocab_body}, examples count: {len(vocab_model.examples)}")
        if vocab_model.examples:
            for ex in vocab_model.examples:
                print(f"  - Example: text_id={ex.text_id}, sentence_id={ex.sentence_id}")
        
        result = {
            "success": True,
            "data": {
                "vocab_id": vocab_model.vocab_id,
                "vocab_body": vocab_model.vocab_body,
                "explanation": vocab_model.explanation,
                "source": vocab_model.source.value if hasattr(vocab_model.source, 'value') else vocab_model.source,
                "is_starred": vocab_model.is_starred,
                "examples": [
                    {
                        "vocab_id": ex.vocab_id,
                        "text_id": ex.text_id,
                        "sentence_id": ex.sentence_id,
                        "context_explanation": ex.context_explanation,
                        "token_indices": ex.token_indices
                    }
                    for ex in vocab_model.examples
                ] if include_examples else []
            }
        }
        print(f"[API] Returning vocab with {len(result['data']['examples'])} examples")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", summary="创建新词汇", status_code=201)
async def create_vocab(
    request: VocabCreateRequest,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    创建新词汇
    
    - **vocab_body**: 词汇内容
    - **explanation**: 词汇解释
    - **source**: 来源（auto/qa/manual）
    - **is_starred**: 是否收藏
    
    需要认证：是
    """
    try:
        # 检查当前用户是否已存在此词汇
        existing = session.query(VocabExpression).filter(
            VocabExpression.vocab_body == request.vocab_body,
            VocabExpression.user_id == current_user.user_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"Vocab '{request.vocab_body}' already exists with ID {existing.vocab_id}"
            )
        
        # 创建词汇（设置 user_id）
        from database_system.business_logic.models import SourceType
        vocab = VocabExpression(
            user_id=current_user.user_id,
            vocab_body=request.vocab_body,
            explanation=request.explanation,
            source=SourceType(request.source),
            is_starred=request.is_starred
        )
        session.add(vocab)
        session.commit()
        session.refresh(vocab)
        
        return {
            "success": True,
            "message": "Vocab created successfully",
            "data": {
                "vocab_id": vocab.vocab_id,
                "vocab_body": vocab.vocab_body,
                "explanation": vocab.explanation,
                "source": vocab.source,
                "is_starred": vocab.is_starred
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{vocab_id}", summary="更新词汇")
async def update_vocab(
    vocab_id: int,
    request: VocabUpdateRequest,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    更新词汇
    
    - **vocab_id**: 词汇ID
    - 其他字段：要更新的内容（仅传需要更新的字段）
    
    需要认证：是
    """
    try:
        # 验证词汇属于当前用户
        vocab = session.query(VocabExpression).filter(
            VocabExpression.vocab_id == vocab_id,
            VocabExpression.user_id == current_user.user_id
        ).first()
        
        if not vocab:
            raise HTTPException(status_code=404, detail=f"Vocab ID {vocab_id} not found")
        
        # 构建更新字典（只包含非 None 的字段）
        update_data = {
            k: v for k, v in request.dict().items() if v is not None
        }
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # 更新词汇
        for key, value in update_data.items():
            setattr(vocab, key, value)
        
        session.commit()
        session.refresh(vocab)
        
        if not vocab:
            raise HTTPException(status_code=404, detail=f"Vocab ID {vocab_id} not found")
        
        return {
            "success": True,
            "message": "Vocab updated successfully",
            "data": {
                "vocab_id": vocab.vocab_id,
                "vocab_body": vocab.vocab_body,
                "explanation": vocab.explanation,
                "source": vocab.source,
                "is_starred": vocab.is_starred
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{vocab_id}", summary="删除词汇")
async def delete_vocab(
    vocab_id: int,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    删除词汇
    
    - **vocab_id**: 词汇ID
    
    需要认证：是
    """
    try:
        # 验证词汇属于当前用户
        vocab = session.query(VocabExpression).filter(
            VocabExpression.vocab_id == vocab_id,
            VocabExpression.user_id == current_user.user_id
        ).first()
        
        if not vocab:
            raise HTTPException(status_code=404, detail=f"Vocab ID {vocab_id} not found")
        
        session.delete(vocab)
        session.commit()
        success = True
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Vocab ID {vocab_id} not found")
        
        return {
            "success": True,
            "message": f"Vocab ID {vocab_id} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{vocab_id}/star", summary="切换收藏状态")
async def toggle_star(
    vocab_id: int,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    切换词汇的收藏状态
    
    - **vocab_id**: 词汇ID
    
    需要认证：是
    """
    try:
        # 验证词汇属于当前用户
        vocab = session.query(VocabExpression).filter(
            VocabExpression.vocab_id == vocab_id,
            VocabExpression.user_id == current_user.user_id
        ).first()
        
        if not vocab:
            raise HTTPException(status_code=404, detail=f"Vocab ID {vocab_id} not found")
        
        vocab.is_starred = not vocab.is_starred
        session.commit()
        is_starred = vocab.is_starred
        
        return {
            "success": True,
            "message": f"Vocab star status toggled to {is_starred}",
            "data": {
                "vocab_id": vocab_id,
                "is_starred": is_starred
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/", summary="搜索词汇")
async def search_vocabs(
    keyword: str = Query(..., description="搜索关键词"),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    搜索词汇（根据词汇内容或解释）
    
    - **keyword**: 搜索关键词
    
    需要认证：是
    """
    try:
        # 搜索当前用户的词汇
        vocabs = session.query(VocabExpression).filter(
            VocabExpression.user_id == current_user.user_id,
            (VocabExpression.vocab_body.like(f"%{keyword}%")) | 
            (VocabExpression.explanation.like(f"%{keyword}%"))
        ).all()
        
        return {
            "success": True,
            "data": {
                "vocabs": [
                    {
                        "vocab_id": v.vocab_id,
                        "vocab_body": v.vocab_body,
                        "explanation": v.explanation,
                        "source": v.source,
                        "is_starred": v.is_starred
                    }
                    for v in vocabs
                ],
                "count": len(vocabs),
                "keyword": keyword
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/examples", summary="添加词汇例句")
async def create_vocab_example(
    request: VocabExampleCreateRequest,
    session: Session = Depends(get_db_session)
):
    """
    为词汇添加例句
    
    - **vocab_id**: 词汇ID
    - **text_id**: 文章ID
    - **sentence_id**: 句子ID
    - **context_explanation**: 上下文解释
    - **token_indices**: 关联的token索引列表
    """
    try:
        vocab_manager = VocabManagerDB(session)
        
        example = vocab_manager.add_vocab_example(
            vocab_id=request.vocab_id,
            text_id=request.text_id,
            sentence_id=request.sentence_id,
            context_explanation=request.context_explanation,
            token_indices=request.token_indices
        )
        
        return {
            "success": True,
            "message": "Vocab example created successfully",
            "data": {
                "vocab_id": example.vocab_id,
                "text_id": example.text_id,
                "sentence_id": example.sentence_id,
                "context_explanation": example.context_explanation,
                "token_indices": example.token_indices
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary", summary="获取词汇统计")
async def get_vocab_stats(
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的词汇统计信息
    
    返回：
    - total: 总词汇数
    - starred: 收藏词汇数
    - auto: 自动生成的词汇数
    - manual: 手动添加的词汇数
    
    需要认证：是
    """
    try:
        # 统计当前用户的词汇
        vocabs = session.query(VocabExpression).filter(
            VocabExpression.user_id == current_user.user_id
        ).all()
        
        from database_system.business_logic.models import SourceType
        stats = {
            "total": len(vocabs),
            "starred": len([v for v in vocabs if v.is_starred]),
            "auto": len([v for v in vocabs if v.source == SourceType.AUTO]),
            "manual": len([v for v in vocabs if v.source == SourceType.MANUAL])
        }
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
