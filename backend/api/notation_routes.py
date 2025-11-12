#!/usr/bin/env python3
"""
标注 API 路由
提供 VocabNotation 和 GrammarNotation 的 API 端点
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from sqlalchemy.orm import Session

# 导入统一管理器
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from data_managers.unified_notation_manager import get_unified_notation_manager
from database_system.database_manager import DatabaseManager

# 依赖注入：数据库Session
def get_db_session():
    """提供数据库Session"""
    db_manager = DatabaseManager('development')
    session = db_manager.get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

router = APIRouter(prefix="/api/v2/notations", tags=["notations"])

# ==================== 请求/响应模型 ====================

class VocabNotationRequest(BaseModel):
    """词汇标注请求模型"""
    user_id: str
    text_id: int
    sentence_id: int
    token_id: int
    vocab_id: Optional[int] = None

class GrammarNotationRequest(BaseModel):
    """语法标注请求模型"""
    user_id: str
    text_id: int
    sentence_id: int
    grammar_id: Optional[int] = None
    marked_token_ids: Optional[List[int]] = None

class NotationResponse(BaseModel):
    """标注响应模型"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None

# ==================== 词汇标注 API ====================

@router.post("/vocab", response_model=NotationResponse)
async def create_vocab_notation(request: VocabNotationRequest):
    """创建词汇标注"""
    try:
        print(f"[API] Creating vocab notation: {request}")
        
        manager = get_unified_notation_manager(use_database=True, use_legacy_compatibility=True)
        success = manager.mark_notation(
            notation_type="vocab",
            user_id=request.user_id,
            text_id=request.text_id,
            sentence_id=request.sentence_id,
            token_id=request.token_id,
            vocab_id=request.vocab_id
        )
        
        if success:
            return NotationResponse(
                success=True,
                data={"notation_key": f"{request.text_id}:{request.sentence_id}:{request.token_id}"},
                message="词汇标注创建成功"
            )
        else:
            return NotationResponse(
                success=False,
                error="词汇标注创建失败"
            )
            
    except Exception as e:
        print(f"[ERROR] Failed to create vocab notation: {e}")
        return NotationResponse(
            success=False,
            error=f"词汇标注创建失败: {str(e)}"
        )

