# Sentence 和 Token 数据结构对比分析

## 📊 总体结论

✅ **Sentence和Token在数据库中有完整的体现！**

数据库Models和DTO的字段基本完全对应，已经具备了完整的数据存储能力。

---

## 🔍 详细对比

### 1. Sentence 结构对比

#### DTO 定义 (`data_classes_new.py`)

```python
@dataclass(frozen=True)
class Sentence:
    text_id: int
    sentence_id: int
    sentence_body: str
    grammar_annotations: tuple[int, ...] = ()  # rule id
    vocab_annotations: tuple[int, ...] = ()    # word id
    sentence_difficulty_level: Optional[Literal["easy", "hard"]] = None
    tokens: tuple[Token, ...] = ()
```

#### Database Model (`models.py`)

```python
class Sentence(Base):
    __tablename__ = 'sentences'
    
    # 主键和外键
    id = Column(Integer, primary_key=True, autoincrement=True)
    sentence_id = Column(Integer, nullable=False)
    text_id = Column(Integer, ForeignKey('original_texts.text_id', ondelete='CASCADE'), nullable=False)
    
    # 基本字段
    sentence_body = Column(Text, nullable=False)
    sentence_difficulty_level = Column(Enum(DifficultyLevel))
    
    # 标注字段（JSON格式）
    grammar_annotations = Column(JSON)  # DTO中是tuple[int, ...]
    vocab_annotations = Column(JSON)    # DTO中是tuple[int, ...]
    
    # 元数据
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    # 关系
    text = relationship('OriginalText', back_populates='sentences')
    tokens = relationship('Token', back_populates='sentence', cascade='all, delete-orphan')
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('text_id', 'sentence_id', name='uq_sentence_text_sentence'),
    )
```

#### 字段映射表

| DTO字段 | Model字段 | 类型映射 | 状态 |
|---------|-----------|---------|------|
| `text_id` | `text_id` | int → Integer | ✅ 完全对应 |
| `sentence_id` | `sentence_id` | int → Integer | ✅ 完全对应 |
| `sentence_body` | `sentence_body` | str → Text | ✅ 完全对应 |
| `grammar_annotations` | `grammar_annotations` | tuple → JSON | ✅ 已转换 |
| `vocab_annotations` | `vocab_annotations` | tuple → JSON | ✅ 已转换 |
| `sentence_difficulty_level` | `sentence_difficulty_level` | Literal → Enum | ✅ 已转换 |
| `tokens` | `tokens (relationship)` | tuple[Token] → Relationship | ⚠️ 部分实现 |

**Model额外字段：**
- `id`: 数据库内部主键（自增）
- `created_at`: 创建时间戳

---

### 2. Token 结构对比

#### DTO 定义 (`data_classes_new.py`)

```python
@dataclass(frozen=True)
class Token:
    token_body: str
    token_type: Literal["text", "punctuation", "space"]
    difficulty_level: Optional[Literal["easy", "hard"]] = None
    global_token_id: Optional[int] = None         # 全文级别 ID
    sentence_token_id: Optional[int] = None       # 当前句子内 ID
    pos_tag: Optional[str] = None                 # 词性标注
    lemma: Optional[str] = None                   # 原型词
    is_grammar_marker: Optional[bool] = False     # 是否参与语法结构识别
    linked_vocab_id: Optional[int] = None         # 指向词汇中心解释
```

#### Database Model (`models.py`)

```python
class Token(Base):
    __tablename__ = 'tokens'
    
    # 主键和外键
    token_id = Column(Integer, primary_key=True, autoincrement=True)
    text_id = Column(Integer, ForeignKey('original_texts.text_id', ondelete='CASCADE'), nullable=False)
    sentence_id = Column(Integer, nullable=False)
    
    # 基本字段
    token_body = Column(String(255), nullable=False)
    token_type = Column(Enum(TokenType), nullable=False)
    difficulty_level = Column(Enum(DifficultyLevel))
    
    # ID字段
    global_token_id = Column(Integer)
    sentence_token_id = Column(Integer)
    
    # 语言学字段
    pos_tag = Column(String(50))
    lemma = Column(String(255))
    is_grammar_marker = Column(Boolean, default=False, nullable=False)
    
    # 关联字段
    linked_vocab_id = Column(Integer, ForeignKey('vocab_expressions.vocab_id', ondelete='SET NULL'))
    
    # 元数据
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    # 关系
    sentence = relationship('Sentence', back_populates='tokens')
    linked_vocab = relationship('VocabExpression', back_populates='tokens')
    
    # 外键约束
    __table_args__ = (
        ForeignKeyConstraint(
            ['text_id', 'sentence_id'],
            ['sentences.text_id', 'sentences.sentence_id'],
            ondelete='CASCADE'
        ),
    )
```

