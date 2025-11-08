"""
认证 API 路由
提供注册、登录、当前用户等认证相关接口
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

# 导入数据库管理器
from database_system.database_manager import DatabaseManager
from database_system.business_logic.models import User

# 导入认证工具
from backend.utils.auth import hash_password, verify_password, create_access_token, decode_access_token


# ==================== 依赖注入 ====================

def get_db_session():
    """获取数据库 Session"""
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


# HTTP Bearer token 认证
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_db_session)
) -> User:
    """
    从 JWT token 中获取当前用户
    
    用法：
        @router.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.user_id}
    """
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
    
    user = session.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


# ==================== Pydantic 模型 ====================

class RegisterRequest(BaseModel):
    """注册请求"""
    password: str = Field(..., min_length=6, description="密码（至少6位）")


class LoginRequest(BaseModel):
    """登录请求"""
    user_id: int = Field(..., description="用户ID")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    user_id: int = Field(..., description="用户ID")


class UserResponse(BaseModel):
    """用户响应"""
    user_id: int
    created_at: Optional[str] = None


# ==================== 路由器 ====================

router = APIRouter(
    prefix="/api/auth",
    tags=["authentication"],
    responses={401: {"description": "Unauthorized"}},
)


# ==================== API 端点 ====================

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    session: Session = Depends(get_db_session)
):
    """
    用户注册
    
    - **password**: 密码（至少6位）
    
    返回：
    - access_token: JWT token
    - user_id: 新创建的用户ID
    """
    try:
        # 加密密码
        password_hash = hash_password(request.password)
        
        # 创建用户
        new_user = User(password_hash=password_hash)
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        
        # 生成 JWT token（sub 必须是字符串）
        access_token = create_access_token(data={"sub": str(new_user.user_id)})
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=new_user.user_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    session: Session = Depends(get_db_session)
):
    """
    用户登录
    
    - **user_id**: 用户ID
    - **password**: 密码
    
    返回：
    - access_token: JWT token
    - user_id: 用户ID
    """
    # 查询用户
    user = session.query(User).filter(User.user_id == request.user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户ID或密码错误"
        )
    
    # 验证密码
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户ID或密码错误"
        )
    
    # 生成 JWT token（sub 必须是字符串）
    access_token = create_access_token(data={"sub": str(user.user_id)})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.user_id
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户信息
    
    需要在请求头中携带 Authorization: Bearer <token>
    """
    return UserResponse(
        user_id=current_user.user_id,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None
    )


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

