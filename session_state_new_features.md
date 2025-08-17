# 新SessionState功能特性说明

## 概述
更新后的 `SessionState` 类完全兼容新数据结构 (`data_classes_new.Sentence`)，同时保持对旧数据结构的向后兼容性，并提供了丰富的分析和管理功能。

## 主要特性

### 1. 数据结构兼容性
- ✅ 支持旧数据结构 `Sentence` (frozen dataclass)
- ✅ 支持新数据结构 `NewSentence` (包含 tokens、难度级别等)
- ✅ 使用 `Union[Sentence, NewSentence]` 类型别名实现统一接口

### 2. 新数据结构特有功能

#### 2.1 句子信息获取
- **基本信息**: 获取句子的基本属性（text_id, sentence_id, sentence_body）
- **数据类型识别**: 自动识别是新数据结构还是旧数据结构
- **难度级别**: 获取句子的整体难度级别
- **Token统计**: 获取token数量和可用性信息

#### 2.2 Token 分析
- **Token分类**: 按类型（text、punctuation、space）分类
- **难度分析**: 识别困难词汇和简单词汇
- **语法标记**: 识别参与语法结构的词汇
- **词性标注**: 统计各种词性的分布

#### 2.3 学习上下文管理
- **完整上下文**: 获取当前学习会话的完整信息
- **状态跟踪**: 跟踪当前输入、响应、总结等状态
- **智能分析**: 基于当前状态提供学习建议

### 3. 核心方法

#### 3.1 基础会话管理
```python
set_current_sentence(sentence: SentenceType)
set_current_input(user_input: str)
set_current_response(ai_response: str)
reset()
```

#### 3.2 新数据结构特有方法
```python
get_current_sentence_info() -> dict
get_current_sentence_tokens() -> dict
get_learning_context() -> dict
is_new_structure_sentence() -> bool
get_sentence_difficulty() -> str
get_hard_tokens() -> list
get_grammar_markers() -> list
```

#### 3.3 语法和词汇管理
```python
add_grammar_summary(name: str, summary: str)
add_vocab_summary(vocab: str)
add_grammar_to_add(rule_name: str, rule_explanation: str)
add_vocab_to_add(vocab: str)
```

### 4. 使用示例

#### 4.1 基本使用
```python
from assistants.chat_info.session_state import SessionState
from data_managers.data_classes_new import Sentence as NewSentence, Token

# 创建session_state实例
session_state = SessionState()

# 创建新数据结构句子
test_sentence = NewSentence(
    text_id=1,
    sentence_id=1,
    sentence_body="Die Finne ist groß.",
    grammar_annotations=(),
    vocab_annotations=(),
    sentence_difficulty_level="hard",
    tokens=(...)
)

# 设置当前句子
session_state.set_current_sentence(test_sentence)
session_state.set_current_input("Finne是什么意思？")
session_state.set_current_response("Finne是德语名词，指鱼类的背鳍。")
```

#### 4.2 获取分析信息
```python
# 获取句子信息
sentence_info = session_state.get_current_sentence_info()

# 获取token信息
tokens_info = session_state.get_current_sentence_tokens()

# 获取学习上下文
learning_context = session_state.get_learning_context()

# 检查数据结构类型
is_new = session_state.is_new_structure_sentence()
difficulty = session_state.get_sentence_difficulty()
hard_tokens = session_state.get_hard_tokens()
grammar_markers = session_state.get_grammar_markers()
```

### 5. 输出示例

#### 5.1 句子信息
```json
{
  "text_id": 2,
  "sentence_id": 1,
  "sentence_body": "Die Finne ist groß und stark gebogen...",
  "data_type": "new",
  "difficulty_level": "hard",
  "token_count": 5,
  "has_tokens": true,
  "grammar_annotations": (),
  "vocab_annotations": ()
}
```

#### 5.2 Token 信息
```json
{
  "total_tokens": 5,
  "text_tokens": ["Die", "Finne", "ist", "groß", "und"],
  "punctuation_tokens": [],
  "space_tokens": [],
  "grammar_markers": ["Die", "ist", "und"],
  "hard_tokens": ["Die", "Finne"],
  "easy_tokens": ["ist", "groß", "und"],
  "pos_tags": {
    "DET": ["Die"],
    "NOUN": ["Finne"],
    "VERB": ["ist"],
    "ADJ": ["groß"],
    "CONJ": ["und"]
  }
}
```

#### 5.3 学习上下文
```json
{
  "current_sentence": {
    "text_id": 2,
    "sentence_id": 1,
    "sentence_body": "Die Finne ist groß und stark gebogen...",
    "data_type": "new",
    "difficulty_level": "hard",
    "token_count": 5,
    "has_tokens": true
  },
  "current_input": "Finne是什么意思？",
  "current_response": "Finne是德语名词，指鱼类的背鳍。",
  "summarized_results_count": 2,
  "grammar_to_add_count": 1,
  "vocab_to_add_count": 1,
  "tokens_info": {
    "total_tokens": 5,
    "text_tokens": ["Die", "Finne", "ist", "groß", "und"],
    "grammar_markers": ["Die", "ist", "und"],
    "hard_tokens": ["Die", "Finne"],
    "easy_tokens": ["ist", "groß", "und"]
  }
}
```

### 6. 优势

1. **向后兼容**: 完全支持旧数据结构
2. **功能丰富**: 提供详细的分析和管理功能
3. **智能识别**: 自动识别数据结构类型
4. **上下文管理**: 完整的学习会话状态管理
5. **类型安全**: 使用类型注解确保代码质量
6. **易于使用**: 简洁的API设计

### 7. 集成方式

在 `MainAssistant` 中，`session_state` 会自动处理新旧两种数据结构：

```python
# 设置句子（支持新旧两种类型）
self.session_state.set_current_sentence(sentence)

# 获取信息（自动适配数据结构）
sentence_info = self.session_state.get_current_sentence_info()
if self.session_state.is_new_structure_sentence():
    tokens_info = self.session_state.get_current_sentence_tokens()
    hard_tokens = self.session_state.get_hard_tokens()
```

### 8. 应用场景

1. **学习进度跟踪**: 跟踪用户的学习状态和进度
2. **智能建议**: 基于token分析提供学习建议
3. **难度评估**: 评估句子的学习难度
4. **语法分析**: 识别和分析语法结构
5. **词汇管理**: 管理新词汇和语法规则
6. **会话管理**: 管理完整的对话会话状态

这样的设计确保了系统的灵活性和可扩展性，同时为语言学习提供了更智能的支持。 