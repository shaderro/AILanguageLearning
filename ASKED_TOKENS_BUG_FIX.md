# Asked Tokens 绿色下划线显示问题修复

## 🐛 问题描述

Asked tokens 数据已从后端成功获取（6个token），但UI未显示绿色下划线。

## 🔍 问题分析

### 控制台日志显示：

```javascript
✅ Loaded asked tokens: ['1:1:3', '1:51:49', '1:3:1', '1:1:1', '1:2:1', '1:14:39']

❌ Token structure: {
  sentence_id: undefined,      // ← 问题所在！
  sentence_token_id: 1,
  sentenceIdx: 0
}
```

### 根本原因

**Token 对象中没有 `sentence_id` 字段！**

原代码错误地尝试从 token 对象读取 `sentence_id`：
```javascript
❌ const isAsked = isTokenAsked(articleId, token.sentence_id, token.sentence_token_id)
```

实际上应该从 `sentenceIdx`（句子索引，从0开始）计算：
```javascript
✅ const tokenSentenceId = sentenceIdx + 1  // 句子ID = 索引 + 1
```

---

## ✅ 修复方案

### 修改文件：`TokenSpan.jsx`

**修改前**：
```javascript
const isAsked = isTextToken && token?.sentence_id != null && token?.sentence_token_id != null 
  ? isTokenAsked(articleId, token.sentence_id, token.sentence_token_id)
  : false
```

**修改后**：
```javascript
// sentence_id 从 sentenceIdx 计算得出 (sentenceIdx + 1)
const tokenSentenceId = sentenceIdx + 1
const tokenSentenceTokenId = token?.sentence_token_id

const isAsked = isTextToken && tokenSentenceTokenId != null
  ? isTokenAsked(articleId, tokenSentenceId, tokenSentenceTokenId)
  : false
```

---

## 🧪 验证

### 预期匹配示例

后端数据：`'1:1:1'` (文章1, 句子1, token 1)

前端匹配：
- sentenceIdx = 0 → tokenSentenceId = 1 ✅
- sentence_token_id = 1 ✅
- 生成 key: `1:1:1` ✅
- 匹配成功 → 显示绿色下划线 ✅

---

## 📋 测试步骤

1. **刷新页面**
2. 控制台应显示：
   ```
   ✅ [useAskedTokens] Loaded asked tokens: 6 tokens
   ✅ [TokenSpan] Found asked token: {token_body: '...', key: '1:1:1'}
   ```
3. **检查UI**：以下token应有绿色下划线
   - 句子1的token 1 和 3
   - 句子2的token 1
   - 句子3的token 1
   - 句子14的token 39
   - 句子51的token 49

---

## 🎨 视觉效果

修复后，已提问的token将显示：

```
普通单词:    word
                  
已提问单词:  word
             ════  ← 绿色下划线 (border-b-2 border-green-500)
```

---

## 📝 关键要点

1. **Token 数据结构**：
   - ✅ `sentence_token_id` - 存在于 token 对象
   - ❌ `sentence_id` - 不存在，需从 `sentenceIdx + 1` 计算

2. **索引转换**：
   - `sentenceIdx` 从 0 开始（前端渲染索引）
   - `sentence_id` 从 1 开始（后端数据库ID）
   - 转换公式：`sentence_id = sentenceIdx + 1`

3. **匹配键格式**：
   - 格式：`{text_id}:{sentence_id}:{sentence_token_id}`
   - 示例：`1:1:3` = 文章1, 句子1, token 3

---

**修复时间**：2025-10-09  
**状态**：✅ 已修复，无Linter错误  
**影响文件**：
- `frontend/my-web-ui/src/modules/article/components/TokenSpan.jsx`
- `frontend/my-web-ui/src/modules/article/hooks/useAskedTokens.js`

