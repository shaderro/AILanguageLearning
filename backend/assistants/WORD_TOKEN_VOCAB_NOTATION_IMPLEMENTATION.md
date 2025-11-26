# Word Token Vocab Notation 功能实现文档

## 1. 功能概述

### 1.1 目标
为非空格语言（中文、日文等）的词汇标注功能添加 word token 级别的支持。当 MainAssistant 总结出的 vocab 与句子中的 word token 匹配时，VocabNotation 应该直接标注到 word token 上，而不是标注到单个字符 token 上。

### 1.2 背景
- **空格语言**（如英文、德文）：token = word，直接使用字符 token 标注即可
- **非空格语言**（如中文、日文）：token = 字符，但语义单位是"词"（word token）
  - 例如："见面" 由两个字符 token ["见", "面"] 组成，但语义上是一个词
  - 用户选择"见"并提问，AI 总结出 vocab "见面"，应该标注到 word token "见面" 上

### 1.3 相关概念说明

#### WordToken.linked_vocab_id
- **定义**：WordToken 表中的一个字段，指向词汇表（vocab_expressions）中的词汇解释
- **用途**：系统级别的自动关联，表示这个词在词汇表中有对应的解释
- **与 VocabNotation 的区别**：
  - `WordToken.linked_vocab_id`：系统自动关联，表示词汇表中有这个词的解释
  - `VocabNotation`：用户级别的标注，表示用户在这个位置标注了这个词汇
- **本次功能**：不涉及 `WordToken.linked_vocab_id`，只处理 `VocabNotation` 的创建

## 2. 设计方案

### 2.1 数据库层修改

#### 2.1.1 修改 `vocab_notations` 表
在 `vocab_notations` 表中添加 `word_token_id` 字段：

```sql
ALTER TABLE vocab_notations 
ADD COLUMN word_token_id INTEGER 
REFERENCES word_tokens(word_token_id) 
ON DELETE SET NULL;
```

**字段说明**：
- `word_token_id`：可为 NULL，指向 word_tokens 表的 word_token_id
- 当 `word_token_id` 不为 NULL 时，表示标注到 word token 上
- 当 `word_token_id` 为 NULL 时，表示标注到字符 token 上（使用 `token_id`）

**约束**：
- 唯一约束需要更新：`(user_id, text_id, sentence_id, token_id, word_token_id)` 的组合必须唯一
- 但考虑到向后兼容，可以保持现有唯一约束 `(user_id, text_id, sentence_id, token_id)`
- 当 `word_token_id` 不为 NULL 时，`token_id` 可以为该 word token 的任意一个字符 token 的 ID（用于兼容）

#### 2.1.2 数据库模型修改
修改 `database_system/business_logic/models.py` 中的 `VocabNotation` 类：

```python
class VocabNotation(Base):
    __tablename__ = 'vocab_notations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    text_id = Column(Integer, ForeignKey('original_texts.text_id', ondelete='CASCADE'), nullable=False)
    sentence_id = Column(Integer, nullable=False)
    token_id = Column(Integer, nullable=False)  # sentence_token_id（保持向后兼容）
    word_token_id = Column(Integer, ForeignKey('word_tokens.word_token_id', ondelete='SET NULL'), nullable=True)  # 新增
    vocab_id = Column(Integer, ForeignKey('vocab_expressions.vocab_id', ondelete='CASCADE'))
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    # 关系
    vocab = relationship('VocabExpression', backref='notations')
    text = relationship('OriginalText', backref='vocab_notations')
    word_token = relationship('WordToken', backref='vocab_notations')  # 新增
```

### 2.2 数据类修改

修改 `backend/data_managers/data_classes_new.py` 中的 `VocabNotation` dataclass：

