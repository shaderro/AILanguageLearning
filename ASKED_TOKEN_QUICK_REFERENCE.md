# Asked Token 功能快速参考

## 📍 关键文件（按重要性排序）

### ⭐⭐⭐ 核心文件

**1. `hooks/useAskedTokens.js`** - 状态管理核心
```
功能：管理asked tokens的状态和操作
关键函数：
  - markAsAsked(textId, sentenceId, tokenId) → Promise<boolean>
  - isTokenAsked(textId, sentenceId, tokenId) → boolean
  - 初始化时自动加载: GET /api/user/asked-tokens
```

**2. `services/api.js`** - API调用
```
功能：封装HTTP请求
关键函数：
  - apiService.markTokenAsked(userId, textId, sentenceId, tokenId)
  - apiService.getAskedTokens(userId, textId)
API端点：
  - POST /api/user/asked-tokens
  - GET /api/user/asked-tokens
```

---

### ⭐⭐ 触发组件

**3. `components/VocabExplanationButton.jsx`** - 单个token标记
```
触发时机：用户点击"vocab explanation"按钮
位置：第26-41行
自动标记：点击后自动调用markAsAsked()
```

**4. `components/ChatView.jsx`** - 批量token标记
```
触发时机：
  - 用户发送问题（第209-240行）
  - 用户点击建议问题（第432-461行）
批量标记：并发调用Promise.all(markPromises)
```

---

### ⭐ 辅助组件

**5. `components/ArticleViewer.jsx`** - 组件集成
```
功能：组装所有组件，传递props
使用hook：const { isTokenAsked, markAsAsked } = useAskedTokens(articleId)
传递给：TokenSpan组件
```

**6. `components/TokenSpan.jsx`** - Token显示
```
功能：显示单个token并检查是否已提问
检查：const isAsked = isTokenAsked(articleId, sentenceIdx+1, token.sentence_token_id)
样式：isAsked ? 'bg-green-100' : 'hover:bg-gray-100'
```

---

## 🔄 两种标记流程

### 流程A: 单个Token（VocabExplanationButton）

```
1. 用户点击token的"vocab explanation"按钮
   ↓
2. VocabExplanationButton.handleClick()
   ↓
3. 获取词汇解释 → 显示
   ↓
4. 自动调用 markAsAsked(textId, sentenceId, tokenId)
   ↓
5. POST /api/user/asked-tokens
   ↓
6. 更新Set，token变绿
```

**特点**: 自动、单个token、立即标记

---

### 流程B: 批量Tokens（ChatView）

```
1. 用户选中多个tokens（拖拽或点击）
   ↓
2. 用户输入问题并发送
   ↓
3. ChatView.handleSendMessage()
   ↓
4. AI响应后，遍历所有选中的tokens
   ↓
5. 并发调用 Promise.all([markAsAsked(), markAsAsked(), ...])
   ↓
6. POST /api/user/asked-tokens ×N次
   ↓
7. 更新Set，所有tokens变绿
```

**特点**: 自动、批量、并发标记

---

## 📊 数据结构

### Token Key格式

```javascript
// 格式
const key = `${text_id}:${sentence_id}:${sentence_token_id}`

// 示例
"1:5:12"  // 文章1，句子5，token 12
"1:7:3"   // 文章1，句子7，token 3
```

### 存储结构

```javascript
// 前端：Set数据结构
askedTokenKeys = new Set([
  "1:5:12",
  "1:5:13",
  "1:7:3"
])

// 特点：
// - 快速查找（O(1)）
// - 自动去重
// - 页面刷新后重新从后端加载
```

### 后端请求格式

```json
// POST /api/user/asked-tokens
{
  "user_id": "default_user",
  "text_id": 1,
  "sentence_id": 5,
  "sentence_token_id": 12
}

// 响应
{
  "success": true,
  "message": "Token marked as asked"
}
```

---

## 🎨 UI效果

### Token样式

```javascript
// 未提问
className="hover:bg-gray-100 cursor-pointer"
// 鼠标悬停时灰色背景

// 已提问
className="bg-green-100 border-green-300"
// 绿色背景和边框，表示已经问过了
```

