# FastAPI 与 DB Manager 集成说明

## 核心问题回答

**Q: FastAPI具体是怎么和DB版本的manager沟通的？**

**A: FastAPI通过依赖注入Session，然后实例化VocabManagerDB，调用其方法即可。VocabManagerDB内部会自动处理所有数据转换。**

---

## 🔄 完整的数据流转

### 1. 请求流程（以GET为例）

```
┌─────────────┐
│  前端请求    │  GET /api/v2/vocab/1
└──────┬──────┘
       ↓
┌─────────────────────────────────────────┐
│  FastAPI 路由 (vocab_routes.py)         │
│  @router.get("/{vocab_id}")             │
│  async def get_vocab(                   │
│      vocab_id: int,                     │
│      session: Session = Depends(...)    │← 依赖注入Session
│  ):                                     │
└──────┬──────────────────────────────────┘
       ↓
┌─────────────────────────────────────────┐
│  创建Manager实例                         │
│  vocab_manager = VocabManagerDB(session)│
└──────┬──────────────────────────────────┘
       ↓
┌─────────────────────────────────────────┐
│  调用Manager方法（返回DTO）              │
│  vocab = vocab_manager.get_vocab_by_id(1)│
│                                         │
│  VocabManagerDB 内部操作：              │
│  1. 调用 db_manager.get_vocab(1)       │
│     → 返回 VocabModel                  │
│  2. 使用 VocabAdapter.model_to_dto()   │
│     → 转换为 VocabDTO                  │
│  3. 返回 VocabDTO                      │
└──────┬──────────────────────────────────┘
       ↓
┌─────────────────────────────────────────┐
│  FastAPI 序列化DTO为JSON                │
│  return {                               │
│      "success": True,                   │
│      "data": {                          │
│          "vocab_id": vocab.vocab_id,    │
│          "vocab_body": vocab.vocab_body,│
│          ...                            │
│      }                                  │
│  }                                      │
└──────┬──────────────────────────────────┘
       ↓
┌─────────────┐
│  返回前端    │  JSON响应
└─────────────┘
```

---

## 📝 FastAPI需要的改动

### ❌ 旧版本（使用JSON文件）

```python
# 旧版本 - 使用VocabManagerJSON
from backend.data_managers import VocabManager  # 默认是JSON版本

@router.get("/{vocab_id}")
async def get_vocab(vocab_id: int):
    # 问题：需要从文件加载
    vocab_manager = VocabManager()
    vocab_manager.load_from_file("data/vocab_expressions.json")
    
    # 返回旧结构（Bundle）
    bundle = vocab_manager.vocab_bundles[vocab_id]
    
    return {
        "vocab": bundle.vocab,
        "examples": bundle.example
    }
```

### ✅ 新版本（使用数据库）

```python
# 新版本 - 使用VocabManagerDB
from backend.data_managers import VocabManagerDB  # 数据库版本
from sqlalchemy.orm import Session

@router.get("/{vocab_id}")
async def get_vocab(
    vocab_id: int,
    session: Session = Depends(get_db_session)  # 依赖注入
):
    # ✅ 只需要创建Manager实例
    vocab_manager = VocabManagerDB(session)
    
    # ✅ 调用方法，直接得到DTO
    vocab = vocab_manager.get_vocab_by_id(vocab_id)
    
    # ✅ DTO已经是标准格式，直接返回
    return {
        "success": True,
        "data": {
            "vocab_id": vocab.vocab_id,
            "vocab_body": vocab.vocab_body,
            "explanation": vocab.explanation,
            "source": vocab.source,
            "is_starred": vocab.is_starred,
            "examples": [
                {
                    "vocab_id": ex.vocab_id,
                    "text_id": ex.text_id,
                    "sentence_id": ex.sentence_id,
                    "context_explanation": ex.context_explanation,
                    "token_indices": ex.token_indices
                }
                for ex in vocab.examples
            ]
        }
    }
```

---

## 🔑 关键改动点

### 1. **依赖注入Session**

```python
# 定义Session依赖
def get_db_session():
    """依赖注入：提供数据库 Session"""
    db_manager = DatabaseManager('development')
    session = db_manager.get_session()
    try:
        yield session
        session.commit()  # 成功时自动提交
    except Exception as e:
        session.rollback()  # 失败时自动回滚
        raise e
    finally:
        session.close()  # 总是关闭Session

# 在路由中使用
@router.get("/{vocab_id}")
async def get_vocab(
    vocab_id: int,
    session: Session = Depends(get_db_session)  # ← 这里注入
):
    pass
```

