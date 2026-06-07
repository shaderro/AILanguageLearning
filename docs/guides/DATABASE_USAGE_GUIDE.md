# 数据库使用步骤指南

## 📋 概述

在真实业务接口中使用数据库的完整步骤指南，基于当前代码库的最佳实践。

### ⚠️ 重要说明：环境自动选择

**这个指南适用于所有环境（开发环境、测试环境、生产环境）。**

数据库的选择是**自动的**，取决于环境变量：
- **开发环境**（本地）：如果 `ENV=development` 且**没有** `DATABASE_URL` → 使用 SQLite
- **生产环境**（云平台）：如果 `ENV=production` 且**有** `DATABASE_URL` → 使用 PostgreSQL

代码中的 `DatabaseManager(ENV)` 会根据环境变量自动选择正确的数据库，**无需修改代码**。

---

## 🔧 方式一：使用依赖注入（推荐）

### 适用场景
- **路由文件**（如 `backend/api/*_routes.py`）
- **需要认证的接口**
- **标准的 CRUD 操作**

### 步骤模板

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database_system.database_manager import DatabaseManager
from database_system.business_logic.models import User
from backend.api.auth_routes import get_current_user

# 1️⃣ 创建依赖注入函数（每个路由文件一个）
def get_db_session():
    """获取数据库 Session（自动管理事务）"""
    from backend.config import ENV
    db_manager = DatabaseManager(ENV)
    session = db_manager.get_session()
    try:
        yield session
        session.commit()  # ✅ 成功时自动提交
    except Exception as e:
        session.rollback()  # ❌ 失败时自动回滚
        raise e
    finally:
        session.close()  # 🔒 总是关闭

# 2️⃣ 在路由函数中使用
@router.post("/api/users")
async def create_user(
    request: CreateUserRequest,
    session: Session = Depends(get_db_session),  # ✅ 依赖注入
    current_user: User = Depends(get_current_user)  # ✅ 可选：认证
):
    # 3️⃣ 写入数据
    new_user = User(
        email=request.email,
        password_hash=hash_password(request.password)
    )
    session.add(new_user)
    # ⚠️ 注意：使用依赖注入时，不需要手动 commit，会在函数成功返回后自动 commit
    
    # 4️⃣ 如果需要立即获取 ID，需要 refresh
    session.flush()  # 或 session.commit()（但不推荐在依赖注入中手动 commit）
    session.refresh(new_user)
    
    return {"user_id": new_user.user_id}
```

---

## 🔨 方式二：直接使用 DatabaseManager

### 适用场景
- **main.py 中的接口**
- **复杂的业务逻辑函数**
- **需要手动控制事务的场景**

### 步骤模板

```python
from database_system.database_manager import DatabaseManager
from database_system.business_logic.models import User
from backend.config import ENV

