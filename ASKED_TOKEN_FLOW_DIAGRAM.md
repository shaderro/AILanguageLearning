# Asked Token 标记流程详解

## 🎬 完整流程图

```
用户操作                前端组件                    Hook/Service              后端API
═══════════════════════════════════════════════════════════════════════════════════

1. 用户点击Token
   的"vocab 
   explanation"
   按钮
      ↓
                    VocabExplanationButton
                    handleClick()
                         ↓
                    获取词汇解释
                    apiService.getVocabExplanation()
                         ↓
                    显示解释
                         ↓
                    调用标记函数 ─────→  useAskedTokens
                    markAsAsked()         markAsAsked()
                                              ↓
                                         构造key
                                         textId:sentenceId:tokenId
                                              ↓
                                         调用API ──────→  api.js
                                                          markTokenAsked()
                                                              ↓
                                                         POST请求 ──→  /api/user/asked-tokens
                                                                           ↓
                                                                      保存到JSON/数据库
                                                                           ↓
                                                         返回success ←─
                                              ↓
                                         更新Set ←─────
                                         askedTokenKeys.add(key)
                                              ↓
                    ←─────────────────  返回true
                         ↓
                    Token变绿色
      ↓
用户看到token
已标记（绿色）


═══════════════════════════════════════════════════════════════════════════════════

2. 用户选中多个
   tokens并发送
   问题
      ↓
                    ChatView
                    用户输入问题
                         ↓
                    handleSendMessage()
                         ↓
                    发送问题
                    apiService.sendChat()
                         ↓
                    收到AI响应
                         ↓
                    批量标记tokens ─────→  useAskedTokens
                    遍历所有选中tokens        ↓
                         ↓                 并发调用
                    Promise.all([              markAsAsked()
                      markAsAsked(token1),         ×N次
                      markAsAsked(token2),          ↓
                      markAsAsked(token3),     并发POST ──→  /api/user/asked-tokens
                      ...                                        ×N次
                    ])                                              ↓
                         ↓                                    保存N个tokens
                    等待所有完成 ←───────  更新Set ←──────  返回N个success
                         ↓                 添加N个keys
                    所有tokens变绿
      ↓
用户看到所有
选中的tokens
都已标记
```

---

## 📂 文件依赖关系

```
ArticleChatView.jsx (顶层页面)
    │
    ├── useAskedTokens(articleId) ────┐
    │        │                         │
    │        └── 提供: markAsAsked()   │
    │                                  │
    ├── ArticleViewer ────────────────┤
    │     │                            │
    │     ├── useAskedTokens() ────────┤ (同一个hook，共享状态)
    │     │        │                   │
    │     │        └── 提供: isTokenAsked(), markAsAsked()
    │     │                            │
    │     └── TokenSpan (循环) ────────┤
    │           │                      │
    │           ├── isTokenAsked ←─────┘
    │           │     └── 检查token是否已提问
    │           │         └── 决定样式（绿色/灰色）
    │           │
    │           └── VocabExplanationButton
    │                 │
    │                 └── markAsAsked ←───┐
    │                       └── 点击后标记  │
    │                                     │
    └── ChatView ─────────────────────────┘
          │
          └── markAsAsked ←───┐
                └── 发送问题后批量标记


useAskedTokens.js (核心Hook)
    │
    ├── useState(Set) ← 存储已提问tokens
    │
    ├── useEffect() ← 初始化时从后端加载
    │     └── apiService.getAskedTokens()
    │
    ├── isTokenAsked() ← 检查函数
    │     └── askedTokenKeys.has(key)
    │
    └── markAsAsked() ← 标记函数
          └── apiService.markTokenAsked()
                └── POST /api/user/asked-tokens
```

---

## 🔑 关键代码片段

### 初始化：加载已提问的tokens

**文件**: `hooks/useAskedTokens.js` 第13-41行

```javascript
useEffect(() => {
  if (!articleId) return

  const fetchAskedTokens = async () => {
    try {
      // 从后端获取该文章的所有已提问tokens
      const response = await apiService.getAskedTokens(userId, articleId)
      
      if (response.success && response.data?.asked_tokens) {
        // asked_tokens是字符串数组: ["1:5:12", "1:5:13", ...]
        const tokens = new Set(response.data.asked_tokens)
        setAskedTokenKeys(tokens)  // ← 初始化Set
        console.log('✅ Loaded', tokens.size, 'asked tokens')
      }
    } catch (err) {
      console.error('❌ Failed to fetch asked tokens:', err)
    }
  }

  fetchAskedTokens()  // ← 组件挂载时自动调用
}, [articleId, userId])
```

**时机**: 页面加载时自动执行

---

### 标记：添加新的asked token

**文件**: `hooks/useAskedTokens.js` 第50-67行

