# Data 文件夹结构说明

本文件夹包含语言学习系统的所有数据文件，按照用途和版本进行了分类整理。

## 📁 文件夹结构

```
data/
├── article/                    # 文章数据文件夹
│   ├── article01.json         # 文章1
│   ├── article02.json         # 文章2
│   └── ...                    # 更多文章文件
├── current/                   # 当前使用的数据文件
│   ├── vocab.json            # 当前词汇数据
│   ├── grammar.json          # 当前语法数据
│   ├── dialogue_history.json # 对话历史
│   └── dialogue_record.json  # 对话记录
├── backup/                   # 备份文件夹
│   ├── legacy/              # 旧版本文件
│   │   ├── vocab_expressions.json    # 旧版词汇文件
│   │   ├── grammar_rules.json        # 旧版语法文件
│   │   ├── original_texts.json       # 旧版文本文件
│   │   └── grammar_rules_en.json     # 英文语法规则
│   ├── versions/            # 新版本文件
│   │   ├── vocab_expressions_new.json  # 新版词汇文件
│   │   ├── grammar_rules_new.json      # 新版语法文件
│   │   └── original_texts_new.json     # 新版文本文件
│   └── test/               # 测试文件
│       ├── test_*.json     # 功能测试文件
│       └── *_test*.json    # 各种测试数据
└── README.md              # 本说明文件
```

## 📋 文件说明

### 当前使用文件 (current/)

- **vocab.json**: 集成系统当前使用的词汇数据文件
- **grammar.json**: 集成系统当前使用的语法规则文件
- **dialogue_history.json**: 用户对话历史记录
- **dialogue_record.json**: 详细的对话记录数据

### 文章文件 (article/)

- **article{ID:02d}.json**: 按ID命名的文章文件
  - 格式: `article01.json`, `article02.json`, `article10.json` 等
  - 结构: 符合 `data_classes_new.OriginalText` 数据结构
  - 包含: `text_id`, `text_title`, `text_by_sentence`

### 备份文件 (backup/)

#### 旧版本文件 (backup/legacy/)
- 系统升级前的旧数据文件
- 保留用于数据迁移和兼容性测试

#### 新版本文件 (backup/versions/)
- 数据结构升级过程中的版本文件
- 包含新字段和结构的数据文件

#### 测试文件 (backup/test/)
- 开发和测试过程中生成的临时数据文件
- 功能测试和特性验证文件

## 🔧 使用说明

1. **生产环境**: 使用 `current/` 文件夹中的文件
2. **开发测试**: 可以使用 `backup/test/` 中的测试数据
3. **数据恢复**: 如需回滚，可从 `backup/legacy/` 或 `backup/versions/` 恢复
4. **文章管理**: 新文章自动保存到 `article/` 文件夹

## ⚠️ 注意事项

- 不要直接修改 `current/` 文件夹中的文件，应通过系统API操作
- `backup/` 文件夹中的文件仅用于备份和参考
- 删除文件前请确认不再需要，建议先移动到备份文件夹

## 🗂️ 文件清理

已清理的重复和相似文件：
- 移动了 18+ 个测试文件到 `backup/test/`
- 整理了多个版本的数据文件到相应分类
- 保持了清晰的文件夹结构和命名规范

最后更新: 2024-08-19 