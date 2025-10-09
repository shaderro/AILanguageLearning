# VocabManager 双版本使用指南

## 📋 概述

目前提供两个版本的 `VocabManager`：
- **旧版本（JSON）**：`VocabManagerJSON` - 基于 JSON 文件
- **新版本（DB）**：`VocabManagerDB` - 基于数据库

---

## 🔄 如何导出两个版本

### 原理讲解

Python 的 `__init__.py` 可以控制模块的导入行为：

```python
# backend/data_managers/__init__.py

# 步骤1: 导入两个不同的类，并重命名避免冲突
from .vocab_manager import VocabManager as VocabManagerJSON      # 旧版本
from .vocab_manager_db import VocabManager as VocabManagerDB    # 新版本

# 步骤2: 设置默认导出（别名）
VocabManager = VocabManagerJSON  # 默认指向旧版本

# 步骤3: 声明公开接口
__all__ = [
    'VocabManager',        # 默认版本
    'VocabManagerJSON',    # 旧版本
    'VocabManagerDB',      # 新版本
]
```

### 关键点解释

#### 1️⃣ **导入时重命名（as）**

```python
from .vocab_manager import VocabManager as VocabManagerJSON
#                                          ^^^ 重命名
```

**作用：**
- 两个文件都有 `class VocabManager`
- 通过 `as` 重命名避免冲突
- `VocabManagerJSON` 和 `VocabManagerDB` 是新名字

#### 2️⃣ **创建别名（默认导出）**

```python
VocabManager = VocabManagerJSON  # 创建别名
```

**作用：**
- `VocabManager` 是一个变量，指向 `VocabManagerJSON`
- 用户导入 `VocabManager` 时，实际得到 `VocabManagerJSON`
- 可以随时改变指向：`VocabManager = VocabManagerDB`

#### 3️⃣ **声明公开接口（__all__）**

```python
__all__ = ['VocabManager', 'VocabManagerJSON', 'VocabManagerDB']
```

**作用：**
- 告诉 Python 哪些名字可以被外部导入
- 支持 `from backend.data_managers import *`
- IDE 会根据 `__all__` 提供自动补全

---

## 📖 使用方式详解

### 方式1：默认导入（不指定版本）

```python
from backend.data_managers import VocabManager

# 实际得到的是 VocabManagerJSON（当前默认）
vocab_manager = VocabManager(use_new_structure=True)
```

**特点：**
- ✅ 最简单，代码不变
- ✅ 前端和旧代码可以继续工作
- ⚠️ 不知道用的哪个版本
- ⚠️ 未来默认可能改变

**适用场景：**
- 现有代码迁移期间
- 前端开发（暂时不改）

---

### 方式2：显式导入旧版本

```python
from backend.data_managers import VocabManagerJSON

# 明确使用旧版本
vocab_manager = VocabManagerJSON(use_new_structure=True)
```

**特点：**
- ✅ 明确使用旧版本
- ✅ 不受默认版本切换影响
- ⚠️ 未来会被淘汰

**适用场景：**
- 临时保持旧功能
- 逐步迁移过程中

---

### 方式3：显式导入新版本（推荐）⭐

```python
from backend.data_managers import VocabManagerDB
from database_system.database_manager import DatabaseManager

# 明确使用新版本（数据库）
db_manager = DatabaseManager('development')
session = db_manager.get_session()
vocab_manager = VocabManagerDB(session)

# 使用方式相同
vocab = vocab_manager.get_vocab_by_id(1)
```

**特点：**
- ✅ 明确使用新版本
- ✅ 基于数据库，性能更好
- ✅ 不受默认版本切换影响
- ✅ 面向未来

**适用场景：**
- 新功能开发
- API 接口
- AI Assistants

---

## 🎯 实际使用示例

### 示例1：前端继续使用旧版本

```python
# frontend/api/vocab.py (不需要改)

from backend.data_managers import VocabManager

vocab_manager = VocabManager(use_new_structure=True)
vocab = vocab_manager.get_vocab_by_id(1)
```

**说明：**
- 前端代码完全不动
- 继续使用 JSON 版本
- 不受新版本影响

---

### 示例2：新接口使用数据库版本

```python
# backend/main.py (新API)

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.data_managers import VocabManagerDB

def get_db_session():
    """依赖注入：提供数据库 Session"""
    from database_system.database_manager import DatabaseManager
    db_manager = DatabaseManager('development')
    session = db_manager.get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

@app.get("/api/v2/vocab/{vocab_id}")
def get_vocab_v2(vocab_id: int, session: Session = Depends(get_db_session)):
    """新版本API - 使用数据库"""
    vocab_manager = VocabManagerDB(session)
    vocab = vocab_manager.get_vocab_by_id(vocab_id)
    return vocab
```

**说明：**
- 新 API 使用数据库版本
- 通过依赖注入提供 Session
- 与旧 API 并行存在

---

### 示例3：AI Assistants 使用数据库版本

