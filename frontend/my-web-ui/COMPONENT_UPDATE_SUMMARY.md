# 组件更新总结

## 更新概述
根据新的数据结构 `VocabExpression`/`GrammarRule` 和 `VocabExpressionExample`/`GrammarExample`，重新定义了 `LearnCard` 和 `LearnDetailPage` 组件。

## 数据结构映射

### VocabExpression 结构
```typescript
{
  vocab_id: number
  vocab_body: string
  explanation: string
  source: "auto" | "qa" | "manual"
  is_starred: boolean
  examples: VocabExpressionExample[]
}
```

### VocabExpressionExample 结构
```typescript
{
  vocab_id: number
  text_id: number
  sentence_id: number
  context_explanation: string
  token_indices: number[]
}
```

### GrammarRule 结构
```typescript
{
  rule_id: number
  name: string
  explanation: string
  source: "auto" | "qa" | "manual"
  is_starred: boolean
  examples: GrammarExample[]
}
```

### GrammarExample 结构
```typescript
{
  rule_id: number
  text_id: number
  sentence_id: number
  explanation_context: string
}
```

## LearnCard 组件更新

### 显示内容
- **词汇卡片**：
  - 词汇本身 (`vocab_body`)
  - 解释的第一行 (`explanation` 的第一行)
  - 第一个例子的第一行 (`examples[0].context_explanation` 的第一行)
  - 来源和星标状态

- **语法卡片**：
  - 语法规则名称 (`name`)
  - 解释的第一行 (`explanation` 的第一行)
  - 第一个例子的第一行 (`examples[0].explanation_context` 的第一行)
  - 来源和星标状态

### 设计特点
- 简洁的卡片布局，只显示关键信息
- 使用 `getFirstLine()` 函数提取文本的第一行
- 标题现在在内容中显示，而不是在卡片标题位置

## LearnDetailPage 组件更新

### 显示内容
- **词汇详情页**：
  - 词汇基本信息（词汇体、ID、星标状态）
  - 完整解释（支持多行文本）
  - 所有使用例子（包含文章ID、句子ID、词汇位置）
  - 元信息（来源、词汇ID）

- **语法详情页**：
  - 语法规则基本信息（规则名称、ID、星标状态）
  - 完整规则解释（支持多行文本）
  - 所有使用例子（包含文章ID、句子ID）
  - 元信息（来源、规则ID）

### 设计特点
- 详细的信息展示，包含所有可用数据
- 使用不同的背景色区分不同类型的内容
- 支持多行文本显示（`whitespace-pre-line`）
- 清晰的层次结构和视觉分隔

## 兼容性
- 保持原有的 props 接口不变
- 支持 `type` 参数区分词汇和语法
- 保持错误处理和加载状态的处理逻辑

## 测试验证
- 后端 API 返回的数据结构完全符合新的数据类定义
- 组件能够正确解析和显示所有字段
- 支持空值和缺失字段的优雅处理
