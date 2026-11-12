# TextProcessor 使用说明

`TextProcessor` 是一个模块化的文本处理类，可以将原始文本文件分割成结构化的数据，生成符合 `token_data.py` 中定义的数据结构。

## 功能特性

- ✅ **模块化设计**：所有功能集成在一个类中
- ✅ **命令行支持**：直接通过命令行处理文件
- ✅ **批量处理**：支持同时处理多个文件
- ✅ **灵活输出**：可自定义输出目录
- ✅ **优化数据结构**：避免重复冗余，通过ID索引建立关联
- ✅ **存储效率**：相比原结构减少约80%存储空间
- ✅ **查询友好**：便于查询和更新特定token
- ✅ **错误处理**：完善的异常处理和错误提示

## 快速开始

### 1. 命令行使用

```bash
# 处理单个文件
python text_processor.py input.txt

# 批量处理多个文件
python text_processor.py file1.txt file2.txt file3.txt
```

### 2. 编程使用

```python
from text_processor import TextProcessor

# 创建处理器实例
processor = TextProcessor(output_base_dir="my_data")

# 处理单个文件
success = processor.process_file("input.txt", text_id=1)

# 批量处理文件
files = ["file1.txt", "file2.txt", "file3.txt"]
success_count = processor.process_multiple_files(files, start_text_id=1)
```

## 输出结构

处理后的数据按照以下结构组织（优化版本，避免重复冗余）：

```
data/
├── text_001/
│   ├── original_texts.json      # 文本元数据和句子ID索引
│   ├── sentences.json           # 句子列表（包含token_ids索引）
│   └── tokens.json              # 所有tokens的独立存储
├── text_002/
│   ├── original_texts.json
│   ├── sentences.json
│   └── tokens.json
└── ...
```

## 类方法说明

### `__init__(output_base_dir="data")`
初始化文本处理器
- `output_base_dir`: 输出基础目录，默认为 "data"

### `process_file(input_path, text_id, output_dir=None) -> bool`
处理单个文本文件
- `input_path`: 输入文件路径
- `text_id`: 文本ID
- `output_dir`: 输出目录（可选，默认使用 `data/text_XXX`）
- 返回：处理是否成功

### `process_multiple_files(input_files, start_text_id=1) -> int`
批量处理多个文件
- `input_files`: 文件路径列表
- `start_text_id`: 起始文本ID
- 返回：成功处理的文件数量

### `process_text_to_structured_data(text, text_id, text_title="") -> OriginalText`
将文本处理成结构化数据对象
- `text`: 文本内容或文件路径
- `text_id`: 文本ID
- `text_title`: 文本标题
- 返回：结构化的文本数据对象

### `save_structured_data(original_text, output_dir)`
保存结构化数据到指定目录
- `original_text`: 结构化的文本数据对象
- `output_dir`: 输出目录路径

## 数据格式

### 1. original_texts.json（文本元数据）
```json
{
  "text_id": 1,
  "text_title": "sample_input.txt",
  "text_body": "Python programming is essential for data science.\nThe language offers powerful libraries...",
  "sentence_ids": [1, 2, 3]
}
```

### 2. sentences.json（句子列表）
```json
[
  {
    "sentence_id": 1,
    "text_id": 1,
    "sentence_body": "Python programming is essential for data science.",
    "token_ids": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
    "grammar_annotations": [],
    "vocab_annotations": []
  }
]
```

### 3. tokens.json（Token独立存储）
```json
[
  {
    "token_id": 0,
    "sentence_id": 1,
    "token_body": "Python",
    "token_type": "text",
    "sentence_token_index": 0,
    "difficulty_level": null,
    "explanation": null,
    "pos_tag": null,
    "lemma": null,
    "is_grammar_marker": false
  }
]
```

## 使用示例

### 示例1：基本使用
```python
from text_processor import TextProcessor

# 创建处理器
processor = TextProcessor()

# 处理文件
processor.process_file("my_article.txt", 1)
```

### 示例2：自定义输出目录
```python
processor = TextProcessor(output_base_dir="custom_data")
processor.process_file("input.txt", 1, "custom_data/my_article")
```

### 示例3：批量处理
```python
files = ["article1.txt", "article2.txt", "article3.txt"]
processor.process_multiple_files(files, start_text_id=10)
```

### 示例4：处理字符串文本
```python
text_content = "Hello, world! This is a test."
original_text = processor.process_text_to_structured_data(text_content, 1, "Test Text")
processor.save_structured_data(original_text, "data/test_output")
```

## 命令行参数

```bash
python text_processor.py <文件路径1> [文件路径2] [文件路径3] ...
```

- 至少需要一个文件路径
- 支持多个文件路径，将进行批量处理
- 文件按顺序分配递增的文本ID

## 错误处理

- 文件不存在：显示错误信息并跳过
- 文件读取失败：显示错误信息并跳过
- 处理异常：显示详细错误信息
- 批量处理：即使部分文件失败，也会继续处理其他文件

## 测试

运行测试脚本：
```bash
python test_text_processor.py
```

## 注意事项

1. **文件编码**：确保输入文件使用UTF-8编码
2. **文件格式**：支持任何文本文件（.txt, .md等）
3. **文本ID**：每个文本应该有唯一的ID
4. **输出目录**：会自动创建不存在的目录
5. **内存使用**：大文件处理时注意内存使用情况

## 依赖

- Python 3.7+
- 标准库：`re`, `json`, `os`, `sys`, `typing`, `dataclasses`

无需额外安装第三方库！ 