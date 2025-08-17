# 新DialogueHistory功能特性说明

## 概述
更新后的 `DialogueHistory` 类完全兼容新数据结构 (`data_classes_new.Sentence`)，同时保持对旧数据结构的向后兼容性，并提供了丰富的分析和总结功能。

## 主要特性

### 1. 数据结构兼容性
- ✅ 支持旧数据结构 `Sentence` (frozen dataclass)
- ✅ 支持新数据结构 `NewSentence` (包含 tokens、难度级别等)
- ✅ 使用 `Union[Sentence, NewSentence]` 类型别名实现统一接口

### 2. 新数据结构特有功能

#### 2.1 智能数据保存
- **自动识别**: 自动识别新旧数据结构类型
- **完整保存**: 保存新数据结构的完整信息（tokens、难度级别等）
- **向后兼容**: 保持对旧数据格式的兼容性

#### 2.2 对话分析
- **数据类型统计**: 统计新旧数据结构的使用情况
- **难度级别分析**: 分析不同难度级别的对话分布
- **Token统计**: 统计token使用情况和困难词汇

#### 2.3 学习进度跟踪
- **参与度评估**: 基于对话数量评估学习参与度
- **新结构使用率**: 跟踪新数据结构的使用比例
- **困难词汇跟踪**: 识别和跟踪困难词汇的学习情况

### 3. 核心方法

#### 3.1 基础对话管理
```python
add_message(user_input: str, ai_response: str, quoted_sentence: SentenceType)
save_to_file(path: str)
load_from_file(path: str)
```

#### 3.2 新数据结构特有方法
```python
get_dialogue_analytics() -> dict
get_new_structure_messages() -> list
get_old_structure_messages() -> list
get_messages_by_difficulty(difficulty: str) -> list
get_hard_tokens_summary() -> dict
```

#### 3.3 总结功能
```python
summarize_dialogue_history() -> str
message_history_to_string() -> str
keep_in_max_turns()
```

### 4. 使用示例

#### 4.1 基本使用
```python
from assistants.chat_info.dialogue_history import DialogueHistory
from data_managers.data_classes_new import Sentence as NewSentence, Token

# 创建DialogueHistory实例
dialogue_history = DialogueHistory(max_turns=5)

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

# 添加对话消息
dialogue_history.add_message("Finne是什么意思？", "Finne是德语名词，指鱼类的背鳍。", test_sentence)
```

#### 4.2 获取分析信息
```python
# 获取对话分析
analytics = dialogue_history.get_dialogue_analytics()

# 获取新数据结构消息
new_messages = dialogue_history.get_new_structure_messages()

# 获取特定难度级别的消息
hard_messages = dialogue_history.get_messages_by_difficulty("hard")

# 获取困难词汇总结
hard_tokens_summary = dialogue_history.get_hard_tokens_summary()
```

### 5. 输出示例

#### 5.1 对话分析
```json
{
  "total_messages": 5,
  "summary": "对话总结内容...",
  "data_types": {
    "old": 2,
    "new": 3
  },
  "difficulty_levels": {
    "hard": 3
  },
  "token_statistics": {
    "total_tokens": 15,
    "hard_tokens": ["Die", "Finne", "Die", "Finne", "Die", "Finne"]
  },
  "learning_progress": {
    "engagement_level": "low",
    "new_structure_usage_ratio": 0.6
  }
}
```

#### 5.2 困难词汇总结
```json
{
  "Die": {
    "count": 3,
    "contexts": [
      {
        "sentence": "Die Finne ist groß und stark gebogen...",
        "user_question": "Finne是什么意思？",
        "ai_response": "Finne是德语名词，指鱼类的背鳍。"
      }
    ]
  },
  "Finne": {
    "count": 3,
    "contexts": [
      {
        "sentence": "Die Finne ist groß und stark gebogen...",
        "user_question": "Finne是什么意思？",
        "ai_response": "Finne是德语名词，指鱼类的背鳍。"
      }
    ]
  }
}
```

#### 5.3 保存的数据格式
```json
{
  "texts": {
    "2": {
      "text_title": "Text 2",
      "current_summary": "",
      "messages": [
        {
          "user": "Finne是什么意思？",
          "ai": "Finne是德语名词，指鱼类的背鳍。",
          "sentence_id": 1,
          "quote": {
            "text_id": 2,
            "sentence_id": 1,
            "sentence_body": "Die Finne ist groß und stark gebogen...",
            "grammar_annotations": [],
            "vocab_annotations": [],
            "sentence_difficulty_level": "hard",
            "tokens": [
              {
                "token_body": "Die",
                "token_type": "text",
                "difficulty_level": "hard",
                "global_token_id": 1,
                "sentence_token_id": 1,
                "pos_tag": "DET",
                "lemma": "der",
                "is_grammar_marker": true,
                "linked_vocab_id": null
              }
            ]
          },
          "timestamp": "2024-01-01T10:00:00Z",
          "data_type": "new"
        }
      ]
    }
  }
}
```

### 6. 优势

1. **向后兼容**: 完全支持旧数据结构
2. **智能识别**: 自动识别数据结构类型
3. **完整保存**: 保存新数据结构的完整信息
4. **丰富分析**: 提供详细的分析和统计功能
5. **学习跟踪**: 跟踪学习进度和困难词汇
6. **类型安全**: 使用类型注解确保代码质量

### 7. 集成方式

在 `DataController` 中，`dialogue_history` 会自动处理新旧两种数据结构：

```python
class DataController:
    def __init__(self, max_turns:int, ...):
        # 对话历史：用于当前会话管理和总结
        self.dialogue_history = DialogueHistory(max_turns)
```

### 8. 应用场景

1. **会话管理**: 管理当前对话会话的历史记录
2. **智能总结**: 使用AI生成对话总结
3. **学习分析**: 分析学习进度和困难词汇
4. **数据持久化**: 保存和加载对话历史
5. **进度跟踪**: 跟踪新数据结构的使用情况
6. **困难词汇识别**: 识别和跟踪困难词汇的学习

### 9. 与DialogueRecord的协同

- **DialogueHistory**: 专注于会话管理和总结，有容量限制
- **DialogueRecord**: 专注于历史数据存储，无容量限制
- **协同工作**: 两个组件同时记录对话，提供不同层次的数据支持

这样的设计确保了系统的灵活性和可扩展性，同时为语言学习提供了更智能的支持。 