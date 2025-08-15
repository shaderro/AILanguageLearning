# AI语言学习应用

**更新日期：2025年8月12日**

这是一个基于AI的语言学习应用，专注于语法规则和词汇表达的学习与管理。

## 🚀 核心功能

### AI助手系统 (assistants/)

#### 主助手 (main_assistant.py)
- **智能对话处理**：接收用户问题，分析句子内容，提供语言学习相关的回答
- **内容相关性判断**：自动识别问题是否与语言学习相关
- **语法和词汇管理**：智能添加新的语法规则和词汇表达
- **会话状态管理**：维护对话上下文和用户学习进度

#### 子助手模块 (sub_assistants/)
- **相关性检查助手**：
  - `check_if_grammar_relevant_assistant.py` - 检查语法相关性
  - `check_if_vocab_relevant_assistant.py` - 检查词汇相关性
  - `check_if_relevant.py` - 通用相关性检查
- **内容总结助手**：
  - `summarize_grammar_rule.py` - 语法规则总结
  - `summarize_vocab.py` - 词汇表达总结
  - `summarize_dialogue_history.py` - 对话历史总结
- **问答助手**：
  - `answer_question.py` - 智能问答处理
  - `grammar_example_explanation.py` - 语法示例解释
  - `vocab_explanation.py` - 词汇解释
- **比较分析助手**：
  - `compare_grammar_rule.py` - 语法规则比较

#### 会话管理 (chat_info/)
- **对话历史管理** (`dialogue_history.py`)：维护多轮对话记录
- **会话状态管理** (`session_state.py`)：跟踪当前学习会话状态

### 数据管理系统 (data_managers/)

#### 核心数据类 (data_classes.py)
- **Sentence**：句子数据结构，包含文本ID、句子ID、语法标注等
- **GrammarRule**：语法规则结构
- **VocabExpression**：词汇表达结构
- **OriginalText**：原始文本结构

#### 数据管理器
- **DataController** (`data_controller.py`)：统一的数据操作控制器
- **GrammarRuleManager** (`grammar_rule_manager.py`)：语法规则管理
- **VocabManager** (`vocab_manager.py`)：词汇表达管理
- **OriginalTextManager** (`original_text_manager.py`)：原始文本管理
- **DialogueRecord** (`dialogue_record.py`)：对话记录管理

#### 数据持久化
- 支持JSON格式的数据存储和加载
- 自动管理语法规则、词汇表达和对话记录
- 提供数据备份和恢复功能

#### 🔄 新结构模式开关
- **USE_NEW_STRUCTURE**：全局开关，默认为`False`
- **渐进式切换**：支持在运行时动态切换数据结构模式
- **向后兼容**：保留旧结构加载逻辑，确保平滑过渡
- **自动回退**：新结构加载失败时自动回退到旧结构

## 🏗️ 架构设计

### 模块化设计
- **AI助手层**：负责智能对话和内容分析
- **数据管理层**：负责数据存储、检索和管理
- **业务逻辑层**：连接AI助手和数据管理

### 数据流
```
用户输入 → AI助手分析 → 内容相关性判断 → 智能回答 → 数据更新 → 持久化存储
```

### 扩展性
- 支持添加新的子助手模块
- 可扩展的数据结构设计
- 模块化的架构便于功能扩展
- 新结构模式支持Token级别的细粒度分析

## 📁 项目结构

```
langApp514/
├── assistants/                    # AI助手系统
│   ├── main_assistant.py         # 主助手
│   ├── sub_assistants/           # 子助手模块
│   ├── chat_info/                # 会话管理
│   └── utility.py                # 工具函数
├── data_managers/                # 数据管理系统
│   ├── data_classes.py           # 旧数据结构类定义
│   ├── data_classes_new.py       # 新数据结构类定义
│   ├── data_controller.py        # 数据控制器（支持双模式）
│   ├── grammar_rule_manager.py   # 旧结构语法规则管理
│   ├── vocab_manager.py          # 旧结构词汇管理
│   ├── original_text_manager.py  # 旧结构原始文本管理
│   └── dialogue_record.py        # 对话记录管理
└── data/                         # 数据文件
    ├── grammar_rules.json        # 语法规则数据
    ├── vocab_expressions.json    # 词汇表达数据
    ├── original_texts.json       # 原始文本数据
    └── dialogue_history.json     # 对话历史数据
```

## 🚀 快速开始

### 环境要求
- Python 3.7+
- 相关依赖包（见requirements.txt）

### 基本使用
```python
from assistants.main_assistant import MainAssistant
from data_managers import data_controller

# 初始化数据控制器（使用默认的旧结构模式）
dc = data_controller.DataController(max_turns=100)

# 或者明确指定使用新结构模式
dc = data_controller.DataController(max_turns=100, use_new_structure=True)

# 创建主助手
assistant = MainAssistant(data_controller_instance=dc)

# 处理用户问题
assistant.run(sentence, user_question, quoted_string)
```

### 新结构模式切换
```python
# 运行时切换到新结构模式
if dc.switch_to_new_structure():
    print("已切换到新数据结构")
else:
    print("切换失败，保持旧结构")

# 切换回旧结构模式
if dc.switch_to_old_structure():
    print("已切换回旧数据结构")

# 查看当前使用的结构模式
current_mode = dc.get_structure_mode()
print(f"当前使用: {current_mode} 结构")
```

## 🔧 配置说明

- **max_turns**：最大对话轮数设置
- **数据文件路径**：可在DataController中配置
- **AI模型参数**：可在各子助手中调整
- **USE_NEW_STRUCTURE**：全局新结构模式开关

## 📝 注意事项

- 确保数据文件路径正确
- 定期备份重要数据
- 监控AI助手的响应质量
- 根据需要调整相关性判断阈值
- 新结构模式需要相应的管理器文件支持
- 切换结构模式前建议备份数据

## 🔄 新结构模式特性

### Token级别分析
- 支持词、标点符号、空格的细粒度识别
- 词性标注和原型词提取
- 语法结构标记识别
- 词汇关联和难度分级

### 渐进式迁移
- 支持运行时动态切换
- 自动数据格式转换
- 失败时自动回退
- 保持向后兼容性

---

*本项目专注于AI驱动的语言学习体验，通过智能分析和数据管理，为用户提供个性化的语言学习支持。支持新旧数据结构模式的平滑过渡。*