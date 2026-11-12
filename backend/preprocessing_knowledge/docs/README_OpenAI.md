# OpenAI 项目集成指南

本项目已集成OpenAI API，提供强大的AI文本分析功能。

## 📋 文件结构

```
preprocessing/
├── config.py              # OpenAI配置管理
├── openai_utils.py        # OpenAI工具函数
├── example_openai_usage.py # 使用示例
├── token_splitter.py      # Token分割
├── get_lemma.py           # 获取lemma
├── get_pos_tag.py         # 获取POS标签
└── README_OpenAI.md       # 本文件
```

## 🚀 快速开始

### 1. 设置API密钥

**方法1: 环境变量（推荐）**
```bash
# Windows
set OPENAI_API_KEY=your_api_key_here

# Linux/Mac
export OPENAI_API_KEY=your_api_key_here
```

**方法2: 代码中设置**
```python
import os
os.environ['OPENAI_API_KEY'] = 'your_api_key_here'
```

### 2. 测试连接

```bash
python openai_utils.py
```

### 3. 运行示例

```bash
python example_openai_usage.py
```

## 🔧 主要功能

### OpenAIHelper 类

```python
from openai_utils import OpenAIHelper

# 初始化
helper = OpenAIHelper()

# 聊天完成
response = helper.chat_completion([
    {"role": "user", "content": "Hello, how are you?"}
])

# 文本分析
analysis = helper.analyze_text("Your text here", "difficulty")

# Token难度分析
difficulty = helper.get_token_difficulty("word", "context")
```

### 文本分析类型

- `"general"`: 一般分析
- `"sentiment"`: 情感分析
- `"grammar"`: 语法检查
- `"difficulty"`: 难度评估

## 📝 使用示例

### 1. 基础聊天

```python
from openai_utils import OpenAIHelper

helper = OpenAIHelper()
response = helper.chat_completion([
    {"role": "user", "content": "解释什么是机器学习"}
])
print(response)
```

### 2. 文本分析

```python
text = "The quick brown fox jumps over the lazy dog."
analysis = helper.analyze_text(text, "difficulty")
print(analysis)
```

### 3. Token分析

```python
from token_splitter import split_tokens
from get_lemma import get_lemma
from get_pos_tag import get_pos_tag

# 分割文本
tokens = split_tokens("Although the weather was terrible, we still enjoyed our vacation.")

for token in tokens:
    if token['token_type'] == 'text':
        lemma = get_lemma(token['token_body'])
        pos_tag = get_pos_tag(token['token_body'])
        difficulty = helper.get_token_difficulty(token['token_body'])
        
        print(f"Token: {token['token_body']}")
        print(f"Lemma: {lemma}")
        print(f"POS: {pos_tag}")
        print(f"Difficulty: {difficulty}")
```

## ⚙️ 配置选项

在 `config.py` 中可以配置：

- `OPENAI_API_KEY`: API密钥
- `OPENAI_BASE_URL`: API基础URL（默认: https://api.openai.com/v1）
- `OPENAI_MODEL`: 使用的模型（默认: gpt-3.5-turbo）

## 🔍 错误处理

常见错误及解决方案：

1. **API密钥错误**
   ```
   ValueError: 请设置OPENAI_API_KEY环境变量
   ```
   解决：检查API密钥是否正确设置

2. **网络连接错误**
   ```
   Exception: OpenAI API调用失败: ...
   ```
   解决：检查网络连接和API密钥有效性

3. **配额超限**
   ```
   Exception: OpenAI API调用失败: 429 Too Many Requests
   ```
   解决：等待配额重置或升级账户

## 📚 高级用法

### 自定义提示词

```python
messages = [
    {"role": "system", "content": "你是一个专业的英语教师。"},
    {"role": "user", "content": "分析这个单词的用法: 'although'"}
]

response = helper.chat_completion(messages, temperature=0.3)
```

### 批量处理

```python
tokens = split_tokens("Your text here")
results = []

for token in tokens:
    if token['token_type'] == 'text':
        difficulty = helper.get_token_difficulty(token['token_body'])
        results.append({
            'token': token['token_body'],
            'difficulty': difficulty
        })
```

## 🛠️ 开发建议

1. **缓存结果**: 对于重复的token分析，考虑缓存结果
2. **批量处理**: 减少API调用次数
3. **错误重试**: 实现重试机制处理临时错误
4. **成本控制**: 监控API使用量和成本

## 📞 支持

如有问题，请检查：
1. API密钥是否正确设置
2. 网络连接是否正常
3. OpenAI账户是否有足够配额
4. 代码语法是否正确 