**好处：**
- ✅ 自动管理Session生命周期
- ✅ 自动commit/rollback
- ✅ 自动close
- ✅ 无需手动处理数据库连接

### 2. **使用VocabManagerDB**

```python
# 导入新的Manager
from backend.data_managers import VocabManagerDB

# 在路由函数中
vocab_manager = VocabManagerDB(session)  # 传入Session
```

**好处：**
- ✅ 统一的DTO接口
- ✅ 内部自动处理数据转换
- ✅ 无需关心数据库细节

### 3. **数据转换在Manager内部**

FastAPI **不需要**处理任何数据转换！

```python
# FastAPI代码很简单
vocab = vocab_manager.get_vocab_by_id(vocab_id)  # 直接得到DTO

# vocab 已经是 VocabDTO 类型，包含：
# - vocab.vocab_id
# - vocab.vocab_body
# - vocab.explanation
# - vocab.source (已经是字符串"auto"/"qa"/"manual")
# - vocab.is_starred
# - vocab.examples (已经是VocabExampleDTO列表)
```

---

## 🎯 数据转换发生在哪里？

### VocabManagerDB 内部流程

```python
# backend/data_managers/vocab_manager_db.py

class VocabManager:
    def get_vocab_by_id(self, vocab_id: int) -> Optional[VocabDTO]:
        # 步骤1: 调用数据库Manager，得到Model
        vocab_model = self.db_manager.get_vocab(vocab_id)
        # vocab_model 是 VocabModel (ORM对象)
        # vocab_model.source 是 SourceType枚举
        
        if not vocab_model:
            return None
        
        # 步骤2: 使用Adapter转换为DTO
        vocab_dto = VocabAdapter.model_to_dto(vocab_model, include_examples=True)
        # vocab_dto 是 VocabDTO (dataclass)
        # vocab_dto.source 是 字符串 "auto"/"qa"/"manual"
        
        # 步骤3: 返回DTO给FastAPI
        return vocab_dto
```

### VocabAdapter 转换逻辑

```python
# backend/adapters/vocab_adapter.py

class VocabAdapter:
    @staticmethod
    def model_to_dto(model: VocabModel, include_examples: bool = True) -> VocabDTO:
        """ORM Model → DTO"""
        
        # 转换例句
        examples = []
        if include_examples and model.examples:
            examples = [
                VocabExampleAdapter.model_to_dto(ex)
                for ex in model.examples
            ]
        
        # 转换主体
        return VocabDTO(
            vocab_id=model.vocab_id,
            vocab_body=model.vocab_body,
            explanation=model.explanation,
            source=VocabAdapter._convert_source_to_dto(model.source),  # 枚举→字符串
            is_starred=model.is_starred,
            examples=examples
        )
    
    @staticmethod
    def _convert_source_to_dto(model_source: SourceType) -> str:
        """枚举转换：SourceType.AUTO → "auto" """
        return model_source.value.lower()
```

---

## 📊 完整示例：创建词汇

### FastAPI路由

```python
@router.post("/", summary="创建新词汇", status_code=201)
async def create_vocab(
    request: VocabCreateRequest,  # Pydantic模型，自动验证
    session: Session = Depends(get_db_session)
):
    try:
        # 1. 创建Manager
        vocab_manager = VocabManagerDB(session)
        
        # 2. 检查是否已存在
        existing = vocab_manager.get_vocab_by_body(request.vocab_body)
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"Vocab '{request.vocab_body}' already exists"
            )
        
        # 3. 创建词汇（内部自动转换）
        vocab = vocab_manager.add_new_vocab(
            vocab_body=request.vocab_body,
            explanation=request.explanation,
            source=request.source,
            is_starred=request.is_starred
        )
        # vocab 已经是 VocabDTO
        
        # 4. 返回DTO（FastAPI自动序列化为JSON）
        return {
            "success": True,
            "message": "Vocab created successfully",
            "data": {
                "vocab_id": vocab.vocab_id,
                "vocab_body": vocab.vocab_body,
                "explanation": vocab.explanation,
                "source": vocab.source,  # 已经是字符串
                "is_starred": vocab.is_starred
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### VocabManagerDB内部

```python
# backend/data_managers/vocab_manager_db.py