@router.get("/vocab", response_model=NotationResponse)
async def get_vocab_notations(
    text_id: int = Query(..., description="文章ID"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    session: Session = Depends(get_db_session)
):
    """获取词汇标注（使用数据库模式）"""
    try:
        print(f"[API] Getting vocab notations: text_id={text_id}, user_id={user_id}")
        
        # 使用数据库ORM获取
        from database_system.business_logic.crud.notation_crud import VocabNotationCRUD
        
        crud = VocabNotationCRUD(session)
        
        # 获取该文章下的所有vocab notations
        all_notations = crud.get_by_text(text_id, user_id)
        
        notation_list = [
            {
                "notation_id": n.id,
                "user_id": n.user_id,
                "text_id": n.text_id,
                "sentence_id": n.sentence_id,
                "token_id": n.token_id,
                "vocab_id": n.vocab_id,
                "created_at": n.created_at.isoformat() if n.created_at else None
            }
            for n in all_notations
        ]
        
        print(f"[API] Found {len(notation_list)} vocab notations")
        
        return NotationResponse(
            success=True,
            data={
                "notations": notation_list,
                "count": len(notation_list),
                "type": "vocab",
                "source": "database"
            },
            message=f"成功获取 {len(notation_list)} 个词汇标注"
        )
        
    except Exception as e:
        print(f"[ERROR] Failed to get vocab notations: {e}")
        import traceback
        traceback.print_exc()
        return NotationResponse(
            success=False,
            error=f"获取词汇标注失败: {str(e)}"
        )

@router.get("/vocab/{text_id}/{sentence_id}", response_model=NotationResponse)
async def get_sentence_vocab_notations(
    text_id: int,
    sentence_id: int,
    user_id: str = Query("default_user", description="用户ID")
):
    """获取句子的所有词汇标注（使用 JSON 模式）"""
    try:
        print(f"[API] Getting vocab notations for sentence: {text_id}:{sentence_id}")
        
        # 使用 JSON 模式
        from backend.data_managers.vocab_notation_manager import get_vocab_notation_manager
        vocab_mgr = get_vocab_notation_manager(use_database=False)
        
        import json
        import os
        json_file = vocab_mgr._get_json_file_path(user_id)
        
        notation_list = []
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                all_notations = json.load(f)
            # 过滤该句子的 notations
            notation_list = [
                n for n in all_notations 
                if n.get('text_id') == text_id and n.get('sentence_id') == sentence_id
            ]
        
        return NotationResponse(
            success=True,
            data=notation_list,
            message=f"成功获取 {len(notation_list)} 个词汇标注"
        )
            
    except Exception as e:
        print(f"[ERROR] Failed to get sentence vocab notations: {e}")
        import traceback
        traceback.print_exc()
        return NotationResponse(
            success=False,
            error=f"获取句子词汇标注失败: {str(e)}"
        )

@router.delete("/vocab/{text_id}/{sentence_id}/{token_id}", response_model=NotationResponse)
async def delete_vocab_notation(
    text_id: int,
    sentence_id: int,
    token_id: int,
    user_id: str = Query(..., description="用户ID")
):
    """删除词汇标注"""
    try:
        print(f"[API] Deleting vocab notation: {text_id}:{sentence_id}:{token_id}")
        
        manager = get_unified_notation_manager(use_database=True, use_legacy_compatibility=True)
        notation_key = f"{text_id}:{sentence_id}:{token_id}"
        success = manager.delete_notation("vocab", user_id, notation_key)
        
        if success:
            return NotationResponse(
                success=True,
                message="词汇标注删除成功"
            )
        else:
            return NotationResponse(
                success=False,
                error="词汇标注删除失败"
            )
            
    except Exception as e:
        print(f"[ERROR] Failed to delete vocab notation: {e}")
        return NotationResponse(
            success=False,
            error=f"词汇标注删除失败: {str(e)}"
        )

# ==================== 语法标注 API ====================

@router.post("/grammar", response_model=NotationResponse)
async def create_grammar_notation(request: GrammarNotationRequest):
    """创建语法标注"""
    try:
        print(f"[API] Creating grammar notation: {request}")
        
        manager = get_unified_notation_manager(use_database=True, use_legacy_compatibility=True)
        success = manager.mark_notation(
            notation_type="grammar",
            user_id=request.user_id,
            text_id=request.text_id,
            sentence_id=request.sentence_id,
            grammar_id=request.grammar_id,
            marked_token_ids=request.marked_token_ids or []
        )
        
        if success:
            return NotationResponse(
                success=True,
                data={"notation_key": f"{request.text_id}:{request.sentence_id}"},
                message="语法标注创建成功"
            )
        else:
            return NotationResponse(
                success=False,
                error="语法标注创建失败"
            )
            
    except Exception as e:
        print(f"[ERROR] Failed to create grammar notation: {e}")
        return NotationResponse(
            success=False,
            error=f"语法标注创建失败: {str(e)}"
        )

@router.get("/grammar", response_model=NotationResponse)
async def get_grammar_notations(
    text_id: int = Query(..., description="文章ID"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    session: Session = Depends(get_db_session)
):
    """获取语法标注（使用数据库模式）"""
    try:
        print(f"[API] Getting grammar notations: text_id={text_id}, user_id={user_id}")
        
        # 使用数据库ORM获取
        from database_system.business_logic.crud.notation_crud import GrammarNotationCRUD
        
        crud = GrammarNotationCRUD(session)
        
        # 获取该文章下的所有grammar notations
        all_notations = crud.get_by_text(text_id, user_id)
        
        notation_list = [
            {
                "notation_id": n.id,
                "user_id": n.user_id,
                "text_id": n.text_id,
                "sentence_id": n.sentence_id,
                "grammar_id": n.grammar_id,
                "marked_token_ids": n.marked_token_ids or [],
                "created_at": n.created_at.isoformat() if n.created_at else None
            }
            for n in all_notations
        ]
        
        print(f"[API] Found {len(notation_list)} grammar notations")
        
        return NotationResponse(
            success=True,
            data={
                "notations": notation_list,
                "count": len(notation_list),
                "type": "grammar",
                "source": "database"
            },
            message=f"成功获取 {len(notation_list)} 个语法标注"
        )
        
    except Exception as e:
        print(f"[ERROR] Failed to get grammar notations: {e}")
        import traceback
        traceback.print_exc()
        return NotationResponse(
            success=False,
            error=f"获取语法标注失败: {str(e)}"
        )

@router.get("/grammar/{text_id}/{sentence_id}", response_model=NotationResponse)
async def get_grammar_notation_details(
    text_id: int,
    sentence_id: int,
    user_id: str = Query("default_user", description="用户ID")
):
    """获取语法标注详情"""
    try:
        print(f"[API] Getting grammar notation details: {text_id}:{sentence_id}")
        
        # 使用 ORM 获取
        from database_system.database_manager import DatabaseManager
        from database_system.business_logic.crud.notation_crud import GrammarNotationCRUD
        
        db_manager = DatabaseManager('development')
        session = db_manager.get_session()
        
        try:
            crud = GrammarNotationCRUD(session)
            notation = crud.get_by_sentence(text_id, sentence_id, user_id)
            
            if notation:
                data = {
                    "user_id": notation.user_id,
                    "text_id": notation.text_id,
                    "sentence_id": notation.sentence_id,
                    "grammar_id": notation.grammar_id,
                    "marked_token_ids": notation.marked_token_ids,
                    "created_at": notation.created_at.isoformat() if notation.created_at else None
                }
                session.close()
                return NotationResponse(
                    success=True,
                    data=data,
                    message="成功获取语法标注详情"
                )
            else:
                session.close()
                return NotationResponse(
                    success=True,
                    data=None,
                    message="语法标注不存在"
                )
        except Exception as e:
            session.close()
            raise e
            
    except Exception as e:
        print(f"[ERROR] Failed to get grammar notation details: {e}")
        import traceback
        traceback.print_exc()
        return NotationResponse(
            success=False,
            error=f"获取语法标注详情失败: {str(e)}"
        )

@router.delete("/grammar/{text_id}/{sentence_id}", response_model=NotationResponse)
async def delete_grammar_notation(
    text_id: int,
    sentence_id: int,
    user_id: str = Query(..., description="用户ID")
):
    """删除语法标注"""
    try:
        print(f"[API] Deleting grammar notation: {text_id}:{sentence_id}")
        
        manager = get_unified_notation_manager(use_database=True, use_legacy_compatibility=True)
        notation_key = f"{text_id}:{sentence_id}"
        success = manager.delete_notation("grammar", user_id, notation_key)
        
        if success:
            return NotationResponse(
                success=True,
                message="语法标注删除成功"
            )
        else:
            return NotationResponse(
                success=False,
                error="语法标注删除失败"
            )
            
    except Exception as e:
        print(f"[ERROR] Failed to delete grammar notation: {e}")
        return NotationResponse(
            success=False,
            error=f"语法标注删除失败: {str(e)}"
        )

# ==================== 统一查询 API ====================

@router.get("/all", response_model=NotationResponse)
async def get_all_notations(
    text_id: int = Query(..., description="文章ID"),
    user_id: Optional[str] = Query(None, description="用户ID")
):
    """获取所有类型的标注"""
    try:
        print(f"[API] Getting all notations: text_id={text_id}, user_id={user_id}")
        
        manager = get_unified_notation_manager(use_database=True, use_legacy_compatibility=True)
        all_keys = manager.get_notations("all", text_id, user_id)
        
        return NotationResponse(
            success=True,
            data={
                "notations": list(all_keys),
                "count": len(all_keys),
                "type": "all"
            },
            message=f"成功获取 {len(all_keys)} 个标注"
        )
        
    except Exception as e:
        print(f"[ERROR] Failed to get all notations: {e}")
        return NotationResponse(
            success=False,
            error=f"获取所有标注失败: {str(e)}"
        )

@router.get("/check", response_model=NotationResponse)
async def check_notation_exists(
    notation_type: str = Query(..., description="标注类型: vocab 或 grammar"),
    user_id: str = Query(..., description="用户ID"),
    text_id: int = Query(..., description="文章ID"),
    sentence_id: int = Query(..., description="句子ID"),
    token_id: Optional[int] = Query(None, description="Token ID（词汇标注必需）")
):
    """检查标注是否存在"""
    try:
        print(f"[API] Checking notation exists: type={notation_type}, {text_id}:{sentence_id}:{token_id}")
        
        manager = get_unified_notation_manager(use_database=True, use_legacy_compatibility=True)
        exists = manager.is_notation_exists(notation_type, user_id, text_id, sentence_id, token_id)
        
        return NotationResponse(
            success=True,
            data={"exists": exists},
            message=f"标注存在性检查完成"
        )
        
    except Exception as e:
        print(f"[ERROR] Failed to check notation exists: {e}")
        return NotationResponse(
            success=False,
            error=f"标注存在性检查失败: {str(e)}"
        )
