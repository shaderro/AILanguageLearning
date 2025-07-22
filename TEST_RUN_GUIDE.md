# Test Run 功能使用指南

## 概述

我已经在 `text_input_chat_screen_test.py` 页面中添加了 `test_run` 功能，可以独立运行当前页面并使用测试数据。

## 新增功能

### 1. test_run() 方法
**位置：** `ui/screens/text_input_chat_screen_test.py`

**功能：**
- 自动设置测试文章数据
- 模拟用户文本选择和提问
- 生成测试对话场景
- 验证所有功能正常工作

### 2. 测试数据
**文章标题：** "The Internet and Language Learning"

**文章内容：** 包含8个句子的完整文章，涵盖：
- 互联网对语言学习的影响
- 在线学习平台的特点
- 真实材料的重要性
- 协作学习的优势

### 3. 测试对话场景
包含3个不同的测试场景：

1. **单词学习场景**
   - 选中文本：`revolutionized`
   - 用户问题：`What does this word mean?`
   - AI回复：解释单词含义和用法

2. **语法结构场景**
   - 选中文本：`the way we learn`
   - 用户问题：`What grammar structure is used here?`
   - AI回复：分析语法结构

3. **文章理解场景**
   - 选中文本：无
   - 用户问题：`Can you help me understand this article?`
   - AI回复：文章概述和帮助

## 使用方法

### 方法1：运行完整测试应用
```bash
python test_chat_screen_app.py
```
- 启动完整的Kivy GUI应用
- 自动调用 `test_run()` 功能
- 显示图形界面和测试数据

### 方法2：运行独立测试脚本
```bash
python test_run_standalone.py
```
- 包含Kivy组件的独立测试
- 验证GUI功能
- 显示详细的测试结果

### 方法3：运行简单测试脚本
```bash
python test_run_simple.py
```
- 纯Python测试，无需GUI
- 只测试核心功能
- 快速验证逻辑

### 方法4：在代码中调用
```python
from ui.screens.text_input_chat_screen_test import TextInputChatScreenTest

# 创建测试页面
test_screen = TextInputChatScreenTest()

# 运行测试功能
test_screen.test_run()
```

## 测试结果示例

### 简单测试输出
```
🚀 启动简单测试运行...
🧪 开始测试运行 SimpleTextInputChatTest...
📖 设置文章: The Internet and Language Learning
📝 文章内容长度: 922 字符
📝 选中文本: 'revolutionized'
📝 模拟选择文本: 'revolutionized'
💬 添加消息: You - What does this word mean?...
💬 添加消息: Test AI Assistant - revolutionized means "to completely change or tran...
✅ 添加了 3 个测试对话场景
✅ 测试数据设置完成

📊 测试结果验证:
✅ 文章标题: The Internet and Language Learning
✅ 文章内容长度: 922 字符
✅ 聊天历史长度: 6 条消息
✅ 选中文本备份: 'the way we learn'
✅ 文本选择状态: False

💬 聊天历史:
  1. You: What does this word mean?...
     引用: 'revolutionized'
  2. Test AI Assistant: revolutionized means "to completely change or tran...
  3. You: What grammar structure is used here?...
     引用: 'the way we learn'
  4. Test AI Assistant: This is a noun phrase structure: "the way we learn...
  5. You: Can you help me understand this article?...
  6. Test AI Assistant: Of course! This article discusses how the internet...

🎉 简单测试运行完成！所有功能正常
```

## 功能验证

### 1. 文章设置功能 ✅
- 正确设置文章标题
- 正确设置文章内容
- 句子列表正确转换为文本

### 2. 文本选择功能 ✅
- 文本选择状态正确更新
- 选中文本正确备份
- 选择清除功能正常

### 3. 聊天消息功能 ✅
- 用户消息正确添加
- AI回复正确生成
- 引用文本正确显示

### 4. AI回复功能 ✅
- 有选中文本时的回复
- 无选中文本时的回复
- 不同问题类型的回复

## 自定义测试

### 1. 修改测试文章
```python
def _create_test_article_data(self):
    class TestArticleData:
        def __init__(self):
            self.text_title = "Your Custom Title"
            self.text_by_sentence = [
                type('MockSentence', (), {'sentence_body': 'Your custom sentence 1.'})(),
                type('MockSentence', (), {'sentence_body': 'Your custom sentence 2.'})()
            ]
    return TestArticleData()
```

### 2. 添加测试场景
```python
def _add_test_messages(self):
    test_scenarios = [
        {
            'selected_text': 'your text',
            'user_message': 'Your question?',
            'ai_response': 'Your AI response.'
        }
        # 添加更多场景...
    ]
```

### 3. 自定义AI回复逻辑
```python
def _generate_ai_response(self, user_message, selected_text):
    # 你的自定义AI回复逻辑
    return "Your custom response"
```

## 优势

### 1. 快速测试
- 无需手动设置数据
- 自动生成测试场景
- 一键运行所有功能

### 2. 完整覆盖
- 测试所有核心功能
- 模拟真实使用场景
- 验证数据流正确性

### 3. 易于调试
- 详细的调试输出
- 清晰的状态显示
- 完整的测试报告

### 4. 灵活扩展
- 易于添加新测试场景
- 支持自定义测试数据
- 可集成真实AI服务

## 下一步计划

1. **集成真实AI**：将测试页面与 `MainAssistant` 集成
2. **添加更多场景**：增加更多测试对话场景
3. **性能测试**：添加性能基准测试
4. **自动化测试**：集成到CI/CD流程中

这个 `test_run` 功能为快速验证和测试新功能提供了强大的工具，可以大大提高开发效率。 