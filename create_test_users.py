"""
创建测试用户并更新 USER_CREDENTIALS.md
"""
import sys
import os
from datetime import datetime

# 添加路径
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, BACKEND_DIR)

from database_system.database_manager import DatabaseManager
from database_system.business_logic.models import User
from backend.utils.auth import hash_password

# 测试用户配置
TEST_USERS = [
    {"user_id": 1, "password": "test123456"},
    {"user_id": 2, "password": "mypassword123"},
    {"user_id": 3, "password": "test123456"},
    {"user_id": 4, "password": "test123456"},
    {"user_id": 5, "password": "testpwd123"},
    {"user_id": 6, "password": "test123"},
]

def main():
    print("\n" + "="*60)
    print("创建测试用户")
    print("="*60)
    
    # 连接数据库
    db_manager = DatabaseManager('development')
    session = db_manager.get_session()
    
    created_users = []
    
    try:
        for user_config in TEST_USERS:
            user_id = user_config["user_id"]
            password = user_config["password"]
            
            # 检查用户是否已存在
            existing_user = session.query(User).filter(User.user_id == user_id).first()
            
            if existing_user:
                print(f"⚠️  User {user_id} 已存在，跳过")
                continue
            
            # 创建新用户
            password_hash = hash_password(password)
            new_user = User(
                user_id=user_id,  # 手动指定 user_id
                password_hash=password_hash
            )
            session.add(new_user)
            session.flush()  # 立即获取生成的数据
            
            created_users.append({
                "user_id": new_user.user_id,
                "password": password,
                "created_at": new_user.created_at
            })
            
            print(f"✅ 创建 User {user_id} (密码: {password})")
        
        # 提交所有更改
        session.commit()
        
        print(f"\n✅ 成功创建 {len(created_users)} 个用户")
        
        # 更新 USER_CREDENTIALS.md
        if created_users:
            update_credentials_file(created_users)
        
    except Exception as e:
        session.rollback()
        print(f"❌ 错误: {e}")
    finally:
        session.close()

def update_credentials_file(users):
    """更新 USER_CREDENTIALS.md 文件"""
    print("\n" + "="*60)
    print("更新 USER_CREDENTIALS.md")
    print("="*60)
    
    content = """# 用户凭据信息

⚠️ **此文件仅用于开发测试，请勿提交到版本控制！**

---

## 所有用户列表

| User ID | 密码 | 创建时间 | 状态 |
|---------|------|----------|------|
"""
    
    for user in users:
        created_at = user["created_at"].strftime("%Y-%m-%d %H:%M:%S") if user["created_at"] else "Unknown"
        content += f"| {user['user_id']} | `{user['password']}` | {created_at} | ✅ 可用 |\n"
    
    content += """
---

## 可用账号（可直接登录）

"""
    
    for user in users:
        created_at = user["created_at"].strftime("%Y-%m-%d %H:%M:%S") if user["created_at"] else "Unknown"
        content += f"""### User {user['user_id']}
- **User ID**: `{user['user_id']}`
- **密码**: `{user['password']}`
- **创建时间**: {created_at}

"""
    
    content += """---

## 使用说明

### 登录方法
1. 访问 http://localhost:5173
2. 点击右上角"登录"按钮
3. 使用上面的 User ID 和密码登录

### 如果密码未知
- 注册新用户（会自动分配新的 User ID）
- 密码会自动保存到浏览器的 localStorage

### API 测试
可以使用 PowerShell 测试登录：

```powershell
$body = @{
    user_id = 1
    password = "test123456"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8001/api/auth/login" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"
```
"""
    
    try:
        with open("USER_CREDENTIALS.md", "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ USER_CREDENTIALS.md 已更新")
    except Exception as e:
        print(f"❌ 更新文件失败: {e}")

if __name__ == "__main__":
    main()

