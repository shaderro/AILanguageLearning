# 聊天历史记录诊断脚本使用指南

## 运行方式

### 1. 本地开发环境（默认）

直接在命令行运行：

```bash
# Windows PowerShell
python backend\diagnose_chat_history_sync.py

# Linux/Mac
python backend/diagnose_chat_history_sync.py
```

**默认行为：**
- 自动读取 `.env` 文件中的 `ENV` 变量
- 如果 `ENV=development` 且没有 `DATABASE_URL`，则连接本地 SQLite 数据库
- 如果设置了 `DATABASE_URL`，则连接 PostgreSQL 数据库

### 2. 指定环境

使用 `--env` 参数指定环境：

```bash
# 查看开发环境
python backend\diagnose_chat_history_sync.py --env development

# 查看测试环境
python backend\diagnose_chat_history_sync.py --env testing

# 查看生产环境
python backend\diagnose_chat_history_sync.py --env production
```

### 3. 查看生产环境数据库

**重要：** 查看生产环境需要设置 `DATABASE_URL` 环境变量。

#### Windows (PowerShell)

```powershell
# 设置生产环境数据库 URL（从 Render 或其他云平台获取）
$env:DATABASE_URL="postgresql://user:password@host:port/database"
$env:ENV="production"

# 运行诊断脚本
python backend\diagnose_chat_history_sync.py --env production
```

#### Windows (CMD)

```cmd
set DATABASE_URL=postgresql://user:password@host:port/database
set ENV=production
python backend\diagnose_chat_history_sync.py --env production
```

#### Linux/Mac

```bash
export DATABASE_URL="postgresql://user:password@host:port/database"
export ENV="production"
python backend/diagnose_chat_history_sync.py --env production
```

#### 从 Render 获取 DATABASE_URL

1. 登录 Render Dashboard
2. 进入你的 PostgreSQL 服务
3. 在 "Connections" 或 "Info" 标签页找到 "Internal Database URL"
4. 复制完整的连接字符串（格式：`postgresql://user:password@host:port/database`）

**安全提示：**
- ⚠️ 不要将 `DATABASE_URL` 提交到 Git
- ⚠️ 不要在公共场合显示完整的连接字符串
- ✅ 使用环境变量临时设置，用完即清除

## 诊断脚本输出说明

脚本会检查以下内容：

1. **数据库连接**
   - 环境类型（development/testing/production）
   - 数据库类型（SQLite/PostgreSQL）
   - 连接状态

2. **表结构**
   - `chat_messages` 表是否存在
   - 表结构（字段和类型）

3. **数据统计**
   - user_id 分布统计
   - 每个 user_id 的消息数量
   - user_id 为 NULL 的消息数量（这些消息无法跨设备同步）

4. **查询测试**
   - 测试不同 user_id 类型的查询（字符串 vs 整数）
   - 检查类型匹配问题

5. **诊断建议**
   - 根据发现的问题提供修复建议

## 常见问题

### Q: 如何查看生产环境的数据？

A: 需要设置 `DATABASE_URL` 环境变量指向生产数据库，然后运行：
```bash
python backend\diagnose_chat_history_sync.py --env production
```

### Q: 脚本显示 "表中没有数据"，怎么办？

A: 可能的原因：
1. 消息确实没有保存到数据库（检查后端日志）
2. 连接到了错误的数据库（检查 `DATABASE_URL`）
3. user_id 不匹配（保存时和查询时使用的 user_id 不一致）

### Q: 如何确认连接的是生产数据库？

A: 脚本会显示：
- 数据库类型：PostgreSQL（生产）或 SQLite（本地）
- 数据库 URL（部分隐藏，只显示协议和主机）

### Q: 脚本运行失败，提示编码错误？

A: 脚本已自动处理 Windows 编码问题。如果仍有问题，可以：
```bash
# 设置控制台编码为 UTF-8
chcp 65001
python backend\diagnose_chat_history_sync.py
```

## 示例输出

```
================================================================================
[诊断] 聊天历史记录跨设备同步诊断
================================================================================

[1] 检查数据库连接...
   环境: production
   [OK] 已检测到 DATABASE_URL 环境变量
   [OK] 数据库连接成功
   数据库类型: PostgreSQL

[2] 检查 chat_messages 表...
   [OK] 表 chat_messages 存在
   表结构:
     - id: INTEGER (nullable=False)
     - user_id: VARCHAR(255) (nullable=True)
     ...

[3] 检查数据库中的 user_id 数据...
   [统计] user_id 分布统计:
     - user_id='2' (类型: str): 150 条消息
     - user_id='8' (类型: str): 45 条消息
     - user_id=NULL: 10 条消息

   总计: 205 条消息
   [WARN] 警告: 有 10 条消息的 user_id 为 NULL（这些消息无法跨设备同步）

[4] 测试 ChatMessageManagerDB 查询...
   测试1: 查询所有消息（不指定 user_id）...
      结果: 205 条消息
   ...
```
