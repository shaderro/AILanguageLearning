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
from backend.data_managers.unified_notation_manager import get_unified_notation_manager
from database_system.database_manager import get_database_manager
from backend.api.auth_routes import get_current_user
from database_system.business_logic.models import User

# 依赖注入：数据库Session
def get_db_session():
    """提供数据库Session"""
    # 从环境变量读取环境配置（与其他 v2 路由保持一致）
    try:
        from backend.config import ENV
        environment = ENV
    except ImportError:
        import os
        environment = os.getenv("ENV", "development")
    # 使用按环境缓存的 DatabaseManager 单例
    db_manager = get_database_manager(environment)
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
    # 兼容字段：前端可能会传 user_id，但后端会强制使用 current_user.user_id
    user_id: Optional[str] = None
    text_id: int
    sentence_id: int
    token_id: int
    vocab_id: Optional[int] = None

class GrammarNotationRequest(BaseModel):
    """语法标注请求模型"""
    # 兼容字段：前端可能会传 user_id，但后端会强制使用 current_user.user_id
    user_id: Optional[str] = None
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
async def create_vocab_notation(request: VocabNotationRequest, current_user: User = Depends(get_current_user)):
    """创建词汇标注"""
    try:
        print(f"[API] Creating vocab notation: {request}")
        effective_user_id = str(current_user.user_id)
        
        manager = get_unified_notation_manager(use_database=True, use_legacy_compatibility=True)
        success = manager.mark_notation(
            notation_type="vocab",
            user_id=effective_user_id,
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
    user_id: Optional[int] = Query(None, description="用户ID（将被忽略，实际以当前登录用户为准）"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """获取词汇标注（使用数据库模式）"""
    try:
        # ✅ 强制按当前用户过滤
        effective_user_id = int(current_user.user_id)
        if user_id is not None and int(user_id) != effective_user_id:
            print(f"⚠️ [Notations] Ignoring user_id={user_id}, using current_user.user_id={effective_user_id}")
        print(f"[API] Getting vocab notations: text_id={text_id}, user_id={effective_user_id}")
        
        # 使用数据库ORM获取
        from database_system.business_logic.crud.notation_crud import VocabNotationCRUD
        
        crud = VocabNotationCRUD(session)
        
        # 获取该文章下的所有vocab notations
        all_notations = crud.get_by_text(text_id, effective_user_id)
        
        # 构建返回的notation列表，如果存在word_token_id，同时返回该word_token的所有token_ids
        print(f"[API] ========== 开始处理 {len(all_notations)} 个 vocab notations ==========")
        
        # 🔍 调试：检查数据库中是否有 WordToken 记录
        try:
            from database_system.business_logic.models import WordToken
            word_token_count = session.query(WordToken).filter(
                WordToken.text_id == text_id
            ).count()
            print(f"[API] 🔍 数据库中 text_id={text_id} 的 WordToken 记录数: {word_token_count}")
        except Exception as e:
            print(f"[API] ⚠️ 无法查询 WordToken 记录数: {e}")
        
        notation_list = []
        for n in all_notations:
            notation_data = {
                "notation_id": n.id,
                "user_id": n.user_id,
                "text_id": n.text_id,
                "sentence_id": n.sentence_id,
                "token_id": n.token_id,
                "vocab_id": n.vocab_id,
                "word_token_id": n.word_token_id,  # 新增：word_token_id（用于非空格语言的完整词标注）
                "created_at": n.created_at.isoformat() if n.created_at else None
            }
            
            # 🔧 如果存在word_token_id，查询该word_token的所有token_ids，以便前端显示完整下划线
            print(f"[API] 检查 notation {n.id}: word_token_id={n.word_token_id}, text_id={n.text_id}, sentence_id={n.sentence_id}")
            if n.word_token_id is not None:
                try:
                    from database_system.business_logic.models import WordToken
                    # 直接查询 WordToken 表（不依赖关系加载）
                    word_token_model = session.query(WordToken).filter(
                        WordToken.word_token_id == n.word_token_id,
                        WordToken.text_id == n.text_id,
                        WordToken.sentence_id == n.sentence_id
                    ).first()
                    print(f"[API] 数据库查询 word_token 结果: {word_token_model is not None}")
                    
                    if word_token_model:
                        # 处理 token_ids（JSON 类型，SQLAlchemy 会自动解析）
                        if hasattr(word_token_model, 'token_ids') and word_token_model.token_ids:
                            token_ids_list = word_token_model.token_ids if isinstance(word_token_model.token_ids, list) else list(word_token_model.token_ids) if word_token_model.token_ids else []
                            notation_data["word_token_token_ids"] = token_ids_list
                            print(f"[API] ✅ 为notation {n.id}添加word_token_token_ids: {token_ids_list}")
                        else:
                            print(f"[API] ⚠️ word_token_model 没有 token_ids 属性或为空")
                    else:
                        # 如果数据库 WordToken 表中没有，尝试从 OriginalTextManagerDB 加载（通过 DTO 转换）
                        print(f"[API] 数据库 WordToken 表中没有找到，尝试从 OriginalTextManagerDB 加载...")
                        try:
                            from backend.data_managers import OriginalTextManagerDB
                            text_manager_db = OriginalTextManagerDB(session)
                            original_text = text_manager_db.get_text_by_id(n.text_id, include_sentences=True)
                            print(f"[API] OriginalTextManagerDB 加载 text: {original_text is not None}")
                            if original_text and hasattr(original_text, 'text_by_sentence') and original_text.text_by_sentence:
                                print(f"[API] text 有 {len(original_text.text_by_sentence)} 个句子")
                                for sentence in original_text.text_by_sentence:
                                    if sentence.sentence_id == n.sentence_id:
                                        print(f"[API] 找到句子 {n.sentence_id}, 检查 word_tokens...")
                                        print(f"[API] 句子类型: {type(sentence)}, 有 word_tokens 属性: {hasattr(sentence, 'word_tokens')}")
                                        if hasattr(sentence, 'word_tokens'):
                                            print(f"[API] sentence.word_tokens 值: {sentence.word_tokens}, 类型: {type(sentence.word_tokens)}")
                                        
                                        if hasattr(sentence, 'word_tokens') and sentence.word_tokens:
                                            print(f"[API] 句子有 {len(sentence.word_tokens)} 个 word_tokens")
                                            for wt in sentence.word_tokens:
                                                print(f"[API] 检查 word_token: word_token_id={wt.word_token_id}, 目标={n.word_token_id}")
                                                if wt.word_token_id == n.word_token_id:
                                                    # 处理 token_ids（可能是 tuple 或 list）
                                                    token_ids_list = list(wt.token_ids) if isinstance(wt.token_ids, (tuple, list)) else [wt.token_ids] if wt.token_ids else []
                                                    notation_data["word_token_token_ids"] = token_ids_list
                                                    print(f"[API] ✅ 从 OriginalTextManagerDB 找到 word_token: word_token_id={wt.word_token_id}, token_ids={token_ids_list}")
                                                    break
                                        else:
                                            print(f"[API] ⚠️ 句子没有 word_tokens 或为空，尝试直接从数据库查询 WordToken 表...")
                                            # 如果 OriginalTextManagerDB 没有加载 word_tokens，直接从数据库查询
                                            try:
                                                from database_system.business_logic.models import WordToken as WordTokenModel
                                                # 查询该句子的所有 word_tokens
                                                word_tokens_in_db = session.query(WordTokenModel).filter(
                                                    WordTokenModel.text_id == n.text_id,
                                                    WordTokenModel.sentence_id == n.sentence_id
                                                ).all()
                                                print(f"[API] 直接从数据库查询到 {len(word_tokens_in_db)} 个 word_tokens")
                                                for wt_db in word_tokens_in_db:
                                                    if wt_db.word_token_id == n.word_token_id:
                                                        token_ids_list = wt_db.token_ids if isinstance(wt_db.token_ids, list) else list(wt_db.token_ids) if wt_db.token_ids else []
                                                        notation_data["word_token_token_ids"] = token_ids_list
                                                        print(f"[API] ✅ 直接从数据库找到 word_token: word_token_id={wt_db.word_token_id}, token_ids={token_ids_list}")
                                                        break
                                            except Exception as db_query_e:
                                                print(f"[API] ⚠️ 直接从数据库查询失败: {db_query_e}")
                                        break
                            else:
                                print(f"[API] ⚠️ OriginalTextManagerDB 返回的 text 为空或没有 sentences")
                        except Exception as db_e:
                            print(f"[API] ⚠️ 从 OriginalTextManagerDB 加载失败: {db_e}")
                            import traceback
                            traceback.print_exc()
                        
                        if "word_token_token_ids" not in notation_data:
                            print(f"[API] ⚠️ notation {n.id} 的 word_token 不存在（WordToken 表和 OriginalTextManagerDB 都没有）")
                except Exception as e:
                    print(f"[WARNING] 无法获取word_token的token_ids: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"[API] notation {n.id} 没有 word_token_id (为 None)")
            
            notation_list.append(notation_data)
        
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
    user_id: str = Query(..., description="用户ID（将被忽略，实际以当前登录用户为准）"),
    current_user: User = Depends(get_current_user),
):
    """删除词汇标注"""
    try:
        print(f"[API] Deleting vocab notation: {text_id}:{sentence_id}:{token_id}")
        
        effective_user_id = str(current_user.user_id)
        manager = get_unified_notation_manager(use_database=True, use_legacy_compatibility=True)
        notation_key = f"{text_id}:{sentence_id}:{token_id}"
        success = manager.delete_notation("vocab", effective_user_id, notation_key)
        
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
async def create_grammar_notation(request: GrammarNotationRequest, current_user: User = Depends(get_current_user)):
    """创建语法标注"""
    try:
        print(f"[API] Creating grammar notation: {request}")
        effective_user_id = str(current_user.user_id)
        
        manager = get_unified_notation_manager(use_database=True, use_legacy_compatibility=True)
        success = manager.mark_notation(
            notation_type="grammar",
            user_id=effective_user_id,
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
    user_id: Optional[int] = Query(None, description="用户ID（将被忽略，实际以当前登录用户为准）"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """获取语法标注（使用数据库模式）"""
    try:
        effective_user_id = int(current_user.user_id)
        if user_id is not None and int(user_id) != effective_user_id:
            print(f"⚠️ [Notations] Ignoring user_id={user_id}, using current_user.user_id={effective_user_id}")
        print(f"[API] Getting grammar notations: text_id={text_id}, user_id={effective_user_id}")
        
        # 使用数据库ORM获取
        from database_system.business_logic.crud.notation_crud import GrammarNotationCRUD
        
        crud = GrammarNotationCRUD(session)
        
        # 获取该文章下的所有grammar notations
        all_notations = crud.get_by_text(text_id, effective_user_id)
        
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
    user_id: str = Query("default_user", description="用户ID（将被忽略，实际以当前登录用户为准）"),
    current_user: User = Depends(get_current_user),
):
    """获取句子的所有语法标注详情（支持多个语法知识点）"""
    try:
        print(f"[API] Getting grammar notation details: {text_id}:{sentence_id}")
        
        # 使用 ORM 获取
        from database_system.database_manager import DatabaseManager
        from database_system.business_logic.crud.notation_crud import GrammarNotationCRUD
        
        try:
            from backend.config import ENV
            environment = ENV
        except ImportError:
            import os
            environment = os.getenv("ENV", "development")
        db_manager = DatabaseManager(environment)
        session = db_manager.get_session()
        
        try:
            crud = GrammarNotationCRUD(session)
            effective_user_id = int(current_user.user_id)
            notations = crud.get_by_sentence(text_id, sentence_id, effective_user_id)  # 🔧 修复：现在返回列表
            
            if notations and len(notations) > 0:
                # 🔧 修复：返回所有 notations 的列表（始终返回数组格式，支持多个语法知识点）
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
                    for n in notations
                ]
                
                # 🔧 始终返回数组格式，支持多个语法知识点
                session.close()
                return NotationResponse(
                    success=True,
                    data=notation_list,  # 数组格式（支持单个或多个语法知识点）
                    message=f"成功获取 {len(notation_list)} 个语法标注"
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
    user_id: str = Query(..., description="用户ID（将被忽略，实际以当前登录用户为准）"),
    current_user: User = Depends(get_current_user),
):
    """删除语法标注"""
    try:
        print(f"[API] Deleting grammar notation: {text_id}:{sentence_id}")
        
        effective_user_id = str(current_user.user_id)
        manager = get_unified_notation_manager(use_database=True, use_legacy_compatibility=True)
        notation_key = f"{text_id}:{sentence_id}"
        success = manager.delete_notation("grammar", effective_user_id, notation_key)
        
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
    user_id: Optional[str] = Query(None, description="用户ID（将被忽略，实际以当前登录用户为准）"),
    current_user: User = Depends(get_current_user),
):
    """获取所有类型的标注"""
    try:
        print(f"[API] Getting all notations: text_id={text_id}, user_id={user_id}")
        
        effective_user_id = str(current_user.user_id)
        manager = get_unified_notation_manager(use_database=True, use_legacy_compatibility=True)
        all_keys = manager.get_notations("all", text_id, effective_user_id)
        
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
    user_id: str = Query(..., description="用户ID（将被忽略，实际以当前登录用户为准）"),
    text_id: int = Query(..., description="文章ID"),
    sentence_id: int = Query(..., description="句子ID"),
    token_id: Optional[int] = Query(None, description="Token ID（词汇标注必需）"),
    current_user: User = Depends(get_current_user),
):
    """检查标注是否存在"""
    try:
        print(f"[API] Checking notation exists: type={notation_type}, {text_id}:{sentence_id}:{token_id}")
        
        effective_user_id = str(current_user.user_id)
        manager = get_unified_notation_manager(use_database=True, use_legacy_compatibility=True)
        exists = manager.is_notation_exists(notation_type, effective_user_id, text_id, sentence_id, token_id)
        
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
