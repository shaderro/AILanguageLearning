# 文章处理模块 (Article Processing Module)

这个模块提供了完整的文章处理功能，包括句子分割、token分割和结构化数据生成。

## 功能特点

- **句子分割**: 使用正则表达式智能分割句子
- **Token分割**: 将句子分割成单词、标点符号和空白字符
- **ID管理**: 为每个token分配全局和句子级别的唯一ID
- **数据保存**: 支持多种格式的数据保存
- **结果验证**: 提供结果有效性验证功能

## 模块结构

```
article_processing/
├── __init__.py              # 模块初始化文件
├── sentence_processor.py    # 句子处理模块
├── token_processor.py       # Token处理模块
├── article_processor.py     # 文章处理主模块
├── utils.py                 # 工具函数模块
├── demo.py                  # 演示脚本
└── README.md               # 说明文档
```

## 快速开始

### 基本使用

```python
from article_processing import process_article_simple

# 处理文章
article = "Hello, world! This is a test. How are you today?"
result = process_article_simple(article)

# 查看结果
print(f"句子数: {result['total_sentences']}")
print(f"Token数: {result['total_tokens']}")
```

### 完整处理

```python
from article_processing import process_article, save_structured_data

# 处理文章
result = process_article(
    raw_text="Your article text here...",
    text_id=1,
    text_title="My Article"
)

# 保存结构化数据
save_structured_data(result, "output_data")
```

### 单独使用模块

```python
from article_processing.sentence_processor import split_sentences
from article_processing.token_processor import split_tokens

# 只分割句子
sentences = split_sentences("Hello! How are you? I'm fine.")

# 只分割tokens
tokens = split_tokens("Hello, world!")
```

## API 参考

### 主要函数

#### `process_article_simple(raw_text: str) -> Dict[str, Any]`
简单处理文章，返回包含句子和tokens的结构化数据。

**参数:**
- `raw_text`: 原始文章文本

**返回:**
- 包含句子和tokens信息的字典

#### `process_article(raw_text: str, text_id: int = 1, text_title: str = "Article") -> Dict[str, Any]`
完整处理文章，包含更多元数据信息。

**参数:**
- `raw_text`: 原始文章文本
- `text_id`: 文章ID
- `text_title`: 文章标题

**返回:**
- 包含完整结构化信息的字典

#### `save_structured_data(result: Dict[str, Any], output_dir: str = "data")`
保存结构化数据到JSON文件。

**参数:**
- `result`: 处理结果
- `output_dir`: 输出目录

### 工具函数

#### `save_result(result: Dict[str, Any], filename: str = "article_result.json")`
保存结果到单个JSON文件。

#### `print_result_summary(result: Dict[str, Any])`
打印结果摘要信息。

#### `get_token_statistics(result: Dict[str, Any]) -> Dict[str, Any]`
获取token统计信息。

#### `validate_result(result: Dict[str, Any]) -> bool`
验证处理结果的有效性。

## 输出格式

### 简单处理结果

```json
{
  "sentences": [
    {
      "sentence_id": 1,
      "sentence_body": "Hello, world!",
      "tokens": [
        {
          "token_body": "Hello",
          "token_type": "text",
          "global_token_id": 0,
          "sentence_token_id": 1
        }
      ],
      "token_count": 5
    }
  ],
  "total_sentences": 1,
  "total_tokens": 5
}
```

### 完整处理结果

生成三个文件：
- `original_text.json`: 原始文本结构
- `sentences.json`: 句子列表
- `tokens.json`: 所有tokens的扁平化列表

## 运行演示

```bash
python -m article_processing.demo
```

## 注意事项

1. 句子分割使用句号(.)、问号(?)、感叹号(!)作为分隔符
2. Token类型包括：`text`(单词)、`punctuation`(标点符号)、`space`(空白字符)
3. 所有ID从0开始计数
4. 支持UTF-8编码的文本处理

## 依赖

- Python 3.6+
- 标准库：`re`, `json`, `os`, `typing`

无需额外安装第三方库。 