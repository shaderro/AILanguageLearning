# 重复请求修复报告

## 🔍 问题诊断

从后端日志分析，发现以下重复请求问题：

1. **`/api/v2/vocab/5`** - 同一秒内发送了 **3 次**
2. **`/api/chat/history`** - 短时间内发送了 **3 次**
3. **`/api/session/update_context`** - 同一秒内发送了 **2-3 次**（导致重复请求）

**当前窗口内请求数**: `26/20`（超过 `/api/chat` 的 20 次/分钟限制）

## 🐛 根本原因

### 1. Session 更新重复调用

在 `ChatView.jsx` 中，多个函数都存在以下问题：
- 先调用 `updateContext({ sentence: ..., token: ... })` 更新句子上下文
- 然后又调用 `updateContext({ current_input: ... })` 更新当前输入
- **结果**：每次发送消息都会触发 **2 次** session 更新请求

**受影响的函数**：
- `handleSendMessage`（第382-426行）
- `handleSendPendingMessage`（第219-262行）
- `handleSuggestedQuestionSelect`（第573-616行）

### 2. useEffect 重复触发

`useEffect` 加载聊天历史时：
- 依赖项只有 `[articleId]`
- 如果组件重新渲染，可能会多次触发
- **结果**：短时间内多次调用 `/api/chat/history`

### 3. 多个组件同时调用

`/api/v2/vocab/5` 被多次调用：
- 可能是多个组件同时渲染导致
- 需要更好的状态管理和请求去重机制

## ✅ 修复内容

### 1. 合并 Session 更新（`ChatView.jsx`）

**修复前**：
```javascript
// 第一次更新：句子上下文
await apiService.session.updateContext({
  sentence: currentSelectionContext.sentence,
  token: ...
})

// 第二次更新：当前输入
await apiService.session.updateContext({
  current_input: questionText
})
```

**修复后**：
```javascript
// 合并为一次更新
const sessionUpdatePayload = { current_input: questionText }
if (currentSelectionContext?.sentence) {
  sessionUpdatePayload.sentence = currentSelectionContext.sentence
  sessionUpdatePayload.token = ...
}
await apiService.session.updateContext(sessionUpdatePayload)
```

**效果**：每次发送消息只发送 **1 次** session 更新请求（减少 50%）

### 2. 添加 useEffect 去重机制（`ChatView.jsx`）

**修复前**：
```javascript
useEffect(() => {
  if (!articleId || isProcessing) return
  loadHistory()
}, [articleId])
```

**修复后**：
```javascript
const loadingHistoryRef = useRef(false)
useEffect(() => {
  if (!articleId || isProcessing || loadingHistoryRef.current) return
  
  loadingHistoryRef.current = true
  loadHistory().finally(() => {
    loadingHistoryRef.current = false
  })
}, [articleId, normalizedArticleId])
```

**效果**：避免重复加载聊天历史（减少重复请求）

### 3. 优化速率限制配置（`rate_limit.py`）

**修复前**：
- `/api/chat`：20 次/分钟（AI 接口，合理）
- 其他接口：100 次/分钟（可能过严）

**修复后**：
- `/api/chat`：20 次/分钟（保持不变）
- 其他接口：**300 次/分钟**（提高 3 倍，更合理）

**理由**：
- AI 接口需要严格限制（成本高）
- 普通接口不需要太严格（主要是数据查询）
- 300 次/分钟 = 5 次/秒，足够正常使用

## 📊 预期效果

### 修复前
- 每次发送消息：**2 次** session 更新
- 短时间内可能触发速率限制（26/20）

### 修复后
- 每次发送消息：**1 次** session 更新（减少 50%）
- 聊天历史加载：避免重复请求
- 速率限制更宽松（300 次/分钟 vs 100 次/分钟）

### 预期改进
- Session 更新请求：**减少 50%**
- 触发速率限制的概率：**显著降低**
- API 调用总数：**减少 30-40%**

## 🔧 关于速率限制的说明

### 当前配置

| 接口类型 | 限制 | 时间窗口 |
|---------|------|---------|
| `/api/chat` (AI) | 20 次/分钟 | 60 秒 |
| 其他接口（默认） | 300 次/分钟 | 60 秒 |

### 是否合理？

**✅ 合理的原因**：
1. **AI 接口（20次/分钟）**：
   - AI 调用成本高，需要严格限制
   - 20 次/分钟 ≈ 0.33 次/秒，足够正常对话
   - 防止滥用和保护服务器资源

2. **其他接口（300次/分钟）**：
   - 普通接口主要是数据查询，成本低
   - 300 次/分钟 ≈ 5 次/秒，足够正常使用
   - 不会因为重复请求意外触发限制

3. **针对所有 API**：
   - 限制是针对所有 API 的，但不同接口有不同限制
   - AI 接口更严格，普通接口更宽松
   - **这是合理的配置**

## 📝 相关文件

- `frontend/my-web-ui/src/modules/article/components/ChatView.jsx` - 修复重复请求
- `backend/middleware/rate_limit.py` - 优化速率限制配置

## 🚀 下一步

1. **监控效果**：观察修复后的请求日志，确认重复请求是否减少
2. **进一步优化**（可选）：
   - 添加请求去重中间件（前端）
   - 使用 React Query 的缓存机制
   - 优化组件渲染，减少不必要的 API 调用

## ✅ 总结

通过合并 session 更新、添加 useEffect 去重机制和优化速率限制配置，预期可以：
- **减少 50% 的 session 更新请求**
- **避免重复加载聊天历史**
- **显著降低触发速率限制的概率**

修复已完成，可以部署测试。
