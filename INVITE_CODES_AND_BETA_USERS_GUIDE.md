# 内测用户与邀请码管理指南

本文档说明如何添加、查看、管理真实的内测用户和邀请码。

---

## 一、线上版本已创建的邀请码

根据项目中的 `add_invite_codes_to_postgres.sql` 和 `add_invite_codes_to_postgres_safe.sql` 脚本，**初始创建的一批邀请码**为：

| 序号 | 邀请码   | Token 额度     | 积分 | 备注       |
|------|----------|----------------|------|------------|
| 1    | JHDKCNTG | 1,000,000      | 100  | 无限期限   |
| 2    | NHUB46HU | 1,000,000      | 100  | 无限期限   |
| 3    | G3BJPX3H | 1,000,000      | 100  | 无限期限   |
| 4    | 83CP37W6 | 1,000,000      | 100  | 无限期限   |
| 5    | S7U5ZGNK | 1,000,000      | 100  | 无限期限   |

> 若之后通过 `generate_invite_codes.py` 或 SQL 手动添加过其他邀请码，以实际数据库为准。

---

## 二、如何查看哪些邀请码已被使用？

邀请码数据存储在数据库的 `invite_codes` 表中。需要通过**连接线上 PostgreSQL 数据库**来查询。

### 方法 1：用 pgAdmin 或 psql 执行 SQL

1. **连接线上数据库**  
   在 pgAdmin（或 psql）中配置并连接到生产环境使用的 PostgreSQL 实例。

2. **执行以下 SQL**（在 Query Tool 中）：

```sql
-- 查看所有邀请码及使用情况
SELECT 
    code,
    token_grant,
    status,
    redeemed_by_user_id,
    redeemed_at,
    created_at,
    note
FROM invite_codes
ORDER BY status, redeemed_at DESC NULLS FIRST;

-- 仅查看已使用的邀请码（含兑换用户）
SELECT 
    ic.code,
    ic.token_grant,
    ic.redeemed_at,
    u.user_id,
    u.email,
    u.token_balance
FROM invite_codes ic
LEFT JOIN users u ON ic.redeemed_by_user_id = u.user_id
WHERE ic.status = 'redeemed'
ORDER BY ic.redeemed_at DESC;

-- 统计汇总
SELECT 
    status,
    COUNT(*) AS count
FROM invite_codes
GROUP BY status;
```

- `status = 'active'`：未使用  
- `status = 'redeemed'`：已使用  
- `redeemed_by_user_id`：兑换该邀请码的用户 ID

### 方法 2：使用项目自带脚本（推荐）

项目根目录有 `list_invite_codes.py`，可快速列出所有邀请码及使用状态：

```bash
# 连接线上库
ENV=production python list_invite_codes.py

# Windows PowerShell
$env:ENV = "production"
python list_invite_codes.py
```

输出包含：邀请码、token 额度、状态（可用/已使用/已禁用/已过期）、兑换用户邮箱、兑换时间等。

---

## 三、添加新邀请码

### 方法 A：使用 Python 脚本（推荐）

1. **配置环境**：确保 `.env` 中 `ENV` 和 `DATABASE_URL` 指向目标数据库（如 production）。

2. **运行脚本**：

```bash
python generate_invite_codes.py
```

- 默认生成 5 个邀请码，每个 1,000,000 token（100 积分）。  
- 脚本会自动选择当前环境（`ENV` 或环境变量），并写入对应数据库。

3. **自定义数量与额度**（需改脚本或加参数）：

可修改 `generate_invite_codes.py` 末尾：

```python
create_invite_codes(count=10, token_grant=500000)  # 10 个码，每个 50 万 token
```

### 方法 B：使用 SQL 直接插入

在 pgAdmin Query Tool 中执行：

```sql
INSERT INTO invite_codes (code, token_grant, status, created_at, expires_at, note)
VALUES 
    ('YOURCODE1', 1000000, 'active', CURRENT_TIMESTAMP, NULL, '内测用户 - 张三'),
    ('YOURCODE2', 1000000, 'active', CURRENT_TIMESTAMP, '2025-12-31 23:59:59', '内测用户 - 李四（有期限）')
ON CONFLICT (code) DO NOTHING;
```

- `code`：唯一，建议 8 位大写字母+数字。  
- `expires_at = NULL`：永不过期；有具体时间则在该时间后不可用。

