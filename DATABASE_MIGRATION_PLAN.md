# 数据库迁移计划

## 📊 当前状态

### ✅ 已完成（2025-10-01）
- [x] 数据库模型定义（models.py）- 包含所有核心表和关联表
- [x] CRUD 操作（crud.py）- 完整的增删改查功能
- [x] 词汇表 + 词汇例句迁移（22条词汇，22条例句）
- [x] 语法规则迁移（8条规则）
- [x] 文章数据迁移（3篇文章，61个句子，2494个tokens）
  - Harry Potter und der Stein der Weisen（51句，1862 tokens）
  - Yu Kongjian 文章 x2（各5句，316 tokens）
- [x] 数据访问层抽象（data_access_layer.py）
- [x] 支持两种文章格式（单文件 + 目录结构）

### 📁 JSON 数据迁移状态
```
backend/data/current/
├── vocab.json              ✅ 已迁移到 dev.db (22条)
├── grammar.json            ✅ 已迁移到 dev.db (8条)
├── dialogue_record.json    ⏳ 待迁移
└── articles/               ✅ 已迁移到 dev.db (3篇)
    ├── hp1_processed_*.json          ✅ Harry Potter (单文件格式)
    └── text_*/                        ✅ Yu Kongjian (目录格式)
        ├── original_text.json
        ├── sentences.json
        └── tokens.json
```

### 📊 数据库内容（dev.db）
```
✓ 词汇表 (vocab_expressions): 22 条
✓ 词汇例句 (vocab_expression_examples): 22 条
✓ 语法规则 (grammar_rules): 8 条
✓ 语法例句 (grammar_examples): 0 条 (JSON中为纯文本格式)
✓ 文章 (original_texts): 3 篇
✓ 句子 (sentences): 61 条
✓ Tokens (tokens): 2494 个
```

---

## 🎯 迁移路线图

### **阶段1：完成数据迁移** (1-2周)

#### Week 1: 核心数据迁移
```bash
# 1. 语法规则迁移
python -m database_system.business_logic.migrate_grammar

# 2. 文章数据迁移
python -m database_system.business_logic.migrate_articles

# 3. 对话历史迁移
python -m database_system.business_logic.migrate_dialogues
```

**任务清单：**
- [x] 扩展 `migrate.py` 添加 `migrate_grammar_and_examples()` ✅ 已完成
- [x] 实现 `migrate_articles()` 处理 text/sentences/tokens ✅ 已完成
  - [x] 支持单文件格式（*_processed_*.json）
  - [x] 支持目录格式（text_*/）
- [ ] 添加 DialogueHistory 模型（如需要）并迁移对话记录 ⏳ 可选
- [x] 每次迁移后验证数据完整性 ✅ 已完成

---

### **阶段2：创建适配器层** (1周)

为了平滑过渡，创建双模式支持：

```python
# database_system/business_logic/hybrid_adapter.py
class HybridDataAdapter:
    """混合模式：优先数据库，降级到 JSON"""
    
    def __init__(self, use_database: bool = True):
        self.use_database = use_database
        if use_database:
            self.db_session = get_session()
            self.dal = DataAccessManager(self.db_session)
        else:
            self.json_manager = VocabManager()  # 旧的 JSON 管理器
    
    def get_vocab(self, vocab_id: int):
        if self.use_database:
            return self.dal.vocab.get_vocab(vocab_id)
        else:
            return self.json_manager.get_vocab_by_id(vocab_id)
```

**任务清单：**
- [ ] 创建 `hybrid_adapter.py`
- [ ] 为每个数据类型实现适配器（vocab/grammar/articles）
- [ ] 添加环境变量控制：`USE_DATABASE=true/false`

---

### **阶段3：重构后端服务** (2-3周)

#### 3.1 更新 API 层 (`backend/main.py`)

**替换前：**
```python
vocab_manager = VocabManager()  # JSON
vocab = vocab_manager.get_vocab_by_id(vocab_id)
```

**替换后：**
```python
from database_system.business_logic.migrate import get_session
from database_system.business_logic.data_access_layer import DataAccessManager

session = get_session()
dal = DataAccessManager(session)
vocab = dal.vocab.get_vocab(vocab_id)
```

#### 3.2 更新 Assistants 层

```python
# backend/assistants/sub_assistants/vocab_explanation.py
# 修改为从数据库读取词汇，而非 JSON
```

**任务清单：**
- [ ] 重构 `backend/main.py` FastAPI 路由
- [ ] 更新所有 Assistant 子模块使用 DAL
- [ ] 重构 `backend/data_managers/` 下的管理器
- [ ] 添加数据库连接池管理

---

### **阶段4：前端适配** (1周)

前端 API 调用无需改变，但需要：

