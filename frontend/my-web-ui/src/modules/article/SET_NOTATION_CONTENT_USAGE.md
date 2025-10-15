# setNotationContent 方法使用说明

## 📋 方法概述

**方法名**: `setNotationContent`  
**位置**: `hooks/useTokenNotations.js`  
**功能**: 为指定的token设置notation内容

---

## 🎯 方法签名

```javascript
setNotationContent(textId, sentenceId, tokenId, content)
```

### 参数说明

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `textId` | number | 文章ID | `1` |
| `sentenceId` | number | 句子ID | `5` |
| `tokenId` | number | Token ID (sentence_token_id) | `12` |
| `content` | string | Notation内容 | `"这是一个重要的词汇"` |

### 返回值

无返回值（void）

---

## 📍 在哪里可以调用

### 当前可用位置

`setNotationContent`方法已经通过props传递到以下组件：

```javascript
ArticleChatView (顶层)
  ↓ 调用 useTokenNotations()
  ↓ 获取 setNotationContent
  ↓
  ├─→ 传递给 ArticleViewer (props)
  │     ↓
  │     └─→ 传递给 TokenSpan (props)
  │           ↓
  │           └─→ 可以在这里调用 setNotationContent()
  │
  └─→ 传递给 ChatView (可选，如需要)
```

---

## 💻 使用示例

### 示例1: 在TokenSpan中设置notation（基础用法）

**场景**: 用户点击已提问的token时设置内容

```javascript
// TokenSpan.jsx

onClick={(e) => {
  // 原有的点击逻辑
  if (!isDraggingRef.current && selectable) {
    e.preventDefault()
    addSingle(sentenceIdx, token)
  }
  
  // 新增：如果是已提问的token，设置notation
  if (isAsked && setNotationContent) {
    setNotationContent(
      articleId,           // textId
      tokenSentenceId,     // sentenceId
      tokenSentenceTokenId, // tokenId
      `这个词已被提问：${token.token_body}`  // content
    )
  }
}}
```

---

### 示例2: 在ChatView中设置notation（发送问题时）

**场景**: 用户发送问题后，自动为相关token添加notation

```javascript
// ChatView.jsx (在标记token之后)

// 标记token成功后，设置notation内容
if (successCount > 0 && setNotationContent) {
  currentSelectionContext.tokens.forEach((token, idx) => {
    const sentenceTokenId = token.sentence_token_id ?? (idx + 1)
    const sentenceId = currentSelectionContext.sentence?.sentence_id
    const textId = currentSelectionContext.sentence?.text_id ?? articleId
    
    // 设置notation内容
    setNotationContent(
      textId,
      sentenceId,
      sentenceTokenId,
      `问题：${questionText}\n回答：${ai_response.substring(0, 100)}...`
    )
  })
}
```

**传递方法**（如果需要在ChatView中使用）:

```javascript
// ArticleChatView.jsx
<ChatView 
  quotedText={quotedText}
  // ... 其他props
  setNotationContent={setNotationContent}  // ← 添加这个prop
/>
```

---

### 示例3: 从API响应设置notation

**场景**: AI回答后，为token设置解释内容

```javascript
// ChatView.jsx (收到AI响应后)

const response = await apiService.sendChat({ user_question: questionText })

if (response.success && response.data) {
  const { ai_response } = response.data
  
  // 为选中的tokens设置AI的回答作为notation
  if (currentSelectionContext && currentSelectionContext.tokens && setNotationContent) {
    currentSelectionContext.tokens.forEach((token, idx) => {
      const sentenceTokenId = token.sentence_token_id ?? (idx + 1)
      const sentenceId = currentSelectionContext.sentence?.sentence_id
      const textId = currentSelectionContext.sentence?.text_id ?? articleId
      
      setNotationContent(
        textId,
        sentenceId,
        sentenceTokenId,
        ai_response  // AI的回答作为notation
      )
    })
  }
}
```

---

### 示例4: 设置词汇解释作为notation

**场景**: 获取词汇解释后保存到notation

```javascript
// VocabExplanationButton.jsx

const handleClick = async () => {
  const result = await apiService.getVocabExplanation(token.token_body)
  setExplanation(result)
  
  // 设置notation内容
  if (setNotationContent && articleId && sentenceIdx != null) {
    const sentenceId = sentenceIdx + 1
    setNotationContent(
      articleId,
      sentenceId,
      token.sentence_token_id,
      result.definition  // 词汇定义作为notation
    )
  }
}
```

---

## 🎯 当前状态（空方法占位）

### 目前的实现

```javascript
// useTokenNotations.js (已实现)

const setNotationContent = useCallback((textId, sentenceId, tokenId, content) => {
  const key = `${textId}:${sentenceId}:${tokenId}`
  
  console.log(`📝 [TokenNotations] Setting notation for ${key}:`, content)
  
  // 更新Map
  setNotations(prev => {
    const newMap = new Map(prev)
    newMap.set(key, content)
    return newMap
  })
}, [])
```

