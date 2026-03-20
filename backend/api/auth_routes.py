"""
认证 API 路由
提供注册、登录、当前用户等认证相关接口
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, sessionmaker
from pydantic import BaseModel, Field
from typing import Optional

# 导入数据库管理器（按环境缓存单例）
from database_system.database_manager import get_database_manager
from database_system.business_logic.models import User
from backend.api.db_deps import get_db_session

# 导入认证工具
from backend.utils.auth import (
    hash_password, 
    verify_password, 
    create_access_token, 
    decode_access_token,
    create_password_reset_token,
    decode_password_reset_token
)


# ==================== 依赖注入 ====================
# get_db_session 见 backend.api.db_deps（全项目共用，保证与路由层同请求只开一个 Session）

# SessionLocal 用于临时调试接口
def _get_session_local():
    """创建 SessionLocal（用于临时调试接口）"""
    try:
        from backend.config import ENV
        environment = ENV
    except ImportError:
        import os
        environment = os.getenv("ENV", "development")
    
    # 复用与 get_db_session 相同的 DatabaseManager 单例 / engine
    db_manager = get_database_manager(environment)
    engine = db_manager.get_engine()
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return SessionLocal

SessionLocal = _get_session_local()


# HTTP Bearer token 认证
# auto_error=False: 如果没有token，不自动抛出错误，返回None
# 这样可以返回401而不是403
security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: Session = Depends(get_db_session)
) -> User:
    """
    从 JWT token 中获取当前用户
    
    用法：
        @router.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.user_id}
    """
    import time
    start_time = time.time()
    
    # 如果没有提供token，返回401错误
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要认证，请先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # 解码 token
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 提取 user_id（从字符串转换为整数）
    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 转换为整数并查询用户
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 查询用户（添加性能日志）
    query_start = time.time()
    user = session.query(User).filter(User.user_id == user_id).first()
    query_elapsed = (time.time() - query_start) * 1000
    
    if query_elapsed > 100:  # 如果查询超过 100ms，记录警告
        print(f"⚠️ [Auth] get_current_user 数据库查询较慢: {query_elapsed:.2f}ms (user_id: {user_id})")
    
    if user is None:
        print(f"❌ [Auth] 用户不存在: user_id={user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    total_elapsed = (time.time() - start_time) * 1000
    if total_elapsed > 100:  # 如果总耗时超过 100ms，记录警告
        print(f"⚠️ [Auth] get_current_user 总耗时较长: {total_elapsed:.2f}ms (user_id: {user_id})")
    
    # 🔧 添加调试日志：记录成功认证的用户
    print(f"✅ [Auth] 用户认证成功: user_id={user.user_id}, email={user.email}")
    
    return user


# ==================== Pydantic 模型 ====================

class RegisterRequest(BaseModel):
    """注册请求"""
    password: str = Field(..., min_length=6, description="密码（至少6位）")
    email: str = Field(..., description="邮箱")


class LoginRequest(BaseModel):
    """登录请求"""
    user_id: Optional[int] = Field(None, description="用户ID（可选，如果提供email则不需要）")
    email: Optional[str] = Field(None, description="邮箱（可选）")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    user_id: int = Field(..., description="用户ID")


class UserResponse(BaseModel):
    """用户响应"""
    user_id: int
    email: Optional[str] = None
    created_at: Optional[str] = None
    token_balance: Optional[int] = None
    total_tokens_used: Optional[int] = None  # 累计使用的 token 数量
    role: Optional[str] = None  # 用户角色（'admin' | 'user'）
    ui_language: Optional[str] = None  # 界面语言偏好（如 'zh' / 'en'）
    content_language: Optional[str] = None  # 当前内容语言代码（如 'zh' / 'en' / 'de'）
    languages_list: Optional[list[str]] = None  # 已添加的内容语言代码列表


class ForgotPasswordRequest(BaseModel):
    """忘记密码请求"""
    email: Optional[str] = Field(None, description="邮箱（可选）")
    user_id: Optional[int] = Field(None, description="用户ID（可选）")


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    token: str = Field(..., description="密码重置 token")
    new_password: str = Field(..., min_length=6, description="新密码（至少6位）")


class ResetPasswordDirectRequest(BaseModel):
    """直接重置密码请求（测试阶段，无需token）"""
    email: Optional[str] = Field(None, description="邮箱（可选）")
    user_id: Optional[int] = Field(None, description="用户ID（可选）")
    new_password: str = Field(..., min_length=6, description="新密码（至少6位）")


class UserPreferencesUpdateRequest(BaseModel):
    """更新用户语言偏好请求"""
    ui_language: Optional[str] = Field(None, description="界面语言代码，如 'zh' / 'en'")
    content_language: Optional[str] = Field(None, description="当前内容语言代码，如 'zh' / 'en' / 'de'")
    languages_list: Optional[list[str]] = Field(None, description="已添加的内容语言代码列表")


# ==================== 路由器 ====================

router = APIRouter(
    prefix="/api/auth",
    tags=["authentication"],
    responses={401: {"description": "Unauthorized"}},
)


# ==================== API 端点 ====================

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    session: Session = Depends(get_db_session)
):
    """
    用户注册
    
    - **password**: 密码（至少6位）
    - **email**: 邮箱（必填，要求唯一）
    
    返回：
    - access_token: JWT token
    - user_id: 新创建的用户ID
    - email: 注册的邮箱
    """
    try:
        # 🔧 强制要求邮箱
        if not request.email or not request.email.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱为必填项"
            )
        
        # 🔧 检查 email 唯一性，如果已存在则拒绝注册
        existing_user = session.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被注册，请使用其他邮箱或直接登录"
            )
        
        # 加密密码
        password_hash = hash_password(request.password)
        
        # 创建用户（强制 email 唯一性）
        new_user = User(password_hash=password_hash, email=request.email.strip())
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        
        # 生成 JWT token（sub 必须是字符串）
        access_token = create_access_token(data={"sub": str(new_user.user_id)})
        
        # 返回结果（包含 email）
        response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=new_user.user_id
        )
        # 添加 email 到响应中
        response_dict = response.model_dump()
        response_dict["email"] = new_user.email
        return response_dict
    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except Exception as e:
        # 如果遇到 UNIQUE 约束错误，返回友好的错误信息
        if 'UNIQUE constraint failed' in str(e) and 'users.email' in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被注册，请使用其他邮箱或直接登录"
            )
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    session: Session = Depends(get_db_session)
):
    """
    用户登录
    
    - **user_id**: 用户ID（可选，如果提供email则不需要）
    - **email**: 邮箱（可选）
    - **password**: 密码
    
    返回：
    - access_token: JWT token
    - user_id: 用户ID
    
    注意：支持两种登录方式：
    1. user_id + password（保留原有方式）
    2. email + password（新方式）
    3. user_id + email + password（同时提供，优先使用user_id）
    """
    import time
    start_time = time.time()
    
    try:
        # 记录请求开始
        login_method = f"user_id={request.user_id}" if request.user_id else f"email={request.email}"
        print(f"🔐 [Login API] 登录请求开始: {login_method}")
        
        user = None
        query_start = time.time()
        
        # 优先使用 user_id 查询（如果提供）
        if request.user_id:
            print(f"🔍 [Login API] 使用 user_id 查询: {request.user_id}")
            user = session.query(User).filter(User.user_id == request.user_id).first()
        # 如果 user_id 未提供或未找到，且提供了 email，则使用 email 查询
        elif request.email:
            print(f"🔍 [Login API] 使用 email 查询: {request.email}")
            user = session.query(User).filter(User.email == request.email).first()
        else:
            # 既没有 user_id 也没有 email
            print("❌ [Login API] 既没有 user_id 也没有 email")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供用户ID或邮箱"
            )
        
        query_time = time.time() - query_start
        print(f"⏱️ [Login API] 数据库查询耗时: {query_time:.3f}秒")
        
        if not user:
            print(f"❌ [Login API] 用户未找到: {login_method}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户ID/邮箱或密码错误"
            )
        
        print(f"✅ [Login API] 用户找到: user_id={user.user_id}, email={user.email}")
        
        # 验证密码
        verify_start = time.time()
        if not verify_password(request.password, user.password_hash):
            print(f"❌ [Login API] 密码验证失败: user_id={user.user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户ID/邮箱或密码错误"
            )
        verify_time = time.time() - verify_start
        print(f"⏱️ [Login API] 密码验证耗时: {verify_time:.3f}秒")
        
        # 生成 JWT token（sub 必须是字符串）
        token_start = time.time()
        access_token = create_access_token(data={"sub": str(user.user_id)})
        token_time = time.time() - token_start
        print(f"⏱️ [Login API] Token 生成耗时: {token_time:.3f}秒")
        
        total_time = time.time() - start_time
        print(f"✅ [Login API] 登录成功: user_id={user.user_id}, 总耗时: {total_time:.3f}秒")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.user_id
        )
    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except Exception as e:
        total_time = time.time() - start_time
        print(f"❌ [Login API] 登录异常: {str(e)}, 总耗时: {total_time:.3f}秒")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    获取当前登录用户信息
    
    需要在请求头中携带 Authorization: Bearer <token>
    
    返回字段：
    - token_balance: 当前剩余 token
    - total_tokens_used: 累计已使用 token（从 TokenLog 表统计）
    """
    import time
    from sqlalchemy import func
    from database_system.business_logic.models import TokenLog
    
    start_time = time.time()
    print(f"🔍 [Auth] /api/auth/me 请求开始，user_id: {current_user.user_id}")
    
    try:
        # 统计累计使用的 token 数量（从 TokenLog 表查询）
        # 不需要额外字段冗余存储，运行时统计即可
        total_tokens_used_result = (
            session.query(func.sum(TokenLog.total_tokens))
            .filter(TokenLog.user_id == current_user.user_id)
            .scalar()
        )
        total_tokens_used = int(total_tokens_used_result) if total_tokens_used_result else 0
        
        result = UserResponse(
            user_id=current_user.user_id,
            email=current_user.email,
            created_at=current_user.created_at.isoformat() if current_user.created_at else None,
            token_balance=current_user.token_balance or 0,
            total_tokens_used=total_tokens_used,
            role=current_user.role or 'user',
            # 不强制默认 'zh'，交由前端根据 localStorage / 默认值决定
            ui_language=current_user.ui_language,
            content_language=current_user.content_language,
            languages_list=current_user.languages_list or None,
        )
        elapsed = (time.time() - start_time) * 1000
        print(f"✅ [Auth] /api/auth/me 请求完成，耗时: {elapsed:.2f}ms")
        return result
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        print(f"❌ [Auth] /api/auth/me 请求失败，耗时: {elapsed:.2f}ms，错误: {e}")
        raise


