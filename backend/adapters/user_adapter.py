"""
用户适配器 - Models ↔ DTO 转换

职责：
1. 将数据库 ORM Models 转换为领域 DTO
2. 将领域 DTO 转换为 ORM Models
3. 处理字段映射、默认值等

使用场景：
- 从数据库读取数据后，转为 DTO 返回给上层
- 接收上层 DTO 数据，转为 Models 存入数据库
"""
from typing import Optional
from database_system.business_logic.models import User as UserModel
from backend.data_managers.data_classes_new import User as UserDTO


class UserAdapter:
    """用户适配器"""
    
    @staticmethod
    def model_to_dto(model: UserModel, include_password: bool = False) -> UserDTO:
        """
        ORM Model → DTO
        从数据库读取后转换为领域对象
        
        参数:
            model: 数据库 ORM 对象
            include_password: 是否包含密码（默认不包含，用于安全）
        
        返回:
            UserDTO: 领域数据对象
        """
        return UserDTO(
            user_id=model.user_id,
            password=model.password if include_password else "***",  # 安全考虑，默认不返回密码
            created_at=model.created_at
        )
    
    @staticmethod
    def dto_to_model(dto: UserDTO) -> UserModel:
        """
        DTO → ORM Model
        准备存入数据库
        
        参数:
            dto: 领域数据对象
        
        返回:
            UserModel: 数据库 ORM 对象
        """
        model = UserModel(
            password=dto.password,
            created_at=dto.created_at
        )
        
        # 如果DTO中有user_id，设置它（用于更新场景）
        if dto.user_id:
            model.user_id = dto.user_id
        
        return model
    
    @staticmethod
    def model_to_dto_safe(model: UserModel) -> dict:
        """
        Model → 安全字典（不包含密码）
        用于API响应
        
        返回:
            dict: 安全的用户数据（不含密码）
        """
        return {
            "user_id": model.user_id,
            "created_at": model.created_at.isoformat() if model.created_at else None
        }


# ==================== 使用示例（注释） ====================
"""
### 示例 1: 从数据库读取后转为 DTO

```python
from database_system.business_logic.managers import UserManager
from backend.adapters import UserAdapter

# 1. 从数据库查询（返回 Model）
user_manager = UserManager(session)
user_model = user_manager.get_user(user_id=1)

# 2. 转换为 DTO（不包含密码）
user_dto = UserAdapter.model_to_dto(user_model, include_password=False)

# 3. 返回给前端（安全）
safe_data = UserAdapter.model_to_dto_safe(user_model)
```

### 示例 2: 创建用户

```python
from backend.adapters import UserAdapter
from database_system.business_logic.managers import UserManager

# 1. 创建用户
user_manager = UserManager(session)
user_model = user_manager.create_user(password="secure123")

# 2. 转换为安全格式返回
return UserAdapter.model_to_dto_safe(user_model)
```
"""