```javascript
const markAsAsked = async (textId, sentenceId, sentenceTokenId) => {
  try {
    // 1. 调用后端API
    const response = await apiService.markTokenAsked(
      userId, textId, sentenceId, sentenceTokenId
    )
    
    if (response.success) {
      // 2. 构造key
      const key = `${textId}:${sentenceId}:${sentenceTokenId}`
      
      // 3. 更新本地Set（React状态）
      setAskedTokenKeys(prev => new Set([...prev, key]))
      
      return true
    }
  } catch (err) {
    return false
  }
}
```

**时机**: 
- VocabExplanationButton点击后
- ChatView发送问题后
- ChatView点击建议问题后

---

### 检查：判断token是否已提问

**文件**: `hooks/useAskedTokens.js` 第44-47行

```javascript
const isTokenAsked = (textId, sentenceId, sentenceTokenId) => {
  const key = `${textId}:${sentenceId}:${sentenceTokenId}`
  return askedTokenKeys.has(key)  // Set.has() 方法，O(1)复杂度
}
```

**时机**: TokenSpan渲染时调用（每次渲染都检查）

---

## 🎯 使用示例

### 示例1: 在自己的组件中使用

```javascript
import { useAskedTokens } from './hooks/useAskedTokens'

function MyComponent({ articleId }) {
  // 1. 使用hook
  const { isTokenAsked, markAsAsked } = useAskedTokens(articleId)
  
  // 2. 检查某个token是否已提问
  const checkToken = () => {
    const isAsked = isTokenAsked(1, 5, 12)  // textId=1, sentenceId=5, tokenId=12
    console.log('Token是否已提问:', isAsked)  // true 或 false
  }
  
  // 3. 标记某个token为已提问
  const markToken = async () => {
    const success = await markAsAsked(1, 5, 12)
    if (success) {
      console.log('✅ 标记成功')
    }
  }
  
  return (
    <button onClick={markToken}>标记token</button>
  )
}
```

---

### 示例2: 批量标记多个tokens

```javascript
// 在ChatView中的实现（第213-224行）
const tokens = [
  { sentence_token_id: 1, token_body: "Der" },
  { sentence_token_id: 2, token_body: "Hund" },
  { sentence_token_id: 3, token_body: "ist" }
]

// 并发标记所有tokens
const markPromises = tokens.map(token => {
  return markAsAsked(textId, sentenceId, token.sentence_token_id)
})

// 等待所有完成
const results = await Promise.all(markPromises)
const successCount = results.filter(r => r).length
console.log(`成功标记 ${successCount}/${tokens.length} 个tokens`)
```

---

## 📞 后端API对接

### 当前后端端点（JSON版本）

**位置**: `server.py` 第96-148行

```python
@app.post("/api/user/asked-tokens")
async def mark_token_asked(payload: dict):
    user_id = payload.get("user_id", "default_user")
    text_id = payload.get("text_id")
    sentence_id = payload.get("sentence_id")
    sentence_token_id = payload.get("sentence_token_id")
    
    # 使用JSON文件存储
    manager = get_asked_tokens_manager(use_database=False)
    success = manager.mark_token_asked(
        user_id=user_id,
        text_id=text_id,
        sentence_id=sentence_id,
        sentence_token_id=sentence_token_id
    )
    
    return {
        "success": True if success else False,
        "message": "Token marked as asked"
    }
```

### 如果要切换到数据库版本

只需修改一行：

```python
# 改为使用数据库
manager = get_asked_tokens_manager(use_database=True)  # ← 改这里
```

---

## 🎉 总结

### 代码位置汇总

| 文件 | 路径 | 关键行号 | 作用 |
|------|------|---------|------|
| **Hook** | `hooks/useAskedTokens.js` | 50-67 | ⭐ 核心标记逻辑 |
| **API** | `services/api.js` | 94-102 | ⭐ HTTP请求 |
| **触发1** | `VocabExplanationButton.jsx` | 26-41 | 词汇解释时标记 |
| **触发2** | `ChatView.jsx` | 209-240 | 发送问题时标记 |
| **触发3** | `ChatView.jsx` | 432-461 | 建议问题时标记 |
| **显示** | `TokenSpan.jsx` | 26, 100 | 检查并显示样式 |
| **集成** | `ArticleViewer.jsx` | 16, 113 | 组件组装 |

### 标记时机

1. ✅ **自动标记** - 用户点击"vocab explanation"
2. ✅ **自动批量标记** - 用户发送问题（包含选中的tokens）
3. ✅ **自动批量标记** - 用户点击建议问题

### 数据格式

```javascript
// Token Key: "textId:sentenceId:tokenId"
"1:5:12"

// 存储: Set数据结构
new Set(["1:5:12", "1:5:13", "1:7:3"])
```

---

**需要修改或扩展asked token功能吗？我可以帮你！** 🚀

