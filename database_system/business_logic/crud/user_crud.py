"""
用户相关 CRUD 操作
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import User


class UserCRUD:
    """用户 CRUD 操作"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, password: str) -> User:
        """创建用户"""
        user = User(password=password)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return self.session.query(User).filter(
            User.user_id == user_id
        ).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """获取所有用户"""
        return self.session.query(User).offset(skip).limit(limit).all()
    
    def update(self, user_id: int, **kwargs) -> Optional[User]:
        """更新用户"""
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        self.session.commit()
        self.session.refresh(user)
        return user
    
    def delete(self, user_id: int) -> bool:
        """删除用户"""
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        self.session.delete(user)
        self.session.commit()
        return True




