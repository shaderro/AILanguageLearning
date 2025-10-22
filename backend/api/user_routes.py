"""
用户 API 路由 - 使用数据库版本的 UserManager

提供用户相关的 RESTful API 接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

# 导入数据库管理器
from database_system.database_manager import DatabaseManager

# 导入数据库版本的 UserManager
from backend.data_managers.user_manager_db import UserManagerDB


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

class UserCreateRequest(BaseModel):
    """创建用户请求"""
    password: str = Field(..., min_length=6, description="密码（至少6位）", example="password123")


class UserUpdateRequest(BaseModel):
    """更新用户请求"""
    password: Optional[str] = Field(None, min_length=6, description="新密码")


class UserResponse(BaseModel):
    """用户响应（不返回密码）"""
    user_id: int
    created_at: Optional[str] = None

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
    prefix="/api/v2/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


# ==================== API 端点 ====================

@router.get("/", summary="获取所有用户")
async def get_all_users(
    skip: int = Query(default=0, ge=0, description="跳过的记录数"),
    limit: int = Query(default=100, ge=1, le=1000, description="返回的最大记录数"),
    session: Session = Depends(get_db_session)
):
    """
    获取所有用户（分页）
    
    - **skip**: 跳过的记录数（用于分页）
    - **limit**: 返回的最大记录数
    
    注意：返回的用户数据不包含密码
    """
    try:
        user_manager = UserManagerDB(session)
        users = user_manager.get_all_users(skip=skip, limit=limit)
        
        return {
            "success": True,
            "data": {
                "users": [
                    {
                        "user_id": u.user_id,
                        "created_at": u.created_at.isoformat() if u.created_at else None
                        # 注意：不返回密码
                    }
                    for u in users
                ],
                "count": len(users),
                "skip": skip,
                "limit": limit
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", summary="获取单个用户")
async def get_user(
    user_id: int,
    session: Session = Depends(get_db_session)
):
    """
    根据 ID 获取用户
    
    - **user_id**: 用户ID
    
    注意：返回的用户数据不包含密码
    """
    try:
        user_manager = UserManagerDB(session)
        user = user_manager.get_user_by_id(user_id, include_password=False)
        
        if not user:
            raise HTTPException(status_code=404, detail=f"User ID {user_id} not found")
        
        return {
            "success": True,
            "data": {
                "user_id": user.user_id,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", summary="创建新用户", status_code=201)
async def create_user(
    request: UserCreateRequest,
    session: Session = Depends(get_db_session)
):
    """
    创建新用户
    
    - **password**: 密码（至少6位）
    
    注意：
    - 实际应用中应该对密码进行加密（bcrypt）
    - 这里为简化演示，直接存储明文（不推荐）
    """
    try:
        user_manager = UserManagerDB(session)
        
        # 创建用户
        user = user_manager.create_user(password=request.password)
        
        return {
            "success": True,
            "message": "User created successfully",
            "data": {
                "user_id": user.user_id,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}", summary="更新用户")
async def update_user(
    user_id: int,
    request: UserUpdateRequest,
    session: Session = Depends(get_db_session)
):
    """
    更新用户
    
    - **user_id**: 用户ID
    - **password**: 新密码（可选）
    """
    try:
        user_manager = UserManagerDB(session)
        
        # 构建更新字典（只包含非 None 的字段）
        update_data = {
            k: v for k, v in request.dict().items() if v is not None
        }
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # 更新用户
        user = user_manager.update_user(user_id, **update_data)
        
        if not user:
            raise HTTPException(status_code=404, detail=f"User ID {user_id} not found")
        
        return {
            "success": True,
            "message": "User updated successfully",
            "data": {
                "user_id": user.user_id,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,
    session: Session = Depends(get_db_session)
):
    """
    删除用户
    
    - **user_id**: 用户ID
    """
    try:
        user_manager = UserManagerDB(session)
        success = user_manager.delete_user(user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"User ID {user_id} not found")
        
        return {
            "success": True,
            "message": f"User ID {user_id} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary", summary="获取用户统计")
async def get_user_stats(
    session: Session = Depends(get_db_session)
):
    """
    获取用户统计信息
    
    返回：
    - total: 总用户数
    """
    try:
        user_manager = UserManagerDB(session)
        total = user_manager.get_user_count()
        
        return {
            "success": True,
            "data": {
                "total": total
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




