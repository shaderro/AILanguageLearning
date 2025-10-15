# 调试：Token未标记为已提问的问题

## 🐛 问题描述

用户选中token后发送问题并得到回答，但token没有显示绿色下划线（未标记为已提问）。

---

## 🔍 可能的原因

### 原因1: selectionContext.tokens为空或undefined

**检查位置**: ChatView.jsx 第209行

```javascript
if (markAsAsked && currentSelectionContext && currentSelectionContext.tokens && currentSelectionContext.tokens.length > 0) {
  // 如果这个条件不满足，标记代码就不会执行
}
```

**诊断方法**: 在浏览器控制台查看日志

```
应该看到：
🏷️ [ChatView] Marking selected tokens as asked...

如果没看到这行日志 → 说明条件不满足
```

---

### 原因2: token.sentence_token_id为null或undefined

**检查位置**: ChatView.jsx 第214行

```javascript
if (token.sentence_token_id != null) {
  // 如果sentence_token_id为null，这里不会执行
}
```

**诊断方法**: 在控制台查找日志

```
应该看到：
🏷️ [ChatView] Marking token: "Der" (1:5:12)

如果没看到 → 说明sentence_token_id为null
```

---

### 原因3: markAsAsked函数未正确传递

**检查链路**:
```
ArticleChatView.jsx (第19行)
  → const { markAsAsked } = useAskedTokens(articleId)
  
ArticleChatView.jsx (第134行)  
  → <ChatView markAsAsked={markAsAsked} ... />
  
ChatView.jsx (第6行)
  → function ChatView({ markAsAsked = null, ... })
```

**诊断方法**: 检查是否为null

---

### 原因4: API调用失败但没有报错

**检查位置**: hooks/useAskedTokens.js 第50-67行

```javascript
const response = await apiService.markTokenAsked(...)

if (response.success) {
  // 只有success=true才会更新Set
}
```

**诊断方法**: 查看网络请求

---

## 🛠️ 诊断步骤

### 步骤1: 检查控制台日志

打开浏览器开发者工具（F12），然后：

1. 选中一个token
2. 发送问题
3. 查看控制台日志

**应该看到的日志顺序**:
```
📋 [ChatView] 选择上下文 (selectionContext):
  - 句子 ID: 1
  - 文章 ID: 1
  - 选中的 tokens: ["Der"]
  - Token 数量: 1

🏷️ [ChatView] Marking selected tokens as asked...
🏷️ [ChatView] Marking token: "Der" (1:1:1)
🏷️ [Frontend] Marking token as asked: 1:1:1
✅ [AskedTokens] Token marked: 1:1:1
```

**如果缺少某些日志，就能定位问题！**

---

### 步骤2: 检查selectionContext结构

在`ChatView.jsx`第143行后添加调试代码：

```javascript
if (currentSelectionContext) {
  console.log('  - 句子 ID:', currentSelectionContext.sentence?.sentence_id)
  
  // 添加详细的token信息
  console.log('  - Tokens详情:', currentSelectionContext.tokens)  // ← 添加这行
  
  if (currentSelectionContext.tokens && currentSelectionContext.tokens.length > 0) {
    currentSelectionContext.tokens.forEach((t, idx) => {
      console.log(`    Token ${idx}:`, {
        token_body: t.token_body,
        sentence_token_id: t.sentence_token_id,  // ← 检查这个字段
        global_token_id: t.global_token_id
      })
    })
  }
}
```

---

### 步骤3: 检查网络请求

在浏览器开发者工具的Network标签：

1. 发送问题
2. 查找 `asked-tokens` 请求
3. 检查：
   - 请求是否发送成功？
   - 响应是否 `success: true`？
   - 请求体是否包含正确的参数？

**期望看到**:
```
POST /api/user/asked-tokens

Request:
{
  "user_id": "default_user",
  "text_id": 1,
  "sentence_id": 1,
  "sentence_token_id": 1
}

Response:
{
  "success": true,
  "message": "Token marked as asked"
}
```

---

### 步骤4: 检查ArticleViewer的token数据

在`ArticleViewer.jsx`中，检查token是否有`sentence_token_id`字段：

```javascript
// 第93-114行
{(sentence?.tokens || []).map((t, tIdx) => (
  <TokenSpan
    key={`${sIdx}-${tIdx}`}
    token={t}  // ← 检查token对象的结构
    // ...
  />
))}
```

**添加调试**:
```javascript
{(sentence?.tokens || []).map((t, tIdx) => {
  // 添加：打印token结构
  if (tIdx === 0) {  // 只打印第一个token
    console.log('Token结构:', t)
  }
  
  return (
    <TokenSpan
      key={`${sIdx}-${tIdx}`}
      token={t}
      // ...
    />
  )
})}
```

---

## 🔧 可能的修复方案

### 修复1: 如果token.sentence_token_id不存在

**问题**: Token数据没有`sentence_token_id`字段

**检查**: 打印token对象
```javascript
console.log('Token:', token)
// 输出：{token_body: "Der", token_type: "text", ...}
// 缺少：sentence_token_id
```

**修复**: 在生成token时添加该字段，或者使用tokenIdx