```python
@dataclass
class VocabNotation:
    """词汇标注"""
    user_id: str
    text_id: int
    sentence_id: int
    token_id: int               # 当前句子中哪个 token（保持向后兼容）
    vocab_id: Optional[int]     # 对应词汇表中的词汇
    word_token_id: Optional[int] = None  # 新增：如果标注到 word token，则为 word_token_id
    created_at: Optional[str] = None  # 时间戳（可选）
```

### 2.3 业务逻辑修改

#### 2.3.1 匹配逻辑设计

在 `MainAssistant.handle_grammar_vocab_function()` 中，当处理 vocab 总结结果时：

**流程**：
1. 检查是否为非空格语言（`self.current_is_non_whitespace == True`）
2. 如果是非空格语言：
   - 获取句子的 `word_tokens`（如果存在）
   - 尝试将总结的 vocab 与 `word_token.word_body` 匹配
   - 匹配成功：使用 `word_token_id` 创建 VocabNotation
   - 匹配失败：回退到字符 token 匹配逻辑（现有逻辑）
3. 如果是空格语言：
   - 使用现有逻辑（字符 token 匹配）

**匹配策略**：
- **精确匹配**：`vocab == word_token.word_body`（忽略大小写、标点符号）
- **模糊匹配**：
  - 忽略大小写
  - 忽略标点符号（中英文标点）
  - 去除首尾空格
- **部分匹配**：
  - 如果 vocab 是单个字符，但属于某个 word token，优先使用 word token
  - 例如：vocab = "见"，word_token = "见面"，应该匹配到 "见面"

#### 2.3.2 实现位置

修改 `backend/assistants/main_assistant.py` 中的以下方法：

1. **`handle_grammar_vocab_function()`**：
   - 在处理现有词汇时（`existing_vocab` 分支）
   - 在处理新词汇时（`new_vocab` 分支）

2. **新增辅助方法 `_match_vocab_to_word_token()`**：
   - 输入：vocab（字符串）、sentence（NewSentence 对象）
   - 输出：匹配的 word_token_id（如果匹配成功），否则返回 None

#### 2.3.3 代码结构

```python
def _match_vocab_to_word_token(self, vocab: str, sentence: SentenceType) -> Optional[int]:
    """
    尝试将 vocab 匹配到句子的 word token
    
    Args:
        vocab: 总结出的词汇
        sentence: 句子对象
        
    Returns:
        word_token_id: 如果匹配成功，返回 word_token_id；否则返回 None
    """
    # 1. 检查是否为非空格语言
    if not self.current_is_non_whitespace:
        return None
    
    # 2. 检查句子是否有 word_tokens
    if not NEW_STRUCTURE_AVAILABLE or not isinstance(sentence, NewSentence):
        return None
    
    if not sentence.word_tokens or len(sentence.word_tokens) == 0:
        return None
    
    # 3. 清理 vocab（去除标点、空格、转小写）
    vocab_clean = self._clean_vocab_for_matching(vocab)
    
    # 4. 尝试匹配 word tokens
    for word_token in sentence.word_tokens:
        word_body_clean = self._clean_vocab_for_matching(word_token.word_body)
        
        # 精确匹配
        if vocab_clean == word_body_clean:
            return word_token.word_token_id
        
        # 部分匹配：如果 vocab 是单个字符，检查是否属于 word token
        if len(vocab_clean) == 1 and vocab_clean in word_body_clean:
            return word_token.word_token_id
    
    return None

def _clean_vocab_for_matching(self, vocab: str) -> str:
    """
    清理词汇用于匹配（去除标点、空格、转小写）
    """
    import string
    # 去除中英文标点
    punctuation = string.punctuation + '。，！？；：""''（）【】《》、'
    cleaned = vocab.strip().lower()
    for p in punctuation:
        cleaned = cleaned.replace(p, '')
    return cleaned.strip()
```

### 2.4 API 层修改

修改 `backend/data_managers/unified_notation_manager.py` 中的 `mark_notation()` 方法：

