# 阶段1详细拆解：数据迁移

## 📋 总览

本阶段目标：将所有 JSON 数据完整迁移到 SQLite 数据库

**预计时间**: 1-2周  
**优先级**: 高  
**依赖**: 已完成 models.py, crud.py, migrate.py (vocab部分)

---

## 任务1：语法规则迁移 (2-3天)

### 📊 现状分析

**源数据文件**: `backend/data/current/grammar.json`

**JSON 结构**:
```json
[
  {
    "rule_name": "Present Simple Tense",
    "rule_summary": "用于描述习惯性动作、客观事实等...",
    "source": "auto",
    "is_starred": true,
    "examples": [
      {
        "text_id": 1,
        "sentence_id": 5,
        "explanation_context": "在这个句子中..."
      }
    ]
  }
]
```

**目标表**: `grammar_rules` + `grammar_examples`

---

### 🔨 实现步骤

#### Step 1.1: 扩展 migrate.py 添加语法迁移函数 (1小时)

```python
# database_system/business_logic/migrate.py

def migrate_grammar_and_examples(session: Session, 
                                 grammar_json_path: str = "backend/data/current/grammar.json") -> Dict[str, int]:
    """迁移语法规则及其例句"""
    path = Path(grammar_json_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        rows: list[Dict[str, Any]] = json.load(f)

    inserted_rules = 0
    inserted_examples = 0

    for r in rows:
        # 检查是否已存在
        existing = session.query(GrammarRule).filter(
            GrammarRule.rule_name == r["rule_name"]
        ).first()
        
        if existing is None:
            # 创建语法规则
            rule = create_grammar_rule(
                session=session,
                rule_name=r["rule_name"],
                rule_summary=r["rule_summary"],
                source=r.get("source", "auto"),
                is_starred=bool(r.get("is_starred", False)),
            )
            inserted_rules += 1
        else:
            rule = existing

        # 迁移例句
        for ex in r.get("examples", []):
            create_grammar_example(
                session=session,
                rule_id=rule.rule_id,
                text_id=ex["text_id"],
                sentence_id=ex["sentence_id"],
                explanation_context=ex.get("explanation_context"),
            )
            inserted_examples += 1

    return {"inserted_rules": inserted_rules, "inserted_examples": inserted_examples}


def verify_grammar_counts(session: Session) -> Dict[str, int]:
    """验证语法数据"""
    total_rules = session.query(GrammarRule).count()
    total_examples = session.query(GrammarExample).count()
    
    stmt = (
        select(GrammarRule.rule_id)
        .join(GrammarExample, GrammarRule.rule_id == GrammarExample.rule_id)
        .group_by(GrammarRule.rule_id)
    )
    rules_with_examples = len(session.execute(stmt).scalars().all())
    
    return {
        "total_rules": total_rules,
        "total_examples": total_examples,
        "rules_with_examples": rules_with_examples,
    }
```

#### Step 1.2: 添加 GrammarExample CRUD 函数 (30分钟)

```python
# database_system/business_logic/crud.py

def create_grammar_example(session: Session, *, rule_id: int, text_id: int,
                           sentence_id: int, 
                           explanation_context: Optional[str] = None) -> GrammarExample:
    """创建语法例句记录"""
    example = GrammarExample(
        rule_id=rule_id,
        text_id=text_id,
        sentence_id=sentence_id,
        explanation_context=explanation_context,
    )
    session.add(example)
    session.commit()
    session.refresh(example)
    return example
```

#### Step 1.3: 导入必要的模块 (5分钟)

```python
# database_system/business_logic/migrate.py (文件顶部添加)

from .models import GrammarRule, GrammarExample
from .crud import create_grammar_rule, create_grammar_example
```

#### Step 1.4: 更新 main() 函数支持语法迁移 (15分钟)

```python
# database_system/business_logic/migrate.py

def main():
    """主迁移函数"""
    session = get_session()
    try:
        # 词汇迁移
        print("\n" + "="*60)
        print("1. 迁移词汇数据")
        print("="*60)
        vocab_results = migrate_vocab_and_examples(session)
        print(f"✓ 插入词汇: {vocab_results['inserted_vocab']}")
        print(f"✓ 插入例句: {vocab_results['inserted_examples']}")
        
        vocab_verify = verify_counts_and_join(session)
        print(f"✓ 总词汇: {vocab_verify['total_vocab']}")
        print(f"✓ 总例句: {vocab_verify['total_examples']}")
        
        # 语法迁移
        print("\n" + "="*60)
        print("2. 迁移语法规则")
        print("="*60)
        grammar_results = migrate_grammar_and_examples(session)
        print(f"✓ 插入规则: {grammar_results['inserted_rules']}")
        print(f"✓ 插入例句: {grammar_results['inserted_examples']}")
        
        grammar_verify = verify_grammar_counts(session)
        print(f"✓ 总规则: {grammar_verify['total_rules']}")
        print(f"✓ 总例句: {grammar_verify['total_examples']}")
        
        print("\n" + "="*60)
        print("迁移完成！")
        print("="*60)
        
    finally:
        session.close()
```