def add_new_vocab(self, vocab_body: str, explanation: str, 
                  source: str = "qa", is_starred: bool = False) -> VocabDTO:
    # 步骤1: 调用数据库Manager创建
    vocab_model = self.db_manager.add_vocab(
        vocab_body=vocab_body,
        explanation=explanation,
        source=source,  # 字符串 "qa"
        is_starred=is_starred
    )
    # vocab_model.source 会被转换为 SourceType.QA (枚举)
    
    # 步骤2: 转换为DTO返回
    return VocabAdapter.model_to_dto(vocab_model)
    # vocab_dto.source 会被转换回 "qa" (字符串)
```

---

## 🎨 架构优势

### 1. **FastAPI只关心业务逻辑**

```python
# FastAPI代码非常简洁
vocab_manager = VocabManagerDB(session)
vocab = vocab_manager.get_vocab_by_id(vocab_id)

# 不需要：
# ❌ 处理数据库连接
# ❌ 转换枚举类型
# ❌ 处理例句关联
# ❌ 手动commit/rollback
```

### 2. **VocabManagerDB是统一接口**

```python
# 对外提供统一的DTO接口
class VocabManager:
    def get_vocab_by_id(self, vocab_id: int) -> Optional[VocabDTO]
    def add_new_vocab(self, ...) -> VocabDTO
    def update_vocab(self, ...) -> Optional[VocabDTO]
    def delete_vocab(self, ...) -> bool
    # ... 所有方法都返回/接收DTO
```

### 3. **Adapter处理所有转换**

```python
# Model → DTO (从数据库读取)
vocab_dto = VocabAdapter.model_to_dto(vocab_model)

# DTO → Model (写入数据库)
vocab_model = VocabAdapter.dto_to_model(vocab_dto)
```

---

## 📋 总结

### FastAPI需要的改动

| 改动项 | 说明 |
|--------|------|
| 1. 导入新Manager | `from backend.data_managers import VocabManagerDB` |
| 2. 添加Session依赖 | `session: Session = Depends(get_db_session)` |
| 3. 创建Manager实例 | `vocab_manager = VocabManagerDB(session)` |
| 4. 调用方法 | `vocab = vocab_manager.get_vocab_by_id(id)` |
| 5. 返回数据 | DTO已经是标准格式，直接返回即可 |

### 数据转换位置

```
┌─────────────────┐
│   FastAPI       │  不处理转换，只调用Manager方法
└────────┬────────┘
         ↓
┌─────────────────┐
│ VocabManagerDB  │  调用Adapter进行转换
└────────┬────────┘
         ↓
┌─────────────────┐
│  VocabAdapter   │  ✅ 数据转换在这里！
│                 │  - Model → DTO
│                 │  - DTO → Model
│                 │  - 枚举 ↔ 字符串
└────────┬────────┘
         ↓
┌─────────────────┐
│  Database       │  ORM Models
└─────────────────┘
```

### 关键优势

1. ✅ **FastAPI代码简洁** - 只需要调用Manager方法
2. ✅ **自动数据转换** - Adapter处理所有转换
3. ✅ **自动Session管理** - 依赖注入处理
4. ✅ **类型安全** - DTO保证数据结构一致
5. ✅ **易于测试** - 每层职责明确

---

## 🚀 实际使用示例

```python
# backend/api/vocab_routes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.data_managers import VocabManagerDB

router = APIRouter(prefix="/api/v2/vocab")

@router.get("/{vocab_id}")
async def get_vocab(
    vocab_id: int,
    session: Session = Depends(get_db_session)  # 依赖注入
):
    # 1. 创建Manager（传入Session）
    vocab_manager = VocabManagerDB(session)
    
    # 2. 调用方法（得到DTO）
    vocab = vocab_manager.get_vocab_by_id(vocab_id)
    
    # 3. 检查结果
    if not vocab:
        raise HTTPException(status_code=404, detail="Vocab not found")
    
    # 4. 返回数据（DTO已经是正确格式）
    return {
        "success": True,
        "data": {
            "vocab_id": vocab.vocab_id,
            "vocab_body": vocab.vocab_body,
            "explanation": vocab.explanation,
            "source": vocab.source,  # 已经是字符串，不是枚举
            "is_starred": vocab.is_starred,
            "examples": vocab.examples  # 已经是DTO列表
        }
    }
```

**就是这么简单！** FastAPI只需要：
1. 注入Session
2. 创建VocabManagerDB
3. 调用方法
4. 返回结果

所有数据转换都在VocabManagerDB和Adapter内部自动完成！

