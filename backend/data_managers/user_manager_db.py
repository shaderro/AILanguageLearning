"""
用户管理器 - 基于数据库的实现

职责：
1. 对外提供统一的 DTO 接口（data_classes_new.py）
2. 内部调用数据库业务层 Manager
3. 使用 Adapter 进行 Model ↔ DTO 转换
4. 处理业务逻辑和错误

使用场景：
- AI Assistants 调用
- FastAPI 接口调用
- 任何需要用户数据的地方

示例：
    from sqlalchemy.orm import Session
    from backend.data_managers import UserManagerDB
    
    session = get_session()
    user_manager = UserManagerDB(session)
    
    # 创建用户
    new_user = user_manager.create_user(password="secure123")
    
    # 获取用户
    user = user_manager.get_user_by_id(1)
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from backend.data_managers.data_classes_new import User as UserDTO
from backend.adapters.user_adapter import UserAdapter
from database_system.business_logic.managers.user_manager import UserManager as DBUserManager


class UserManagerDB:
    """
    用户管理器 - 数据库版本
    
    设计原则：
    - 对外统一返回 DTO（领域对象）
    - 内部使用数据库 Manager 操作
    - 通过 Adapter 转换 Model ↔ DTO
    """
    
    def __init__(self, session: Session):
        """
        初始化用户管理器
        
        参数:
            session: SQLAlchemy Session（数据库会话）
        """
        self.session = session
        self.db_manager = DBUserManager(session)
    
    def get_user_by_id(self, user_id: int, include_password: bool = False) -> Optional[UserDTO]:
        """
        根据ID获取用户
        
        参数:
            user_id: 用户ID
            include_password: 是否包含密码（默认不包含）
            
        返回:
            UserDTO: 用户数据对象
            None: 用户不存在
            
        使用示例:
            user = user_manager.get_user_by_id(1)
            if user:
                print(f"用户ID: {user.user_id}")
        """
        user_model = self.db_manager.get_user(user_id)
        if not user_model:
            return None
        
        return UserAdapter.model_to_dto(user_model, include_password=include_password)
    
    def create_user(self, password: str) -> UserDTO:
        """
        创建新用户
        
        参数:
            password: 密码（明文，实际应用中应该先加密）
            
        返回:
            UserDTO: 新创建的用户数据对象
            
        使用示例:
            new_user = user_manager.create_user(password="secure123")
            print(f"创建用户ID: {new_user.user_id}")
        """
        user_model = self.db_manager.create_user(password)
        return UserAdapter.model_to_dto(user_model, include_password=False)
    
    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[UserDTO]:
        """
        获取所有用户（分页）
        
        参数:
            skip: 跳过的记录数（用于分页）
            limit: 返回的最大记录数
            
        返回:
            List[UserDTO]: 用户列表
            
        使用示例:
            # 获取前20个用户
            users = user_manager.get_all_users(skip=0, limit=20)
        """
        user_models = self.db_manager.list_users(skip=skip, limit=limit)
        return [UserAdapter.model_to_dto(m, include_password=False) for m in user_models]
    
    def update_user(self, user_id: int, **kwargs) -> Optional[UserDTO]:
        """
        更新用户
        
        参数:
            user_id: 用户ID
            **kwargs: 要更新的字段（password等）
            
        返回:
            UserDTO: 更新后的用户
            None: 用户不存在
            
        使用示例:
            updated = user_manager.update_user(user_id=1, password="new_password")
        """
        user_model = self.db_manager.update_user(user_id, **kwargs)
        if not user_model:
            return None
        
        return UserAdapter.model_to_dto(user_model, include_password=False)
    
    def delete_user(self, user_id: int) -> bool:
        """
        删除用户
        
        参数:
            user_id: 用户ID
            
        返回:
            bool: 是否删除成功
            
        使用示例:
            success = user_manager.delete_user(1)
            if success:
                print("删除成功")
        """
        return self.db_manager.delete_user(user_id)
    
    def get_user_count(self) -> int:
        """
        获取用户总数
        
        返回:
            int: 用户总数
            
        使用示例:
            count = user_manager.get_user_count()
            print(f"总用户数: {count}")
        """
        return self.db_manager.get_user_count()
    
    def get_user_safe_data(self, user_id: int) -> Optional[dict]:
        """
        获取用户安全数据（不含密码）
        
        参数:
            user_id: 用户ID
            
        返回:
            dict: 安全的用户数据
            None: 用户不存在
            
        使用示例:
            safe_data = user_manager.get_user_safe_data(1)
            # 返回: {"user_id": 1, "created_at": "2025-10-16T..."}
        """
        user_model = self.db_manager.get_user(user_id)
        if not user_model:
            return None
        
        return UserAdapter.model_to_dto_safe(user_model)




