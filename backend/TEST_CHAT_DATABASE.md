# Chat Record Database 测试指南

## 📋 功能概述

Chat Record Database 功能实现了聊天记录的数据库持久化，支持：
- ✅ 自动保存所有用户消息和 AI 回复到 SQLite 数据库
- ✅ 跨设备/跨会话的聊天记录恢复
- ✅ 通过 API 查询历史记录
- ✅ 与 localStorage 配合使用（localStorage 用于快速加载，数据库用于跨设备同步）

## 🗄️ 数据库结构

**表名**: `chat_messages`

**字段**:
- `id` - 主键，自增
- `user_id` - 用户ID（预留，当前为 NULL）
- `text_id` - 文章ID
- `sentence_id` - 句子ID
- `is_user` - 是否用户消息（1=用户，0=AI）
- `content` - 消息内容
- `quote_sentence_id` - 引用的句子ID
- `quote_text` - 引用句子内容
- `selected_token_json` - 选中的token信息（JSON格式）
- `created_at` - 创建时间（ISO格式）

**数据库位置**: `backend/database_system/data_storage/data/language_learning.db`

## 🧪 测试步骤

### 1. 验证数据库表已创建

运行测试脚本：

```bash
cd backend
python test_chat_history.py
```

**预期输出**:
- ✅ 表 `chat_messages` 存在
- 📈 显示总记录数
- 📚 按文章分组统计
- 📝 显示最近10条消息

**如果表不存在**:
- 先发送几条聊天消息，系统会自动创建表
- 或者手动运行一次 `ChatMessageManagerDB()` 初始化

### 2. 测试消息自动保存

#### 步骤：
1. 启动后端服务器
2. 打开前端应用
3. 选择一篇文章
4. 发送几条聊天消息（用户消息 + AI回复）
5. 检查后端控制台日志，应该看到：
   ```
   ✅ [DB] Chat message added: ID=xxx, User=True, Text='...'
   ✅ [DB] Chat message added: ID=xxx, User=False, Text='...'
   ```

#### 验证方法：

**方法1：使用测试脚本**
```bash
cd backend
python test_chat_history.py
```

**方法2：直接查询数据库**
```bash
# 使用 SQLite 命令行工具
sqlite3 backend/database_system/data_storage/data/language_learning.db

# 查看表结构
.schema chat_messages

# 查看总记录数
SELECT COUNT(*) FROM chat_messages;

# 查看最近10条消息
SELECT id, text_id, sentence_id, is_user, content, created_at 
FROM chat_messages 
ORDER BY created_at DESC 
LIMIT 10;

# 按文章分组统计
SELECT text_id, COUNT(*) as count 
FROM chat_messages 
GROUP BY text_id 
ORDER BY count DESC;
```

### 3. 测试 API 读取历史记录

#### 步骤：
1. 确保后端服务器正在运行
2. 打开浏览器开发者工具（F12）
3. 切换到 Network 标签
4. 刷新文章页面
5. 查找 `/api/chat/history` 请求

#### API 端点：

**GET** `/api/chat/history`

**查询参数**:
- `text_id` (可选) - 文章ID
- `sentence_id` (可选) - 句子ID
- `user_id` (可选) - 用户ID（预留）
- `limit` (可选，默认100) - 最大返回条数
- `offset` (可选，默认0) - 偏移量

**示例请求**:
```bash
# 获取文章ID=1的所有消息
curl "http://localhost:8000/api/chat/history?text_id=1&limit=50"

# 获取文章ID=1，句子ID=5的消息
curl "http://localhost:8000/api/chat/history?text_id=1&sentence_id=5"
```