@router.post("/test-protected")
async def test_protected_route(current_user: User = Depends(get_current_user)):
    """
    测试受保护的路由
    
    这是一个示例端点，展示如何使用 get_current_user 保护路由
    """
    return {
        "message": "你已成功访问受保护的路由",
        "user_id": current_user.user_id,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }


@router.get("/check-email")
async def check_email_unique(
    email: str = Query(..., description="要检查的邮箱"),
    session: Session = Depends(get_db_session)
):
    """
    检查邮箱唯一性（用于前端debug UI）
    
    - **email**: 要检查的邮箱
    
    返回：
    - unique: 是否唯一
    - message: 检查结果消息
    """
    try:
        existing_user = session.query(User).filter(User.email == email).first()
        is_unique = existing_user is None
        
        return {
            "unique": is_unique,
            "message": "邮箱可用" if is_unique else "邮箱已被使用"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查邮箱失败: {str(e)}")


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    session: Session = Depends(get_db_session)
):
    """
    忘记密码 - 生成密码重置链接（模拟流程，不发送邮件）
    
    - **email**: 邮箱（可选）
    - **user_id**: 用户ID（可选）
    
    返回：
    - reset_link: 密码重置链接（前端直接跳转）
    - message: 提示信息
    
    注意：至少需要提供 email 或 user_id 之一
    """
    try:
        user = None
        
        # 优先使用 email 查询
        if request.email:
            user = session.query(User).filter(User.email == request.email).first()
        # 如果 email 未提供或未找到，且提供了 user_id，则使用 user_id 查询
        elif request.user_id:
            user = session.query(User).filter(User.user_id == request.user_id).first()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供邮箱或用户ID"
            )
        
        # 为了安全，即使用户不存在也返回成功（防止用户枚举攻击）
        if not user:
            # 返回假的链接，但不包含有效 token
            return {
                "success": True,
                "message": "如果该邮箱/用户ID存在，重置链接已生成（开发模式：请查看返回的链接）",
                "reset_link": "/reset-password?token=invalid_token_placeholder"
            }
        
        # 生成密码重置 token
        reset_token = create_password_reset_token(user.user_id)
        
        # 生成重置链接（前端会直接跳转）
        reset_link = f"/reset-password?token={reset_token}"
        
        return {
            "success": True,
            "message": "密码重置链接已生成（开发模式：请使用返回的链接）",
            "reset_link": reset_link,
            "token": reset_token  # 开发模式：直接返回 token 方便测试
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成重置链接失败: {str(e)}")


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    session: Session = Depends(get_db_session)
):
    """
    重置密码
    
    - **token**: 密码重置 token（从忘记密码接口获取）
    - **new_password**: 新密码（至少6位）
    
    返回：
    - success: 是否成功
    - message: 提示信息
    """
    try:
        # 解码并验证 token
        user_id = decode_password_reset_token(request.token)
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效或已过期的重置链接"
            )
        
        # 查询用户
        user = session.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 加密新密码
        new_password_hash = hash_password(request.new_password)
        
        # 更新密码
        user.password_hash = new_password_hash
        session.commit()
        
        return {
            "success": True,
            "message": "密码重置成功，请使用新密码登录"
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"重置密码失败: {str(e)}")


