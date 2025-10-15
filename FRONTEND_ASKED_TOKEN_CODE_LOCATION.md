# 前端标记Token为Asked Token的代码位置

## 📍 核心文件位置

### 1. 自定义Hook（核心逻辑）

**文件**: `frontend/my-web-ui/src/modules/article/hooks/useAskedTokens.js`

**职责**: 
- 管理asked tokens状态
- 从后端获取已提问的tokens
- 提供标记token的函数

**关键代码**:
```javascript
// 第50-67行：标记token为已提问的核心函数
const markAsAsked = async (textId, sentenceId, sentenceTokenId) => {
  try {
    const response = await apiService.markTokenAsked(userId, textId, sentenceId, sentenceTokenId)
    
    if (response.success) {
      const key = `${textId}:${sentenceId}:${sentenceTokenId}`
      setAskedTokenKeys(prev => new Set([...prev, key]))  // ← 更新本地状态
      console.log('✅ [AskedTokens] Token marked:', key)
      return true
    }
  } catch (err) {
    console.error('❌ [AskedTokens] Error:', err)
    return false
  }
}
```

**导出**:
```javascript
return {
  askedTokenKeys,      // Set类型，包含所有已提问的token keys
  isTokenAsked,        // 检查函数：(textId, sentenceId, tokenId) => boolean
  markAsAsked          // 标记函数：(textId, sentenceId, tokenId) => Promise<boolean>
}
```

---

### 2. API服务（网络请求）

**文件**: `frontend/my-web-ui/src/services/api.js`

**职责**: 封装HTTP请求

**关键代码**:
```javascript
// 第94-102行：标记token的API调用
markTokenAsked: (userId = 'default_user', textId, sentenceId, sentenceTokenId) => {
  console.log(`🏷️ [Frontend] Marking token as asked: ${textId}:${sentenceId}:${sentenceTokenId}`);
  return api.post('/api/user/asked-tokens', {
    user_id: userId,
    text_id: textId,
    sentence_id: sentenceId,
    sentence_token_id: sentenceTokenId
  });
}
```

**API端点**: `POST /api/user/asked-tokens`

---

### 3. 词汇解释按钮组件（触发点1）

**文件**: `frontend/my-web-ui/src/modules/article/components/VocabExplanationButton.jsx`

**职责**: 用户点击"vocab explanation"按钮时触发

**关键代码**:
```javascript
// 第26-41行：获取词汇解释后标记token
if (markAsAsked && articleId && sentenceIdx != null && token.sentence_token_id != null) {
  console.log('🏷️ [VocabExplanationButton] Marking token as asked...')
  const sentenceId = sentenceIdx + 1  // sentenceId从sentenceIdx计算
  
  try {
    const success = await markAsAsked(articleId, sentenceId, token.sentence_token_id)
    if (success) {
      console.log('✅ [VocabExplanationButton] Token marked as asked successfully')
    }
  } catch (error) {
    console.error('❌ [VocabExplanationButton] Error marking token as asked:', error)
  }
}
```

**触发时机**: 用户点击某个token的"vocab explanation"按钮

---

### 4. 聊天视图组件（触发点2）

**文件**: `frontend/my-web-ui/src/modules/article/components/ChatView.jsx`

**职责**: 用户发送问题时，标记选中的tokens

**关键代码**:
```javascript
// 第209-240行：发送问题后标记所有选中的tokens
if (markAsAsked && currentSelectionContext && currentSelectionContext.tokens && currentSelectionContext.tokens.length > 0) {
  console.log('🏷️ [ChatView] Marking selected tokens as asked...')
  
  // 标记所有选中的tokens
  const markPromises = currentSelectionContext.tokens.map(token => {
    if (token.sentence_token_id != null) {
      const sentenceId = currentSelectionContext.sentence?.sentence_id
      const textId = currentSelectionContext.sentence?.text_id
      
      if (sentenceId && textId) {
        console.log(`🏷️ [ChatView] Marking token: "${token.token_body}" (${textId}:${sentenceId}:${token.sentence_token_id})`)
        return markAsAsked(textId, sentenceId, token.sentence_token_id)
      }
    }
    return Promise.resolve(false)
  })
  
  const results = await Promise.all(markPromises)
  const successCount = results.filter(r => r).length
  console.log(`✅ [ChatView] Successfully marked ${successCount}/${markPromises.length} tokens as asked`)
}
```

**触发时机**: 
- 用户选中token后发送问题
- 用户点击建议问题（也会标记）

---

### 5. 文章查看器（组装组件）

**文件**: `frontend/my-web-ui/src/modules/article/components/ArticleViewer.jsx`

**职责**: 组装所有组件，传递props

