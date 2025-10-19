"""
用户管理器 - 业务逻辑层
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from ..data_access_layer import UserDataAccessLayer
from ..models import User


class UserManager:
    """用户管理器 - 提供高级业务逻辑"""
    
    def __init__(self, session: Session):
        self.session = session
        self.dal = UserDataAccessLayer(session)
    
    def get_user(self, user_id: int) -> Optional[User]:
        """获取用户"""
        return self.dal.get_user(user_id)
    
    def create_user(self, password: str) -> User:
        """
        创建用户
        
        注意：实际应用中应该对密码进行加密
        例如：hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        """
        return self.dal.create_user(password)
    
    def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """列出用户"""
        return self.dal.list_users(skip, limit)
    
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """更新用户"""
        return self.dal.update_user(user_id, **kwargs)
    
    def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        return self.dal.delete_user(user_id)
    
    def get_user_count(self) -> int:
        """获取用户总数"""
        users = self.list_users(skip=0, limit=10000)
        return len(users)



