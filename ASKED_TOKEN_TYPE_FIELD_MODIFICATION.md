# Asked Token Type 字段修改总结

## 📋 修改概述

为 `AskedToken` 数据结构添加 `type` 字段，用于区分标记的是**单词（token）**还是**句子（sentence）**的语法知识点。

### 需求背景

- **原有逻辑**: AskedToken 只能标记单词（需要 `sentence_token_id`）
- **新增需求**: 需要支持标记整个句子的语法知识点
- **向后兼容**: 现有数据不受影响，默认为 `type='token'`

---

## 🔧 修改详情

### 1. 数据库模型修改

**文件**: `database_system/business_logic/models.py`

#### 新增枚举类型
```python
class AskedTokenType(enum.Enum):
    TOKEN = 'token'      # 标记的是单词（需要 sentence_token_id）
    SENTENCE = 'sentence'  # 标记的是句子（sentence_token_id 可为空）
```

#### 修改 AskedToken 模型
- **新增字段**: `type` (Enum(AskedTokenType), 默认值='token')
- **修改字段**: `sentence_token_id` (nullable=True，原为 nullable=False)
- **修改约束**: UniqueConstraint 增加 `type` 字段

```python
class AskedToken(Base):
    __tablename__ = 'asked_tokens'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False)
    text_id = Column(Integer, ForeignKey('original_texts.text_id', ondelete='CASCADE'), nullable=False)
    sentence_id = Column(Integer, nullable=False)
    sentence_token_id = Column(Integer, nullable=True)  # ✅ 改为可空
    type = Column(Enum(AskedTokenType), default=AskedTokenType.TOKEN, nullable=False)  # ✅ 新增
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    __table_args__ = (
        # ... 省略 ...
        UniqueConstraint('user_id', 'text_id', 'sentence_id', 'sentence_token_id', 'type', ...)  # ✅ 新增 type
    )
```

---

### 2. 数据类 (DTO) 修改

#### 文件 1: `backend/data_managers/data_classes_new.py`
```python
@dataclass
class AskedToken:
    """已提问的 token 记录"""
    user_id: str
    text_id: int
    sentence_id: int
    sentence_token_id: Optional[int] = None  # ✅ 改为可选
    type: Literal["token", "sentence"] = "token"  # ✅ 新增
```

#### 文件 2: `backend/data_managers/data_classes.py`
```python
@dataclass
class AskedToken:
    """已提问的 token 记录"""
    user_id: str
    text_id: int
    sentence_id: int
    sentence_token_id: Optional[int] = None  # ✅ 改为可选
    type: str = "token"  # ✅ 新增
    asked_at: Optional[int] = None
```

---

### 3. CRUD 操作修改

**文件**: `database_system/business_logic/crud/asked_token_crud.py`

#### create 方法
```python
def create(self, user_id: str, text_id: int, 
           sentence_id: int, sentence_token_id: Optional[int] = None,
           type: str = 'token') -> AskedToken:
    """
    创建已提问token记录
    
    向后兼容逻辑：
    - 如果 type 未指定但 sentence_token_id 不为空，则默认 type='token'
    - 如果 type='sentence'，sentence_token_id 可以为 None
    """
    # 向后兼容：如果 type 未明确指定且 sentence_token_id 不为空，默认为 'token'
    if type is None and sentence_token_id is not None:
        type = 'token'
    
    asked_type = AskedTokenType.TOKEN if type == 'token' else AskedTokenType.SENTENCE
    
    asked_token = AskedToken(
        user_id=user_id,
        text_id=text_id,
        sentence_id=sentence_id,
        sentence_token_id=sentence_token_id,
        type=asked_type
    )
    # ... 保存逻辑 ...
```

#### get 方法
```python
def get(self, user_id: str, text_id: int, 
        sentence_id: int, sentence_token_id: Optional[int] = None,
        type: Optional[str] = None) -> Optional[AskedToken]:
    """支持根据 type 查询"""
    conditions = [
        AskedToken.user_id == user_id,
        AskedToken.text_id == text_id,
        AskedToken.sentence_id == sentence_id
    ]
    
    if sentence_token_id is not None:
        conditions.append(AskedToken.sentence_token_id == sentence_token_id)
    
    if type is not None:
        asked_type = AskedTokenType.TOKEN if type == 'token' else AskedTokenType.SENTENCE
        conditions.append(AskedToken.type == asked_type)
    
    return self.session.query(AskedToken).filter(and_(*conditions)).first()
```

#### delete 方法
```python
def delete(self, user_id: str, text_id: int, 
           sentence_id: int, sentence_token_id: Optional[int] = None,
           type: Optional[str] = None) -> bool:
    """支持根据 type 删除"""
    asked_token = self.get(user_id, text_id, sentence_id, sentence_token_id, type)
    if asked_token:
        self.session.delete(asked_token)
        self.session.commit()
        return True
    return False
```

---

### 4. 数据访问层修改