#### Step 1.5: 测试运行 (30分钟)

```bash
# 运行迁移
python -m database_system.business_logic.migrate

# 验证数据
python -c "
from database_system.business_logic.migrate import get_session
from database_system.business_logic.models import GrammarRule
session = get_session()
rules = session.query(GrammarRule).limit(5).all()
for r in rules:
    print(f'{r.rule_name}: {len(r.examples)} 例句')
session.close()
"
```

#### Step 1.6: 验证清单

- [ ] grammar.json 文件能正常读取
- [ ] 语法规则数量正确
- [ ] 例句关联正确
- [ ] 字段完整（rule_name, rule_summary, source, is_starred）
- [ ] 时间戳自动生成
- [ ] 重复运行不会重复插入

---

## 任务2：文章数据迁移 (3-4天)

### 📊 现状分析

**源数据结构**:
```
backend/data/current/articles/
├── text_1758864042/
│   ├── original_text.json    # 文章元数据
│   ├── sentences.json         # 句子列表
│   └── tokens.json           # Token 列表
└── text_1758873454/
    └── ...
```

**文件内容示例**:

```json
// original_text.json
{
  "text_id": 1758864042,
  "text_title": "Learning a New Language"
}

// sentences.json
[
  {
    "sentence_id": 1,
    "sentence_body": "Learning a new language is challenging but rewarding.",
    "sentence_difficulty_level": "easy",
    "grammar_annotations": [1, 3],
    "vocab_annotations": [5, 8]
  }
]

// tokens.json
[
  {
    "global_token_id": 1,
    "sentence_id": 1,
    "sentence_token_id": 1,
    "token_body": "Learning",
    "token_type": "text",
    "difficulty_level": "easy",
    "pos_tag": "VBG",
    "lemma": "learn",
    "is_grammar_marker": false,
    "linked_vocab_id": 5
  }
]
```

**目标表**: `original_texts` + `sentences` + `tokens`

---

### 🔨 实现步骤

#### Step 2.1: 实现文章迁移函数 (2小时)

```python
# database_system/business_logic/migrate.py

def migrate_articles(session: Session, 
                    articles_dir: str = "backend/data/current/articles") -> Dict[str, int]:
    """迁移所有文章数据（原文、句子、tokens）"""
    articles_path = Path(articles_dir)
    if not articles_path.exists():
        raise FileNotFoundError(f"Articles directory not found: {articles_path}")
    
    inserted_texts = 0
    inserted_sentences = 0
    inserted_tokens = 0
    
    # 遍历所有 text_* 目录
    for text_dir in articles_path.glob("text_*"):
        if not text_dir.is_dir():
            continue
        
        try:
            # 1. 读取文章元数据
            original_text_file = text_dir / "original_text.json"
            if not original_text_file.exists():
                print(f"⚠️  跳过 {text_dir.name}：缺少 original_text.json")
                continue
            
            with open(original_text_file, "r", encoding="utf-8") as f:
                text_data = json.load(f)
            
            # 检查文章是否已存在
            text_id = text_data["text_id"]
            existing_text = session.query(OriginalText).filter(
                OriginalText.text_id == text_id
            ).first()
            
            if existing_text:
                print(f"⚠️  文章 {text_id} 已存在，跳过")
                continue
            
            # 2. 创建文章记录
            text = OriginalText(
                text_id=text_id,
                text_title=text_data["text_title"]
            )
            session.add(text)
            session.flush()
            inserted_texts += 1
            
            # 3. 读取并插入句子
            sentences_file = text_dir / "sentences.json"
            if sentences_file.exists():
                with open(sentences_file, "r", encoding="utf-8") as f:
                    sentences_data = json.load(f)
                
                for sent in sentences_data:
                    sentence = Sentence(
                        text_id=text_id,
                        sentence_id=sent["sentence_id"],
                        sentence_body=sent["sentence_body"],
                        sentence_difficulty_level=sent.get("sentence_difficulty_level"),
                        grammar_annotations=sent.get("grammar_annotations"),
                        vocab_annotations=sent.get("vocab_annotations")
                    )
                    session.add(sentence)
                    inserted_sentences += 1
                
                session.flush()
            
            # 4. 读取并插入 tokens
            tokens_file = text_dir / "tokens.json"
            if tokens_file.exists():
                with open(tokens_file, "r", encoding="utf-8") as f:
                    tokens_data = json.load(f)
                
                for tok in tokens_data:
                    token = Token(
                        text_id=text_id,
                        sentence_id=tok["sentence_id"],
                        token_body=tok["token_body"],
                        token_type=tok["token_type"],
                        difficulty_level=tok.get("difficulty_level"),
                        global_token_id=tok.get("global_token_id"),
                        sentence_token_id=tok.get("sentence_token_id"),
                        pos_tag=tok.get("pos_tag"),
                        lemma=tok.get("lemma"),
                        is_grammar_marker=tok.get("is_grammar_marker", False),
                        linked_vocab_id=tok.get("linked_vocab_id")
                    )
                    session.add(token)
                    inserted_tokens += 1
            
            session.commit()
            print(f"✓ 迁移文章 {text_id}: {text_data['text_title']}")
            
        except Exception as e:
            print(f"✗ 迁移文章 {text_dir.name} 失败: {e}")
            session.rollback()
            continue
    
    return {
        "inserted_texts": inserted_texts,
        "inserted_sentences": inserted_sentences,
        "inserted_tokens": inserted_tokens
    }


def verify_articles_counts(session: Session) -> Dict[str, int]:
    """验证文章数据"""
    from sqlalchemy import func
    
    total_texts = session.query(OriginalText).count()
    total_sentences = session.query(Sentence).count()
    total_tokens = session.query(Token).count()
    
    # 统计每篇文章的句子数
    texts_with_sentences = session.query(
        func.count(func.distinct(Sentence.text_id))
    ).scalar()
    
    return {
        "total_texts": total_texts,
        "total_sentences": total_sentences,
        "total_tokens": total_tokens,
        "texts_with_sentences": texts_with_sentences,
    }
```