**预期响应**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "user_id": null,
        "text_id": 1,
        "sentence_id": 5,
        "is_user": true,
        "text": "这个词是什么意思？",
        "quote_sentence_id": 5,
        "quote_text": "Die Finne ist groß...",
        "selected_token": {...},
        "created_at": "2024-01-01T12:00:00"
      },
      {
        "id": 2,
        "user_id": null,
        "text_id": 1,
        "sentence_id": 5,
        "is_user": false,
        "text": "这个词的意思是...",
        "quote_sentence_id": 5,
        "quote_text": "Die Finne ist groß...",
        "selected_token": null,
        "created_at": "2024-01-01T12:00:05"
      }
    ],
    "count": 2,
    "limit": 50,
    "offset": 0
  }
}
```

### 4. 测试跨设备/跨会话恢复

#### 步骤：
1. 在设备A上发送几条消息
2. 等待消息保存到数据库（查看后端日志）
3. 清除浏览器 localStorage：
   ```javascript
   // 在浏览器控制台执行
   localStorage.clear()
   ```
4. 刷新页面
5. 打开文章，应该能看到之前的聊天记录

#### 验证方法：

**检查前端日志**:
- 打开浏览器控制台
- 查找日志：`🔄 [ChatView] 从数据库加载聊天历史`
- 应该看到从 API 获取的消息数量

**检查 Network 请求**:
- 查找 `GET /api/chat/history?text_id=xxx`
- 检查响应中是否包含之前的消息

### 5. 测试数据完整性

#### 验证字段：

**用户消息应该包含**:
- ✅ `is_user: true`
- ✅ `content`: 用户输入的问题
- ✅ `quote_text`: 引用的句子内容
- ✅ `selected_token`: 选中的token信息（如果有）

**AI 消息应该包含**:
- ✅ `is_user: false`
- ✅ `content`: AI 回复内容
- ✅ `quote_text`: 引用的句子内容
- ✅ `selected_token: null`（AI消息通常没有selected_token）

#### 测试脚本：

```python
# 在 backend/test_chat_history.py 中添加验证逻辑
def test_data_integrity():
    """验证数据完整性"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查是否有用户消息没有对应的AI回复
    cursor.execute("""
        SELECT text_id, sentence_id, COUNT(*) 
        FROM chat_messages 
        WHERE is_user = 1
        GROUP BY text_id, sentence_id
    """)
    user_messages = cursor.fetchall()
    
    cursor.execute("""
        SELECT text_id, sentence_id, COUNT(*) 
        FROM chat_messages 
        WHERE is_user = 0
        GROUP BY text_id, sentence_id
    """)
    ai_messages = cursor.fetchall()
    
    print(f"用户消息组数: {len(user_messages)}")
    print(f"AI消息组数: {len(ai_messages)}")
    
    conn.close()
```

## 🔍 调试技巧

### 1. 查看后端日志

启动后端时，应该看到：
```
✅ [DB] Chat message added: ID=1, User=True, Text='这个词是什么意思？'
✅ [DB] Chat message added: ID=2, User=False, Text='这个词的意思是...'
```

如果没有看到这些日志，检查：
- `DialogueRecordBySentenceNew` 是否正确初始化了 `db_manager`
- 是否有异常被捕获但没有打印

### 2. 检查数据库文件

```bash
# 检查文件是否存在
ls -lh backend/database_system/data_storage/data/language_learning.db

# 检查文件大小（应该随着消息增加而增长）
du -h backend/database_system/data_storage/data/language_learning.db
```

### 3. 前端调试

在浏览器控制台执行：

```javascript
// 检查 localStorage 中的消息
const all = JSON.parse(localStorage.getItem('chat_messages_all') || '[]')
console.log('LocalStorage 消息数:', all.length)

// 检查全局 ref
console.log('全局 ref 消息数:', window.chatViewMessagesRef?.length || 0)

// 手动调用 API 获取历史记录
const resp = await fetch('http://localhost:8000/api/chat/history?text_id=1&limit=50')
const data = await resp.json()
console.log('数据库消息数:', data.data.count)
console.log('消息列表:', data.data.items)
```

## ⚠️ 常见问题

### 1. 表不存在

**问题**: `test_chat_history.py` 报告表不存在

**解决**:
- 先发送几条消息，系统会自动创建表
- 或者手动初始化：`ChatMessageManagerDB()`

### 2. 消息没有保存到数据库

**检查**:
- 后端日志是否有错误信息
- `DialogueRecordBySentenceNew` 是否正确调用 `db_manager.add_message`
- 数据库文件是否有写入权限

### 3. API 返回空列表

**检查**:
- 数据库是否有记录（使用 `test_chat_history.py` 验证）
- API 查询参数是否正确（`text_id`, `sentence_id`）
- 后端路由是否已注册（检查 `main.py` 中的 `app.include_router(chat_history_router)`）

### 4. 跨设备测试不工作

**检查**:
- localStorage 是否已清除
- 前端是否正确调用 `getChatHistory` API
- Network 面板中是否有 `/api/chat/history` 请求
- API 响应是否包含消息数据

## 📊 性能测试

### 测试大量消息：

```python
# 生成测试数据
from backend.data_managers.chat_message_manager_db import ChatMessageManagerDB

manager = ChatMessageManagerDB()
for i in range(1000):
    manager.add_message(
        text_id=1,
        sentence_id=1,
        is_user=(i % 2 == 0),
        content=f"测试消息 {i}"
    )

# 测试查询性能
import time
start = time.time()
messages = manager.list_messages(text_id=1, limit=1000)
end = time.time()
print(f"查询1000条消息耗时: {end - start:.2f}秒")
```

## ✅ 测试清单

- [ ] 数据库表已创建
- [ ] 用户消息自动保存到数据库
- [ ] AI 回复自动保存到数据库
- [ ] API 可以读取历史记录
- [ ] 清除 localStorage 后可以从数据库恢复
- [ ] 消息字段完整（content, quote_text, selected_token等）
- [ ] 消息按时间顺序正确排序
- [ ] 分页功能正常（limit, offset）
- [ ] 按文章ID过滤正常
- [ ] 按句子ID过滤正常

## 🎯 下一步

1. **用户认证集成**: 将 `user_id` 从 NULL 改为真实用户ID
2. **消息搜索**: 添加全文搜索功能
3. **消息导出**: 支持导出聊天记录为 JSON/CSV
4. **消息删除**: 支持删除特定消息或整个对话
5. **消息统计**: 添加消息数量、对话次数等统计功能

