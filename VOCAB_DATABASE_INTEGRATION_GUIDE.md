# Vocab 数据库适配完整指南

## 📋 架构概览

```
前端 (React)
    ↓ HTTP请求
FastAPI (server.py)
    ↓ 路由转发
vocab_routes.py
    ↓ 调用业务层
VocabManagerDB (vocab_manager_db.py)
    ↓ 使用适配器
VocabAdapter (vocab_adapter.py)
    ↓ Model ↔ DTO 转换
数据库Manager (database_system/business_logic/managers/)
    ↓ CRUD操作
数据库DAL (database_system/business_logic/data_access_layer/)
    ↓ ORM操作
SQLAlchemy ORM
    ↓
SQLite数据库
```

## ✅ 已完成的组件

### 1. 数据库层 (`database_system/`)
- ✅ **ORM Models** - `business_logic/models.py`
  - `VocabExpression` - 词汇表
  - `VocabExpressionExample` - 例句表
  - `SourceType` - 来源枚举

- ✅ **CRUD** - `business_logic/crud/vocab_crud.py`
  - 创建、查询、更新、删除操作
  - 支持事务管理

- ✅ **DAL** - `business_logic/data_access_layer/vocab_dal.py`
  - 数据访问层封装
  - 查询优化

- ✅ **Manager** - `business_logic/managers/vocab_manager.py`
  - 高级业务逻辑
  - 统计、搜索等功能

### 2. 适配器层 (`backend/adapters/`)
- ✅ **VocabAdapter** - `vocab_adapter.py`
  - `model_to_dto()` - ORM Model → DTO
  - `dto_to_model()` - DTO → ORM Model
  - 枚举转换（SourceType ↔ 字符串）

- ✅ **VocabExampleAdapter** - `vocab_adapter.py`
  - 例句的Model ↔ DTO转换

### 3. 业务逻辑层 (`backend/data_managers/`)
- ✅ **VocabManagerDB** - `vocab_manager_db.py`
  - 统一的DTO接口
  - 所有业务方法封装
  - 错误处理

- ✅ **DTO定义** - `data_classes_new.py`
  - `VocabExpression` - 词汇DTO
  - `VocabExpressionExample` - 例句DTO

### 4. API层 (`backend/api/`)
- ✅ **vocab_routes.py** - FastAPI路由
  - RESTful API端点
  - 依赖注入（Session管理）
  - 请求/响应模型
  - 错误处理

### 5. 服务器集成 (`server.py`)
- ✅ FastAPI应用初始化
- ✅ CORS配置
- ✅ 路由注册
- ✅ 健康检查端点

## 🔄 数据流转换

### 查询流程（GET）
```
1. 前端发送请求
   ↓
2. vocab_routes.py 接收请求
   ↓
3. 创建数据库Session（依赖注入）
   ↓
4. VocabManagerDB.get_vocab_by_id(vocab_id)
   ↓
5. DBVocabManager.get_vocab(vocab_id) → 返回 VocabModel
   ↓
6. VocabAdapter.model_to_dto(model) → 转换为 VocabDTO
   ↓
7. 返回VocabDTO给API层
   ↓
8. API层序列化为JSON
   ↓
9. 返回给前端
```

### 创建流程（POST）
```
1. 前端发送创建请求（JSON）
   ↓
2. vocab_routes.py 接收并验证（Pydantic）
   ↓
3. VocabManagerDB.add_new_vocab(vocab_body, explanation, ...)
   ↓
4. DBVocabManager.add_vocab(...) → 创建并返回 VocabModel
   ↓
5. VocabAdapter.model_to_dto(model) → 转换为 VocabDTO
   ↓
6. Session.commit() 提交事务
   ↓
7. 返回VocabDTO给前端
```

## 🧪 测试步骤

### 步骤1: 数据库层测试

```bash
# 运行数据库层测试
python test_vocab_db_integration.py
```

**测试内容：**
- ✅ 数据库连接
- ✅ VocabManagerDB初始化
- ✅ CRUD操作
- ✅ Adapter转换
- ✅ 例句功能
- ✅ 搜索和统计

### 步骤2: 启动API服务器

```bash
# 启动FastAPI服务器
python server.py

# 或使用uvicorn
uvicorn server:app --reload --port 8001
```

**预期输出：**
```
🚀 启动 Asked Tokens API 服务器...
📡 服务地址: http://localhost:8001
📚 API 文档: http://localhost:8001/docs
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### 步骤3: API集成测试

在**另一个终端**中运行：

```bash
# 运行API集成测试
python test_vocab_api_integration.py
```

**测试内容：**
- ✅ 健康检查
- ✅ 获取所有词汇
- ✅ 创建词汇
- ✅ 获取单个词汇
- ✅ 更新词汇
- ✅ 切换收藏
- ✅ 添加例句
- ✅ 搜索词汇
- ✅ 获取统计
- ✅ 删除词汇

### 步骤4: 浏览器测试

访问 API 文档：
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

在Swagger UI中可以交互式测试所有API端点。

## 📡 API端点列表

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/v2/vocab/` | 获取所有词汇（分页） |
| GET | `/api/v2/vocab/{id}` | 获取单个词汇 |
| POST | `/api/v2/vocab/` | 创建新词汇 |
| PUT | `/api/v2/vocab/{id}` | 更新词汇 |
| DELETE | `/api/v2/vocab/{id}` | 删除词汇 |
| POST | `/api/v2/vocab/{id}/star` | 切换收藏状态 |
| GET | `/api/v2/vocab/search/` | 搜索词汇 |
| POST | `/api/v2/vocab/examples` | 添加例句 |
| GET | `/api/v2/vocab/stats/summary` | 获取统计 |