**状态**: ✅ 完全实现（不是空方法）

---

## 🔍 数据结构

### Notations Map

```javascript
// 内部存储结构
notations = new Map([
  ["1:5:12", "这是一个重要的词汇"],
  ["1:5:13", "这个词表示..."],
  ["1:7:3", "语法标记词"]
])

// Key格式: "textId:sentenceId:tokenId"
// Value: notation内容（字符串）
```

### 获取内容

```javascript
// 获取token的notation
const content = getNotationContent(1, 5, 12)
// 返回: "这是一个重要的词汇" 或 null
```

---

## 🧪 测试验证

### 在浏览器控制台测试

```javascript
// 1. 在React DevTools中找到ArticleChatView组件
// 2. 在hooks中找到useTokenNotations
// 3. 展开查看notations Map

// 或者在代码中添加测试
console.log('Current notations:', Array.from(notations.entries()))
```

### 手动设置测试

在`ArticleChatView.jsx`中添加测试代码：

```javascript
// 在useEffect中测试
useEffect(() => {
  // 测试：为token 1:1:1 设置notation
  if (setNotationContent) {
    setTimeout(() => {
      setNotationContent(1, 1, 1, "测试notation内容")
      console.log('✅ 测试notation已设置')
    }, 2000)  // 2秒后自动设置
  }
}, [setNotationContent])
```

然后hover token 1:1:1，应该看到"测试notation内容"

---

## 📊 完整的数据流

```
用户操作 / API响应
    ↓
调用 setNotationContent(textId, sentenceId, tokenId, content)
    ↓
更新 notations Map
    ↓ key = "textId:sentenceId:tokenId"
    ↓ value = content
    ↓
React状态更新
    ↓
TokenSpan重新渲染
    ↓
调用 getNotationContent(textId, sentenceId, tokenId)
    ↓
从Map中获取内容
    ↓
传递给 TokenNotation
    ↓
Hover时显示内容
```

---

## 🎨 未来可能的应用

### 应用1: 保存AI回答摘要

```javascript
// AI回答后
setNotationContent(textId, sentenceId, tokenId, ai_response.substring(0, 200))
// hover时显示AI回答的前200字符
```

### 应用2: 保存词汇定义

```javascript
// 获取词汇解释后
setNotationContent(textId, sentenceId, tokenId, vocabDefinition)
// hover时显示词汇定义
```

### 应用3: 保存用户笔记

```javascript
// 用户添加笔记后
setNotationContent(textId, sentenceId, tokenId, userNote)
// hover时显示用户的笔记
```

### 应用4: 保存语法解释

```javascript
// AI解释语法后
setNotationContent(textId, sentenceId, tokenId, grammarExplanation)
// hover时显示语法解释
```

---

## ✅ 完成清单

- [x] 创建useTokenNotations hook
- [x] 实现setNotationContent方法（完整实现，非空方法）
- [x] 实现getNotationContent方法
- [x] 集成到ArticleChatView
- [x] 传递到ArticleViewer
- [x] 传递到TokenSpan
- [x] TokenSpan使用getNotationContent获取内容
- [x] TokenNotation显示动态内容

---

## 🎯 当前可用的方法

```javascript
// 在ArticleChatView中可用
const { 
  getNotationContent,     // 获取notation内容
  setNotationContent,     // ← 设置notation内容（你需要的方法）
  clearNotationContent,   // 清除单个notation
  clearAllNotations       // 清除所有notations
} = useTokenNotations()
```

---

## 💡 使用建议

### 何时调用setNotationContent？

**推荐时机**:
1. ✅ AI回答问题后 - 保存回答摘要
2. ✅ 获取词汇解释后 - 保存词汇定义
3. ✅ 用户添加笔记后 - 保存用户笔记
4. ✅ 标记token为已提问时 - 保存提问信息

**调用位置**:
- ChatView.jsx（AI回答后）
- VocabExplanationButton.jsx（词汇解释后）
- 自定义的笔记功能中

---

## 🚀 下一步

**测试notation功能**:

1. 刷新页面
2. 在浏览器控制台输入：
   ```javascript
   // 手动设置一个notation（用于测试）
   // 注意：需要在React组件中调用，控制台无法直接访问
   ```

3. 或者在ChatView中添加自动设置（作为测试）：
   ```javascript
   // 发送问题后，自动设置notation
   setNotationContent(textId, sentenceId, tokenId, "AI回答: " + ai_response)
   ```

**状态**: ✅ 方法已完整实现  
**测试**: 准备就绪  
**可用性**: 立即可用

---

**需要我在某个特定位置自动调用这个方法吗？比如在AI回答后自动设置？** 🎯


