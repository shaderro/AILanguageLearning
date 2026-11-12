# 难度评估和Lemma集成说明

## 📋 概述

本文档说明了在 `text_processor.py` 中集成 `get_difficulty_agent` 和 `get_lemma` 功能的具体实现。

## 🔧 集成功能

### 1. 核心功能

- ✅ 自动识别token类型
- ✅ 只对 `token_type` 为 "text" 的token进行难度评估和lemma处理
- ✅ 保持其他token类型（space、punctuation）的 `difficulty_level` 和 `lemma` 为 `null`
- ✅ 错误处理和异常捕获
- ✅ 结果格式验证

### 2. 实现细节

#### 2.1 导入依赖

```python
from single_token_difficulty_estimation import SingleTokenDifficultyEstimator
from get_lemma import get_lemma
```

#### 2.2 初始化处理器

```python
def __init__(self, output_base_dir: str = "data"):
    self.output_base_dir = output_base_dir
    os.makedirs(output_base_dir, exist_ok=True)
    # 初始化难度评估器
    self.difficulty_estimator = SingleTokenDifficultyEstimator()
```

#### 2.3 难度评估方法

```python
def assess_token_difficulty(self, token_body: str, context: str = "") -> str:
    """
    评估token的难度级别
    
    Args:
        token_body: token内容
        context: 上下文（可选）
        
    Returns:
        str: 难度级别 ("easy" 或 "hard")
    """
    try:
        # 只对text类型的token进行难度评估
        if not token_body or not token_body.strip():
            return None
        
        # 调用难度评估器
        difficulty_result = self.difficulty_estimator.run(token_body, verbose=False)
        
        # 清理结果，确保只返回 "easy" 或 "hard"
        difficulty_result = difficulty_result.strip().lower()
        if difficulty_result in ["easy", "hard"]:
            return difficulty_result
        else:
            # 如果结果不是预期的格式，返回默认值
            print(f"⚠️  警告：token '{token_body}' 的难度评估结果格式异常: '{difficulty_result}'")
            return "easy"  # 默认返回easy
            
    except Exception as e:
        print(f"❌ 评估token '{token_body}' 难度时发生错误: {e}")
        return None
```

#### 2.4 Lemma处理方法

```python
def get_token_lemma(self, token_body: str) -> str:
    """
    获取token的lemma形式
    
    Args:
        token_body: token内容
        
    Returns:
        str: lemma形式，如果无法获取则返回None
    """
    try:
        # 只对text类型的token进行lemma处理
        if not token_body or not token_body.strip():
            return None
        
        # 调用get_lemma函数
        lemma = get_lemma(token_body)
        return lemma
        
    except Exception as e:
        print(f"❌ 获取token '{token_body}' 的lemma时发生错误: {e}")
        return None
```

#### 2.5 集成到处理流程

```python
# 在 process_text_to_structured_data 方法中
for token_id, token_dict in enumerate(token_dicts, 1):
    # 评估难度级别和获取lemma（只对text类型的token）
    difficulty_level = None
    lemma = None
    if token_dict["token_type"] == "text":
        difficulty_level = self.assess_token_difficulty(token_dict["token_body"], sentence_text)
        lemma = self.get_token_lemma(token_dict["token_body"])
    
    token = Token(
        token_body=token_dict["token_body"],
        token_type=token_dict["token_type"],
        global_token_id=global_token_id,
        sentence_token_id=token_id,
        difficulty_level=difficulty_level,
        lemma=lemma
    )
    tokens.append(token)
    global_token_id += 1
```

## 📊 测试结果

### 测试用例

使用测试文本：`"Artificial intelligence has revolutionized the way we interact with technology."`

### 结果分析

```
📈 统计信息:
   总token数量: 20
   text类型token: 10
   有lemma的token: 10
   无lemma的token: 10

✅ 验证结果:
✅ 所有text类型token都有lemma
✅ 所有非text类型token都没有lemma
```

### 具体示例

```json
{
  "token_id": 0,
  "sentence_id": 1,
  "token_body": "Artificial",
  "token_type": "text",
  "sentence_token_index": 0,
  "difficulty_level": "hard",
  "explanation": null,
  "pos_tag": null,
  "lemma": "artificial",
  "is_grammar_marker": false
},
{
  "token_id": 1,
  "sentence_id": 1,
  "token_body": " ",
  "token_type": "space",
  "sentence_token_index": 1,
  "difficulty_level": null,
  "explanation": null,
  "pos_tag": null,
  "lemma": null,
  "is_grammar_marker": false
}
```

## 🎯 关键特性

### 1. 类型识别

- **text**: 进行难度评估和lemma处理，返回相应的值
- **space**: 保持 `difficulty_level` 和 `lemma` 为 `null`
- **punctuation**: 保持 `difficulty_level` 和 `lemma` 为 `null`

### 2. 错误处理

- 空token或空白token：返回 `None`
- API调用失败：返回 `None` 并打印错误信息
- 格式异常：返回默认值并打印警告
- NLTK数据缺失：自动下载必要数据

### 3. 性能优化

- 只对必要的token进行API调用
- 避免重复评估
- 异常情况下有合理的默认值
- 静默处理NLTK错误

## 🚀 使用方法

### 1. 基本使用

```python
from text_processor import TextProcessor

# 创建处理器
processor = TextProcessor()

# 处理文本
original_text = processor.process_text_to_structured_data(
    "Your text here", 
    text_id=1, 
    text_title="测试文本"
)

# 查看结果
for sentence in original_text.text_by_sentence:
    for token in sentence.tokens:
        if token.token_type == "text":
            print(f"Token: {token.token_body}")
            print(f"  Difficulty: {token.difficulty_level}")
            print(f"  Lemma: {token.lemma}")
```

### 2. 文件处理

```python
# 处理文件
success = processor.process_file("input.txt", text_id=1)
if success:
    print("处理完成！")
```

## 🔍 验证方法

运行验证脚本：

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行测试
python test_difficulty_integration.py
python test_lemma_integration.py

# 运行完整验证
python verify_processing.py
```

## 📝 注意事项

1. **API依赖**: 需要安装 `openai` 模块
2. **NLTK依赖**: 需要安装 `nltk` 模块和相关数据
3. **网络连接**: 需要网络连接来调用AI API和下载NLTK数据
4. **API限制**: 注意API调用频率和配额限制
5. **错误处理**: 异常情况下会有合理的默认值
6. **性能考虑**: 大量文本处理时可能需要较长时间

## 🎉 总结

成功集成了 `get_difficulty_agent` 和 `get_lemma` 功能到 `text_processor.py` 中，实现了：

- ✅ 自动token类型识别
- ✅ 智能难度评估
- ✅ 准确的lemma处理
- ✅ 完善的错误处理
- ✅ 数据一致性保证
- ✅ 详细的测试验证

集成后的系统能够自动为文本token提供难度评估和lemma处理，同时保持数据结构的完整性和一致性。 