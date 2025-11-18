"""
语法规则 API 路由 - 使用数据库版本的 GrammarRuleManager

提供语法规则相关的 RESTful API 接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import cast, String
from typing import List, Optional
from pydantic import BaseModel, Field

# 导入数据库管理器
from database_system.database_manager import DatabaseManager
from database_system.business_logic.models import User, GrammarRule

# 导入认证依赖
from backend.api.auth_routes import get_current_user

# 导入数据库版本的 GrammarRuleManager
from backend.data_managers import GrammarRuleManagerDB
from database_system.business_logic.models import Sentence

# 导入 DTO（用于类型提示和响应）
from backend.data_managers.data_classes_new import (
    GrammarRule as GrammarDTO,
    GrammarExample as GrammarExampleDTO
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
    print(f"[DEBUG] Created session, engine URL: {db_manager.get_engine().url}")
    try:
        yield session
        session.commit()  # 成功时提交事务
    except Exception as e:
        print(f"[ERROR] Session error: {e}")
        session.rollback()  # 失败时回滚事务
        raise e
    finally:
        session.close()  # 总是关闭 Session


# ==================== Pydantic 模型（请求/响应） ====================

class GrammarRuleCreateRequest(BaseModel):
    """创建语法规则请求"""
    name: str = Field(..., description="规则名称", example="德语定冠词变格")
    explanation: str = Field(..., description="规则解释", example="德语定冠词根据格、性、数变化")
    language: Optional[str] = Field(None, description="语言：中文、英文、德文")
    source: str = Field(default="manual", description="来源：auto/qa/manual")
    is_starred: bool = Field(default=False, description="是否收藏")


class GrammarRuleUpdateRequest(BaseModel):
    """更新语法规则请求"""
    name: Optional[str] = Field(None, description="规则名称")
    explanation: Optional[str] = Field(None, description="规则解释")
    language: Optional[str] = Field(None, description="语言：中文、英文、德文")
    source: Optional[str] = Field(None, description="来源")
    is_starred: Optional[bool] = Field(None, description="是否收藏")
    learn_status: Optional[str] = Field(None, description="学习状态：mastered/not_mastered")


class GrammarExampleCreateRequest(BaseModel):
    """创建语法例句请求"""
    rule_id: int = Field(..., description="规则ID")
    text_id: int = Field(..., description="文章ID")
    sentence_id: int = Field(..., description="句子ID")
    explanation_context: str = Field(..., description="上下文解释")


class GrammarRuleResponse(BaseModel):
    """语法规则响应（基于 DTO）"""
    rule_id: int
    name: str
    explanation: str
    language: Optional[str] = None
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
    prefix="/api/v2/grammar",
    tags=["grammar-db"],
    responses={404: {"description": "Not found"}},
)


# ==================== API 端点 ====================

@router.get("/", summary="获取所有语法规则")
async def get_all_grammar_rules(
    skip: int = Query(default=0, ge=0, description="跳过的记录数"),
    limit: int = Query(default=100, ge=1, le=1000, description="返回的最大记录数"),
    starred_only: bool = Query(default=False, description="是否只返回收藏的规则"),
    language: Optional[str] = Query(default=None, description="语言过滤：中文、英文、德文"),
    learn_status: Optional[str] = Query(default=None, description="学习状态过滤：all/mastered/not_mastered"),
    text_id: Optional[int] = Query(default=None, description="文章ID过滤：只返回有该文章example的语法规则"),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的所有语法规则（分页）
    
    - **skip**: 跳过的记录数（用于分页）
    - **limit**: 返回的最大记录数
    - **starred_only**: 是否只返回收藏的规则
    - **language**: 语言过滤（中文、英文、德文），None表示不过滤
    - **learn_status**: 学习状态过滤（all/mastered/not_mastered），None或'all'表示不过滤
    
    需要认证：是
    """
    try:
        from database_system.business_logic.models import LearnStatus
        
        print(f"🔍 [GrammarAPI] 查询参数: user_id={current_user.user_id}, language={language}, learn_status={learn_status}, starred_only={starred_only}, text_id={text_id}")
        
        # 查询当前用户的语法规则
        query = session.query(GrammarRule).filter(GrammarRule.user_id == current_user.user_id)
        
        if starred_only:
            query = query.filter(GrammarRule.is_starred == True)
        
        # 语言过滤
        if language and language != 'all':
            query = query.filter(GrammarRule.language == language)
            print(f"🔍 [GrammarAPI] 应用语言过滤: {language}")
        
        # 学习状态过滤
        # 🔧 修复：SQLite 中 Enum 存储为字符串，使用枚举对象进行比较
        if learn_status and learn_status != 'all':
            if learn_status == 'mastered':
                # 使用枚举对象进行比较（SQLAlchemy 会自动处理枚举转换）
                query = query.filter(GrammarRule.learn_status == LearnStatus.MASTERED)
                print(f"🔍 [GrammarAPI] 应用学习状态过滤: mastered (使用枚举对象比较)")
            elif learn_status == 'not_mastered':
                # 使用枚举对象进行比较（SQLAlchemy 会自动处理枚举转换）
                query = query.filter(GrammarRule.learn_status == LearnStatus.NOT_MASTERED)
                print(f"🔍 [GrammarAPI] 应用学习状态过滤: not_mastered (使用枚举对象比较)")
        else:
            print(f"🔍 [GrammarAPI] 不应用学习状态过滤 (learn_status={learn_status})")
        
        # 文章过滤：只返回有该文章example的语法规则
        if text_id is not None:
            from database_system.business_logic.models import GrammarExample
            # 使用 exists 子查询来过滤
            from sqlalchemy import exists
            query = query.filter(
                exists().where(
                    GrammarExample.rule_id == GrammarRule.rule_id,
                    GrammarExample.text_id == text_id
                )
            )
            print(f"🔍 [GrammarAPI] 应用文章过滤: text_id={text_id}")
        
        rules = query.offset(skip).limit(limit).all()
        print(f"🔍 [GrammarAPI] 查询结果: {len(rules)} 个语法规则")
        
        # 🔧 调试：打印前几个规则的 learn_status 值（用于排查过滤问题）
        if rules:
            for i, r in enumerate(rules[:3]):
                learn_status_value = r.learn_status.value if hasattr(r.learn_status, 'value') else str(r.learn_status)
                print(f"🔍 [GrammarAPI] 规则 {i+1} (ID={r.rule_id}): learn_status={learn_status_value} (type={type(r.learn_status)})")
        elif learn_status and learn_status != 'all':
            # 如果没有结果，打印调试信息
            print(f"⚠️ [GrammarAPI] 过滤后没有结果，检查所有规则的 learn_status...")
            all_rules = session.query(GrammarRule).filter(GrammarRule.user_id == current_user.user_id).limit(5).all()
            for r in all_rules:
                learn_status_value = r.learn_status.value if hasattr(r.learn_status, 'value') else str(r.learn_status)
                print(f"🔍 [GrammarAPI] 规则 ID={r.rule_id}: learn_status={learn_status_value} (期望: {learn_status})")
        
        return {
            "success": True,
            "data": [
                {
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,  # 前端期望的字段名
                    "rule_summary": r.rule_summary,  # 前端期望的字段名
                    "name": r.rule_name,  # 保留兼容性
                    "explanation": r.rule_summary,  # 保留兼容性
                    "language": r.language,
                    "source": r.source.value if hasattr(r.source, 'value') else r.source,
                    "is_starred": r.is_starred,
                    "learn_status": r.learn_status.value if hasattr(r.learn_status, 'value') else (str(r.learn_status) if r.learn_status else "not_mastered"),
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "updated_at": r.updated_at.isoformat() if r.updated_at else None
                }
                for r in rules
            ],
            "count": len(rules),
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{rule_id}", summary="获取单个语法规则")
async def get_grammar_rule(
    rule_id: int,
    include_examples: bool = Query(default=True, description="是否包含例句"),
    session: Session = Depends(get_db_session)
):
    """
    根据 ID 获取语法规则
    
    - **rule_id**: 规则ID
    - **include_examples**: 是否包含例句
    """
    try:
        print(f"[API] Getting grammar rule {rule_id}")
        
        # 🔧 直接从数据库模型获取，以便访问 created_at 和 updated_at 字段
        from database_system.business_logic.models import GrammarRule as GrammarModel
        grammar_model = session.query(GrammarModel).filter(GrammarModel.rule_id == rule_id).first()
        
        if not grammar_model:
            print(f"[API] Grammar rule {rule_id} not found")
            raise HTTPException(status_code=404, detail=f"Grammar Rule ID {rule_id} not found")
        
        print(f"[API] Found grammar rule: {grammar_model.rule_name}")

        # 为每个 example 尝试查找原句
        examples_data = []
        if include_examples and grammar_model.examples:
            for ex in grammar_model.examples:
                original_sentence = None
                try:
                    if ex.text_id is not None and ex.sentence_id is not None:
                        sentence_obj = session.query(Sentence).filter(
                            Sentence.text_id == ex.text_id,
                            Sentence.sentence_id == ex.sentence_id
                        ).first()
                        if sentence_obj:
                            original_sentence = sentence_obj.sentence_body
                except Exception as se:
                    print(f"⚠️ [GrammarAPI] 获取例句原句失败: text_id={ex.text_id}, sentence_id={ex.sentence_id}, error={se}")

                examples_data.append({
                    "rule_id": ex.rule_id,
                    "text_id": ex.text_id,
                    "sentence_id": ex.sentence_id,
                    "original_sentence": original_sentence,
                    "explanation_context": ex.explanation_context,
                })

        # 🔧 修复：返回前端期望的字段名（rule_name 和 rule_summary）
        return {
            "success": True,
            "data": {
                "rule_id": grammar_model.rule_id,
                "rule_name": grammar_model.rule_name,  # 前端期望 rule_name
                "rule_summary": grammar_model.rule_summary,  # 前端期望 rule_summary
                "name": grammar_model.rule_name,  # 保留兼容性
                "explanation": grammar_model.rule_summary,  # 保留兼容性
                "language": grammar_model.language,
                "source": grammar_model.source.value if hasattr(grammar_model.source, 'value') else str(grammar_model.source),
                "is_starred": grammar_model.is_starred,
                "learn_status": grammar_model.learn_status.value if hasattr(grammar_model.learn_status, 'value') else (str(grammar_model.learn_status) if grammar_model.learn_status else "not_mastered"),
                "created_at": grammar_model.created_at.isoformat() if hasattr(grammar_model, 'created_at') and grammar_model.created_at else None,
                "updated_at": grammar_model.updated_at.isoformat() if hasattr(grammar_model, 'updated_at') and grammar_model.updated_at else None,
                "examples": examples_data if include_examples else []
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to get grammar rule {rule_id}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", summary="创建新语法规则", status_code=201)
async def create_grammar_rule(
    request: GrammarRuleCreateRequest,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    创建新语法规则
    
    - **name**: 规则名称
    - **explanation**: 规则解释
    - **source**: 来源（auto/qa/manual）
    - **is_starred**: 是否收藏
    """
    try:
        grammar_manager = GrammarRuleManagerDB(session)
        
        # 检查是否已存在
        existing = grammar_manager.get_rule_by_name(request.name)
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"Grammar Rule '{request.name}' already exists with ID {existing.rule_id}"
            )
        
        # 创建规则
        rule = grammar_manager.add_new_rule(
            name=request.name,
            explanation=request.explanation,
            language=request.language,
            source=request.source,
            is_starred=request.is_starred,
            user_id=current_user.user_id
        )
        
        return {
            "success": True,
            "message": "Grammar Rule created successfully",
            "data": {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "explanation": rule.explanation,
                "language": rule.language,
                "source": rule.source,
                "is_starred": rule.is_starred
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{rule_id}", summary="更新语法规则")
async def update_grammar_rule(
    rule_id: int,
    request: GrammarRuleUpdateRequest,
    session: Session = Depends(get_db_session)
):
    """
    更新语法规则
    
    - **rule_id**: 规则ID
    - 其他字段：要更新的内容（仅传需要更新的字段）
    """
    try:
        from database_system.business_logic.models import LearnStatus
        
        grammar_manager = GrammarRuleManagerDB(session)
        
        # 构建更新字典（只包含非 None 的字段）
        update_data = {
            k: v for k, v in request.dict().items() if v is not None
        }
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        print(f"🔍 [GrammarAPI] 更新语法规则 {rule_id}, 更新数据: {update_data}")
        
        # 处理 learn_status：将字符串转换为枚举
        if 'learn_status' in update_data:
            learn_status_str = update_data['learn_status']
            print(f"🔍 [GrammarAPI] 处理 learn_status: {learn_status_str}")
            if learn_status_str == 'mastered':
                update_data['learn_status'] = LearnStatus.MASTERED
            elif learn_status_str == 'not_mastered':
                update_data['learn_status'] = LearnStatus.NOT_MASTERED
            else:
                # 尝试直接使用字符串值查找枚举
                try:
                    update_data['learn_status'] = LearnStatus(learn_status_str)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid learn_status: {learn_status_str}")
            print(f"🔍 [GrammarAPI] 转换后的 learn_status: {update_data['learn_status']}")
        
        # 更新规则
        rule = grammar_manager.update_rule(rule_id, **update_data)
        
        if not rule:
            raise HTTPException(status_code=404, detail=f"Grammar Rule ID {rule_id} not found")
        
        print(f"✅ [GrammarAPI] 语法规则 {rule_id} 更新成功")
        
        return {
            "success": True,
            "message": "Grammar Rule updated successfully",
            "data": {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "explanation": rule.explanation,
                "source": rule.source.value if hasattr(rule.source, 'value') else str(rule.source),
                "is_starred": rule.is_starred,
                "learn_status": rule.learn_status.value if hasattr(rule.learn_status, 'value') else (str(rule.learn_status) if rule.learn_status else "not_mastered")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = str(e)
        traceback_str = traceback.format_exc()
        print(f"❌ [GrammarAPI] 更新语法规则错误详情: {error_detail}")
        print(f"❌ [GrammarAPI] 更新语法规则错误堆栈:\n{traceback_str}")
        raise HTTPException(status_code=500, detail=error_detail)


@router.delete("/{rule_id}", summary="删除语法规则")
async def delete_grammar_rule(
    rule_id: int,
    session: Session = Depends(get_db_session)
):
    """
    删除语法规则
    
    - **rule_id**: 规则ID
    """
    try:
        grammar_manager = GrammarRuleManagerDB(session)
        success = grammar_manager.delete_rule(rule_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Grammar Rule ID {rule_id} not found")
        
        return {
            "success": True,
            "message": f"Grammar Rule ID {rule_id} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{rule_id}/star", summary="切换收藏状态")
async def toggle_star(
    rule_id: int,
    session: Session = Depends(get_db_session)
):
    """
    切换语法规则的收藏状态
    
    - **rule_id**: 规则ID
    """
    try:
        grammar_manager = GrammarRuleManagerDB(session)
        is_starred = grammar_manager.toggle_star(rule_id)
        
        return {
            "success": True,
            "message": f"Grammar Rule star status toggled to {is_starred}",
            "data": {
                "rule_id": rule_id,
                "is_starred": is_starred
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/", summary="搜索语法规则")
async def search_grammar_rules(
    keyword: str = Query(..., description="搜索关键词"),
    session: Session = Depends(get_db_session)
):
    """
    搜索语法规则（根据名称或解释）
    
    - **keyword**: 搜索关键词
    """
    try:
        grammar_manager = GrammarRuleManagerDB(session)
        rules = grammar_manager.search_rules(keyword)
        
        return {
            "success": True,
            "data": {
                "rules": [
                    {
                        "rule_id": r.rule_id,
                        "name": r.name,
                        "explanation": r.explanation,
                        "source": r.source,
                        "is_starred": r.is_starred
                    }
                    for r in rules
                ],
                "count": len(rules),
                "keyword": keyword
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/examples", summary="添加语法例句")
async def create_grammar_example(
    request: GrammarExampleCreateRequest,
    session: Session = Depends(get_db_session)
):
    """
    为语法规则添加例句
    
    - **rule_id**: 规则ID
    - **text_id**: 文章ID
    - **sentence_id**: 句子ID
    - **explanation_context**: 上下文解释
    """
    try:
        grammar_manager = GrammarRuleManagerDB(session)
        
        example = grammar_manager.add_grammar_example(
            rule_id=request.rule_id,
            text_id=request.text_id,
            sentence_id=request.sentence_id,
            explanation_context=request.explanation_context
        )
        
        return {
            "success": True,
            "message": "Grammar Example created successfully",
            "data": {
                "rule_id": example.rule_id,
                "text_id": example.text_id,
                "sentence_id": example.sentence_id,
                "explanation_context": example.explanation_context
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary", summary="获取语法规则统计")
async def get_grammar_stats(
    session: Session = Depends(get_db_session)
):
    """
    获取语法规则统计信息
    
    返回：
    - total: 总规则数
    - starred: 收藏规则数
    - auto: 自动生成的规则数
    - manual: 手动添加的规则数
    - qa: QA生成的规则数
    """
    try:
        grammar_manager = GrammarRuleManagerDB(session)
        stats = grammar_manager.get_grammar_stats()
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