### 视觉反馈

```
未提问的token:
┌─────┐
│ Der │  ← 鼠标悬停：灰色背景
└─────┘

已提问的token:
┌─────┐
│ Der │  ← 绿色背景 + 绿色边框
└─────┘
```

---

## 🔍 调试指南

### 查看当前已提问的tokens

在浏览器控制台输入：

```javascript
// 1. 找到React组件实例（使用React DevTools）
// 2. 或者在代码中添加console.log

// 查看Set内容
console.log('Asked tokens:', Array.from(askedTokenKeys))
// 输出: ["1:5:12", "1:5:13", "1:7:3"]

// 查看数量
console.log('Total asked:', askedTokenKeys.size)
// 输出: 3
```

### 跟踪标记过程

查看控制台日志（按顺序）：

```
🏷️ [VocabExplanationButton] Marking token as asked...
🏷️ [VocabExplanationButton] Marking token: "Der" (1:5:12)
🏷️ [Frontend] Marking token as asked: 1:5:12
✅ [AskedTokens] Token marked: 1:5:12
```

### 测试标记功能

在浏览器控制台：

```javascript
// 假设已经有useAskedTokens的实例
const testMark = async () => {
  const success = await markAsAsked(1, 5, 12)
  console.log('标记结果:', success)
}

testMark()
```

---

## 🛠️ 常见修改

### 修改1: 改变已提问token的颜色

**位置**: `components/TokenSpan.jsx`

```javascript
// 找到样式代码，修改颜色
className={`
  ${isAsked 
    ? 'bg-green-100 border-green-300'  // ← 改这里
    : 'hover:bg-gray-100'
  }
`}

// 改为蓝色：
? 'bg-blue-100 border-blue-300'

// 改为黄色：
? 'bg-yellow-100 border-yellow-300'
```

---

### 修改2: 添加标记确认提示

**位置**: `components/VocabExplanationButton.jsx` 第34行后

```javascript
if (success) {
  console.log('✅ Token marked as asked successfully')
  
  // 添加：显示Toast提示
  showSuccessToast('✅ 该词已标记为已提问')
}
```

---

### 修改3: 禁止重复标记已提问的token

**位置**: `hooks/useAskedTokens.js` 第50行开始

```javascript
const markAsAsked = async (textId, sentenceId, sentenceTokenId) => {
  // 添加：检查是否已经标记过
  const key = `${textId}:${sentenceId}:${sentenceTokenId}`
  if (askedTokenKeys.has(key)) {
    console.log('ℹ️ Token已经标记过了，跳过')
    return true  // 返回成功（已存在）
  }
  
  // 原有逻辑...
  try {
    const response = await apiService.markTokenAsked(...)
    // ...
  }
}
```

---

### 修改4: 切换到数据库版API

**位置**: 修改后端 `server.py`

```python
# 当前：使用JSON文件
manager = get_asked_tokens_manager(use_database=False)

# 改为：使用数据库
manager = get_asked_tokens_manager(use_database=True)
```

**前端无需修改**（API接口相同）

---

## 📚 相关文档

- `ASKED_TOKEN_FLOW_DIAGRAM.md` - 详细流程图
- `FRONTEND_ASKED_TOKEN_CODE_LOCATION.md` - 完整代码说明
- `frontend/my-web-ui/src/modules/article/ASKED_TOKENS_FEATURE.md` - 功能文档

---

## 🎯 快速定位

**想找**：初始化加载代码  
**位置**：`hooks/useAskedTokens.js` 第13-41行

**想找**：标记token的核心函数  
**位置**：`hooks/useAskedTokens.js` 第50-67行 ⭐

**想找**：API请求代码  
**位置**：`services/api.js` 第94-102行 ⭐

**想找**：点击解释按钮时的标记  
**位置**：`VocabExplanationButton.jsx` 第26-41行

**想找**：发送问题时的批量标记  
**位置**：`ChatView.jsx` 第209-240行

**想找**：Token样式显示  
**位置**：`TokenSpan.jsx` 查找 `isAsked` 变量

---

**需要修改某个功能或添加新功能吗？告诉我具体需求！** 🚀