**文件**: `database_system/business_logic/data_access_layer.py`

所有方法签名都添加了 `type` 参数支持：

```python
class AskedTokenDataAccessLayer:
    def create_asked_token(self, user_id: str, text_id: int, 
                          sentence_id: int, sentence_token_id: Optional[int] = None,
                          type: str = 'token'):
        """创建已提问token记录"""
        return self._crud.create(user_id, text_id, sentence_id, sentence_token_id, type)
    
    def get_asked_token(self, user_id: str, text_id: int, 
                        sentence_id: int, sentence_token_id: Optional[int] = None,
                        type: Optional[str] = None):
        """获取指定的已提问token记录"""
        return self._crud.get(user_id, text_id, sentence_id, sentence_token_id, type)
    
    def delete_asked_token(self, user_id: str, text_id: int, 
                           sentence_id: int, sentence_token_id: Optional[int] = None,
                           type: Optional[str] = None) -> bool:
        """删除已提问token记录"""
        return self._crud.delete(user_id, text_id, sentence_id, sentence_token_id, type)
```

---

### 5. 管理器修改

**文件**: `database_system/business_logic/managers/asked_token_manager.py`

```python
class AskedTokenManager:
    def mark_token_as_asked(self, user_id: str, text_id: int, 
                           sentence_id: int, sentence_token_id: Optional[int] = None,
                           type: str = 'token') -> AskedToken:
        """标记token或sentence为已提问"""
        return self.dal.create_asked_token(user_id, text_id, sentence_id, sentence_token_id, type)
    
    def is_token_asked(self, user_id: str, text_id: int, 
                      sentence_id: int, sentence_token_id: Optional[int] = None,
                      type: Optional[str] = None) -> bool:
        """检查token或sentence是否已被提问"""
        return self.dal.get_asked_token(user_id, text_id, sentence_id, sentence_token_id, type) is not None
    
    def unmark_token_as_asked(self, user_id: str, text_id: int, 
                             sentence_id: int, sentence_token_id: Optional[int] = None,
                             type: Optional[str] = None) -> bool:
        """取消标记token或sentence为已提问"""
        return self.dal.delete_asked_token(user_id, text_id, sentence_id, sentence_token_id, type)
```

---

### 6. API 路由修改

**文件**: `server.py`

#### POST /api/user/asked-tokens
```python
@app.post("/api/user/asked-tokens")
async def mark_token_asked(payload: dict):
    """
    标记 token 或 sentence 为已提问
    
    支持两种类型的标记：
    1. type='token': 标记单词（需要 sentence_token_id）
    2. type='sentence': 标记句子（sentence_token_id 可选）
    
    向后兼容：如果 type 未指定但 sentence_token_id 存在，默认为 'token'
    """
    user_id = payload.get("user_id", "default_user")
    text_id = payload.get("text_id")
    sentence_id = payload.get("sentence_id")
    sentence_token_id = payload.get("sentence_token_id")
    type_param = payload.get("type", None)  # 新增：标记类型
    
    # 向后兼容逻辑：如果 type 未指定但 sentence_token_id 不为空，默认为 'token'
    if type_param is None:
        if sentence_token_id is not None:
            type_param = "token"
        else:
            type_param = "sentence"
    
    # 验证：如果是 token 类型，sentence_token_id 必须提供
    if type_param == "token" and sentence_token_id is None:
        return {"success": False, "error": "type='token' 时，sentence_token_id 是必需的"}
    
    # ... 调用 manager 标记 ...
```

---

### 7. 旧管理器修改（JSON 模式）

**文件**: `backend/data_managers/asked_tokens_manager.py`

```python
class AskedTokensManager:
    def mark_token_asked(self, user_id: str, text_id: int, sentence_id: int, 
                        sentence_token_id: int = None, type: str = "token") -> bool:
        """
        标记 token 或 sentence 为已提问
        
        向后兼容：如果 type 未指定但 sentence_token_id 不为空，默认为 'token'
        """
        # 向后兼容逻辑
        if type is None and sentence_token_id is not None:
            type = "token"
        
        asked_token = AskedToken(
            user_id=user_id,
            text_id=text_id,
            sentence_id=sentence_id,
            sentence_token_id=sentence_token_id,
            type=type
        )
        
        if self.use_database:
            return self._mark_asked_database(asked_token)
        else:
            return self._mark_asked_json(asked_token)
```

#### 数据库模式
```python
def _mark_asked_database(self, asked_token: AskedToken) -> bool:
    cursor.execute("""
        INSERT OR REPLACE INTO asked_tokens 
        (user_id, text_id, sentence_id, sentence_token_id, type)
        VALUES (?, ?, ?, ?, ?)
    """, (
        asked_token.user_id,
        asked_token.text_id,
        asked_token.sentence_id,
        asked_token.sentence_token_id,
        asked_token.type
    ))
```

