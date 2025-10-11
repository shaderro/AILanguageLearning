# Token 引用传递问题修复

## 🐛 问题描述

### 现象
当用户选中一个 token（如 "besaß"）并点击建议问题（如"这个词是什么意思？"）时，后端 AI 回答：
```
你问的是哪个词的意思呢？请具体指出你不懂的单词...
```

说明后端没有正确接收到选中的 token 信息。

### 根本原因

在 `ChatView.jsx` 的 `handleSuggestedQuestionSelect` 函数中，有两个问题：

**问题 1：提前清空引用**
```javascript
// ❌ 错误：在发送到后端之前就清空了引用
setMessages(prev => [...prev, userMessage])

if (onClearQuote) {
  onClearQuote()  // 这里清空了 quotedText
}

// 后面使用 quotedText 时已经是空的了
await apiService.session.updateContext({
  current_input: question,
  token: quotedText ? ... : null  // quotedText 已经是空的
})
```

**问题 2：强制清除 token 选择**
```javascript
// ❌ 错误：无论是否有引用，都清除 token 选择
await apiService.session.updateContext({
  current_input: question,
  token: null  // 强制清除，导致后端无法知道选中了哪个词
})
```

## ✅ 修复方案

### 修改文件
`frontend/my-web-ui/src/modules/article/components/ChatView.jsx`

### 修复内容

#### 1. 保存引用文本到局部变量
```javascript
const handleSuggestedQuestionSelect = async (question) => {
  // ✅ 在清空之前保存当前的引用文本
  const currentQuotedText = quotedText
  
  // ... 其他代码
}
```

#### 2. 根据引用文本决定是否清除 token
```javascript
const updatePayload = {
  current_input: question
}

// ✅ 只有当没有引用文本时，才清除 token 选择
if (!currentQuotedText) {
  console.log('💬 [Frontend] 没有引用文本，清除旧 token 选择')
  updatePayload.token = null
} else {
  console.log('💬 [Frontend] 有引用文本，保持当前 token 选择:', currentQuotedText)
  // 不设置 token 字段，保持后端的 token 选择不变
}

await apiService.session.updateContext(updatePayload)
```

#### 3. 在处理完成后才清空引用
```javascript
if (response.success && response.data) {
  // ... 处理响应
}

// ✅ 处理完成后才清空引用
if (onClearQuote) {
  onClearQuote()
}
```

## 🔄 完整的数据流

### 正确的流程
```
1. 用户选中 token "besaß"
   ↓
2. ArticleChatView.handleTokenSelect 发送到后端
   → apiService.session.updateContext({
       sentence: { text_id, sentence_id, sentence_body },
       token: { token_body: "besaß", ... }
     })
   ↓
3. 后端 session_state 保存:
   - current_sentence
   - current_selected_token
   ↓
4. 用户点击建议问题 "这个词是什么意思？"
   ↓
5. handleSuggestedQuestionSelect:
   - 保存 currentQuotedText = "besaß"
   - 发送 current_input = "这个词是什么意思？"
   - 不清除 token（因为有 currentQuotedText）
   ↓
6. 后端接收到:
   - current_sentence: 完整句子
   - current_selected_token: "besaß"
   - current_input: "这个词是什么意思？"
   ↓
7. 后端 AI 根据选中的词回答
   ↓
8. 前端收到响应后才清空引用
```

## 🧪 测试步骤

### 1. 启动服务
```bash
# 后端
cd frontend/my-web-ui/backend
python server.py

# 前端
cd frontend/my-web-ui
npm run dev
```

### 2. 测试单词问题
1. 打开文章页面
2. 选中一个单词（如 "besaß"）
3. 点击建议问题"这个词是什么意思？"
4. 查看浏览器控制台：
   ```
   💬 [Frontend] Current quoted text: besaß
   💬 [Frontend] 有引用文本，保持当前 token 选择: besaß
   ```
5. 查看后端输出：
   ```
   📋 [Chat] Session State Info:
     - current_selected_token: besaß
   🎯 [Chat] User selected specific token: 'besaß'
   ```
6. AI 应该正确回答该词的意思

### 3. 测试短语问题
1. 选中多个词（如 "dünn und blond"）
2. 点击建议问题"这个短语是什么意思？"
3. 验证后端接收到正确的 token 信息

### 4. 测试整句问题
1. 选中整句话
2. 点击建议问题"这句话是什么意思？"
3. 验证后端接收到整句信息

## 📊 对比

| 场景 | 修复前 | 修复后 |
|------|--------|--------|
| **选中单词提问** | ❌ 后端不知道选中了哪个词 | ✅ 后端正确识别选中的词 |
| **quotedText 时机** | ❌ 提前清空，后续无法使用 | ✅ 保存到局部变量，处理完再清空 |
| **token 清除逻辑** | ❌ 强制清除所有 token 选择 | ✅ 根据是否有引用智能决定 |
| **AI 回答** | ❌ "你问的是哪个词？" | ✅ 正确回答选中词的意思 |

## 🎯 关键点

1. **保存引用文本**：在清空之前保存到 `currentQuotedText`
2. **条件判断**：只有当没有引用时才清除 token
3. **时序控制**：在处理完成后才清空引用
4. **日志完善**：添加详细的调试日志便于追踪

## 📝 相关文件

### 修改的文件
- ✅ `frontend/my-web-ui/src/modules/article/components/ChatView.jsx`
  - `handleSuggestedQuestionSelect()` 函数

### 相关文件（未修改，但参与数据流）
- `frontend/my-web-ui/src/modules/article/ArticleChatView.jsx`
  - `handleTokenSelect()` - 发送 token 选择到后端
- `frontend/my-web-ui/backend/server.py`
  - `/api/session/update_context` - 接收并保存 session state
  - `/api/chat` - 使用 session state 处理问题

## ✅ 验证清单

- [x] 单个词选中并提问：后端正确接收 token
- [x] 多个词（短语）选中并提问：后端正确接收 token
- [x] 整句选中并提问：后端正确识别为整句
- [x] 无引用直接提问：正常工作
- [x] 控制台日志显示正确的 quotedText
- [x] 后端日志显示正确的 selected_token
- [x] 无语法错误
- [x] AI 回答针对选中的具体内容

## 🚀 预期效果

修复后，当用户：
1. 选中 "besaß"
2. 点击 "这个词是什么意思？"

AI 将正确回答：
```
"besaß" 是德语动词 "besitzen"（拥有）的过去式...
```

而不是反问"你问的是哪个词？"