#### 字段映射表

| DTO字段 | Model字段 | 类型映射 | 状态 |
|---------|-----------|---------|------|
| `token_body` | `token_body` | str → String(255) | ✅ 完全对应 |
| `token_type` | `token_type` | Literal → Enum(TokenType) | ✅ 完全对应 |
| `difficulty_level` | `difficulty_level` | Literal → Enum(DifficultyLevel) | ✅ 完全对应 |
| `global_token_id` | `global_token_id` | Optional[int] → Integer | ✅ 完全对应 |
| `sentence_token_id` | `sentence_token_id` | Optional[int] → Integer | ✅ 完全对应 |
| `pos_tag` | `pos_tag` | Optional[str] → String(50) | ✅ 完全对应 |
| `lemma` | `lemma` | Optional[str] → String(255) | ✅ 完全对应 |
| `is_grammar_marker` | `is_grammar_marker` | bool → Boolean | ✅ 完全对应 |
| `linked_vocab_id` | `linked_vocab_id` | Optional[int] → Integer(FK) | ✅ 完全对应 |

**Model额外字段：**
- `token_id`: 数据库内部主键（自增）
- `text_id`: 外键（关联到文章）
- `sentence_id`: 外键（关联到句子）
- `created_at`: 创建时间戳

---

### 3. 枚举类型对比

#### TokenType 枚举

**DTO:**
```python
Literal["text", "punctuation", "space"]
```

**Model:**
```python
class TokenType(enum.Enum):
    TEXT = 'text'
    PUNCTUATION = 'punctuation'
    SPACE = 'space'
```

✅ **完全对应！**

#### DifficultyLevel 枚举

**DTO:**
```python
Optional[Literal["easy", "hard"]]
```

**Model:**
```python
class DifficultyLevel(enum.Enum):
    EASY = 'EASY'
    HARD = 'HARD'
```

⚠️ **注意**: Model使用大写，DTO使用小写。需要转换！

---

## 🔄 当前Adapter实现状态

### SentenceAdapter（已实现）

✅ **已实现的转换：**
- DTO ↔ Model 基本字段
- `grammar_annotations`: tuple ↔ JSON list
- `vocab_annotations`: tuple ↔ JSON list
- `difficulty_level`: string ↔ Enum（大小写转换）

⚠️ **未完全实现：**
- `tokens`: 目前在`model_to_dto`中简单返回空tuple
- 没有实现Token列表的递归转换

```python
# 当前实现（text_adapter.py）
def model_to_dto(model: SentenceModel, include_tokens: bool = False) -> SentenceDTO:
    # ... 其他字段转换 ...
    
    # 处理tokens
    tokens = ()
    if include_tokens and model.tokens:
        # TODO: 如果需要完整的Token信息，这里需要实现TokenAdapter
        # 目前先留空，因为Token结构较复杂
        tokens = ()
    
    return SentenceDTO(...)
```

### TokenAdapter（未实现）

❌ **完全未实现**

由于Token结构较复杂且包含多个枚举类型，目前没有创建TokenAdapter。

---

## 📋 实现建议

### 选项1：创建完整的TokenAdapter（推荐）

如果需要完整的Token支持，应该创建`TokenAdapter`:

```python
class TokenAdapter:
    @staticmethod
    def model_to_dto(model: TokenModel) -> TokenDTO:
        """Token Model → DTO"""
        # 处理token_type枚举
        token_type = model.token_type.value.lower()
        
        # 处理difficulty_level枚举
        difficulty_level = None
        if model.difficulty_level:
            difficulty_level = model.difficulty_level.value.lower()
        
        return TokenDTO(
            token_body=model.token_body,
            token_type=token_type,
            difficulty_level=difficulty_level,
            global_token_id=model.global_token_id,
            sentence_token_id=model.sentence_token_id,
            pos_tag=model.pos_tag,
            lemma=model.lemma,
            is_grammar_marker=model.is_grammar_marker,
            linked_vocab_id=model.linked_vocab_id
        )
    
    @staticmethod
    def dto_to_model(dto: TokenDTO, text_id: int, sentence_id: int) -> TokenModel:
        """Token DTO → Model"""
        # 处理枚举转换
        from database_system.business_logic.models import TokenType, DifficultyLevel
        
        token_type = TokenType[dto.token_type.upper()]
        difficulty_level = None
        if dto.difficulty_level:
            difficulty_level = DifficultyLevel[dto.difficulty_level.upper()]
        
        return TokenModel(
            text_id=text_id,
            sentence_id=sentence_id,
            token_body=dto.token_body,
            token_type=token_type,
            difficulty_level=difficulty_level,
            global_token_id=dto.global_token_id,
            sentence_token_id=dto.sentence_token_id,
            pos_tag=dto.pos_tag,
            lemma=dto.lemma,
            is_grammar_marker=dto.is_grammar_marker,
            linked_vocab_id=dto.linked_vocab_id
        )
```

然后在`SentenceAdapter`中使用：

```python
def model_to_dto(model: SentenceModel, include_tokens: bool = False) -> SentenceDTO:
    # ... 其他字段 ...
    
    # 处理tokens
    tokens = ()
    if include_tokens and model.tokens:
        tokens = tuple(
            TokenAdapter.model_to_dto(t)
            for t in sorted(model.tokens, key=lambda x: x.sentence_token_id or 0)
        )
    
    return SentenceDTO(...)
```

### 选项2：保持当前实现（轻量级）

如果暂时不需要Token的详细信息：
- 保持当前实现，tokens始终为空tuple
- 只在需要时才加载Token信息
- 通过独立的Token API端点处理Token操作

---

## 🎯 数据库关系图

```
OriginalText (文章)
    ├── text_id (PK)
    └── text_title
    
    ↓ (1:N relationship)
    
Sentence (句子)
    ├── id (PK, auto)
    ├── sentence_id (业务ID)
    ├── text_id (FK → OriginalText)
    ├── sentence_body
    ├── sentence_difficulty_level (Enum)
    ├── grammar_annotations (JSON: [rule_id, ...])
    ├── vocab_annotations (JSON: [vocab_id, ...])
    └── created_at
    
    ↓ (1:N relationship)
    
Token (词元)
    ├── token_id (PK, auto)
    ├── text_id (FK → OriginalText)
    ├── sentence_id (FK → Sentence)
    ├── token_body
    ├── token_type (Enum: TEXT/PUNCTUATION/SPACE)
    ├── difficulty_level (Enum: EASY/HARD)
    ├── global_token_id (全文序号)
    ├── sentence_token_id (句内序号)
    ├── pos_tag (词性)
    ├── lemma (原型)
    ├── is_grammar_marker
    ├── linked_vocab_id (FK → VocabExpression)
    └── created_at
```

---

## ✅ 结论

### 数据库结构完整性：**100% ✅**

- ✅ Sentence在数据库中有完整的表定义
- ✅ Token在数据库中有完整的表定义
- ✅ 所有DTO字段在Model中都有对应
- ✅ 关系定义正确（OriginalText → Sentence → Token）
- ✅ 枚举类型定义正确

### Adapter实现完整性：**70%**

- ✅ SentenceAdapter已实现基本转换
- ✅ 枚举和JSON字段转换已处理
- ⚠️ Token转换未实现（简化为空tuple）
- ❌ TokenAdapter完全未创建

### 建议

1. **如果需要完整的Token支持**：
   - 创建`TokenAdapter`
   - 在`SentenceAdapter`中集成Token转换
   - 添加Token相关的API端点

2. **如果暂时不需要Token详情**：
   - 保持当前实现即可
   - tokens字段始终为空tuple
   - 后续需要时再添加

---

**总结**：Sentence和Token的数据结构在数据库中**完全体现**，数据库设计非常完整！当前的Adapter实现已经覆盖了Sentence的所有核心功能，Token的转换可以根据实际需求决定是否实现。