#### JSON 模式
```python
def _mark_asked_json(self, asked_token: AskedToken) -> bool:
    # 检查是否已存在（需要比较 type 字段）
    for token_data in asked_tokens:
        if (token_data.get("text_id") == asked_token.text_id and
            token_data.get("sentence_id") == asked_token.sentence_id and
            token_data.get("sentence_token_id") == asked_token.sentence_token_id and
            token_data.get("type", "token") == asked_token.type):  # 向后兼容
            existing = True
            break
```

---

## 🔄 数据库迁移

### 迁移脚本

**文件**: `migrate_asked_tokens_add_type.py`

#### 功能
1. 备份现有 `asked_tokens` 表数据
2. 重建表结构（添加 `type` 字段，修改 `sentence_token_id` 为可空）
3. 恢复数据，所有现有记录设置 `type='token'`
4. 验证迁移结果

#### 使用方法
```bash
python migrate_asked_tokens_add_type.py
```

#### 迁移内容
- 为所有现有记录设置 `type='token'`（向后兼容）
- `sentence_token_id` 保持原值不变
- 保留 `created_at` 时间戳

---

## 📝 使用示例

### 1. 标记单词（Token）

```python
# API 请求
POST /api/user/asked-tokens
{
  "user_id": "user123",
  "text_id": 1,
  "sentence_id": 2,
  "sentence_token_id": 5,
  "type": "token"  # 或者不传，向后兼容
}
```

```python
# Python 代码
manager.mark_token_as_asked(
    user_id="user123",
    text_id=1,
    sentence_id=2,
    sentence_token_id=5,
    type="token"
)
```

### 2. 标记句子（Sentence/语法知识点）

```python
# API 请求
POST /api/user/asked-tokens
{
  "user_id": "user123",
  "text_id": 1,
  "sentence_id": 2,
  "type": "sentence"
  // sentence_token_id 可以不传或传 null
}
```

```python
# Python 代码
manager.mark_token_as_asked(
    user_id="user123",
    text_id=1,
    sentence_id=2,
    sentence_token_id=None,  # 或不传
    type="sentence"
)
```

### 3. 向后兼容（旧代码）

```python
# 旧代码仍然有效
manager.mark_token_asked(
    user_id="user123",
    text_id=1,
    sentence_id=2,
    sentence_token_id=5
)
# 自动识别为 type="token"
```

---

## ✅ 向后兼容性

### 自动识别规则
1. **如果 `type` 未指定 且 `sentence_token_id` 不为空** → 默认 `type='token'`
2. **如果 `type` 未指定 且 `sentence_token_id` 为空** → 默认 `type='sentence'`
3. **如果 `type='token'` 但 `sentence_token_id` 为空** → 报错

### 现有数据
- 所有现有数据在迁移后自动设置为 `type='token'`
- 现有 API 调用无需修改，自动向后兼容

---

## 🎯 修改点总结

### 必须修改的文件（共 7 个）

1. ✅ `database_system/business_logic/models.py` - 数据库模型
2. ✅ `backend/data_managers/data_classes_new.py` - 数据类 (新)
3. ✅ `backend/data_managers/data_classes.py` - 数据类 (旧)
4. ✅ `database_system/business_logic/crud/asked_token_crud.py` - CRUD 操作
5. ✅ `database_system/business_logic/data_access_layer.py` - 数据访问层
6. ✅ `database_system/business_logic/managers/asked_token_manager.py` - 管理器
7. ✅ `server.py` - API 路由

### 可选修改的文件（向后兼容，但建议更新）

8. ✅ `backend/data_managers/asked_tokens_manager.py` - 旧管理器 (JSON模式)

### 新增文件

9. ✅ `migrate_asked_tokens_add_type.py` - 数据库迁移脚本
10. ✅ `ASKED_TOKEN_TYPE_FIELD_MODIFICATION.md` - 本文档

---

## 🚀 部署步骤

1. **备份数据库**
   ```bash
   cp database_system/data_storage/data/dev.db database_system/data_storage/data/dev.db.backup
   ```

2. **运行迁移脚本**
   ```bash
   python migrate_asked_tokens_add_type.py
   ```

3. **验证迁移结果**
   - 检查 `asked_tokens` 表结构
   - 确认所有记录的 `type` 字段为 'token'

4. **更新代码**
   - 所有修改已完成，直接部署即可

5. **测试**
   - 测试标记单词功能（原有功能）
   - 测试标记句子功能（新功能）
   - 验证向后兼容性

---

## 📞 注意事项

1. **数据库迁移**：运行迁移脚本前请务必备份数据库
2. **API 兼容性**：旧的 API 调用仍然有效，无需修改前端代码
3. **类型验证**：新代码会验证 `type='token'` 时 `sentence_token_id` 必须存在
4. **唯一约束**：同一用户可以对同一句子既标记单词，又标记句子（因为 type 不同）

---

## 📅 修改日期

2025-10-16

---

**修改完成！所有代码已更新，数据库迁移脚本已准备就绪。**


