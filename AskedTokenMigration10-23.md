# AskedToken 迁移计划 - 2024年10月23日

## 📋 迁移目标

将现有的 `AskedToken` 逐步替换为 `VocabNotation` 和 `GrammarNotation`，实现词汇和语法知识点标注的分离，更好管理并实现以后功能。

### 🎯 **迁移目标**
- 将现有的 `AskedToken` 逐步替换为 `VocabNotation` 和 `GrammarNotation`
- 实现词汇和语法知识点标注的分离
- 保持向后兼容性，确保现有功能不受影响

### 📊 **当前状况分析**
1. **数据结构**：现有的 `AskedToken` 已经包含 `type` 字段区分 token/sentence
2. **存储方式**：同时支持 JSON 文件和 SQLite 数据库
3. **使用场景**：目前所有 `AskedToken` 都是 `type="token"`，对应词汇标注

---

## 🚀 **迁移计划（5个阶段）**

### **阶段1：基础架构准备** ⚙️
**目标**：创建新的管理器和数据结构支持

**任务**：
1. **创建 VocabNotationManager**
   ```python
   # backend/data_managers/vocab_notation_manager.py
   class VocabNotationManager:
       def __init__(self, use_database: bool = True)
       def create_vocab_notation(self, user_id, text_id, sentence_id, token_id, vocab_id)
       def is_vocab_notation_exists(self, ...)
       def get_vocab_notations_for_article(self, ...)
   ```

2. **创建 GrammarNotationManager**
   ```python
   # backend/data_managers/grammar_notation_manager.py  
   class GrammarNotationManager:
       def __init__(self, use_database: bool = True)
       def create_grammar_notation(self, user_id, text_id, sentence_id, grammar_id, marked_token_ids)
       def is_grammar_notation_exists(self, ...)
   ```

3. **添加数据迁移工具**
   ```python
   # backend/data_managers/migration_tools.py
   class NotationMigrationTool:
       def migrate_asked_tokens_to_vocab_notations(self)
       def backup_existing_data(self)
       def validate_migration(self)
   ```

### **阶段2：并行运行期** 🔄
**目标**：新旧系统并行运行，确保兼容性

**任务**：
1. **扩展 AskedTokensManager**
   ```python
   # 添加向后兼容方法
   def mark_as_vocab_notation(self, ...) -> VocabNotation
   def mark_as_grammar_notation(self, ...) -> GrammarNotation
   ```

2. **创建统一接口**
   ```python
   # backend/data_managers/unified_notation_manager.py
   class UnifiedNotationManager:
       def mark_notation(self, type: str, ...)  # 'vocab' 或 'grammar'
       def get_notations(self, type: str, ...)
   ```

3. **前端适配**
   - 修改前端调用，支持新的数据结构
   - 保持现有 UI 不变

### **阶段3：数据迁移** 📦
**目标**：将现有 AskedToken 数据迁移到新结构

**任务**：
1. **数据迁移脚本**
   ```python
   # 迁移逻辑
   for asked_token in existing_asked_tokens:
       if asked_token.type == "token":
           # 转换为 VocabNotation
           vocab_notation = VocabNotation(
               user_id=asked_token.user_id,
               text_id=asked_token.text_id,
               sentence_id=asked_token.sentence_id,
               token_id=asked_token.sentence_token_id,
               vocab_id=asked_token.vocab_id
           )
       # 保存到新系统
   ```

2. **数据验证**
   - 确保迁移数据完整性
   - 验证新旧系统数据一致性

### **阶段4：逐步切换** 🔄
**目标**：逐步将功能切换到新系统

**任务**：
1. **API 层切换**
   ```python
   # 修改 API 端点
   @app.post("/api/user/vocab-notation")  # 新端点
   @app.post("/api/user/grammar-notation")  # 新端点
   
   # 保持旧端点兼容
   @app.post("/api/user/asked-tokens")  # 标记为废弃
   ```

2. **前端逐步切换**
   - 新功能使用新 API
   - 旧功能保持兼容

### **阶段5：清理和优化** 🧹
**目标**：移除旧系统，优化新系统

**任务**：
1. **移除 AskedToken 相关代码**
2. **优化新系统性能**
3. **更新文档和测试**

---

## 🛡️ **安全保障措施**

### **数据备份**
```python
# 每个阶段开始前自动备份
def backup_data():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"asked_tokens_backup_{timestamp}.json"
    # 备份现有数据
```

