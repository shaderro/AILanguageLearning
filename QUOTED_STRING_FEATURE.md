# Quoted String 功能说明

## 概述

`MainAssistant.run` 方法现在支持一个新的可选参数 `quoted_string`，允许用户选择句子中的部分内容进行提问，而后端会自动补全整句话放入实际的prompt中。

## 功能特性

### 1. 向后兼容性
- 现有的调用方式完全不受影响
- 如果不提供 `quoted_string` 参数，系统会使用完整的句子

### 2. 部分文本选择
- 用户可以只选择句子中的特定单词、短语或片段
- 系统会智能地将选中的部分与完整句子结合使用

### 3. 智能处理
- AI会基于选中的部分内容回答用户问题
- 语法和词汇分析也会基于选中的内容进行

## 使用方法

### 基本用法（向后兼容）
```python
# 使用完整句子
main_assistant.run(quoted_sentence, user_question)
```

### 新功能用法
```python
# 使用部分句子
main_assistant.run(quoted_sentence, user_question, "revolutionized")

# 使用短语
main_assistant.run(quoted_sentence, user_question, "the way we learn")
```

## 实际应用场景

### 1. 单词学习
```python
sentence = Sentence(text_id=1, sentence_id=1, sentence_body="The internet has revolutionized the way we learn languages.")
main_assistant.run(sentence, "What does this word mean?", "revolutionized")
```

### 2. 语法结构学习
```python
sentence = Sentence(text_id=1, sentence_id=1, sentence_body="The internet has revolutionized the way we learn languages.")
main_assistant.run(sentence, "What grammar structure is used here?", "the way we learn")
```

### 3. 短语理解
```python
sentence = Sentence(text_id=1, sentence_id=1, sentence_body="The internet has revolutionized the way we learn languages.")
main_assistant.run(sentence, "How do you use this phrase?", "has revolutionized")
```

## 技术实现

### 参数变化
```python
def run(self, quoted_sentence: Sentence, user_question: str, quoted_string: str = None):
```

### 内部处理逻辑
1. 如果提供了 `quoted_string`，使用它作为有效句子内容
2. 如果没有提供，使用 `quoted_sentence.sentence_body`
3. 所有后续的AI处理都基于这个有效句子内容

### 影响的方法
- `answer_question_function`: 使用有效句子内容生成AI回答
- `handle_grammar_vocab_function`: 基于有效句子内容进行语法和词汇分析
- 所有子助手的调用都使用有效句子内容

## 测试验证

功能已通过以下测试验证：
1. ✅ 向后兼容性测试
2. ✅ 单词选择测试
3. ✅ 短语选择测试
4. ✅ 语法和词汇分析测试

## 注意事项

1. **数据完整性**: 虽然使用部分内容进行AI处理，但对话记录仍然保存完整的句子信息
2. **上下文保持**: 系统会保持完整的句子上下文，确保AI回答的准确性
3. **错误处理**: 如果 `quoted_string` 为空或无效，系统会自动回退到使用完整句子

## 未来扩展

这个功能为以下扩展提供了基础：
1. UI层的文本选择功能集成
2. 更精确的语法和词汇分析
3. 个性化的学习内容推荐 