**关键代码**:
```javascript
// 第16行：使用useAskedTokens hook
const { askedTokenKeys, isTokenAsked, markAsAsked } = useAskedTokens(articleId)

// 第113行：传递给TokenSpan组件
<TokenSpan
  // ... 其他props
  isTokenAsked={isTokenAsked}
  markAsAsked={markAsAsked}
/>
```

---

## 🔄 完整的调用流程

### 流程1: 用户点击"vocab explanation"按钮

```
用户点击Token的"vocab explanation"按钮
    ↓
VocabExplanationButton.jsx (第12-48行)
    ↓ handleClick()
    ↓
1. 获取词汇解释
    ↓ apiService.getVocabExplanation(token.token_body)
    ↓
2. 显示解释
    ↓ setExplanation(result)
    ↓
3. 标记token为已提问 (第26-41行)
    ↓ markAsAsked(articleId, sentenceId, token.sentence_token_id)
    ↓
useAskedTokens.js (第50-67行)
    ↓ markAsAsked()
    ↓
api.js (第94-102行)
    ↓ apiService.markTokenAsked()
    ↓
POST /api/user/asked-tokens
    ↓ 后端API
    ↓
后端保存到JSON文件/数据库
    ↓
前端更新本地状态
    ↓ setAskedTokenKeys(prev => new Set([...prev, key]))
    ↓
Token样式更新（显示为已提问状态）
```

---

### 流程2: 用户选中tokens后发送问题

```
用户选中一个或多个tokens
    ↓
用户在ChatView中输入问题并发送
    ↓
ChatView.jsx (第141-333行)
    ↓ handleSendMessage()
    ↓
1. 发送问题到AI
    ↓ apiService.sendChat()
    ↓
2. 收到AI响应
    ↓
3. 标记所有选中的tokens (第209-240行)
    ↓ 遍历 currentSelectionContext.tokens
    ↓ 为每个token调用 markAsAsked()
    ↓
useAskedTokens.js
    ↓ markAsAsked()
    ↓
api.js
    ↓ POST /api/user/asked-tokens (并发调用)
    ↓
后端保存每个token
    ↓
前端更新本地状态（添加所有keys）
    ↓
所有选中的tokens显示为已提问状态
```

---

## 📋 代码位置速查表

| 功能 | 文件路径 | 行号 | 说明 |
|------|---------|------|------|
| **核心Hook** | `hooks/useAskedTokens.js` | 全文 | 状态管理和API调用 |
| - 初始化加载 | `hooks/useAskedTokens.js` | 13-41 | useEffect获取已提问tokens |
| - 检查函数 | `hooks/useAskedTokens.js` | 44-47 | `isTokenAsked()` |
| - 标记函数 | `hooks/useAskedTokens.js` | 50-67 | `markAsAsked()` ⭐ 核心 |
| **API服务** | `services/api.js` | 89-102 | HTTP请求封装 |
| - 获取API | `services/api.js` | 89-92 | `getAskedTokens()` |
| - 标记API | `services/api.js` | 94-102 | `markTokenAsked()` ⭐ |
| **触发点1** | `components/VocabExplanationButton.jsx` | 26-41 | 点击词汇解释按钮 |
| **触发点2** | `components/ChatView.jsx` | 209-240 | 发送问题后 |
| **触发点3** | `components/ChatView.jsx` | 432-461 | 点击建议问题后 |
| **组件集成** | `components/ArticleViewer.jsx` | 16, 113 | 使用hook并传递 |
| **Token显示** | `components/TokenSpan.jsx` | 26, 100 | 接收markAsAsked prop |

---

## 🎯 关键数据结构

### Asked Token Key格式

```javascript
// Key格式：`${text_id}:${sentence_id}:${sentence_token_id}`
const key = "1:5:12"  // 文章1，句子5，token 12

// 存储在Set中
askedTokenKeys = new Set([
  "1:5:12",
  "1:5:13",
  "1:7:3"
])
```

### 检查Token是否已提问

```javascript
// 在 useAskedTokens.js (第44-47行)
const isTokenAsked = (textId, sentenceId, sentenceTokenId) => {
  const key = `${textId}:${sentenceId}:${sentenceTokenId}`
  return askedTokenKeys.has(key)  // Set查找，O(1)复杂度
}
```

---

## 🔍 详细代码解析

### 核心函数：markAsAsked

**位置**: `hooks/useAskedTokens.js` 第50-67行

```javascript
const markAsAsked = async (textId, sentenceId, sentenceTokenId) => {
  try {
    // 1. 调用后端API标记token
    const response = await apiService.markTokenAsked(
      userId,              // 用户ID（默认'default_user'）
      textId,              // 文章ID
      sentenceId,          // 句子ID
      sentenceTokenId      // 句子内token的ID
    )
    
    if (response.success) {
      // 2. 生成token key
      const key = `${textId}:${sentenceId}:${sentenceTokenId}`
      
      // 3. 更新本地状态（添加到Set中）
      setAskedTokenKeys(prev => new Set([...prev, key]))
      
      console.log('✅ [AskedTokens] Token marked:', key)
      return true  // 返回成功
    } else {
      console.error('❌ [AskedTokens] Failed to mark token:', response.error)
      return false
    }
  } catch (err) {
    console.error('❌ [AskedTokens] Error:', err)
    return false
  }
}
```

