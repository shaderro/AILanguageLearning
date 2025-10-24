#!/usr/bin/env python3
"""
标注 API 路由
提供 VocabNotation 和 GrammarNotation 的 API 端点
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

# 导入统一管理器
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from data_managers.unified_notation_manager import get_unified_notation_manager

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
        
        manager = get_unified_notation_manager(use_database=False, use_legacy_compatibility=True)
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
    user_id: Optional[str] = Query(None, description="用户ID")
):
    """获取词汇标注"""
    try:
        print(f"[API] Getting vocab notations: text_id={text_id}, user_id={user_id}")
        
        manager = get_unified_notation_manager(use_database=False, use_legacy_compatibility=True)
        keys = manager.get_notations("vocab", text_id, user_id)
        
        return NotationResponse(
            success=True,
            data={
                "notations": list(keys),
                "count": len(keys),
                "type": "vocab"
            },
            message=f"成功获取 {len(keys)} 个词汇标注"
        )
        
    except Exception as e:
        print(f"[ERROR] Failed to get vocab notations: {e}")
        return NotationResponse(
            success=False,
            error=f"获取词汇标注失败: {str(e)}"
        )

@router.get("/vocab/{text_id}/{sentence_id}/{token_id}", response_model=NotationResponse)
async def get_vocab_notation_details(
    text_id: int,
    sentence_id: int,
    token_id: int,
    user_id: str = Query(..., description="用户ID")
):
    """获取词汇标注详情"""
    try:
        print(f"[API] Getting vocab notation details: {text_id}:{sentence_id}:{token_id}")
        
        manager = get_unified_notation_manager(use_database=False, use_legacy_compatibility=True)
        details = manager.get_notation_details("vocab", user_id, text_id, sentence_id, token_id)
        
        if details:
            return NotationResponse(
                success=True,
                data=details.__dict__,
                message="成功获取词汇标注详情"
            )
        else:
            return NotationResponse(
                success=False,
                error="词汇标注不存在"
            )
            
    except Exception as e:
        print(f"[ERROR] Failed to get vocab notation details: {e}")
        return NotationResponse(
            success=False,
            error=f"获取词汇标注详情失败: {str(e)}"
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
        
        manager = get_unified_notation_manager(use_database=False, use_legacy_compatibility=True)
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
        
        manager = get_unified_notation_manager(use_database=False, use_legacy_compatibility=True)
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
    user_id: Optional[str] = Query(None, description="用户ID")
):
    """获取语法标注"""
    try:
        print(f"[API] Getting grammar notations: text_id={text_id}, user_id={user_id}")
        
        manager = get_unified_notation_manager(use_database=False, use_legacy_compatibility=True)
        keys = manager.get_notations("grammar", text_id, user_id)
        
        return NotationResponse(
            success=True,
            data={
                "notations": list(keys),
                "count": len(keys),
                "type": "grammar"
            },
            message=f"成功获取 {len(keys)} 个语法标注"
        )
        
    except Exception as e:
        print(f"[ERROR] Failed to get grammar notations: {e}")
        return NotationResponse(
            success=False,
            error=f"获取语法标注失败: {str(e)}"
        )

@router.get("/grammar/{text_id}/{sentence_id}", response_model=NotationResponse)
async def get_grammar_notation_details(
    text_id: int,
    sentence_id: int,
    user_id: str = Query(..., description="用户ID")
):
    """获取语法标注详情"""
    try:
        print(f"[API] Getting grammar notation details: {text_id}:{sentence_id}")
        
        manager = get_unified_notation_manager(use_database=False, use_legacy_compatibility=True)
        details = manager.get_notation_details("grammar", user_id, text_id, sentence_id)
        
        if details:
            return NotationResponse(
                success=True,
                data=details.__dict__,
                message="成功获取语法标注详情"
            )
        else:
            return NotationResponse(
                success=False,
                error="语法标注不存在"
            )
            
    except Exception as e:
        print(f"[ERROR] Failed to get grammar notation details: {e}")
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
        
        manager = get_unified_notation_manager(use_database=False, use_legacy_compatibility=True)
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
        
        manager = get_unified_notation_manager(use_database=False, use_legacy_compatibility=True)
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
        
        manager = get_unified_notation_manager(use_database=False, use_legacy_compatibility=True)
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