```python
# backend/assistants/sub_assistants/vocab_explanation.py

from backend.data_managers import VocabManagerDB

class VocabExplanationAssistant:
    def __init__(self, session):
        self.vocab_manager = VocabManagerDB(session)
    
    def generate_explanation(self, vocab_id: int) -> str:
        # 从数据库获取词汇
        vocab = self.vocab_manager.get_vocab_by_id(vocab_id)
        
        # AI 处理
        explanation = self.call_llm(vocab)
        
        return explanation
```

**说明：**
- AI 逻辑使用数据库版本
- 获取实时数据
- 性能更好

---

## 🔄 迁移策略

### 阶段1：并行运行（当前）✅

```python
# __init__.py
VocabManager = VocabManagerJSON  # 默认 = 旧版本

__all__ = [
    'VocabManager',          # → VocabManagerJSON
    'VocabManagerJSON',      # 显式旧版本
    'VocabManagerDB',        # 显式新版本
]
```

**状态：**
- 前端：使用 `VocabManager` → 旧版本
- 新API：使用 `VocabManagerDB` → 新版本
- 共存，互不影响

---

### 阶段2：切换默认（测试完成后）

```python
# __init__.py
VocabManager = VocabManagerDB  # 默认 = 新版本 ✅

__all__ = [
    'VocabManager',          # → VocabManagerDB ✅
    'VocabManagerJSON',      # 保留，逐步淘汰
    'VocabManagerDB',        # 新版本
]
```

**影响：**
- ⚠️ 使用 `VocabManager` 的代码会切换到数据库版本
- ✅ 使用 `VocabManagerJSON` 的代码不受影响
- 需要：更新所有使用 `VocabManager` 的代码

---

### 阶段3：移除旧版本（完全迁移后）

```python
# __init__.py
from .vocab_manager_db import VocabManager

# 删除旧版本导入
# from .vocab_manager import VocabManager as VocabManagerJSON  # 已删除

__all__ = ['VocabManager']  # 只保留一个版本
```

**操作：**
- 删除 `vocab_manager.py`（或移到 `deprecated/`）
- 只保留数据库版本

---

## 📊 版本对比

| 特性 | VocabManagerJSON | VocabManagerDB |
|-----|------------------|----------------|
| **存储方式** | JSON 文件 | SQLite 数据库 |
| **初始化** | `VocabManager()` | `VocabManager(session)` |
| **查询性能** | 慢（全文件加载） | 快（索引查询） |
| **并发支持** | ❌ 不支持 | ✅ 支持 |
| **事务支持** | ❌ 无 | ✅ 有 |
| **分页支持** | ⚠️ 手动实现 | ✅ 内置 |
| **搜索功能** | ⚠️ 简单匹配 | ✅ SQL LIKE |
| **关联查询** | ⚠️ 手动处理 | ✅ ORM 自动 |
| **状态** | 逐步淘汰 | 推荐使用 ✅ |

---

## ⚠️ 注意事项

### 1. 构造函数不同

```python
# 旧版本
vocab_manager = VocabManagerJSON(use_new_structure=True)

# 新版本
vocab_manager = VocabManagerDB(session)  # 需要 Session
```

### 2. Session 生命周期

```python
# ✅ 正确：使用完关闭
session = get_session()
try:
    vocab_manager = VocabManagerDB(session)
    vocab = vocab_manager.get_vocab_by_id(1)
    session.commit()
finally:
    session.close()

# ❌ 错误：忘记关闭
vocab_manager = VocabManagerDB(session)
vocab = vocab_manager.get_vocab_by_id(1)
# session 没关闭，造成资源泄漏
```

### 3. 数据不同步

- 旧版本修改 JSON 文件
- 新版本修改数据库
- **两者数据不会自动同步**

---

## 🚀 快速开始

### 新项目：直接使用数据库版本

```python
from backend.data_managers import VocabManagerDB
from database_system.database_manager import DatabaseManager

# 1. 获取 Session
db_manager = DatabaseManager('development')
session = db_manager.get_session()

# 2. 创建 Manager
vocab_manager = VocabManagerDB(session)

# 3. 使用
vocab = vocab_manager.get_vocab_by_id(1)
print(f"{vocab.vocab_body}: {vocab.explanation}")

# 4. 提交并关闭
session.commit()
session.close()
```

### 现有项目：继续使用旧版本

```python
from backend.data_managers import VocabManager

# 无需改动
vocab_manager = VocabManager(use_new_structure=True)
vocab = vocab_manager.get_vocab_by_id(1)
```

---

## 📚 总结

### `__init__.py` 导出两个版本的核心

1. **导入时重命名**：`as VocabManagerJSON`, `as VocabManagerDB`
2. **创建默认别名**：`VocabManager = VocabManagerJSON`
3. **声明公开接口**：`__all__ = [...]`

### 使用建议

- ✅ 新功能：使用 `VocabManagerDB`
- ✅ 旧代码：继续使用 `VocabManager`（暂时不改）
- ✅ 明确版本：使用 `VocabManagerJSON` 或 `VocabManagerDB`
- ⚠️ 逐步迁移：一个接口一个接口地切换

### 迁移路径

```
当前 → 旧版本默认，新版本可选
  ↓
阶段2 → 新版本默认，旧版本保留
  ↓
阶段3 → 只保留新版本
```

