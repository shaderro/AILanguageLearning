# 完整上下文传递与日志修复

## 🐛 问题描述

用户反馈：选中 token 后提问时，后端仍然没有接收到完整的句子信息，并且控制台没有显示当前引用的 token 和句子原文。

## ✅ 修复内容

### 1. ArticleChatView - 保存完整上下文

**文件：** `frontend/my-web-ui/src/modules/article/ArticleChatView.jsx`

#### 新增状态
```javascript
const [currentContext, setCurrentContext] = useState(null)  // 保存完整的选择上下文
```

#### 更新 handleTokenSelect
```javascript
const handleTokenSelect = async (tokenText, selectedSet, selectedTexts = [], context = null) => {
  setSelectedTokens(selectedTexts)
  setQuotedText(selectedTexts.join(' '))
  setHasSelectedToken(selectedTexts.length > 0)
  setCurrentContext(context)  // ✅ 保存完整的上下文信息
  
  // ... 其他代码
}
```

#### 清除上下文
```javascript
const handleClearQuote = () => {
  setQuotedText('')
  setCurrentContext(null)  // ✅ 同时清除上下文
}
```

#### 传递给 ChatView
```javascript
<ChatView 
  quotedText={quotedText}
  onClearQuote={handleClearQuote}
  disabled={isUploadMode && !uploadComplete}
  hasSelectedToken={hasSelectedToken}
  selectedTokenCount={selectedTokens.length || 1}
  selectionContext={currentContext}  // ✅ 传递完整上下文
/>
```

### 2. ChatView - 接收上下文并添加详细日志

**文件：** `frontend/my-web-ui/src/modules/article/components/ChatView.jsx`

#### 新增 Props
```javascript
export default function ChatView({ 
  quotedText, 
  onClearQuote, 
  disabled = false, 
  hasSelectedToken = false, 
  selectedTokenCount = 1, 
  selectionContext = null  // ✅ 接收完整上下文
}) {
```

#### handleSendMessage 修复

**修复 1：保存引用和上下文**
```javascript
const handleSendMessage = async () => {
  if (inputText.trim() === '') return

  const questionText = inputText
  // ✅ 保存当前的引用文本和上下文，因为后面会清空
  const currentQuotedText = quotedText
  const currentSelectionContext = selectionContext
  
  // ... 其他代码
}
```

**修复 2：详细的控制台日志**
```javascript
console.log('\n' + '='.repeat(80))
console.log('💬 [ChatView] ========== 发送消息 ==========')
console.log('📝 [ChatView] 问题文本:', questionText)
console.log('📌 [ChatView] 引用文本 (quotedText):', currentQuotedText || '无')
console.log('📋 [ChatView] 选择上下文 (selectionContext):')
if (currentSelectionContext) {
  console.log('  - 句子 ID:', currentSelectionContext.sentence?.sentence_id)
  console.log('  - 文章 ID:', currentSelectionContext.sentence?.text_id)
  console.log('  - 句子原文:', currentSelectionContext.sentence?.sentence_body)
  console.log('  - 选中的 tokens:', currentSelectionContext.selectedTexts)
  console.log('  - Token 数量:', currentSelectionContext.tokens?.length)
} else {
  console.log('  - 无上下文（未选择任何token）')
}
console.log('='.repeat(80) + '\n')
```

**修复 3：延迟清空引用**
```javascript
// ✅ 处理完成后清空引用
if (onClearQuote) {
  onClearQuote()
}

// ... 在 catch 块中也同样清空
```

#### handleSuggestedQuestionSelect 修复

同样的修复应用到建议问题处理函数：
- ✅ 保存 `currentQuotedText` 和 `currentSelectionContext`
- ✅ 添加详细的控制台日志
- ✅ 延迟清空引用

## 📊 控制台日志示例

### 成功情况

```
================================================================================
💬 [ChatView] ========== 发送消息 ==========
📝 [ChatView] 问题文本: 这个词是什么意思？
📌 [ChatView] 引用文本 (quotedText): besaß
📋 [ChatView] 选择上下文 (selectionContext):
  - 句子 ID: 3
  - 文章 ID: 1
  - 句子原文: Er war dünn, blond, besaß nicht die notwendige Kraft, die nützlich gewesen wäre, sich über den Gartenzaun zu recken und zu spähen.
  - 选中的 tokens: ['besaß']
  - Token 数量: 1
================================================================================

💬 [ChatView] 有引用文本，保持当前 token 选择不变
✅ [ChatView] Session context 更新完成: {success: true, ...}
💬 [Frontend] 步骤4: 调用 /api/chat 接口...
✅ [Frontend] 步骤5: 收到响应
```

### 无引用情况

