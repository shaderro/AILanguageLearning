# 数据文件结构说明

## 当前数据结构

```
backend/data/current/
├── vocab.json              # 词汇数据
├── grammar.json            # 语法规则数据
├── dialogue_history.json   # 对话历史
├── dialogue_record.json    # 对话记录
└── articles/               # 文章数据目录
    ├── hp1_processed_*.json    # 处理后的文章数据
    └── hp1_summary_*.json      # 文章摘要数据
```

## 数据文件说明

### 核心学习数据
- **vocab.json**: 词汇表达数据，包含词汇、解释、例句等
- **grammar.json**: 语法规则数据，包含规则名称、解释、例句等

### 对话数据
- **dialogue_history.json**: 用户与AI的对话历史记录
- **dialogue_record.json**: 对话记录，包含句子信息和token分析

### 文章数据
- **articles/**: 文章数据目录
  - 处理后的文章JSON文件（包含句子、token等结构化数据）
  - 文章摘要文件

## 数据更新流程

1. **词汇数据**: 通过前端Word Demo页面的收藏功能或API调用更新
2. **语法数据**: 通过前端Grammar Demo页面更新
3. **文章数据**: 通过文章处理流程生成，存储在articles目录
4. **对话数据**: 通过聊天功能自动更新

## 备份建议

定期备份 `backend/data/current/` 目录下的所有文件，确保学习数据不丢失。