### **回滚机制**
```python
# 每个阶段都有回滚能力
def rollback_migration():
    # 从备份恢复数据
    # 切换回旧系统
```

### **验证检查**
```python
# 数据一致性验证
def validate_migration():
    old_count = count_asked_tokens()
    new_count = count_vocab_notations() + count_grammar_notations()
    assert old_count == new_count
```

---

## 📅 **时间安排建议**

- **阶段1**：1-2天（基础架构）
- **阶段2**：2-3天（并行运行）
- **阶段3**：1天（数据迁移）
- **阶段4**：3-5天（逐步切换）
- **阶段5**：1-2天（清理优化）

**总计**：8-13天

---

## 📝 **数据结构对比**

### **当前 AskedToken**
```python
@dataclass
class AskedToken:
    user_id: str
    text_id: int
    sentence_id: int
    sentence_token_id: Optional[int] = None
    type: Literal["token", "sentence"] = "token"
    vocab_id: Optional[int] = None
    grammar_id: Optional[int] = None
```

### **新的 VocabNotation**
```python
@dataclass
class VocabNotation:
    user_id: str
    text_id: int
    sentence_id: int
    token_id: int               # 当前句子中哪个 token
    vocab_id: Optional[int]     # 对应词汇表中的词汇
    created_at: Optional[str] = None  # 时间戳（可选）
```

### **新的 GrammarNotation**
```python
@dataclass
class GrammarNotation:
    user_id: str
    text_id: int
    sentence_id: int
    grammar_id: Optional[int]   # 对应 grammar_rules 表
    marked_token_ids: list[int] # 句中重点语法成分的 token id 列表
    created_at: Optional[str] = None
```

---

## 🔍 **当前使用情况分析**

### **AskedToken 使用位置**
1. **数据管理器**：`backend/data_managers/asked_tokens_manager.py`
2. **数据库模型**：`database_system/business_logic/models.py`
3. **CRUD 操作**：`database_system/business_logic/crud/asked_token_crud.py`
4. **业务逻辑**：`database_system/business_logic/managers/asked_token_manager.py`
5. **前端调用**：通过 API 端点 `/api/user/asked-tokens`

### **当前数据示例**
```json
[
  {
    "user_id": "default_user",
    "text_id": 1,
    "sentence_id": 3,
    "sentence_token_id": 22,
    "type": "token",
    "vocab_id": null,
    "grammar_id": null
  }
]
```

---

## ❓ **需要确认的问题**

1. **是否立即开始阶段1**？
2. **是否需要保持 AskedToken 作为兼容层**？
3. **数据库迁移策略**（是否需要新的数据库表）？
4. **前端切换的优先级**（哪些功能优先切换）？

---

## 📋 **检查清单**

### 阶段1 检查清单
- [x] 创建 VocabNotationManager 类 ✅
- [x] 创建 GrammarNotationManager 类 ✅
- [ ] 创建 NotationMigrationTool 类
- [x] 编写单元测试 ✅
- [x] 更新文档 ✅

### 阶段2 检查清单
- [x] 扩展 AskedTokensManager ✅
- [x] 创建 UnifiedNotationManager ✅
- [ ] 修改前端调用
- [x] 测试兼容性 ✅
- [ ] 性能测试

### 阶段3 检查清单
- [ ] 编写数据迁移脚本
- [ ] 执行数据备份
- [ ] 运行迁移脚本
- [ ] 验证数据完整性
- [ ] 测试功能正常性

### 阶段4 检查清单
- [ ] 创建新 API 端点
- [ ] 修改前端调用
- [ ] 测试新功能
- [ ] 监控系统稳定性
- [ ] 用户验收测试

### 阶段5 检查清单
- [ ] 移除旧代码
- [ ] 清理无用文件
- [ ] 优化性能
- [ ] 更新文档
- [ ] 最终测试

---

## 📚 **相关文档**

- [数据结构定义](backend/data_managers/data_classes_new.py)
- [当前 AskedToken 管理器](backend/data_managers/asked_tokens_manager.py)
- [数据库模型](database_system/business_logic/models.py)
- [前端 API 调用](frontend/my-web-ui/src/services/api.js)

---

**创建时间**：2024年10月23日  
**最后更新**：2024年10月23日  
**状态**：计划阶段