## 🔍 前端集成示例

```javascript
// 获取所有词汇
const getVocabs = async () => {
  const response = await fetch('http://localhost:8001/api/v2/vocab/?limit=20');
  const data = await response.json();
  if (data.success) {
    console.log('词汇列表:', data.data.vocabs);
  }
};

// 创建词汇
const createVocab = async (vocabBody, explanation) => {
  const response = await fetch('http://localhost:8001/api/v2/vocab/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      vocab_body: vocabBody,
      explanation: explanation,
      source: 'manual',
      is_starred: false
    })
  });
  const data = await response.json();
  if (data.success) {
    console.log('创建成功:', data.data);
  }
};

// 搜索词汇
const searchVocabs = async (keyword) => {
  const response = await fetch(
    `http://localhost:8001/api/v2/vocab/search/?keyword=${keyword}`
  );
  const data = await response.json();
  if (data.success) {
    console.log('搜索结果:', data.data.vocabs);
  }
};
```

## 🎯 下一步计划

### 当前阶段：Vocab功能数据库适配 ✅

1. ✅ 数据库层实现
2. ✅ 适配器层实现
3. ✅ 业务逻辑层实现
4. ✅ API层实现
5. ✅ 服务器集成
6. 🔄 **测试和验证**（当前）
7. ⏳ 前端集成（下一步）

### 下一阶段：其他功能数据库适配

在完成Vocab功能的测试和前端集成后，可以按照相同的模式适配其他功能：

1. **GrammarRule** - 语法规则管理
2. **OriginalText** - 文章管理
3. **DialogueRecord** - 对话记录管理
4. **AskedTokens** - 已提问token管理

## 📝 关键设计模式

### 1. 适配器模式（Adapter Pattern）
- **目的**：分离数据库模型和业务DTO
- **位置**：`backend/adapters/vocab_adapter.py`
- **优点**：
  - 数据库变更不影响业务层
  - DTO可以包含计算字段
  - 类型转换集中管理

### 2. 依赖注入（Dependency Injection）
- **目的**：管理数据库Session生命周期
- **位置**：`backend/api/vocab_routes.py::get_db_session()`
- **优点**：
  - 自动管理commit/rollback
  - 自动关闭连接
  - 易于测试

### 3. 分层架构（Layered Architecture）
```
API层 (vocab_routes.py)
  ↓ 依赖
业务逻辑层 (vocab_manager_db.py)
  ↓ 依赖
适配器层 (vocab_adapter.py)
  ↓ 依赖
数据库层 (database_system/)
```

### 4. DTO模式（Data Transfer Object）
- **目的**：在不同层之间传输数据
- **位置**：`backend/data_managers/data_classes_new.py`
- **优点**：
  - 解耦数据结构
  - 可序列化
  - 类型安全

## ❓ 常见问题

### Q1: 为什么需要Adapter？
A: Adapter将数据库ORM Model和业务DTO解耦，使得：
- 数据库表结构变化不影响业务逻辑
- 可以在DTO中添加计算字段
- 枚举类型可以转换为字符串

### Q2: Session管理怎么做？
A: 使用FastAPI的依赖注入：
```python
def get_db_session():
    session = db_manager.get_session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
```

### Q3: 如何添加新的API端点？
A: 在`vocab_routes.py`中添加新的路由函数：
```python
@router.get("/my-endpoint")
async def my_endpoint(session: Session = Depends(get_db_session)):
    vocab_manager = VocabManagerDB(session)
    # 实现逻辑
    return {"success": True, "data": ...}
```

### Q4: 前端如何调用？
A: 使用标准的HTTP请求：
```javascript
const response = await fetch('http://localhost:8001/api/v2/vocab/...');
const data = await response.json();
```

## 📚 相关文档

- `backend/api/VOCAB_API_USAGE.md` - API使用详细文档
- `backend/api/QUICK_START.md` - 快速开始指南
- `backend/adapters/README.md` - 适配器详细说明
- `database_system/README.md` - 数据库系统文档

## 🎉 总结

Vocab功能的数据库适配已经完成所有核心组件的实现：

1. ✅ **数据库层** - ORM Models、CRUD、DAL、Manager
2. ✅ **适配器层** - Model ↔ DTO转换
3. ✅ **业务逻辑层** - VocabManagerDB统一接口
4. ✅ **API层** - RESTful端点
5. ✅ **服务器** - FastAPI集成

**现在可以运行测试验证整个流程！**

```bash
# 1. 数据库层测试
python test_vocab_db_integration.py

# 2. 启动服务器
python server.py

# 3. API测试（在另一个终端）
python test_vocab_api_integration.py
```

