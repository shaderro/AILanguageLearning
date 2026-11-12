# 文本处理工具集 (Text Processing Tools)

一个功能完整的文本处理工具集，支持句子分割、token分割、难度评估、lemma处理、vocab生成等功能。

## 📁 项目结构

```
preprocessing/
├── src/                          # 源代码目录
│   ├── core/                     # 核心功能模块
│   │   ├── __init__.py
│   │   ├── text_processor.py     # 主文本处理器
│   │   ├── token_data.py         # 数据结构定义
│   │   ├── sentence_splitter.py  # 句子分割器
│   │   └── token_splitter.py     # Token分割器
│   ├── agents/                   # AI代理模块
│   │   ├── __init__.py
│   │   ├── get_difficulty_agent.py           # 难度评估代理
│   │   ├── single_token_difficulty_estimation.py  # 单token难度评估
│   │   ├── sub_assistant.py      # 子助手
│   │   ├── vocab_explanation.py  # 词汇解释助手
│   │   ├── vocab_example_explanation.py  # 词汇示例解释助手
│   │   └── grammar_analysis.py   # 语法分析助手
│   ├── utils/                    # 工具模块
│   │   ├── __init__.py
│   │   ├── get_lemma.py          # Lemma处理
│   │   ├── get_pos_tag.py        # POS标签处理
│   │   ├── openai_utils.py       # OpenAI工具
│   │   ├── token_to_vocab.py     # Token到Vocab转换
│   │   ├── utility.py            # 通用工具
│   │   ├── config.py             # 配置
│   │   └── promp.py              # 提示模板
│   └── tests/                    # 测试模块
│       ├── __init__.py
│       ├── test_difficulty_integration.py    # 难度评估集成测试
│       ├── test_lemma_integration.py         # Lemma集成测试
│       ├── test_difficulty_estimation.py     # 难度评估测试
│       ├── test_token_to_vocab.py            # Token到Vocab转换测试
│       └── verify_processing.py  # 处理验证
├── examples/                     # 示例和演示
│   ├── example_openai_usage.py   # OpenAI使用示例
│   ├── vocab_generation_example.py  # Vocab生成示例
│   ├── grammar_analysis_example.py  # 语法分析示例
│   ├── final_demo.py             # 最终演示
│   └── test_article_5sentences.txt  # 测试文本
├── docs/                         # 文档
│   ├── README_TextProcessor.md   # 文本处理器文档
│   ├── README_OpenAI.md          # OpenAI使用文档
│   └── README_Difficulty_Integration.md  # 难度评估集成文档
├── data/                         # 数据输出目录
├── main.py                       # 主入口文件
└── README.md                     # 项目说明文档
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 基本使用

```bash
# 处理单个文件
python main.py examples/test_article_5sentences.txt 1

# 处理多个文件
python -c "
from src.core.text_processor import TextProcessor
processor = TextProcessor()
processor.process_multiple_files(['file1.txt', 'file2.txt'], start_text_id=1)
"
```

### 3. 生成Vocab

```bash
# 从文本生成vocab
python examples/vocab_generation_example.py

# 使用API生成vocab
python -c "
from src.core.text_processor import TextProcessor
from src.utils.token_to_vocab import TokenToVocabConverter

# 处理文本
processor = TextProcessor()
text = 'Artificial intelligence has revolutionized technology.'
original_text = processor.process_text_to_structured_data(text, 1, '测试文本')

# 生成vocab
converter = TokenToVocabConverter()
vocab_expressions = converter.convert_tokens_from_text(original_text)
converter.save_vocab_data(vocab_expressions)
"
```

### 4. 语法分析

```bash
# 运行语法分析示例
python examples/grammar_analysis_example.py

# 使用API进行语法分析
python -c "
from src.agents import GrammarAnalysisAssistant

# 创建语法分析助手
assistant = GrammarAnalysisAssistant()

# 分析句子语法
result = assistant.analyze_grammar(
    'Artificial intelligence has revolutionized technology.',
    'This sentence discusses the impact of AI on technology.'
)

print(f'语法讲解: {result[\"explanation\"]}')
print(f'关键词: {result[\"keywords\"]}')
"
```

### 4. 运行测试

```bash
# 运行难度评估集成测试
python src/tests/test_difficulty_integration.py

# 运行lemma集成测试
python src/tests/test_lemma_integration.py

# 运行token_to_vocab测试
python src/tests/test_token_to_vocab.py

# 运行处理验证
python src/tests/verify_processing.py
```

## 🔧 核心功能

### 1. 文本处理器 (TextProcessor)

- **句子分割**：智能分割文本为句子
- **Token分割**：将句子分割为tokens（文本、标点、空格）
- **难度评估**：对text类型token进行难度评估
- **Lemma处理**：对text类型token进行lemma处理
- **结构化输出**：生成JSON格式的结构化数据

### 2. AI代理功能

- **难度评估**：使用OpenAI API评估token难度
- **词汇解释**：生成详细的词汇解释
- **上下文解释**：生成词汇在特定语境中的解释
- **语法分析**：分析句子的语法结构和关键词
- **智能分析**：支持上下文相关的分析
- **错误处理**：完善的异常处理机制

### 3. Token到Vocab转换

- **自动识别**：自动识别hard难度的text类型token
- **词汇解释**：使用AI生成详细的词汇解释
- **上下文分析**：分析词汇在句子中的具体用法
- **数据持久化**：将vocab数据保存为JSON格式
- **批量处理**：支持批量处理多个token

### 4. 工具模块

- **Lemma处理**：使用NLTK进行词形还原
- **POS标签**：词性标注功能
- **OpenAI集成**：OpenAI API工具类

## 📊 输出格式

### 处理后的文本数据

```json
{
  "text_id": 1,
  "text_title": "示例文本",
  "text_by_sentence": [
    {
      "sentence_id": 1,
      "sentence_body": "示例句子。",
      "tokens": [
        {
          "token_body": "示例",
          "token_type": "text",
          "difficulty_level": "easy",
          "lemma": "示例"
        }
      ]
    }
  ]
}
```

### 生成的Vocab数据

```json
{
  "vocab_expressions": [
    {
      "vocab_id": 1,
      "vocab_body": "Artificial",
      "explanation": "Artificial 是一个形容词，意思是'人造的'或'非自然的'...",
      "source": "auto",
      "is_starred": false,
      "examples": [
        {
          "vocab_id": 1,
          "text_id": 1,
          "sentence_id": 1,
          "context_explanation": "在这里，'Artificial' 指的是由人类创造或制造的..."
        }
      ]
    }
  ],
  "next_vocab_id": 2
}
```

## 🧪 测试

项目包含完整的测试套件：

- **集成测试**：测试核心功能的集成
- **单元测试**：测试各个模块的功能
- **验证测试**：验证数据处理的正确性
- **Vocab生成测试**：测试token到vocab的转换功能

## 📚 文档

详细文档请查看 `docs/` 目录：

- [文本处理器文档](docs/README_TextProcessor.md)
- [OpenAI使用文档](docs/README_OpenAI.md)
- [难度评估集成文档](docs/README_Difficulty_Integration.md)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## �� 许可证

MIT License 