**调用签名**: `markAsAsked(textId, sentenceId, sentenceTokenId) => Promise<boolean>`

---

### API调用：markTokenAsked

**位置**: `services/api.js` 第94-102行

```javascript
markTokenAsked: (userId = 'default_user', textId, sentenceId, sentenceTokenId) => {
  console.log(`🏷️ [Frontend] Marking token as asked: ${textId}:${sentenceId}:${sentenceTokenId}`);
  
  // 发送POST请求到后端
  return api.post('/api/user/asked-tokens', {
    user_id: userId,
    text_id: textId,
    sentence_id: sentenceId,
    sentence_token_id: sentenceTokenId
  });
}
```

**后端端点**: `POST /api/user/asked-tokens`

**请求体**:
```json
{
  "user_id": "default_user",
  "text_id": 1,
  "sentence_id": 5,
  "sentence_token_id": 12
}
```

---

## 🎬 使用场景详解

### 场景1: 点击词汇解释按钮

**组件**: `VocabExplanationButton.jsx`

**流程**:
```javascript
// 1. 用户点击token上的"vocab explanation"按钮
<button onClick={handleClick}>vocab explanation</button>

// 2. 获取解释
const result = await apiService.getVocabExplanation(token.token_body)

// 3. 显示解释
setExplanation(result)

// 4. 自动标记该token为已提问（第26-41行）
if (markAsAsked && articleId && sentenceIdx != null && token.sentence_token_id != null) {
  const sentenceId = sentenceIdx + 1  // ← 注意：sentenceIdx需要+1
  const success = await markAsAsked(articleId, sentenceId, token.sentence_token_id)
}
```

**何时调用**: ✅ 用户点击词汇解释按钮后**自动**标记

---

### 场景2: 选中tokens后发送问题

**组件**: `ChatView.jsx`

**流程**:
```javascript
// 1. 用户选中了1个或多个tokens
// selectionContext包含：
{
  sentence: { text_id: 1, sentence_id: 5, ... },
  tokens: [
    { token_body: "Der", sentence_token_id: 1, ... },
    { token_body: "Hund", sentence_token_id: 2, ... }
  ],
  selectedTexts: ["Der", "Hund"]
}

// 2. 用户输入问题并发送
handleSendMessage()

// 3. AI响应后，标记所有选中的tokens（第209-240行）
const markPromises = currentSelectionContext.tokens.map(token => {
  if (token.sentence_token_id != null) {
    const sentenceId = currentSelectionContext.sentence?.sentence_id
    const textId = currentSelectionContext.sentence?.text_id
    
    return markAsAsked(textId, sentenceId, token.sentence_token_id)
  }
  return Promise.resolve(false)
})

// 4. 并发标记所有tokens
const results = await Promise.all(markPromises)
const successCount = results.filter(r => r).length
console.log(`✅ Successfully marked ${successCount} tokens`)
```

**何时调用**: ✅ 用户发送问题后**自动批量**标记所有选中的tokens

---

### 场景3: 点击建议问题

**组件**: `ChatView.jsx`

**流程**:
```javascript
// 1. 用户点击建议问题（如"这个词是什么意思？"）
handleSuggestedQuestionSelect(question)

// 2. 自动发送问题
const response = await apiService.sendChat({ user_question: question })

// 3. 标记tokens（第432-461行，逻辑与场景2相同）
if (markAsAsked && currentSelectionContext && currentSelectionContext.tokens) {
  // 批量标记所有选中的tokens
  const markPromises = currentSelectionContext.tokens.map(token => {
    return markAsAsked(textId, sentenceId, token.sentence_token_id)
  })
  
  await Promise.all(markPromises)
}
```

**何时调用**: ✅ 用户点击建议问题后**自动批量**标记

---

## 🎨 UI展示（Token样式变化）

### TokenSpan组件

**文件**: `frontend/my-web-ui/src/modules/article/components/TokenSpan.jsx`

**判断逻辑**:
```javascript
// 检查token是否已提问
const isAsked = isTokenAsked && isTokenAsked(
  articleId,           // 文章ID
  sentenceIdx + 1,     // 句子ID
  token.sentence_token_id
)

// 根据状态应用样式
className={`
  ${isAsked ? 'bg-green-100 border-green-300' : 'hover:bg-gray-100'}
  // ... 其他样式
`}
```

