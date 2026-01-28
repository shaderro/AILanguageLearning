# 在 PostgreSQL 中添加邀请码的指南

## 快速方法（推荐）

### 在 pgAdmin 中执行

1. **打开 Query Tool**
   - 在 pgAdmin 中，右键点击你的数据库
   - 选择 `Query Tool`

2. **执行脚本**
   - 点击 `Open File`（或按 `Ctrl+O`）
   - 选择 `add_invite_codes_to_postgres.sql` 文件
   - 点击 `Execute`（或按 `F5`）

3. **查看结果**
   - 在 `Data Output` 标签页中查看插入的邀请码
   - 确认所有5个邀请码都已成功添加

## 邀请码列表

以下邀请码将被添加到数据库：

1. **JHDKCNTG** - 1,000,000 tokens (100 积分)
2. **NHUB46HU** - 1,000,000 tokens (100 积分)
3. **G3BJPX3H** - 1,000,000 tokens (100 积分)
4. **83CP37W6** - 1,000,000 tokens (100 积分)
5. **S7U5ZGNK** - 1,000,000 tokens (100 积分)

**特点：**
- ✅ 状态：`active`（可用）
- ✅ 无限期限：`expires_at = NULL`
- ✅ 每个邀请码只能被一个用户兑换一次

## 两种脚本说明

### 1. `add_invite_codes_to_postgres.sql`（简单版本）

**特点：**
- 使用 `INSERT ... ON CONFLICT DO NOTHING`
- 如果邀请码已存在，自动跳过（不会报错）
- 执行速度快

**适用场景：**
- 快速添加邀请码
- 不确定邀请码是否已存在

### 2. `add_invite_codes_to_postgres_safe.sql`（安全版本）

**特点：**
- 先检查哪些邀请码已存在
- 只插入不存在的邀请码
- 显示详细的执行日志
- 更详细的验证查询

**适用场景：**
- 需要查看详细的执行过程
- 需要确认哪些邀请码已存在

## 手动执行 SQL（如果不想用文件）

在 Query Tool 中直接粘贴以下 SQL：

```sql
INSERT INTO invite_codes (code, token_grant, status, created_at, expires_at, note)
VALUES 
    ('JHDKCNTG', 1000000, 'active', CURRENT_TIMESTAMP, NULL, '批量添加 - 无限期限'),
    ('NHUB46HU', 1000000, 'active', CURRENT_TIMESTAMP, NULL, '批量添加 - 无限期限'),
    ('G3BJPX3H', 1000000, 'active', CURRENT_TIMESTAMP, NULL, '批量添加 - 无限期限'),
    ('83CP37W6', 1000000, 'active', CURRENT_TIMESTAMP, NULL, '批量添加 - 无限期限'),
    ('S7U5ZGNK', 1000000, 'active', CURRENT_TIMESTAMP, NULL, '批量添加 - 无限期限')
ON CONFLICT (code) DO NOTHING;
```

## 验证邀请码

执行后，运行以下查询验证：

```sql
SELECT 
    code,
    token_grant,
    ROUND(token_grant / 10000.0, 0) AS points,
    status,
    created_at,
    expires_at,
    CASE 
        WHEN expires_at IS NULL THEN '无限期限'
        ELSE '有期限'
    END AS expiry_status
FROM invite_codes
WHERE code IN ('JHDKCNTG', 'NHUB46HU', 'G3BJPX3H', '83CP37W6', 'S7U5ZGNK')
ORDER BY code;
```

## 注意事项

1. **唯一性约束**：`code` 字段有唯一约束，如果邀请码已存在，插入会失败（使用 `ON CONFLICT DO NOTHING` 可以避免错误）

2. **大小写**：邀请码在数据库中存储为大写，但用户输入时可以不区分大小写（后端会自动转换）

3. **状态**：新添加的邀请码状态为 `active`，可以立即使用

4. **兑换限制**：每个邀请码只能被一个用户兑换一次，兑换后状态会变为 `redeemed`

5. **无限期限**：`expires_at = NULL` 表示邀请码永不过期

## 常见问题

### Q: 如果邀请码已存在怎么办？

A: 使用 `ON CONFLICT DO NOTHING` 的脚本会自动跳过已存在的邀请码，不会报错。

### Q: 如何查看所有邀请码？

A: 执行以下查询：
```sql
SELECT * FROM invite_codes ORDER BY created_at DESC;
```

### Q: 如何查看已使用的邀请码？

A: 执行以下查询：
```sql
SELECT * FROM invite_codes WHERE status = 'redeemed' ORDER BY redeemed_at DESC;
```

### Q: 如何禁用某个邀请码？

A: 执行以下更新：
```sql
UPDATE invite_codes SET status = 'disabled' WHERE code = 'JHDKCNTG';
```
