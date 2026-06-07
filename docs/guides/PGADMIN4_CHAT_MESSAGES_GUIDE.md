# 在 pgAdmin4 中查看消息历史记录表

## 📋 消息历史记录表信息

**表名**: `chat_messages`

**表结构**:
```sql
CREATE TABLE IF NOT EXISTS chat_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,  -- PostgreSQL 中应使用 SERIAL
  user_id TEXT,
  text_id INTEGER,
  sentence_id INTEGER,
  is_user INTEGER NOT NULL,  -- 1=用户消息，0=AI回复
  content TEXT NOT NULL,
  quote_sentence_id INTEGER,
  quote_text TEXT,
  selected_token_json TEXT,
  created_at TEXT NOT NULL  -- ISO 格式时间字符串
);
```

## 🔍 在 pgAdmin4 中查看表的步骤

### 方法 1: 通过图形界面查看

1. **连接到数据库**
   - 打开 pgAdmin4
   - 在左侧服务器树中找到你的 PostgreSQL 服务器
   - 展开：`Servers` → `你的服务器` → `Databases` → `你的数据库名`

2. **查看表列表**
   - 展开数据库节点
   - 展开 `Schemas` → `public` → `Tables`
   - 查找 `chat_messages` 表

3. **查看表数据**
   - 右键点击 `chat_messages` 表
   - 选择 `View/Edit Data` → `All Rows` 或 `First 100 Rows`

4. **查看表结构**
   - 右键点击 `chat_messages` 表
   - 选择 `Properties` → `Columns` 标签页

### 方法 2: 使用 Query Tool 查询

1. **打开 Query Tool**
   - 右键点击数据库名
   - 选择 `Query Tool`

2. **执行查询语句**

   **查看所有消息（最近100条）**:
   ```sql
   SELECT * FROM chat_messages 
   ORDER BY created_at DESC 
   LIMIT 100;
   ```

   **按文章分组统计**:
   ```sql
   SELECT 
     text_id,
     COUNT(*) as message_count,
     SUM(CASE WHEN is_user = 1 THEN 1 ELSE 0 END) as user_messages,
     SUM(CASE WHEN is_user = 0 THEN 1 ELSE 0 END) as ai_messages,
     MIN(created_at) as first_message,
     MAX(created_at) as last_message
   FROM chat_messages
   GROUP BY text_id
   ORDER BY last_message DESC;
   ```

   **查看特定文章的消息**:
   ```sql
   SELECT * FROM chat_messages 
   WHERE text_id = 1770178389  -- 替换为你的文章ID
   ORDER BY created_at ASC;
   ```

   **查看特定用户的消息**:
   ```sql
   SELECT * FROM chat_messages 
   WHERE user_id = '3'  -- 替换为你的用户ID
   ORDER BY created_at DESC
   LIMIT 50;
   ```

   **查看消息统计**:
   ```sql
   SELECT 
     COUNT(*) as total_messages,
     SUM(CASE WHEN is_user = 1 THEN 1 ELSE 0 END) as user_messages,
     SUM(CASE WHEN is_user = 0 THEN 1 ELSE 0 END) as ai_messages,
     COUNT(DISTINCT text_id) as unique_articles,
     COUNT(DISTINCT user_id) as unique_users
   FROM chat_messages;
   ```

## ⚠️ 如果表不存在

如果 `chat_messages` 表在 PostgreSQL 中不存在，需要手动创建：

### 在 pgAdmin4 中创建表

1. **打开 Query Tool**
   - 右键点击数据库名 → `Query Tool`

2. **执行创建表语句**（PostgreSQL 版本）:
   ```sql
   CREATE TABLE IF NOT EXISTS chat_messages (
     id SERIAL PRIMARY KEY,
     user_id TEXT,
     text_id INTEGER,
     sentence_id INTEGER,
     is_user INTEGER NOT NULL,
     content TEXT NOT NULL,
     quote_sentence_id INTEGER,
     quote_text TEXT,
     selected_token_json TEXT,
     created_at TEXT NOT NULL
   );

   -- 创建索引以提高查询性能
   CREATE INDEX IF NOT EXISTS idx_chat_messages_text_id ON chat_messages(text_id);
   CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON chat_messages(user_id);
   CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);
   ```

3. **验证表已创建**
   ```sql
   SELECT table_name 
   FROM information_schema.tables 
   WHERE table_schema = 'public' 
   AND table_name = 'chat_messages';
   ```

## 📊 常用查询示例

### 1. 查看最近的消息对话
```sql
SELECT 
  id,
  CASE WHEN is_user = 1 THEN '用户' ELSE 'AI' END as sender,
  content,
  text_id,
  sentence_id,
  created_at
FROM chat_messages
ORDER BY created_at DESC
LIMIT 20;
```

### 2. 查看特定文章的所有对话
```sql
SELECT 
  id,
  CASE WHEN is_user = 1 THEN '用户' ELSE 'AI' END as sender,
  content,
  sentence_id,
  created_at
FROM chat_messages
WHERE text_id = 1770178389  -- 替换为你的文章ID
ORDER BY created_at ASC;
```

### 3. 统计每个用户的对话数量
```sql
SELECT 
  user_id,
  COUNT(*) as total_messages,
  COUNT(DISTINCT text_id) as articles_count
FROM chat_messages
WHERE user_id IS NOT NULL
GROUP BY user_id
ORDER BY total_messages DESC;
```

### 4. 查看包含特定关键词的消息
```sql
SELECT * FROM chat_messages
WHERE content LIKE '%关键词%'  -- 替换为你要搜索的关键词
ORDER BY created_at DESC;
```

## 🔧 注意事项

1. **数据类型差异**:
   - SQLite 使用 `INTEGER PRIMARY KEY AUTOINCREMENT`
   - PostgreSQL 使用 `SERIAL PRIMARY KEY`

2. **时间格式**:
   - 当前使用 `TEXT` 类型存储 ISO 格式时间字符串
   - 如果需要，可以转换为 `TIMESTAMP` 类型：
     ```sql
     ALTER TABLE chat_messages 
     ALTER COLUMN created_at TYPE TIMESTAMP 
     USING created_at::TIMESTAMP;
     ```

3. **性能优化**:
   - 如果表数据量大，建议在 `text_id`, `user_id`, `created_at` 上创建索引
   - 已在创建表语句中包含索引创建

## 📝 相关文件位置

- **表定义**: `backend/data_managers/chat_message_manager_db.py`
- **API 路由**: `backend/api/chat_history_routes.py`
- **测试脚本**: `backend/test_chat_history.py`
