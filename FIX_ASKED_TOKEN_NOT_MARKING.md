# 修复：选中Token后发送问题未标记的问题

## 🐛 问题现象

用户选中token后发送问题并得到AI回答，但token没有显示绿色下划线（未标记为已提问）。

---

## 🔍 问题诊断

### 可能原因分析

根据代码分析，有4个可能的原因：

| 可能原因 | 检查方法 | 代码位置 |
|---------|---------|---------|
| ❶ selectionContext为空 | 检查console.log | ChatView.jsx:209 |
| ❷ tokens数组为空 | 检查console.log | ChatView.jsx:209 |
| ❸ sentence_token_id缺失 | 检查token对象 | ChatView.jsx:214 |
| ❹ markAsAsked未传递 | 检查props | ArticleChatView.jsx:134 |

---

## 🎯 立即诊断方法

### 方法1: 添加调试日志（临时）

在 `ChatView.jsx` 第208行后添加：

```javascript
// 第208行后添加
console.log('🔍 ===== 标记Token诊断 =====')
console.log('markAsAsked存在?', !!markAsAsked)
console.log('currentSelectionContext存在?', !!currentSelectionContext)
console.log('currentSelectionContext:', currentSelectionContext)
console.log('tokens数组:', currentSelectionContext?.tokens)
console.log('tokens长度:', currentSelectionContext?.tokens?.length)

if (currentSelectionContext?.tokens) {
  currentSelectionContext.tokens.forEach((token, idx) => {
    console.log(`Token ${idx}:`, {
      body: token.token_body,
      sentence_token_id: token.sentence_token_id  // ← 关键！检查是否存在
    })
  })
}
console.log('===========================')

// 原有的标记代码
if (markAsAsked && currentSelectionContext && currentSelectionContext.tokens && currentSelectionContext.tokens.length > 0) {
  // ...
}
```

然后：
1. 刷新页面
2. 选中一个token
3. 发送问题
4. 查看控制台输出

---

### 方法2: 检查数据API返回

检查文章API返回的sentence数据是否包含text_id和sentence_id：

打开Network标签，查找文章请求：
```
GET /api/article/{articleId}

响应应该包含：
{
  "data": {
    "sentences": [
      {
        "text_id": 1,          // ← 必须有
        "sentence_id": 1,      // ← 必须有
        "sentence_body": "...",
        "tokens": [
          {
            "token_body": "Der",
            "sentence_token_id": 1,  // ← 关键！必须有
            // ...
          }
        ]
      }
    ]
  }
}
```

---

## 🔧 可能的修复方案

### 修复方案A: 如果sentence_token_id缺失

**问题**: Token对象没有`sentence_token_id`字段

**修复**: 在`ChatView.jsx`中使用fallback

```javascript
// 修改 ChatView.jsx 第213-224行
const markPromises = currentSelectionContext.tokens.map((token, tokenIdx) => {
  // 使用tokenIdx作为fallback
  const sentenceTokenId = token.sentence_token_id ?? (tokenIdx + 1)  // ← 添加fallback
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

### 修复方案B: 如果sentence.text_id缺失

**问题**: Sentence对象没有`text_id`字段

**修复**: 使用articleId作为text_id

```javascript
// 修改 ChatView.jsx 第215-220行
const sentenceId = currentSelectionContext.sentence?.sentence_id
const textId = currentSelectionContext.sentence?.text_id ?? articleId  // ← 添加fallback

if (sentenceId && textId) {
  console.log(`🏷️ [ChatView] Marking token: "${token.token_body}" (${textId}:${sentenceId}:${token.sentence_token_id})`)
  return markAsAsked(textId, sentenceId, token.sentence_token_id)
}
```

---

### 修复方案C: 如果整个条件不满足（综合修复）

**完整的修复代码**（替换ChatView.jsx第209-240行）:

```javascript
// 标记选中的tokens为已提问（增强版，包含详细日志和fallback）
console.log('🔍 [DEBUG] 检查标记条件...')
console.log('  markAsAsked:', !!markAsAsked)
console.log('  selectionContext:', !!currentSelectionContext)
console.log('  tokens:', currentSelectionContext?.tokens)
console.log('  articleId:', articleId)