**任务清单：**
- [ ] 验证所有前端 API 调用仍正常工作
- [ ] 更新前端错误处理（数据库可能返回不同错误）
- [ ] 性能测试：对比 JSON vs DB 响应时间

---

### **阶段5：测试与优化** (1-2周)

#### 5.1 单元测试
```python
# tests/test_dal.py
def test_vocab_dal():
    session = get_test_session()
    dal = DataAccessManager(session)
    vocab = dal.vocab.add_vocab("test", "test explanation")
    assert vocab.vocab_id is not None
```

#### 5.2 集成测试
- [ ] 端到端测试：前端 → API → 数据库
- [ ] 性能测试：查询速度、并发处理
- [ ] 数据一致性测试

#### 5.3 性能优化
- [ ] 添加数据库索引（vocab_body, rule_name 等）
- [ ] 实现查询缓存（Redis 或内存缓存）
- [ ] 批量操作优化

---

### **阶段6：清理与文档** (1周)

**任务清单：**
- [ ] 删除或归档旧 JSON 文件
- [ ] 移除旧的 JSON 管理器代码
- [ ] 更新 README 和 API 文档
- [ ] 编写数据库维护文档（备份、恢复、迁移）

---

## 🔧 技术要点

### 数据库连接管理
```python
# backend/main.py
from contextlib import asynccontextmanager
from database_system.business_logic.migrate import get_session

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    app.state.db_session = get_session()
    yield
    # 关闭时
    app.state.db_session.close()

app = FastAPI(lifespan=lifespan)
```

### 环境配置
```python
# .env
USE_DATABASE=true
DATABASE_URL=sqlite:///database_system/data_storage/data/dev.db
```

### 数据备份
```bash
# 定期备份数据库
cp database_system/data_storage/data/dev.db backups/dev_$(date +%Y%m%d).db
```

---

## 📈 风险管理

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 数据迁移错误 | 高 | 1. 先在 test.db 测试<br>2. 保留 JSON 备份<br>3. 实现回滚机制 |
| 性能下降 | 中 | 1. 添加索引<br>2. 实现缓存<br>3. 优化查询 |
| API 兼容性问题 | 中 | 1. 保持 API 接口不变<br>2. 充分测试<br>3. 灰度发布 |
| 并发冲突 | 低 | 1. 使用事务<br>2. 乐观锁<br>3. 连接池 |

---

## 📝 回滚方案

如果迁移出现问题：

```python
# 1. 切换回 JSON 模式
USE_DATABASE=false

# 2. 或使用混合适配器降级
adapter = HybridDataAdapter(use_database=False)

# 3. 从备份恢复数据库
cp backups/dev_20250930.db database_system/data_storage/data/dev.db
```

---

## ✅ 验收标准

### 阶段1（数据迁移） ✅ 已达成
- [x] 所有核心 JSON 数据成功迁移到数据库
  - [x] 词汇 22条 ✅
  - [x] 语法规则 8条 ✅
  - [x] 文章 3篇 ✅
  - [x] 句子 61条 ✅
  - [x] Tokens 2494个 ✅
- [x] 无数据丢失或损坏 ✅
- [x] 关联关系完整（外键约束满足）✅

### 阶段2-6（待完成）
- [ ] 前端所有功能正常工作
- [ ] API 响应时间 < 100ms (P95)
- [ ] 完整的测试覆盖率 > 80%
- [ ] 文档完整且最新

---

## 🚀 下一步行动

### 阶段1已完成 ✅ - 立即可执行阶段2

1. **测试数据访问层** (15分钟)
```python
from database_system.business_logic.migrate import get_session
from database_system.business_logic.data_access_layer import DataAccessManager

session = get_session()
dal = DataAccessManager(session)

# 测试查询
vocab = dal.vocab.find_vocab_by_body("challenging")
print(vocab.explanation)

# 查询文章
texts = dal.vocab.session.query(OriginalText).all()
for t in texts:
    print(f"{t.text_id}: {t.text_title}")
```

2. **创建混合适配器** (1-2小时) - 推荐优先
- 创建 `hybrid_adapter.py`
- 支持数据库 + JSON双模式
- 添加环境变量控制开关

3. **替换第一个 API endpoint** (30-60分钟)
- 选择简单的端点（如 GET /vocab/{id}）
- 用 DAL 替换 JSON 管理器
- 测试前后端交互

### 重新运行完整迁移
```bash
# 如需重新迁移所有数据
Remove-Item database_system\data_storage\data\dev.db -Force
python -m database_system.business_logic.migrate
```

---

## 📞 需要帮助？

- 数据迁移问题 → 查看 `migrate.py`
- API 集成问题 → 查看 `data_access_layer.py`
- 性能问题 → 添加索引和缓存 