#### Step 2.2: 导入必要模块 (5分钟)

```python
# database_system/business_logic/migrate.py (文件顶部添加)

from .models import OriginalText, Sentence, Token
```

#### Step 2.3: 更新 main() 添加文章迁移 (10分钟)

```python
# 在 main() 中添加
print("\n" + "="*60)
print("3. 迁移文章数据")
print("="*60)
articles_results = migrate_articles(session)
print(f"✓ 插入文章: {articles_results['inserted_texts']}")
print(f"✓ 插入句子: {articles_results['inserted_sentences']}")
print(f"✓ 插入tokens: {articles_results['inserted_tokens']}")

articles_verify = verify_articles_counts(session)
print(f"✓ 总文章: {articles_verify['total_texts']}")
print(f"✓ 总句子: {articles_verify['total_sentences']}")
print(f"✓ 总tokens: {articles_verify['total_tokens']}")
```

#### Step 2.4: 处理潜在问题 (1小时)

**问题1**: `DifficultyLevel` 和 `TokenType` 枚举值不匹配

```python
# 在迁移前添加值转换函数
def _coerce_difficulty(value: Optional[str]) -> Optional[str]:
    """转换难度等级字符串"""
    if value is None:
        return None
    value_lower = value.lower()
    if value_lower in ['easy', 'hard']:
        return value_lower
    return None  # 忽略无效值

def _coerce_token_type(value: str) -> str:
    """转换 token 类型"""
    value_lower = value.lower()
    if value_lower in ['text', 'punctuation', 'space']:
        return value_lower
    return 'text'  # 默认为 text
```

**问题2**: 外键约束检查

```python
# 在插入 token 前检查 linked_vocab_id 是否存在
if tok.get("linked_vocab_id"):
    vocab_exists = session.query(VocabExpression).filter(
        VocabExpression.vocab_id == tok["linked_vocab_id"]
    ).first()
    if not vocab_exists:
        print(f"⚠️  Token '{tok['token_body']}' 引用的 vocab_id {tok['linked_vocab_id']} 不存在")
        tok["linked_vocab_id"] = None  # 设为 None
```

#### Step 2.5: 测试运行 (1小时)

```bash
# 运行迁移
python -m database_system.business_logic.migrate

# 验证数据
python -c "
from database_system.business_logic.migrate import get_session
from database_system.business_logic.models import OriginalText
session = get_session()
texts = session.query(OriginalText).all()
for t in texts:
    print(f'文章 {t.text_id}: {t.text_title}')
    print(f'  句子数: {len(t.sentences)}')
    if t.sentences:
        total_tokens = sum(len(s.tokens) for s in t.sentences)
        print(f'  Token数: {total_tokens}')
session.close()
"
```

#### Step 2.6: 验证清单

- [ ] 所有 text_* 目录都被处理
- [ ] 文章元数据正确
- [ ] 句子关联到文章
- [ ] Tokens 关联到句子
- [ ] 外键约束满足（vocab_id, text_id 等）
- [ ] 枚举值正确转换
- [ ] 错误处理正常（跳过问题文章但继续其他）

