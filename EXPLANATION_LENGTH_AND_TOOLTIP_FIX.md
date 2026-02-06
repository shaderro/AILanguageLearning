# Grammar Explanation 和 Context Explanation 限制长度报告

## 当前限制长度

### 1. Grammar Example Explanation (context_explanation)
**文件：** `backend/assistants/sub_assistants/grammar_example_explanation.py`
- **当前限制：** `max_tokens=100`
- **问题：** 100 tokens 对于中文解释来说太短，容易被截断

### 2. Vocab Example Explanation (context_explanation)
**文件：** `backend/assistants/sub_assistants/vocab_example_explanation.py`
- **当前限制：** `max_tokens=4000`
- **状态：** ✅ 已优化，足够长

### 3. Grammar Rule Explanation (rule_summary)
**文件：** 通过 grammar assistant 生成，无明确限制
- **状态：** 需要检查

## Grammar Notation Tooltip 当前设置

**文件：** `frontend/my-web-ui/src/modules/article/components/notation/GrammarNotationCard.jsx`

### 当前宽度设置
- `maxWidth: '800px'`
- `minWidth: '300px'`
- `width: '100%'`

### 当前高度设置
- `maxHeight: '200px'`
- `minHeight: '80px'`
- 内部滚动容器：`maxHeight: 'calc(200px - 16px - 16px)'` = `168px`

### ArticleViewer 宽度
- ArticleViewer 使用 `flex-1`，占据剩余空间
- 与 ChatView 并排显示，ChatView 默认宽度 320px，最大 600px
- 布局：`flex gap-8` (gap = 32px)
- 实际宽度 = 视口宽度 - ChatView 宽度 - gap(32px) - padding(32px)

## 修复建议

1. **增加 grammar_example_explanation 的 max_tokens**
   - 从 100 增加到 4000（与 vocab_example_explanation 保持一致）

2. **修改 GrammarNotationCard tooltip 宽度**
   - 使用 `calc(100vw - 600px - 32px - 32px)` 或类似计算
   - 确保与 ArticleViewer 宽度一致

3. **增加最大高度并启用滚动**
   - 增加 `maxHeight` 到更合理的值（如 500px 或 600px）
   - 确保内部滚动容器正确工作