@router.patch("/preferences")
async def update_user_preferences(
    request: UserPreferencesUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """
    更新当前用户的语言偏好（UI 语言、内容语言、已添加语言列表）。

    请求体字段均为可选，只有提供的字段才会被更新。
    """
    try:
        updated = False

        if request.ui_language is not None:
            current_user.ui_language = request.ui_language
            updated = True

        if request.content_language is not None:
            current_user.content_language = request.content_language
            updated = True

        if request.languages_list is not None:
            # 简单过滤：仅保留非空字符串
            cleaned = [code for code in request.languages_list if isinstance(code, str) and code.strip()]
            current_user.languages_list = cleaned
            updated = True

        if updated:
            session.add(current_user)
            # 先不 commit，与预置文章导入同事务（任一失败则整体回滚）
            session.flush()

            # onboarding 或设置里「添加语言」时，自动为该用户导入对应语言的预置文章
            languages_list = current_user.languages_list or []
            if languages_list:
                from backend.data_managers.preset_articles import seed_presets_for_user
                seed_presets_for_user(session, current_user.user_id, languages_list, commit=False)

            session.commit()

        return {
            "success": True,
            "data": {
                "ui_language": current_user.ui_language,
                "content_language": current_user.content_language,
                "languages_list": current_user.languages_list,
            },
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"更新偏好失败: {str(e)}")


@router.get("/debug/all-users")
async def get_all_users_debug(session: Session = Depends(get_db_session)):
    """
    获取所有用户信息（仅用于开发调试）
    
    ⚠️ 警告：此端点返回密码哈希，仅用于开发环境
    ⚠️ 生产环境必须移除或添加严格的权限控制
    """
    users = session.query(User).all()
    
    return {
        "success": True,
        "data": {
            "users": [
                {
                    "user_id": user.user_id,
                    "password_hash": user.password_hash,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                }
                for user in users
            ],
            "count": len(users)
        }
    }


@router.post("/reset-password-direct")
async def reset_password_direct(
    request: ResetPasswordDirectRequest,
    session: Session = Depends(get_db_session)
):
    """
    直接重置密码（测试阶段，无需token）
    
    - **email**: 邮箱（可选）
    - **user_id**: 用户ID（可选）
    - **new_password**: 新密码（至少6位）
    
    返回：
    - success: 是否成功
    - message: 提示信息
    
    注意：至少需要提供 email 或 user_id 之一
    ⚠️ 此接口仅用于测试阶段，生产环境应移除或添加严格权限控制
    """
    try:
        user = None
        
        # 优先使用 email 查询
        if request.email:
            user = session.query(User).filter(User.email == request.email).first()
        # 如果 email 未提供或未找到，且提供了 user_id，则使用 user_id 查询
        elif request.user_id:
            user = session.query(User).filter(User.user_id == request.user_id).first()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供邮箱或用户ID"
            )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 加密新密码
        new_password_hash = hash_password(request.new_password)
        
        # 更新密码
        user.password_hash = new_password_hash
        session.commit()
        
        print(f"✅ [ResetPasswordDirect] 密码重置成功: user_id={user.user_id}, email={user.email}")
        
        return {
            "success": True,
            "message": "密码重置成功，请使用新密码登录",
            "user_id": user.user_id
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        print(f"❌ [ResetPasswordDirect] 重置密码失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重置密码失败: {str(e)}")


@router.get("/debug/users")
def debug_users():
    """临时调试接口：验证 PostgreSQL 数据"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        return [
            {"id": u.user_id, "email": u.email}
            for u in users
        ]
    finally:
        db.close()