---

## 任务3：对话历史迁移 (1-2天)

### 📊 现状分析

**源数据文件**: `backend/data/current/dialogue_record.json`

**JSON 结构**:
```json
{
  "texts": {
    "1758864042": {
      "sentences": {
        "1": [
          {
            "user_question": "What does 'challenging' mean?",
            "ai_response": "...",
            "is_learning_related": true,
            "timestamp": "2025-09-30T10:00:00"
          }
        ]
      }
    }
  }
}
```

---

### 🔨 实现步骤

#### Step 3.1: 添加 DialogueHistory 模型（如未定义） (30分钟)

```python
# database_system/business_logic/models.py

class DialogueHistory(Base):
    __tablename__ = 'dialogue_history'
    
    message_id = Column(Integer, primary_key=True, autoincrement=True)
    text_id = Column(Integer, ForeignKey('original_texts.text_id', ondelete='CASCADE'), nullable=False)
    sentence_id = Column(Integer, nullable=False)
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text)
    is_learning_related = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    __table_args__ = (
        ForeignKeyConstraint(
            ['text_id', 'sentence_id'],
            ['sentences.text_id', 'sentences.sentence_id'],
            ondelete='CASCADE'
        ),
    )
```

#### Step 3.2: 添加 CRUD 函数 (20分钟)

```python
# database_system/business_logic/crud.py

def create_dialogue_message(session: Session, *, text_id: int, sentence_id: int,
                            user_message: str, ai_response: Optional[str] = None,
                            is_learning_related: bool = True):
    """创建对话记录"""
    message = DialogueHistory(
        text_id=text_id,
        sentence_id=sentence_id,
        user_message=user_message,
        ai_response=ai_response,
        is_learning_related=is_learning_related
    )
    session.add(message)
    session.commit()
    session.refresh(message)
    return message
```

#### Step 3.3: 实现对话迁移函数 (1小时)

```python
# database_system/business_logic/migrate.py

def migrate_dialogue_history(session: Session,
                             dialogue_json: str = "backend/data/current/dialogue_record.json") -> Dict[str, int]:
    """迁移对话历史"""
    path = Path(dialogue_json)
    if not path.exists():
        print(f"⚠️  对话记录文件不存在: {path}")
        return {"inserted_messages": 0}
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    inserted_messages = 0
    
    for text_id_str, text_data in data.get("texts", {}).items():
        text_id = int(text_id_str)
        
        for sentence_id_str, messages in text_data.get("sentences", {}).items():
            sentence_id = int(sentence_id_str)
            
            for msg in messages:
                try:
                    create_dialogue_message(
                        session=session,
                        text_id=text_id,
                        sentence_id=sentence_id,
                        user_message=msg["user_question"],
                        ai_response=msg.get("ai_response"),
                        is_learning_related=msg.get("is_learning_related", True)
                    )
                    inserted_messages += 1
                except Exception as e:
                    print(f"✗ 插入对话失败 (text={text_id}, sent={sentence_id}): {e}")
    
    return {"inserted_messages": inserted_messages}
```

#### Step 3.4: 测试运行 (30分钟)

```bash
python -m database_system.business_logic.migrate
```

#### Step 3.5: 验证清单

- [ ] 对话记录数量正确
- [ ] 文章和句子关联正确
- [ ] user_message 和 ai_response 都存在
- [ ] is_learning_related 标志正确

---

## 🎯 完成标准

完成本阶段后，你应该能够：

✅ 运行 `python -m database_system.business_logic.migrate` 一次性完成所有迁移  
✅ 数据库包含：
  - 词汇 + 词汇例句
  - 语法规则 + 语法例句
  - 文章 + 句子 + Tokens
  - 对话历史

✅ 所有关联关系正确（外键约束满足）  
✅ 可以通过 JOIN 查询验证数据完整性  
✅ JSON 源文件保持不变（作为备份）

---

## 🚀 下一步

完成阶段1后，立即进入：
- **阶段2**: 创建混合适配器（支持 JSON 降级）
- **阶段3**: 逐步替换后端 API

---

## 📞 常见问题

**Q: 迁移过程中出错怎么办？**
A: 所有迁移函数都有错误处理，会跳过问题数据继续。检查输出日志定位问题。

**Q: 如何重新迁移？**
A: 删除 `dev.db` 文件后重新运行迁移脚本。

**Q: 外键约束报错？**
A: 确保引用的数据已存在。例如 token 的 linked_vocab_id 必须在 vocab_expressions 表中存在。

**Q: 枚举值不匹配？**
A: 添加值转换函数（_coerce_difficulty, _coerce_token_type）处理不匹配的值。 