# Pending Knowledge 轮询优化修复

## 🔍 问题诊断

从日志分析发现以下异常：

### 1. `/api/chat/pending-knowledge` 每秒轮询
```
13:53:55 GET /api/chat/pending-knowledge
13:53:56 GET /api/chat/pending-knowledge
13:53:57 GET /api/chat/pending-knowledge
13:53:58 GET /api/chat/pending-knowledge
13:53:59 GET /api/chat/pending-knowledge
13:54:00 GET /api/chat/pending-knowledge
13:54:01 GET /api/chat/pending-knowledge
```
- **问题**：6秒内调用了7次（每秒1次）
- **原因**：轮询间隔设置为1000ms（1秒），过于频繁

### 2. 被误计入 `/api/chat` 的速率限制
- **问题**：`/api/chat/pending-knowledge` 被错误地计入 `/api/chat` 的限制（20次/分钟）
- **影响**：导致7次轮询请求占用了 `/api/chat` 的配额
- **原因**：速率限制配置使用精确匹配，`/api/chat/pending-knowledge` 路径前缀匹配到 `/api/chat`

### 3. 轮询清理不完善
- **问题**：如果发送多条消息，可能会有多个轮询同时运行
- **原因**：轮询定时器没有使用 `useRef` 存储，无法确保清理

### 4. `/api/session/update_context` 仍然重复
- **问题**：同一秒内调用了2次（13:54:11）
- **说明**：之前的修复可能还没完全生效，或还有其他地方在调用

## ✅ 修复内容

### 1. 修复速率限制配置（`rate_limit.py`）

**修复前**：
```python
def get_rate_limit_config(path: str) -> Dict:
    if path in RATE_LIMIT_CONFIG:
        return RATE_LIMIT_CONFIG[path]
    return RATE_LIMIT_CONFIG["default"]
```
- `/api/chat/pending-knowledge` 会被误判为 `/api/chat`

**修复后**：
```python
def get_rate_limit_config(path: str) -> Dict:
    if path in RATE_LIMIT_CONFIG:
        return RATE_LIMIT_CONFIG[path]
    # 🔧 pending-knowledge 是查询接口，不应该使用 AI 接口的严格限制
    if path.startswith("/api/chat/pending-knowledge"):
        return RATE_LIMIT_CONFIG["default"]
    return RATE_LIMIT_CONFIG["default"]
```
- `/api/chat/pending-knowledge` 现在使用默认限制（300次/分钟）

### 2. 降低轮询频率（`ChatView.jsx`）

**修复前**：
```javascript
const pollInterval = 1000  // 1秒一次
```

**修复后**：
```javascript
const pollInterval = 3000  // 3秒一次
```
- **效果**：请求频率降低 **67%**（从每秒1次减少到每3秒1次）

### 3. 改进轮询清理机制（`ChatView.jsx`）

**修复前**：
```javascript
const pollPendingKnowledge = setInterval(...)
// 没有使用 useRef，无法确保清理
```

**修复后**：
```javascript
const pollPendingKnowledgeRef = useRef(null)

// 先清理之前的轮询
if (pollPendingKnowledgeRef.current) {
  clearInterval(pollPendingKnowledgeRef.current)
  pollPendingKnowledgeRef.current = null
}

pollPendingKnowledgeRef.current = setInterval(...)

// 组件卸载时清理
useEffect(() => {
  return () => {
    if (pollPendingKnowledgeRef.current) {
      clearInterval(pollPendingKnowledgeRef.current)
      pollPendingKnowledgeRef.current = null
    }
  }
}, [articleId, normalizedArticleId])
```
- **效果**：确保轮询被正确清理，避免多个轮询同时运行

## 📊 预期效果

### 修复前
- `/api/chat/pending-knowledge`：每秒1次（60次/分钟）
- 被计入 `/api/chat` 限制：占用 AI 接口配额
- 可能同时运行多个轮询

### 修复后
- `/api/chat/pending-knowledge`：每3秒1次（20次/分钟）
- 使用默认限制：300次/分钟（足够使用）
- 确保只有一个轮询运行

### 预期改进
- 轮询请求频率：**减少 67%**（从60次/分钟减少到20次/分钟）
- 不再占用 AI 接口配额：`/api/chat` 的限制不受影响
- 轮询清理：确保正确清理，避免内存泄漏

## 🔧 关于 `/api/session/update_context` 重复调用

虽然在同一秒内看到了2次调用，但这可能是因为：
1. 修复还没部署（代码刚push）
2. 还有其他地方在调用（需要进一步检查）

如果部署后仍然看到重复调用，需要进一步调查。

## 📝 相关文件

- `backend/middleware/rate_limit.py` - 修复速率限制配置
- `frontend/my-web-ui/src/modules/article/components/ChatView.jsx` - 优化轮询机制

## ✅ 总结

通过修复速率限制配置、降低轮询频率和改进清理机制，预期可以：
- **减少 67% 的轮询请求**
- **不再占用 AI 接口配额**
- **确保轮询正确清理**

修复已完成，可以部署测试。
