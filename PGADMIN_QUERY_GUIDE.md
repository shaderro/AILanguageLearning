# 在 pgAdmin 中查询用户 role 和 status 的指南

## 快速查询：所有用户的 role 和 status

### 步骤 1: 打开 Query Tool

1. 在 pgAdmin 左侧对象浏览器中，找到并展开你的数据库
2. 右键点击数据库名称
3. 选择 `Query Tool`（查询工具）

### 步骤 2: 执行查询

在 Query Tool 的编辑器中，复制并粘贴以下 SQL 查询：

```sql
-- 查询所有用户的 role 和 status
SELECT 
    user_id,
    email,
    role,
    token_balance,
    ROUND(token_balance / 10000.0, 1) AS points,
    CASE 
        WHEN role = 'admin' THEN 'Admin (无限制)'
        WHEN role IS NULL OR role = '' THEN 'User (role为空，应视为user)'
        WHEN role != 'admin' THEN 'User (受限制)'
        ELSE 'Unknown'
    END AS role_status,
    CASE 
        WHEN token_balance IS NULL THEN 'Token为NULL'
        WHEN token_balance < 0 THEN 'Token为负数'
        WHEN token_balance < 1000 THEN '积分不足 (< 0.1)'
        WHEN token_balance >= 1000 THEN '积分充足 (>= 0.1)'
        ELSE 'Unknown'
    END AS token_status
FROM users
ORDER BY user_id;
```

### 步骤 3: 执行查询

1. 点击工具栏上的 `Execute` 按钮（或按 `F5`）
2. 查看结果在底部的 `Data Output` 标签页中

## 查询结果说明

查询结果包含以下列：

- **user_id**: 用户ID
- **email**: 用户邮箱
- **role**: 用户角色（'admin' 或 'user'）
- **token_balance**: Token 余额
- **points**: 积分（token_balance / 10000，保留1位小数）
- **role_status**: 角色状态说明
  - `Admin (无限制)` - admin 用户，不受 token 限制
  - `User (受限制)` - 普通用户，受 token 限制
  - `User (role为空，应视为user)` - role 字段为空，应视为普通用户
- **token_status**: Token 状态说明
  - `Token为NULL` - token_balance 为 NULL
  - `Token为负数` - token_balance < 0
  - `积分不足 (< 0.1)` - token_balance < 1000
  - `积分充足 (>= 0.1)` - token_balance >= 1000

## 其他有用的查询

### 1. 统计信息

```sql
SELECT 
    COUNT(*) AS total_users,
    COUNT(CASE WHEN role = 'admin' THEN 1 END) AS admin_count,
    COUNT(CASE WHEN role IS NULL OR role = '' OR role != 'admin' THEN 1 END) AS user_count,
    COUNT(CASE WHEN token_balance < 0 THEN 1 END) AS negative_balance_count,
    COUNT(CASE 
        WHEN (role IS NULL OR role = '' OR role != 'admin') 
        AND (token_balance IS NULL OR token_balance < 1000) 
        THEN 1 
    END) AS insufficient_count
FROM users;
```

### 2. 查找可能有问题的用户

```sql
-- 查找应该被阻止但仍可能使用的用户（非admin且积分不足）
SELECT 
    user_id,
    email,
    role,
    token_balance,
    ROUND(token_balance / 10000.0, 1) AS points,
    '应该被阻止' AS issue
FROM users
WHERE 
    (role IS NULL OR role = '' OR role != 'admin')
    AND (token_balance IS NULL OR token_balance < 1000)
ORDER BY user_id;
```

### 3. 按角色分组统计

```sql
SELECT 
    COALESCE(role, 'NULL') AS role_value,
    COUNT(*) AS user_count,
    MIN(token_balance) AS min_balance,
    MAX(token_balance) AS max_balance,
    AVG(token_balance) AS avg_balance
FROM users
GROUP BY role
ORDER BY role;
```

### 4. 检查特定用户（例如 user_id = 5）

```sql
SELECT 
    user_id,
    email,
    role,
    token_balance,
    ROUND(token_balance / 10000.0, 1) AS points,
    CASE 
        WHEN role = 'admin' THEN 'Admin (无限制，不受token限制)'
        ELSE 'User (受限制)'
    END AS status
FROM users
WHERE user_id = 5;
```

## 使用文件中的查询

你也可以直接打开项目根目录下的 `query_all_users_role_status.sql` 文件：

1. 在 Query Tool 中，点击 `Open File` 按钮（或按 `Ctrl+O`）
2. 选择 `query_all_users_role_status.sql` 文件
3. 点击 `Execute` 执行

## 注意事项

1. **Admin 用户不受限制**：如果 `role = 'admin'`，无论 token_balance 是多少，都可以使用 AI 功能
2. **Role 为 NULL 或空字符串**：应该被视为 'user'，受 token 限制
3. **Token 为负数**：UI 会显示为 0 积分，但后端允许负数（用于审计）

## 根据你的查询结果

你发现 user_id=5 是 admin，所以：
- ✅ **这是正常的**：admin 用户不受 token 限制
- ✅ **余额为 -5,167 是允许的**：admin 用户可以继续使用 AI 功能
- ✅ **不需要修复**：这是预期的行为

如果你想让 user_id=5 也受 token 限制，需要将其 role 改为 'user'：

```sql
UPDATE users 
SET role = 'user' 
WHERE user_id = 5;
```