```javascript
// 方案A: 使用tokenIdx作为sentence_token_id
const markPromises = currentSelectionContext.tokens.map((token, idx) => {
  const sentenceTokenId = token.sentence_token_id ?? (idx + 1)  // 如果没有，用索引+1
  
  return markAsAsked(textId, sentenceId, sentenceTokenId)
})
```

---

### 修复2: 如果selectionContext不完整

**问题**: `selectionContext`传递时丢失了部分信息

**检查**: ArticleChatView.jsx 第24-34行

```javascript
const handleTokenSelect = async (tokenText, selectedSet, selectedTexts = [], context = null) => {
  setCurrentContext(context)  // ← 检查context是否完整
  
  // 添加调试
  console.log('🎯 Context received:', context)
  if (context && context.tokens) {
    console.log('🎯 Tokens in context:', context.tokens)
  }
}
```

---

### 修复3: 如果ArticleViewer没有正确创建context

**检查**: `hooks/useTokenSelection.js` 或选择逻辑

查找创建`context`对象的代码，确保包含：
```javascript
const context = {
  sentence: {
    text_id: articleId,
    sentence_id: sIdx + 1,
    sentence_body: sentence.sentence_body
  },
  tokens: selectedTokens,  // ← 必须包含完整的token对象
  selectedTexts: [...],
  tokenIndices: [...]
}
```

---

## 🎯 立即诊断代码

创建文件 `frontend/my-web-ui/src/debug-asked-tokens.js`:

```javascript
// 在浏览器控制台粘贴此代码进行诊断

function debugAskedTokens() {
  console.log('='.repeat(60))
  console.log('🔍 Asked Tokens 诊断')
  console.log('='.repeat(60))
  
  // 1. 检查useAskedTokens hook
  console.log('\n1. 检查 useAskedTokens 状态:')
  // 在React DevTools中找到ArticleChatView组件
  // 查看hooks -> askedTokenKeys
  
  // 2. 检查当前选择的context
  console.log('\n2. 检查 selectionContext:')
  // 在React DevTools中找到ChatView组件
  // 查看props -> selectionContext
  
  // 3. 检查token结构
  console.log('\n3. 检查 token 数据结构:')
  // 在ArticleViewer中查看sentence.tokens
  
  // 4. 模拟标记
  console.log('\n4. 测试标记功能:')
  // 手动调用markAsAsked(1, 1, 1)
}

debugAskedTokens()
```

---

## 📝 快速修复方案

### 方案A: 添加详细日志（推荐）

**修改文件**: `ChatView.jsx`

在第209行之前添加：

```javascript
// 在第208行后添加详细日志
console.log('🔍 [DEBUG] 检查标记条件:')
console.log('  - markAsAsked存在?', !!markAsAsked)
console.log('  - currentSelectionContext存在?', !!currentSelectionContext)
console.log('  - tokens存在?', !!currentSelectionContext?.tokens)
console.log('  - tokens长度:', currentSelectionContext?.tokens?.length)
console.log('  - tokens详情:', currentSelectionContext?.tokens)

// 标记选中的tokens为已提问
if (markAsAsked && currentSelectionContext && currentSelectionContext.tokens && currentSelectionContext.tokens.length > 0) {
  // ...原有代码
```

---

### 方案B: 强制使用tokenIdx（临时方案）

如果token没有sentence_token_id，使用索引：

```javascript
// 修改第213-224行
const markPromises = currentSelectionContext.tokens.map((token, tokenIdx) => {
  // 使用tokenIdx作为fallback
  const sentenceTokenId = token.sentence_token_id ?? (tokenIdx + 1)
  const sentenceId = currentSelectionContext.sentence?.sentence_id
  const textId = currentSelectionContext.sentence?.text_id
  
  if (sentenceId && textId && sentenceTokenId != null) {
    console.log(`🏷️ [ChatView] Marking token: "${token.token_body}" (${textId}:${sentenceId}:${sentenceTokenId})`)
    return markAsAsked(textId, sentenceId, sentenceTokenId)
  }
  
  return Promise.resolve(false)
})
```

---

## 🚀 立即诊断步骤

**请执行以下操作并告诉我结果**：

1. **打开浏览器开发者工具（F12）**

2. **打开Console标签**

3. **清空控制台**

4. **选中一个token**

5. **发送一个问题**

6. **在控制台搜索以下关键词，告诉我是否能找到**：

```
搜索1: "选择上下文"
  - 能找到? □ 是 □ 否
  - 如果能找到，Token 数量是多少? ____

搜索2: "Marking selected tokens"
  - 能找到? □ 是 □ 否
  
搜索3: "Marking token:"
  - 能找到? □ 是 □ 否
  - 如果能找到，显示什么内容? ________________

搜索4: "Successfully marked"
  - 能找到? □ 是 □ 否
  - 如果能找到，成功数量是多少? ____

搜索5: "Error marking"
  - 能找到? □ 是 □ 否
  - 如果能找到，错误信息是什么? ________________
```

7. **检查Network标签**
   - 搜索 `asked-tokens`
   - 是否有POST请求？□ 是 □ 否
   - 如果有，响应是什么？

---

## 💡 我的建议

**先不要修改代码**，让我们先诊断问题在哪里。

请按照上面的步骤操作，然后告诉我：
1. 控制台有哪些日志？
2. 哪些日志缺失？
3. Network中是否有asked-tokens的请求？

这样我能精准定位问题并修复！🎯