**样式区别**:
- 未提问：`hover:bg-gray-100`（鼠标悬停灰色）
- 已提问：`bg-green-100 border-green-300`（绿色背景和边框）

---

## 📊 数据流图

```
前端组件树：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ArticleChatView (根组件)
  │
  ├── useAskedTokens(articleId)  ← Hook初始化
  │     │
  │     ├── 加载：GET /api/user/asked-tokens
  │     ├── 状态：askedTokenKeys (Set)
  │     └── 函数：markAsAsked(), isTokenAsked()
  │
  ├── ArticleViewer
  │     │
  │     │── useAskedTokens() ← 再次调用（同一个hook）
  │     │
  │     └── TokenSpan (每个token)
  │           │
  │           ├── isTokenAsked(textId, sentenceId, tokenId) ← 检查
  │           │     └── 返回 boolean
  │           │
  │           └── VocabExplanationButton
  │                 │
  │                 └── onClick → markAsAsked() ← 标记
  │
  └── ChatView
        │
        └── onSendMessage → markAsAsked() ← 批量标记


标记Token流程：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

组件调用 markAsAsked(textId, sentenceId, tokenId)
    ↓
useAskedTokens.js
    ↓
apiService.markTokenAsked(userId, textId, sentenceId, tokenId)
    ↓
POST /api/user/asked-tokens
    ↓
后端处理（server.py 第96-148行）
    ↓
保存到JSON文件（或数据库）
    ↓
返回 {success: true}
    ↓
前端更新Set
    ↓ setAskedTokenKeys(prev => new Set([...prev, key]))
    ↓
React重新渲染
    ↓
TokenSpan检查 isTokenAsked()
    ↓
应用绿色样式（已提问）
```

---

## 🔧 如何修改/扩展

### 修改1: 改变样式

**位置**: `components/TokenSpan.jsx`

```javascript
// 当前：绿色背景
className={`${isAsked ? 'bg-green-100 border-green-300' : '...'}`}

// 改为：蓝色背景
className={`${isAsked ? 'bg-blue-100 border-blue-300' : '...'}`}
```

---

### 修改2: 添加标记确认

**位置**: `components/VocabExplanationButton.jsx` 第32行之后

```javascript
const success = await markAsAsked(articleId, sentenceId, token.sentence_token_id)
if (success) {
  // 添加：显示成功提示
  showToast('✅ Token已标记为已提问')
}
```

---

### 修改3: 改变后端API地址

**位置**: `services/api.js` 第96行

```javascript
// 当前：
return api.post('/api/user/asked-tokens', { ... })

// 改为新的数据库API：
return api.post('/api/v2/asked-tokens', { ... })
```

---

### 修改4: 添加取消标记功能

**位置**: `hooks/useAskedTokens.js` 添加新函数

```javascript
// 在markAsAsked后面添加
const unmarkAsAsked = async (textId, sentenceId, sentenceTokenId) => {
  const key = `${textId}:${sentenceId}:${sentenceTokenId}`
  
  try {
    const response = await apiService.unmarkTokenAsked(userId, key)
    
    if (response.success) {
      // 从Set中移除
      setAskedTokenKeys(prev => {
        const newSet = new Set(prev)
        newSet.delete(key)
        return newSet
      })
      return true
    }
  } catch (err) {
    console.error('Error:', err)
    return false
  }
}

// 导出
return {
  // ...
  markAsAsked,
  unmarkAsAsked  // 新增
}
```

---

## 🐛 调试技巧

### 查看已提问的tokens

```javascript
// 在浏览器控制台
console.log('Asked tokens:', Array.from(askedTokenKeys))
// 输出：["1:5:12", "1:5:13", "1:7:3"]
```

### 跟踪标记过程

所有关键步骤都有console.log，查看控制台：

```
🏷️ [VocabExplanationButton] Marking token as asked...
🏷️ [VocabExplanationButton] Marking token: "Der" (1:5:12)
🏷️ [Frontend] Marking token as asked: 1:5:12
✅ [AskedTokens] Token marked: 1:5:12
```

---

## 📝 总结

### 核心代码位置

**最重要的3个文件**:
1. ⭐ `hooks/useAskedTokens.js` - 状态管理和标记逻辑
2. ⭐ `services/api.js` - API调用
3. ⭐ `components/VocabExplanationButton.jsx` - 主要触发点

### 标记时机

1. ✅ 用户点击"vocab explanation"按钮（自动）
2. ✅ 用户选中tokens后发送问题（自动批量）
3. ✅ 用户点击建议问题（自动批量）

### 数据存储

- **前端**: Set数据结构（内存，页面刷新后重新加载）
- **后端**: JSON文件或数据库（持久化）

### Key格式

```
格式：${text_id}:${sentence_id}:${sentence_token_id}
示例：1:5:12
```

---

**需要修改某个部分吗？我可以帮你详细讲解或修改！**

