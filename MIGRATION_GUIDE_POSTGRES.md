# PostgreSQL 迁移指南：Token 和邀请码系统

本指南说明如何将 Token 和邀请码功能相关的数据库修改迁移到 PostgreSQL 数据库。

## 迁移内容

本次迁移包括以下内容：

1. **users 表新增字段**：
   - `role`: VARCHAR(32) - 用户角色（admin/user），默认 'user'
   - `token_balance`: BIGINT - 当前 token 余额，默认 0
   - `token_updated_at`: TIMESTAMP - 最近一次余额变动时间

2. **invite_codes 表**（新建）：
   - 一次性邀请码表
   - 每个邀请码只能被一个用户兑换一次
   - 默认发放 1,000,000 tokens（100 积分）

3. **token_ledger 表**（新建）：
   - Token 账本表
   - 记录所有 token 变动（正数发放，负数消耗）
   - 用于审计与余额回算

4. **token_logs 表**（新建）：
   - Token 使用日志表
   - 记录每次 DeepSeek API 调用的真实 token 使用量
   - 包含 `assistant_name` 字段（记录调用的 SubAssistant 名称）

## 迁移步骤

### 方法 1: 使用 SQL 脚本（推荐）

1. **备份数据库**（重要！）
   ```bash
   pg_dump -h <host> -U <username> -d <database_name> > backup_before_migration.sql
   ```

2. **连接到 PostgreSQL 数据库**
   - 使用 pgAdmin 或其他 PostgreSQL 客户端工具
   - 或者使用命令行：`psql -h <host> -U <username> -d <database_name>`

3. **执行迁移脚本**
   ```sql
   \i migrate_token_system_postgres_complete.sql
   ```
   或者在 pgAdmin 中：
   - 打开 `migrate_token_system_postgres_complete.sql` 文件
   - 执行整个脚本（F5 或点击 Execute）

4. **验证迁移结果**
   - 脚本会自动验证所有表和字段是否创建成功
   - 检查 NOTICE 消息，确认所有步骤都成功

### 方法 2: 使用 Python 脚本（适用于已连接的环境）

如果你已经在 Python 环境中配置了 PostgreSQL 连接，可以使用 Python 迁移脚本：

```bash
# 设置环境变量指向 PostgreSQL
export ENV=production  # 或你的生产环境名称
export DATABASE_URL=postgresql://user:password@host:port/database

# 运行迁移脚本
python migrate_add_invite_token_system.py
python migrate_add_token_logs_table.py
python migrate_add_assistant_name_to_token_logs.py
```

## 迁移脚本说明

### `migrate_token_system_postgres_complete.sql`

这是完整的 PostgreSQL 迁移脚本，包含：

- ✅ 使用 `DO $$ ... END $$;` 块确保字段/表不存在时才创建（幂等性）
- ✅ 自动检查并添加 `token_logs.assistant_name` 字段（如果表已存在但字段不存在）
- ✅ 创建所有必要的索引
- ✅ 添加表和字段的注释
- ✅ 自动验证迁移结果

### 脚本特点

1. **幂等性**：可以安全地多次执行，不会重复创建已存在的表和字段
2. **向后兼容**：如果表已存在，会检查并添加缺失的字段（如 `assistant_name`）
3. **详细验证**：执行后会输出验证结果，显示哪些表和字段已创建

## 验证迁移

执行迁移脚本后，检查以下内容：

### 1. 检查 users 表新字段

```sql
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_name = 'users'
AND column_name IN ('role', 'token_balance', 'token_updated_at');
```

### 2. 检查新表是否存在

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_name IN ('invite_codes', 'token_ledger', 'token_logs');
```

### 3. 检查 token_logs 表结构

```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'token_logs'
ORDER BY ordinal_position;
```

应该包含以下字段：
- `id`
- `user_id`
- `total_tokens`
- `prompt_tokens`
- `completion_tokens`
- `model_name`
- `assistant_name` ✅
- `created_at`

### 4. 检查索引

```sql
SELECT indexname, tablename
FROM pg_indexes
WHERE tablename IN ('users', 'invite_codes', 'token_ledger', 'token_logs')
ORDER BY tablename, indexname;
```

## 回滚方案

如果需要回滚迁移，可以执行以下 SQL（**谨慎使用，会删除数据**）：

```sql
-- 删除新表（会删除所有数据）
DROP TABLE IF EXISTS token_logs CASCADE;
DROP TABLE IF EXISTS token_ledger CASCADE;
DROP TABLE IF EXISTS invite_codes CASCADE;

-- 删除 users 表的新字段（需要先删除依赖）
-- 注意：如果 token_balance 中有数据，需要先备份
ALTER TABLE users DROP COLUMN IF EXISTS token_updated_at;
ALTER TABLE users DROP COLUMN IF EXISTS token_balance;
ALTER TABLE users DROP COLUMN IF EXISTS role;

-- 删除索引
DROP INDEX IF EXISTS idx_users_role;
```

## 常见问题

### Q: 迁移脚本执行失败怎么办？

A: 
1. 检查 PostgreSQL 版本（建议 12+）
2. 检查是否有足够的权限（需要 CREATE TABLE, ALTER TABLE 权限）
3. 查看错误消息，可能是某个表/字段已存在（这是正常的，脚本会跳过）

### Q: 如果 token_logs 表已存在但没有 assistant_name 字段？

A: 迁移脚本会自动检测并添加该字段。如果手动添加：

```sql
ALTER TABLE token_logs ADD COLUMN assistant_name VARCHAR(128);
```

### Q: 迁移后如何验证功能？

A: 
1. 测试邀请码兑换功能
2. 测试 AI 聊天功能（应该会记录 token_logs）
3. 检查用户 profile 中的 token_balance 是否正确显示

## 注意事项

1. **备份数据**：迁移前务必备份数据库
2. **测试环境**：建议先在测试环境执行迁移，验证无误后再在生产环境执行
3. **停机时间**：迁移脚本执行时间很短（通常 < 1 秒），但建议在低峰期执行
4. **数据迁移**：如果 SQLite 中有现有数据需要迁移到 PostgreSQL，需要单独的数据迁移脚本

## 后续步骤

迁移完成后：

1. 更新应用配置，确保连接到 PostgreSQL 数据库
2. 测试邀请码功能
3. 测试 AI 聊天功能（验证 token 扣减和日志记录）
4. 监控数据库性能（新索引应该能保证查询性能）

## 相关文件

- `migrate_token_system_postgres_complete.sql` - 完整的 PostgreSQL 迁移脚本
- `migrate_add_invite_token_system.py` - Python 迁移脚本（SQLite）
- `migrate_add_token_logs_table.py` - TokenLog 表迁移脚本（SQLite）
- `migrate_add_assistant_name_to_token_logs.py` - assistant_name 字段迁移脚本（SQLite）
