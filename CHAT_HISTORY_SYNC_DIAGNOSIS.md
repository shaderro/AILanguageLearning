# 聊天历史记录跨设备同步诊断指南

## 问题描述
历史记录没有实现跨设备同步

## 诊断步骤

### 1. 检查数据库中的数据

运行诊断脚本：
```bash
python backend/diagnose_chat_history_sync.py
```

**关键检查点：**
- 表中是否有数据
- user_id 是否为 NULL
- user_id 的类型（字符串 vs 整数）

### 2. 需要添加的日志点

#### 2.1 消息保存时（后端）

**位置：** `backend/data_managers/dialogue_record.py`

在 `add_user_message` 和 `add_ai_response` 方法中，已存在日志：
```python
print(f"✅ [DB] Chat message added: User=True, user_id={user_id_str}, Text='{user_input[:30]}...', text_id={sentence.text_id}, sentence_id={sentence.sentence_id}")
```

**需要确认：**
- 日志中 `user_id` 是否为 `None`
- 如果为 `None`，说明 `session_state.user_id` 未设置

#### 2.2 session_state.user_id 设置（后端）

**位置：** `frontend/my-web-ui/backend/main.py` 的 `/api/chat` 端点

**当前代码：**
```python
user_id = 2  # 默认用户 ID
if authorization and authorization.startswith("Bearer "):
    try:
        token = authorization.replace("Bearer ", "")
        from backend.utils.auth import decode_access_token
        payload_data = decode_access_token(token)
        if payload_data and "sub" in payload_data:
            user_id = int(payload_data["sub"])
            print(f"✅ [Chat #{request_id}] 使用认证用户: {user_id}")
    except Exception as e:
        print(f"⚠️ [Chat #{request_id}] Token 解析失败，使用默认用户: {e}")
else:
    print(f"ℹ️ [Chat #{request_id}] 未提供认证 token，使用默认用户: {user_id}")

# 设置到 session_state
local_state.user_id = user_id
```

**需要添加的日志：**
```python
print(f"[DEBUG] session_state.user_id 设置为: {local_state.user_id} (类型: {type(local_state.user_id).__name__})")
```

#### 2.3 历史记录查询时（后端）

**位置：** `backend/api/chat_history_routes.py` 的 `/api/chat/history` 端点

**当前代码：**
```python
user_id = str(current_user.user_id)
messages: List[Dict[str, Any]] = chat_manager.list_messages(
    user_id=user_id,
    text_id=text_id,
    sentence_id=sentence_id,
    limit=limit,
    offset=offset,
)
```

**需要添加的日志：**
```python
print(f"[DEBUG] [ChatHistory] 查询历史记录: user_id={user_id} (类型: {type(user_id).__name__}), text_id={text_id}, 结果数量={len(messages)}")
```

#### 2.4 前端调用历史记录 API

**位置：** `frontend/my-web-ui/src/modules/article/components/ChatView.jsx`

**当前代码：**
```javascript
const resp = await apiService.getChatHistory({ textId: articleId, limit: 200 })
```

**需要添加的日志：**
```javascript
console.log('[DEBUG] [ChatView] 加载历史记录:', { articleId, userId: /* 从 context 获取 */ })
console.log('[DEBUG] [ChatView] API 响应:', resp?.data)
```

### 3. 常见问题排查

#### 问题1: user_id 为 NULL

**可能原因：**
- `/api/chat` 端点未正确提取 user_id
- session_state.user_id 未设置
- add_user_message/add_ai_response 未接收到 user_id

**检查方法：**
1. 查看后端日志，查找 `[DB] Chat message added` 日志
2. 检查 `user_id` 字段是否为 `None`

#### 问题2: 类型不匹配（字符串 vs 整数）

**可能原因：**
- 保存时使用整数，查询时使用字符串（或反之）
- 数据库中存储的类型与查询类型不匹配

**检查方法：**
1. 运行诊断脚本，查看 user_id 的类型
2. 确保保存和查询时统一使用字符串类型

#### 问题3: 查询结果为空

**可能原因：**
- 前端未传递 Authorization header
- get_current_user 返回的用户 ID 与保存时的 user_id 不匹配
- 数据库环境不一致（开发 vs 生产）

**检查方法：**
1. 检查前端网络请求，确认 Authorization header 存在
2. 检查后端日志，确认查询使用的 user_id
3. 确认数据库环境一致

### 4. 快速诊断命令

```bash
# 检查数据库中的 user_id 分布
python backend/diagnose_chat_history_sync.py

# 或者直接查询数据库（SQLite）
sqlite3 database_system/data_storage/data/dev.db "SELECT user_id, COUNT(*) FROM chat_messages GROUP BY user_id;"

# PostgreSQL
psql $DATABASE_URL -c "SELECT user_id, COUNT(*) FROM chat_messages GROUP BY user_id;"
```

### 5. 修复建议

如果发现 user_id 为 NULL：
1. 确保 `/api/chat` 端点正确从 token 提取 user_id
2. 确保 `local_state.user_id` 正确设置
3. 确保 `add_user_message` 和 `add_ai_response` 接收到 user_id

如果发现类型不匹配：
1. 统一使用字符串类型：`str(user_id)`
2. 在查询时也使用字符串类型

如果查询结果为空：
1. 检查前端是否正确传递 Authorization header
2. 检查后端日志，确认查询使用的 user_id 与保存时的 user_id 一致