@app.post("/api/example")
async def example_endpoint():
    # 1️⃣ 创建数据库管理器
    db_manager = DatabaseManager(ENV)
    session = db_manager.get_session()
    
    try:
        # 2️⃣ 写入数据
        new_user = User(
            email="test@example.com",
            password_hash="hashed_password"
        )
        session.add(new_user)
        session.commit()  # ✅ 手动提交
        session.refresh(new_user)  # 刷新以获取自动生成的 ID
        
        # 3️⃣ 读取数据
        user = session.query(User).filter(User.user_id == new_user.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 4️⃣ 更新数据
        user.email = "new_email@example.com"
        session.commit()  # ✅ 提交更新
        
        # 5️⃣ 删除数据（可选）
        # session.delete(user)
        # session.commit()
        
        return {"user_id": user.user_id, "email": user.email}
        
    except Exception as e:
        session.rollback()  # ❌ 出错时回滚
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()  # 🔒 总是关闭
```

---

## 📝 详细步骤说明

### 1️⃣ 创建 Session

#### 方式 A：依赖注入（推荐）
```python
session: Session = Depends(get_db_session)
```

#### 方式 B：直接创建
```python
from database_system.database_manager import DatabaseManager
from backend.config import ENV

db_manager = DatabaseManager(ENV)  # ENV 从环境变量读取（development/testing/production）
session = db_manager.get_session()

# ⚠️ 数据库自动选择：
# - 开发环境：ENV=development + 无 DATABASE_URL → SQLite (dev.db)
# - 生产环境：ENV=production + 有 DATABASE_URL → PostgreSQL（云数据库）
```

---

### 2️⃣ 写入数据（CREATE）

```python
# 创建模型实例
new_user = User(
    email="user@example.com",
    password_hash="hashed_password"
)

# 添加到 session
session.add(new_user)

# 提交事务
session.commit()  # 依赖注入模式下会自动提交，不需要手动调用

# 刷新以获取自动生成的 ID
session.refresh(new_user)
print(new_user.user_id)  # 现在可以获取 ID
```

---

### 3️⃣ 读取数据（READ）

#### 查询单个记录
```python
# 方式 1：使用 filter().first()
user = session.query(User).filter(User.user_id == user_id).first()
if not user:
    raise HTTPException(status_code=404, detail="用户不存在")

# 方式 2：使用 get()（仅适用于主键）
user = session.get(User, user_id)  # 如果不存在返回 None
```

#### 查询多个记录
```python
# 查询所有
users = session.query(User).all()

# 带条件查询
users = session.query(User).filter(User.email.isnot(None)).all()

# 带排序
users = session.query(User).order_by(User.created_at.desc()).all()

# 分页查询
page = 1
page_size = 10
users = session.query(User)\
    .offset((page - 1) * page_size)\
    .limit(page_size)\
    .all()
```

#### 条件查询示例
```python
# 等于
user = session.query(User).filter(User.user_id == user_id).first()

# 不等于
users = session.query(User).filter(User.email != None).all()

# 包含（LIKE）
users = session.query(User).filter(User.email.contains("@gmail")).all()

# IN
user_ids = [1, 2, 3]
users = session.query(User).filter(User.user_id.in_(user_ids)).all()

# AND（多个 filter）
user = session.query(User)\
    .filter(User.user_id == user_id)\
    .filter(User.email == email)\
    .first()

# OR（需要导入）
from sqlalchemy import or_
user = session.query(User)\
    .filter(or_(User.user_id == user_id, User.email == email))\
    .first()
```

---

### 4️⃣ 更新数据（UPDATE）

```python
# 1. 先查询要更新的记录
user = session.query(User).filter(User.user_id == user_id).first()
if not user:
    raise HTTPException(status_code=404, detail="用户不存在")

# 2. 修改属性
user.email = "new_email@example.com"

# 3. 提交事务
session.commit()  # 依赖注入模式下会自动提交

# ⚠️ 注意：SQLAlchemy 会自动跟踪修改，不需要额外操作
```

---

### 5️⃣ 删除数据（DELETE）

```python
# 1. 先查询要删除的记录
user = session.query(User).filter(User.user_id == user_id).first()
if not user:
    raise HTTPException(status_code=404, detail="用户不存在")

# 2. 删除
session.delete(user)

# 3. 提交事务
session.commit()  # 依赖注入模式下会自动提交
```

---

### 6️⃣ 错误处理和事务管理

#### 使用依赖注入（自动管理）
```python
def get_db_session():
    session = db_manager.get_session()
    try:
        yield session
        session.commit()  # ✅ 自动提交
    except Exception as e:
        session.rollback()  # ❌ 自动回滚
        raise e
    finally:
        session.close()  # 🔒 自动关闭
```

#### 手动管理（try/except/finally）
```python
session = db_manager.get_session()
try:
    # 业务逻辑
    user = User(...)
    session.add(user)
    session.commit()
except Exception as e:
    session.rollback()  # ❌ 出错时回滚
    raise HTTPException(status_code=500, detail=str(e))
finally:
    session.close()  # 🔒 总是关闭
```

---

## 📚 实际业务接口示例

### 示例 1：用户注册（来自 `backend/api/auth_routes.py`）

```python
@router.post("/register")
async def register(
    request: RegisterRequest,
    session: Session = Depends(get_db_session)  # ✅ 依赖注入
):
    # 1. 检查唯一性
    existing_user = session.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="邮箱已被使用")
    
    # 2. 创建用户
    password_hash = hash_password(request.password)
    new_user = User(
        password_hash=password_hash,
        email=request.email
    )
    session.add(new_user)
    # ⚠️ 依赖注入会自动 commit，但我们需要立即获取 user_id
    session.flush()  # 或 session.commit() + session.refresh()
    session.refresh(new_user)
    
    # 3. 返回结果
    return {"user_id": new_user.user_id}
```

### 示例 2：上传文章（来自 `main.py`）

```python
@app.post("/api/upload/file")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    # 1. 创建 session
    db_manager = DatabaseManager(ENV)
    session = db_manager.get_session()
    
    try:
        # 2. 创建文章记录
        text_model = OriginalText(
            text_id=article_id,
            text_title=title,
            user_id=current_user.user_id,
            language=language,
            processing_status='processing'
        )
        session.add(text_model)
        session.commit()  # ✅ 手动提交
        print(f"✅ 创建文章记录: {title}")
        
    except Exception as e:
        session.rollback()  # ❌ 出错时回滚
        print(f"⚠️ 创建文章记录失败: {e}")
    finally:
        session.close()  # 🔒 关闭 session
```

---

## ✅ 最佳实践清单

### ✅ 必须做的

1. **总是使用 try/except/finally 或依赖注入**
   - 确保 session 正确关闭
   - 确保事务正确提交或回滚

2. **在写入数据后检查结果**
   - 使用 `session.refresh()` 获取自动生成的 ID
   - 验证数据是否正确写入

3. **使用适当的查询方法**
   - `.first()` 用于单个结果
   - `.all()` 用于多个结果
   - `.filter()` 用于条件查询

4. **处理异常情况**
   - 检查记录是否存在（`if not user:`）
   - 返回适当的 HTTP 状态码
   - 提供清晰的错误消息

### ⚠️ 注意事项

1. **不要混用依赖注入和手动管理**
   - 如果使用 `Depends(get_db_session)`，不要手动 `commit()`
   - 如果手动创建 session，记得手动 `commit()` 和 `close()`

2. **注意事务边界**
   - 一个请求 = 一个事务（通常）
   - 需要多个事务时，创建多个 session

3. **性能优化**
   - 使用 `.filter()` 而不是加载所有数据
   - 使用索引字段查询（如 `user_id`）
   - 批量操作时考虑使用 `bulk_insert_mappings()`

---

## 🔄 下一步建议

1. **选择一个现有的业务接口进行改造**
   - 建议从简单的接口开始（如用户查询）
   - 参考 `backend/api/auth_routes.py` 的实现

2. **测试数据库操作**
   - 使用 `/api/db-test` 接口验证连接
   - 测试创建、读取、更新、删除操作

3. **逐步迁移**
   - 先迁移读取操作（GET）
   - 再迁移写入操作（POST/PUT/DELETE）
   - 最后处理复杂的业务逻辑

4. **验证用户隔离**
   - 确保所有操作都包含 `user_id` 过滤
   - 测试不同用户之间的数据隔离
