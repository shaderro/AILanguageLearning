# Swagger UI 测试指南

## 🎯 目标

通过浏览器中的Swagger UI交互式测试Vocab API，查看完整的请求和响应。

---

## 📋 步骤

### 步骤1: 启动服务器

在终端运行：

```bash
# Windows
start_server.bat

# 或者直接运行
python server.py
```

**预期输出：**
```
Starting FastAPI server...

Once started, you can access:
- Swagger UI: http://localhost:8001/docs
- API Health: http://localhost:8001/api/health

INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Application startup complete.
```

---

### 步骤2: 打开Swagger UI

在浏览器中访问：
```
http://localhost:8001/docs
```

你会看到一个漂亮的API文档界面。

---

### 步骤3: 测试健康检查

1. 找到 `GET /api/health` 端点
2. 点击展开
3. 点击 **"Try it out"**
4. 点击 **"Execute"**

**查看响应：**
```json
{
  "status": "healthy",
  "message": "Language Learning API is running",
  "services": {
    "asked_tokens": "active",
    "vocab_v2": "active (database)"
  }
}
```

---

### 步骤4: 测试获取所有词汇

1. 找到 `GET /api/v2/vocab/` 端点（在 vocab-db 标签下）
2. 点击展开
3. 点击 **"Try it out"**
4. 设置参数：
   - `skip`: 0
   - `limit`: 5
   - `starred_only`: false
5. 点击 **"Execute"**

**查看响应：**
```json
{
  "success": true,
  "data": {
    "vocabs": [
      {
        "vocab_id": 1,
        "vocab_body": "challenging",
        "explanation": "具有挑战性的...",
        "source": "auto",  ← 注意：已经是字符串
        "is_starred": true
      },
      ...
    ],
    "count": 5,
    "skip": 0,
    "limit": 5
  }
}
```

**关键观察点：**
- `source` 字段是字符串 `"auto"`/`"qa"`/`"manual"`
- 不是数据库中的枚举类型
- 这证明 Adapter 已经完成了转换

---

### 步骤5: 测试获取单个词汇（包含例句）

1. 找到 `GET /api/v2/vocab/{vocab_id}` 端点
2. 点击展开
3. 点击 **"Try it out"**
4. 设置参数：
   - `vocab_id`: 1
   - `include_examples`: true
5. 点击 **"Execute"**

**查看响应：**
```json
{
  "success": true,
  "data": {
    "vocab_id": 1,
    "vocab_body": "challenging",
    "explanation": "具有挑战性的...",
    "source": "auto",
    "is_starred": true,
    "examples": [
      {
        "vocab_id": 1,
        "text_id": 1,
        "sentence_id": 3,
        "context_explanation": "...",
        "token_indices": [5, 6]
      }
    ]
  }
}
```

**关键观察点：**
- 例句已经是DTO格式
- `token_indices` 是数组
- 所有数据都是前端可以直接使用的格式

---

### 步骤6: 测试创建词汇

1. 找到 `POST /api/v2/vocab/` 端点
2. 点击展开
3. 点击 **"Try it out"**
4. 在 Request body 中输入：

```json
{
  "vocab_body": "swagger_test",
  "explanation": "通过Swagger测试创建的词汇",
  "source": "manual",
  "is_starred": true
}
```

5. 点击 **"Execute"**

**查看响应：**
```json
{
  "success": true,
  "message": "Vocab created successfully",
  "data": {
    "vocab_id": 30,  ← 新生成的ID
    "vocab_body": "swagger_test",
    "explanation": "通过Swagger测试创建的词汇",
    "source": "manual",
    "is_starred": true
  }
}
```

**记住这个 `vocab_id`，后续步骤会用到！**

---

### 步骤7: 测试搜索词汇

1. 找到 `GET /api/v2/vocab/search/` 端点
2. 点击展开
3. 点击 **"Try it out"**
4. 设置参数：
   - `keyword`: swagger
5. 点击 **"Execute"**

**查看响应：**
```json
{
  "success": true,
  "data": {
    "vocabs": [
      {
        "vocab_id": 30,
        "vocab_body": "swagger_test",
        ...
      }
    ],
    "count": 1,
    "keyword": "swagger"
  }
}
```

---

### 步骤8: 测试添加例句

1. 找到 `POST /api/v2/vocab/examples` 端点
2. 点击展开
3. 点击 **"Try it out"**
4. 在 Request body 中输入：

```json
{
  "vocab_id": 30,  ← 使用步骤6创建的ID
  "text_id": 1,
  "sentence_id": 1,
  "context_explanation": "这是通过Swagger添加的例句",
  "token_indices": [1, 2, 3]
}
```

5. 点击 **"Execute"**

**查看响应：**
```json
{
  "success": true,
  "message": "Vocab example created successfully",
  "data": {
    "vocab_id": 30,
    "text_id": 1,
    "sentence_id": 1,
    "context_explanation": "这是通过Swagger添加的例句",
    "token_indices": [1, 2, 3]
  }
}
```

---

### 步骤9: 再次查询词汇（验证例句）