---

## 四、查看内测用户（兑换过邀请码的用户）

### 1. 通过 SQL 查询

```sql
SELECT 
    u.user_id,
    u.email,
    u.role,
    u.token_balance,
    u.created_at,
    ic.code AS invite_code_used,
    ic.redeemed_at
FROM users u
INNER JOIN invite_codes ic ON ic.redeemed_by_user_id = u.user_id
ORDER BY ic.redeemed_at DESC;
```

### 2. 通过项目脚本

```bash
ENV=production python view_all_users.py
```

可查看所有用户（含 token 余额、角色等）。结合 `invite_codes` 的 `redeemed_by_user_id` 可筛选出内测用户。

### 3. 生产环境用户状态检查

```bash
ENV=production python check_production_user_status.py
```

会列出用户及其 token、角色等信息，方便判断哪些是内测用户。

---

## 五、管理邀请码

### 禁用某个邀请码

```sql
UPDATE invite_codes 
SET status = 'disabled' 
WHERE code = 'JHDKCNTG';
```

禁用后该码不可再兑换。

### 查看某邀请码是否已被使用

```sql
SELECT code, status, redeemed_by_user_id, redeemed_at 
FROM invite_codes 
WHERE code = 'JHDKCNTG';
```

### 批量查看可用 / 已用数量

```sql
SELECT 
    COUNT(*) FILTER (WHERE status = 'active') AS available,
    COUNT(*) FILTER (WHERE status = 'redeemed') AS used,
    COUNT(*) AS total
FROM invite_codes;
```

---

## 六、连接线上数据库的配置

### 1. 环境变量

在 `.env` 中设置（或部署平台的环境变量）：

```
ENV=production
DATABASE_URL=postgresql://user:password@host:port/dbname
```

### 2. 本地连接线上库

- 确保 `DATABASE_URL` 指向线上 PostgreSQL。  
- 运行脚本时设置 `ENV=production`，例如：

```bash
# Windows PowerShell
$env:ENV = "production"
python generate_invite_codes.py

# Linux / macOS
ENV=production python generate_invite_codes.py
```

### 3. 安全注意

- 不要将 `DATABASE_URL`、密码等敏感信息提交到 Git。  
- 生产环境操作前建议先备份或做好回滚准备。

---

## 七、邀请码状态说明

| 状态       | 含义                         |
|------------|------------------------------|
| `active`   | 可用，可被兑换               |
| `disabled` | 已禁用，不可兑换             |
| `redeemed` | 已被某用户兑换               |
| `expired`  | 已过期（由 `expires_at` 决定）|

---

## 八、快速参考

| 操作                 | 方式 / 命令 |
|----------------------|-------------|
| 添加新邀请码         | `python generate_invite_codes.py` 或 SQL `INSERT` |
| 查看所有邀请码及状态 | `ENV=production python list_invite_codes.py` |
| 查看所有邀请码       | SQL: `SELECT * FROM invite_codes ORDER BY created_at DESC` |
| 查看已使用的邀请码   | SQL: `WHERE status = 'redeemed'` |
| 查看内测用户         | SQL: `users` JOIN `invite_codes` ON `redeemed_by_user_id` |
| 禁用邀请码           | SQL: `UPDATE invite_codes SET status = 'disabled' WHERE code = '...'` |
| 查看用户列表         | `python view_all_users.py`（设置 `ENV` 可查生产库） |
| 检查生产用户状态     | `python check_production_user_status.py`（需 `ENV=production`） |

---

## 九、常见问题

### Q1: 如何确认当前连接的是哪个数据库？

- 检查 `.env` 中 `ENV` 和 `DATABASE_URL`。  
- 在 `config.py` / 数据库配置里，`production` 使用 `DATABASE_URL`。

### Q2: 邀请码输入区分大小写吗？

不区分。后端会把邀请码统一转为大写再校验。

### Q3: 一个邀请码可以被多个用户使用吗？

不可以。每个邀请码只能被一个用户兑换一次，兑换后状态变为 `redeemed`。

### Q4: 如何给某个用户手动加 token？

需要直接操作 `users` 表或通过后台逻辑：

```sql
UPDATE users SET token_balance = token_balance + 1000000 WHERE user_id = 123;
```

并建议在 `token_ledger` 中记录相应变动，便于审计。
