# 环境状态和切换指南

## 📊 当前环境状态

### 开发环境 (dev.db) ✅
- ✅ **有user_id字段**
- ✅ **有language字段**
- ✅ **有数据**：
  - 6个用户（user_id: 1, 2, 3, 4, 5, 6）
  - 66个vocab（user 1: 46个, user 2: 18个, user 3: 2个）
  - 16个grammar（user 1: 10个, user 2: 6个）
  - 4个文章（user 2: 4个）
- **状态**: 正常，完全支持用户隔离和语言过滤

### 测试环境 (test.db) ⚠️
- ❌ **没有user_id字段**（旧结构）
- ❌ **没有language字段**（旧结构）
- ✅ **有数据**：
  - **0个用户**
  - 3个vocab（test, challenging, component）
  - 2个grammar（德语定冠词变化, 德语形容词词尾变化）
  - 0个文章
- **状态**: 需要迁移，表结构是旧的

### 生产环境 (language_learning.db) ⚠️
- ❌ **没有user_id字段**（旧结构）
- ✅ **有language字段**
- ✅ **没有数据**：0个vocab, 0个grammar, 0个文章
- **状态**: 需要迁移，表结构是旧的，但没有数据

## 🔍 问题回答

### 1. 之前做用户数据测试创建的用户都在开发环境对吗？

**答案：是的！** ✅

所有用户数据测试创建的用户都在开发环境（dev.db）：
- 6个用户（user_id: 1, 2, 3, 4, 5, 6）
- 所有vocab和grammar数据都在开发环境
- 所有文章数据都在开发环境

### 2. 我现在运行的是开发环境吗？

**答案：是的！** ✅

当前所有API路由都硬编码使用开发环境：
- `backend/api/text_routes.py`: `DatabaseManager('development')`
- `backend/api/vocab_routes.py`: `DatabaseManager('development')`
- `backend/api/grammar_routes.py`: `DatabaseManager('development')`
- `frontend/my-web-ui/backend/main.py`: `DatabaseManager('development')`

所以现在运行的**一定是开发环境**。

### 3. 测试环境有哪些数据？

**测试环境数据：**
- **0个用户**（没有用户数据）
- **3个vocab**：
  1. `test` - "这是一个测试词汇"
  2. `challenging` - "形容词，表示具有挑战性的、困难的"
  3. `component` - "名词，表示组成部分、要素、组件"
- **2个grammar**：
  1. `德语定冠词变化` - "德语定冠词根据名词的性、数、格发生变化"
  2. `德语形容词词尾变化` - "德语形容词在名词前需要根据名词的性、数、格变化词尾"
- **0个文章**

### 4. 如何切换环境运行？

**当前问题：** 所有API路由都硬编码使用`'development'`环境。

**切换方法：**

#### 方法1：使用环境变量（推荐）

1. **创建环境变量配置文件**（`.env`文件）：
```env
DATABASE_ENVIRONMENT=development
```

2. **修改所有API路由的`get_db_session()`函数**：
```python
import os

def get_db_session():
    # 从环境变量读取，默认为development
    env = os.getenv('DATABASE_ENVIRONMENT', 'development')
    db_manager = DatabaseManager(env)
    session = db_manager.get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
```

3. **启动时设置环境变量**：
```bash
# Windows PowerShell
$env:DATABASE_ENVIRONMENT="testing"
python frontend/my-web-ui/backend/main.py

# Linux/Mac
export DATABASE_ENVIRONMENT="testing"
python frontend/my-web-ui/backend/main.py
```

#### 方法2：修改代码中的环境名称（不推荐）

直接修改所有API路由文件中的`DatabaseManager('development')`为`DatabaseManager('testing')`或`DatabaseManager('production')`。

#### 方法3：使用配置文件（最佳实践）

1. **创建配置文件**（`config.py`）：
```python
# config.py
import os

# 从环境变量读取，默认为development
DATABASE_ENVIRONMENT = os.getenv('DATABASE_ENVIRONMENT', 'development')
```

2. **在所有API路由中导入并使用**：
```python
from config import DATABASE_ENVIRONMENT

def get_db_session():
    db_manager = DatabaseManager(DATABASE_ENVIRONMENT)
    session = db_manager.get_session()
    # ...
```

## 📋 需要修改的文件

如果要支持环境切换，需要修改以下文件：

1. **backend/api/text_routes.py** - `get_db_session()`函数
2. **backend/api/vocab_routes.py** - `get_db_session()`函数
3. **backend/api/grammar_routes.py** - `get_db_session()`函数
4. **backend/api/notation_routes.py** - `get_db_session()`函数
5. **backend/api/auth_routes.py** - `get_db_session()`函数
6. **backend/api/user_routes.py** - `get_db_session()`函数
7. **frontend/my-web-ui/backend/main.py** - 所有`DatabaseManager('development')`调用

## 🎯 建议

### 当前建议：
1. **继续使用开发环境**（当前状态）
   - 开发环境有完整的数据和用户
   - 所有功能都正常工作
   - 不需要切换

2. **如果要测试环境切换**：
   - 先迁移测试环境（添加user_id和language字段）
   - 创建配置文件支持环境变量
   - 修改所有API路由支持环境切换
   - 测试环境切换功能

3. **如果要使用生产环境**：
   - 先更新生产环境（添加user_id字段）
   - 设置环境变量为`production`
   - 重启服务器

## 🚀 快速检查当前环境

运行以下命令检查当前使用的环境：

```bash
python check_all_environments_status.py
```

或者查看API路由文件：
```bash
grep -r "DatabaseManager" backend/api/
```

## 📝 总结

1. **用户数据都在开发环境** ✅
2. **当前运行的是开发环境** ✅
3. **测试环境有3个vocab和2个grammar，但没有用户** ⚠️
4. **切换环境需要修改代码或使用环境变量** 📝