1. 回到 `GET /api/v2/vocab/{vocab_id}` 端点
2. 输入 `vocab_id`: 30
3. `include_examples`: true
4. 点击 **"Execute"**

**查看响应：**
```json
{
  "success": true,
  "data": {
    "vocab_id": 30,
    "vocab_body": "swagger_test",
    "examples": [
      {
        "vocab_id": 30,
        "text_id": 1,
        "sentence_id": 1,
        "context_explanation": "这是通过Swagger添加的例句",
        "token_indices": [1, 2, 3]
      }
    ]
  }
}
```

**验证成功！** 例句已经关联到词汇。

---

### 步骤10: 测试获取统计

1. 找到 `GET /api/v2/vocab/stats/summary` 端点
2. 点击展开
3. 点击 **"Try it out"**
4. 点击 **"Execute"**

**查看响应：**
```json
{
  "success": true,
  "data": {
    "total": 30,
    "starred": 3,
    "auto": 29,
    "manual": 1
  }
}
```

---

### 步骤11: 清理测试数据

1. 找到 `DELETE /api/v2/vocab/{vocab_id}` 端点
2. 点击展开
3. 点击 **"Try it out"**
4. 输入 `vocab_id`: 30
5. 点击 **"Execute"**

**查看响应：**
```json
{
  "success": true,
  "message": "Vocab ID 30 deleted successfully"
}
```

---

## 🔍 查看数据转换过程

### 在FastAPI路由中（vocab_routes.py）

```python
@router.get("/{vocab_id}")
async def get_vocab(
    vocab_id: int,
    session: Session = Depends(get_db_session)
):
    # 1. 创建Manager
    vocab_manager = VocabManagerDB(session)
    
    # 2. 调用方法（得到DTO）
    vocab = vocab_manager.get_vocab_by_id(vocab_id)
    # vocab.source 已经是字符串 "auto"/"qa"/"manual"
    
    # 3. 直接返回（FastAPI自动序列化为JSON）
    return {
        "success": True,
        "data": {
            "vocab_id": vocab.vocab_id,
            "source": vocab.source,  # 直接用，无需转换
            ...
        }
    }
```

### 在VocabManagerDB内部（vocab_manager_db.py）

```python
def get_vocab_by_id(self, vocab_id: int) -> Optional[VocabDTO]:
    # 1. 从数据库获取Model
    vocab_model = self.db_manager.get_vocab(vocab_id)
    # vocab_model.source = SourceType.AUTO (枚举)
    
    # 2. 使用Adapter转换
    vocab_dto = VocabAdapter.model_to_dto(vocab_model)
    # vocab_dto.source = "auto" (字符串)
    
    # 3. 返回DTO
    return vocab_dto
```

### 在VocabAdapter中（vocab_adapter.py）

```python
@staticmethod
def model_to_dto(model: VocabModel) -> VocabDTO:
    return VocabDTO(
        vocab_id=model.vocab_id,
        vocab_body=model.vocab_body,
        explanation=model.explanation,
        source=VocabAdapter._convert_source_to_dto(model.source),  # ← 转换在这里
        is_starred=model.is_starred,
        examples=[...]
    )

@staticmethod
def _convert_source_to_dto(model_source: SourceType) -> str:
    # SourceType.AUTO -> "auto"
    return model_source.value.lower()
```

---

## 📊 数据流转总结

```
浏览器请求
    ↓
FastAPI (vocab_routes.py)
    | vocab_manager = VocabManagerDB(session)
    | vocab = vocab_manager.get_vocab_by_id(1)
    ↓
VocabManagerDB (vocab_manager_db.py)
    | vocab_model = db_manager.get_vocab(1)
    | vocab_dto = VocabAdapter.model_to_dto(vocab_model)
    | return vocab_dto
    ↓
VocabAdapter (vocab_adapter.py)
    | 转换: SourceType.AUTO -> "auto"
    | 转换: SQLAlchemy关系 -> List[DTO]
    | 返回: VocabDTO
    ↓
FastAPI自动序列化为JSON
    ↓
浏览器收到响应: {"source": "auto"}
```

---

## ✅ 验证要点

通过Swagger UI测试，你应该能看到：

1. ✅ **source字段是字符串**
   - 响应中 `"source": "auto"` 而不是 `"source": 0` 或枚举值

2. ✅ **examples是数组**
   - 不是数据库关系对象
   - 每个example都有完整的字段

3. ✅ **token_indices是数组**
   - `[1, 2, 3]` 而不是 `"1,2,3"` 或其他格式

4. ✅ **所有数据都是前端友好的格式**
   - 字符串、数字、布尔值、数组
   - 没有枚举、没有ORM对象

5. ✅ **FastAPI代码简洁**
   - 只调用Manager方法
   - 不需要任何转换代码

---

## 🎉 结论

通过Swagger UI测试，你可以：

1. 看到完整的API请求和响应
2. 验证数据格式正确
3. 确认数据转换成功
4. 无需前端代码就能测试整个流程

**所有数据转换都在VocabManagerDB和Adapter内部完成，FastAPI只需要调用方法即可！**