if (markAsAsked && currentSelectionContext && currentSelectionContext.tokens && currentSelectionContext.tokens.length > 0) {
  console.log('✅ [ChatView] 进入标记逻辑')
  console.log('🏷️ [ChatView] Marking selected tokens as asked...')
  
  // 标记所有选中的tokens为已提问
  const markPromises = currentSelectionContext.tokens.map((token, tokenIdx) => {
    // 使用fallback确保所有必需字段都存在
    const sentenceTokenId = token.sentence_token_id ?? (tokenIdx + 1)
    const sentenceId = currentSelectionContext.sentence?.sentence_id
    const textId = currentSelectionContext.sentence?.text_id ?? articleId
    
    console.log(`🏷️ [ChatView] 准备标记 token ${tokenIdx}:`, {
      token_body: token.token_body,
      textId,
      sentenceId,
      sentenceTokenId
    })
    
    if (sentenceId && textId && sentenceTokenId != null) {
      console.log(`🏷️ [ChatView] 执行标记: "${token.token_body}" (${textId}:${sentenceId}:${sentenceTokenId})`)
      return markAsAsked(textId, sentenceId, sentenceTokenId)
    } else {
      console.error(`❌ [ChatView] 缺少必需字段:`, {
        sentenceId: !!sentenceId,
        textId: !!textId,
        sentenceTokenId: !!sentenceTokenId
      })
      return Promise.resolve(false)
    }
  })
  
  try {
    const results = await Promise.all(markPromises)
    const successCount = results.filter(r => r).length
    console.log(`✅ [ChatView] Successfully marked ${successCount}/${markPromises.length} tokens as asked`)
    
    // 如果标记成功，等待一小段时间让状态更新
    if (successCount > 0) {
      setTimeout(() => {
        console.log('🔄 [ChatView] Token states should be updated now')
      }, 100)
    } else {
      console.warn('⚠️ [ChatView] 没有token被成功标记')
    }
  } catch (error) {
    console.error('❌ [ChatView] Error marking tokens as asked:', error)
  }
} else {
  console.warn('⚠️ [ChatView] 标记条件不满足:')
  console.log('  - markAsAsked存在?', !!markAsAsked)
  console.log('  - selectionContext存在?', !!currentSelectionContext)
  console.log('  - tokens存在且非空?', !!(currentSelectionContext?.tokens && currentSelectionContext.tokens.length > 0))
}
```

---

## 🚀 推荐的修复步骤

### 步骤1: 先诊断（不修改代码）

1. 打开浏览器控制台（F12）
2. 选中一个token
3. 观察控制台输出：

**查找这些日志**:
```
✅ 如果看到：
   🏷️ [ChatView] Marking selected tokens as asked...
   → 说明进入了标记逻辑

❌ 如果没看到：
   → selectionContext有问题，跳到步骤2