```python
def mark_notation(
    self,
    notation_type: str,
    user_id: Union[int, str],
    text_id: int,
    sentence_id: int,
    token_id: int,
    vocab_id: Optional[int] = None,
    grammar_id: Optional[int] = None,
    word_token_id: Optional[int] = None,  # 新增参数
    ...
):
    # 创建 VocabNotation 时，传递 word_token_id
    if notation_type == "vocab":
        # ... 创建 VocabNotation，包含 word_token_id
```

## 3. 实现步骤

### 步骤 1：数据库迁移
1. 创建迁移脚本 `migrate_add_word_token_id_to_vocab_notation.py`
2. 在 `vocab_notations` 表中添加 `word_token_id` 字段
3. 添加外键约束

### 步骤 2：数据模型修改
1. 修改 `database_system/business_logic/models.py` 中的 `VocabNotation` 类
2. 修改 `backend/data_managers/data_classes_new.py` 中的 `VocabNotation` dataclass

### 步骤 3：业务逻辑实现
1. 在 `MainAssistant` 中添加 `_match_vocab_to_word_token()` 方法
2. 在 `MainAssistant` 中添加 `_clean_vocab_for_matching()` 方法
3. 修改 `handle_grammar_vocab_function()` 方法，在处理现有词汇和新词汇时调用匹配逻辑

### 步骤 4：API 层修改
1. 修改 `unified_notation_manager.py` 中的 `mark_notation()` 方法，支持 `word_token_id` 参数
2. 修改数据库 CRUD 操作，支持创建带 `word_token_id` 的 VocabNotation

### 步骤 5：测试
1. 测试非空格语言（中文）的 word token 匹配
2. 测试匹配失败时的回退逻辑
3. 测试空格语言（英文）不受影响

## 4. 注意事项

### 4.1 向后兼容
- `token_id` 字段保持必需，用于向后兼容
- 当 `word_token_id` 不为 NULL 时，`token_id` 可以是该 word token 的任意一个字符 token 的 ID
- 现有查询逻辑不需要修改（可以继续使用 `token_id`）

### 4.2 语言隔离
- **重要**：此功能只针对非空格语言（`is_non_whitespace == True`）
- 空格语言继续使用现有逻辑（字符 token 匹配）
- 在代码中明确检查 `self.current_is_non_whitespace`，避免混淆

### 4.3 匹配优先级
1. 优先尝试 word token 匹配（非空格语言）
2. 如果匹配失败，回退到字符 token 匹配（现有逻辑）
3. 如果都匹配失败，使用 `current_selected_token` 的 token_id（现有逻辑）

### 4.4 错误处理
- 如果句子没有 `word_tokens`，静默回退到字符 token 匹配
- 如果匹配过程中出现异常，记录日志并回退到字符 token 匹配

## 5. 测试用例

### 测试用例 1：精确匹配
- **输入**：vocab = "见面"，句子 word_tokens = [{"word_token_id": 1, "word_body": "见面", ...}]
- **预期**：返回 word_token_id = 1

### 测试用例 2：部分匹配（单个字符）
- **输入**：vocab = "见"，句子 word_tokens = [{"word_token_id": 1, "word_body": "见面", ...}]
- **预期**：返回 word_token_id = 1（因为"见"属于"见面"）

### 测试用例 3：匹配失败
- **输入**：vocab = "其他词"，句子 word_tokens = [{"word_token_id": 1, "word_body": "见面", ...}]
- **预期**：返回 None，回退到字符 token 匹配

### 测试用例 4：空格语言不受影响
- **输入**：vocab = "hello"，`is_non_whitespace = False`
- **预期**：直接返回 None，使用现有字符 token 匹配逻辑

## 6. 后续优化

1. **性能优化**：如果 word_tokens 很多，可以考虑使用字典索引加速匹配
2. **匹配算法优化**：可以考虑使用编辑距离、相似度算法等更智能的匹配
3. **UI 显示**：前端显示 VocabNotation 时，如果 `word_token_id` 不为 NULL，应该高亮整个 word token，而不是单个字符

