# AI语言学习应用

**更新日期：2025年1月**

这是一个基于AI的语言学习应用，专注于语法规则和词汇表达的学习与管理。项目采用前后端分离架构，支持多种前端技术栈。

## 🏗️ 项目架构

### Backend 后端 (`backend/`)
包含所有后端功能模块，提供AI助手、数据管理和预处理服务。

### Frontend 前端 (`frontend/`)
新的前端开发目录，支持Web、移动端和桌面端开发。

## 🚀 核心功能

### AI助手系统 (`backend/assistants/`)

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

### 数据管理系统 (`backend/data_managers/`)

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

### 数据预处理系统 (`backend/preprocessing/`)
- **文章处理器** (`article_processor.py`)
- **句子处理器** (`sentence_processor.py`)
- **词汇处理器** (`token_processor.py`)
- **难度评估** (`single_token_difficulty_estimation.py`)

## 📁 项目结构

```
AILanguageLearning/
├── backend/                      # 后端功能模块
│   ├── assistants/               # AI助手系统
│   ├── data_managers/            # 数据管理系统
│   ├── preprocessing/            # 数据预处理
│   ├── data/                     # 数据文件
│   └── main.py                   # 主程序入口
├── frontend/                     # 前端（Web UI）
│   └── my-web-ui/
├── database_system/              # 数据库层
├── scripts/                      # 运维/迁移/检查脚本
│   ├── admin/                    # 数据管理、种子数据
│   ├── migrations/               # Python 迁移
│   ├── sql/                      # SQL 脚本
│   └── checks/                   # 环境检查与测试
├── docs/                         # 文档与资源
│   ├── guides/                   # 使用指南
│   └── assets/                   # 截图、样例文本
├── start_backend.ps1             # 启动后端
├── start_frontend.ps1            # 启动前端
├── requirements.txt              # Python 依赖
└── README.md                     # 项目说明
```

## 🚀 快速开始

### 环境要求
- Python 3.7+
- 相关依赖包（见requirements.txt）

### 运行后端服务
```bash
cd backend
python main.py
```

### 基本使用示例
```python
from backend.assistants.main_assistant import MainAssistant
from backend.data_managers import data_controller

# 初始化数据控制器
dc = data_controller.DataController(max_turns=100)

# 创建主助手
assistant = MainAssistant(data_controller_instance=dc)

# 处理用户问题
assistant.run(sentence, user_question, quoted_string)
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

## 🎯 开发计划

### 前端开发
- **Web前端**: React/Vue.js + TypeScript
- **移动端**: React Native 或 Flutter
- **桌面端**: Electron

### 功能模块
- 用户认证和授权
- 文章阅读界面
- 词汇学习界面
- 语法学习界面
- AI对话界面
- 学习进度跟踪
- 数据可视化

---

*本项目专注于AI驱动的语言学习体验，通过智能分析和数据管理，为用户提供个性化的语言学习支持。支持新旧数据结构模式的平滑过渡，并采用现代化的前后端分离架构。*