```

### 步骤2: 应用修复（如果诊断有问题）

**替换** `frontend/my-web-ui/src/modules/article/components/ChatView.jsx` 第209-240行

使用上面"修复方案C"中的代码（包含详细日志和fallback）

### 步骤3: 验证修复

1. 刷新页面
2. 选中一个token
3. 发送问题
4. 检查：
   - 控制台是否有 `✅ Successfully marked` 日志？
   - Token是否变绿？
   - Network是否有 `POST /api/user/asked-tokens` 请求？

---

## 📋 完整的诊断检查清单

**请按顺序检查并勾选**：

### ✅ 前端检查

- [ ] 打开浏览器控制台（F12）
- [ ] 选中一个token，看到token变色/高亮
- [ ] 观察控制台，找到 `选择上下文 (selectionContext)`
- [ ] 检查 `Token 数量` 是否 > 0
- [ ] 检查 `句子 ID` 是否有值（不是undefined）
- [ ] 检查 `文章 ID` 是否有值（不是undefined）

### ✅ 发送问题检查

- [ ] 输入问题并发送
- [ ] 看到AI响应
- [ ] 在控制台搜索 `Marking selected tokens`
  - [ ] 如果找到 → 进入标记逻辑 ✅
  - [ ] 如果没找到 → 条件不满足 ❌

### ✅ 标记执行检查

- [ ] 搜索 `Marking token:` 
  - [ ] 如果找到，记录显示的参数：`(textId:sentenceId:tokenId)`
  - [ ] 如果没找到 → token.sentence_token_id为null ❌

### ✅ API调用检查  

- [ ] 打开Network标签
- [ ] 搜索 `asked-tokens`
- [ ] 查看POST请求：
  - [ ] 请求发送了？
  - [ ] 响应是 `success: true`？
  - [ ] 响应状态码是200？

### ✅ 状态更新检查

- [ ] 搜索 `Successfully marked`
  - [ ] 成功数量 > 0？
  - [ ] Token的key是什么？

### ✅ UI更新检查

- [ ] Token是否变绿？
  - [ ] 如果没变绿，可能是渲染问题

---

## 🎯 快速诊断命令

**在浏览器控制台粘贴运行**：

```javascript
// 诊断Asked Tokens功能
(function diagnose() {
  console.log('='.repeat(60))
  console.log('🔍 Asked Tokens 诊断工具')
  console.log('='.repeat(60))
  
  // 步骤1: 检查React组件状态
  console.log('\n步骤1: 请在React DevTools中检查:')
  console.log('  - 找到ArticleChatView组件')
  console.log('  - 查看hooks -> useAskedTokens -> askedTokenKeys')
  console.log('  - 当前有多少个asked tokens?')
  
  // 步骤2: 检查selectionContext
  console.log('\n步骤2: 请在React DevTools中检查:')
  console.log('  - 找到ChatView组件')
  console.log('  - 查看props -> selectionContext')
  console.log('  - tokens数组是否为空?')
  console.log('  - token对象是否有sentence_token_id字段?')
  
  // 步骤3: 检查markAsAsked函数
  console.log('\n步骤3: 请在React DevTools中检查:')
  console.log('  - ChatView组件的props')
  console.log('  - markAsAsked是否存在?')
  console.log('  - markAsAsked是否为null?')
  
  console.log('\n请截图并分享结果！')
  console.log('='.repeat(60))
})()
```

---

## 🔧 最可能的修复方案

基于代码分析，我认为**最可能的问题**是：

### 问题：sentence.text_id缺失

**原因**: 
- `useTokenSelection.js`第49-52行创建context时，从`sentence.text_id`读取
- 但API返回的sentence可能没有`text_id`字段！

**证据**:
```javascript
// useTokenSelection.js 第49-52行
sentence: {
  text_id: sentence.text_id,        // ← 如果原始数据没有这个字段？
  sentence_id: sentence.sentence_id, // ← 如果原始数据没有这个字段？
  sentence_body: sentence.sentence_body
}
```

**检查**: 查看API返回的sentence数据结构

---

## 💡 推荐修复（两处修改）

### 修复1: 在useTokenSelection.js中添加articleId

**文件**: `frontend/my-web-ui/src/modules/article/hooks/useTokenSelection.js`

**修改**: 第7行和第49-52行

```javascript
// 第7行：添加articleId参数
export function useTokenSelection({ sentences, onTokenSelect, articleId }) {  // ← 添加articleId
  // ...

  // 第49-52行：使用articleId作为fallback
  const buildSelectionContext = (sIdx, idSet) => {
    if (sIdx == null || !sentences[sIdx]) return null
    
    const sentence = sentences[sIdx]
    const tokens = sentence.tokens || []
    const selectedTokens = []
    const selectedTexts = []
    const tokenIndices = []
    
    for (let i = 0; i < tokens.length; i++) {
      const tk = tokens[i]
      if (tk && typeof tk === 'object') {
        const id = getTokenId(tk)
        if (id && idSet.has(id)) {
          selectedTokens.push(tk)
          selectedTexts.push(tk.token_body ?? '')
          tokenIndices.push(tk.sentence_token_id ?? i)
        }
      }
    }
    
    return {
      sentence: {
        text_id: sentence.text_id ?? articleId,  // ← 添加fallback
        sentence_id: sentence.sentence_id ?? (sIdx + 1),  // ← 添加fallback
        sentence_body: sentence.sentence_body
      },
      tokens: selectedTokens,
      selectedTexts,
      tokenIndices
    }
  }
  // ...
}
```

---

### 修复2: 在ArticleViewer.jsx中传递articleId

**文件**: `frontend/my-web-ui/src/modules/article/components/ArticleViewer.jsx`

**修改**: 第40行

```javascript
// 第40行：添加articleId参数
const {
  selectedTokenIds,
  activeSentenceIndex,
  activeSentenceRef,
  clearSelection,
  addSingle,
  emitSelection
} = useTokenSelection({ sentences, onTokenSelect, articleId })  // ← 添加articleId
```

---

### 修复3: 在ChatView.jsx中添加fallback（保险）

**文件**: `frontend/my-web-ui/src/modules/article/components/ChatView.jsx`

**修改**: 第213-220行

```javascript
// 标记所有选中的tokens为已提问
const markPromises = currentSelectionContext.tokens.map((token, tokenIdx) => {
  // 使用fallback确保字段存在
  const sentenceTokenId = token.sentence_token_id ?? (tokenIdx + 1)
  const sentenceId = currentSelectionContext.sentence?.sentence_id
  const textId = currentSelectionContext.sentence?.text_id ?? articleId  // ← 添加fallback
  
  if (sentenceId && textId && sentenceTokenId != null) {
    console.log(`🏷️ [ChatView] Marking token: "${token.token_body}" (${textId}:${sentenceId}:${sentenceTokenId})`)
    return markAsAsked(textId, sentenceId, sentenceTokenId)
  }
  
  return Promise.resolve(false)
})
```

---

## 🎯 我的建议

**立即执行以下操作**：

### 选项A: 先诊断（5分钟）

1. 在浏览器控制台查看日志
2. 告诉我看到了什么、没看到什么
3. 我帮你精准定位问题

### 选项B: 直接应用修复（10分钟）

我立即帮你修改3个文件：
1. `useTokenSelection.js` - 添加articleId fallback
2. `ArticleViewer.jsx` - 传递articleId
3. `ChatView.jsx` - 添加详细日志和fallback

**你选择哪个？我建议先选A诊断，这样能找到根本原因！** 🎯

---

## 📞 需要的信息

**请告诉我**：

1. 在浏览器控制台能否找到这些日志：
   - `选择上下文 (selectionContext)` □ 能 □ 不能
   - `Marking selected tokens as asked` □ 能 □ 不能
   - `Marking token:` □ 能 □ 不能

2. 如果能找到，请复制粘贴以下日志的内容：
   ```
   - 句子 ID: ____
   - 文章 ID: ____
   - Token 数量: ____
   ```

3. Network标签中是否有 `POST /api/user/asked-tokens` 请求？
   - □ 有
   - □ 没有

**有了这些信息，我就能立即修复！** 🚀