```
================================================================================
💬 [ChatView] ========== 发送消息 ==========
📝 [ChatView] 问题文本: 这句话是什么意思？
📌 [ChatView] 引用文本 (quotedText): 无
📋 [ChatView] 选择上下文 (selectionContext):
  - 无上下文（未选择任何token）
================================================================================

💬 [ChatView] 没有引用文本，清除旧 token 选择
```

## 🔄 完整数据流

```
1. 用户选中 token "besaß"
   ↓
2. ArticleViewer → useTokenSelection.emitSelection()
   - 构建完整上下文：{ sentence, tokens, selectedTexts, tokenIndices }
   ↓
3. ArticleChatView.handleTokenSelect()
   - setCurrentContext(context) ← 保存完整上下文
   - 发送到后端：apiService.session.updateContext({ sentence, token })
   ↓
4. 后端 session_state 保存：
   - current_sentence: { text_id, sentence_id, sentence_body }
   - current_selected_token: { token_text, token_indices, ... }
   ↓
5. 用户点击建议问题或手动输入
   ↓
6. ChatView.handleSendMessage() 或 handleSuggestedQuestionSelect()
   - 保存 currentQuotedText = quotedText
   - 保存 currentSelectionContext = selectionContext
   - 打印详细日志（句子原文、token等）
   - 发送 current_input（不清除 token，因为有引用）
   ↓
7. 后端接收：
   - current_sentence: 完整句子 ✅
   - current_selected_token: "besaß" ✅
   - current_input: 用户问题 ✅
   ↓
8. AI 正确回答
   ↓
9. 前端收到响应后清空引用
```

## 🧪 测试验证

### 测试步骤

1. **刷新页面并打开控制台**
   ```bash
   npm run dev
   ```

2. **选择单个词**
   - 点击选中 "besaß"
   - 查看控制台应显示：
     ```
     🎯 [ArticleChatView] Token selection changed:
       - Context: { sentence: {...}, tokens: [...] }
     📤 [ArticleChatView] Sending selection context to backend...
     ✅ [ArticleChatView] Session context updated
     ```

3. **发送建议问题**
   - 点击"这个词是什么意思？"
   - 查看控制台应显示完整上下文：
     ```
     ================================================================================
     💬 [ChatView] ========== 发送建议问题 ==========
     📝 [ChatView] 问题文本: 这个词是什么意思？
     📌 [ChatView] 引用文本 (quotedText): besaß
     📋 [ChatView] 选择上下文 (selectionContext):
       - 句子 ID: 3
       - 文章 ID: 1
       - 句子原文: Er war dünn, blond, besaß...
       - 选中的 tokens: ['besaß']
       - Token 数量: 1
     ================================================================================
     ```

4. **验证后端响应**
   - AI 应该正确回答："besaß" 是动词 "besitzen" 的过去式...

### 预期结果

✅ 控制台清晰显示：
- 问题文本
- 引用的 token
- 完整的句子原文
- 句子 ID 和文章 ID

✅ 后端正确接收所有信息

✅ AI 回答准确针对选中的 token

## 📝 修改的文件

1. ✅ `frontend/my-web-ui/src/modules/article/ArticleChatView.jsx`
   - 新增 `currentContext` 状态
   - 保存完整的选择上下文
   - 传递给 ChatView

2. ✅ `frontend/my-web-ui/src/modules/article/components/ChatView.jsx`
   - 新增 `selectionContext` prop
   - 修复 `handleSendMessage` - 保存引用和上下文
   - 修复 `handleSuggestedQuestionSelect` - 保存引用和上下文
   - 添加详细的控制台日志
   - 延迟清空引用（在处理完成后）

## ✅ 验证清单

- [x] 保存完整上下文到 `currentContext` 状态
- [x] 传递 `selectionContext` 给 ChatView
- [x] 在发送消息前保存引用和上下文
- [x] 添加详细的控制台日志（句子原文、token等）
- [x] 延迟清空引用（在响应后）
- [x] 建议问题也应用相同修复
- [x] 无语法错误
- [x] 控制台日志格式清晰易读

## 🎯 关键改进

### 之前的问题
❌ 只保存了 `quotedText`（文本字符串）
❌ 没有保存句子上下文信息
❌ 提前清空引用导致无法使用
❌ 控制台日志不够详细

### 现在的解决方案
✅ 保存完整的 `selectionContext`（包含句子信息）
✅ 传递完整上下文给 ChatView
✅ 延迟清空引用（处理完成后）
✅ 详细的控制台日志，包含：
  - 问题文本
  - 引用的 token
  - 句子原文
  - 句子 ID 和文章 ID
  - Token 数量

## 🚀 使用效果

现在每次发送消息时，开发者可以在控制台清楚地看到：
1. 用户问了什么问题
2. 引用了哪个/哪些 token
3. 完整的句子原文是什么
4. 句子和文章的 ID

这大大提高了调试效率，也确保了后端能接收到完整的上下文信息！

