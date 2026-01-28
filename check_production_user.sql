-- ============================================================
-- 检查生产环境 PostgreSQL 数据库中用户的角色和 token 状态
-- 用于排查为什么余额小于0还能使用AI功能
-- ============================================================

-- 1. 检查所有用户的角色和 token 状态
SELECT 
    user_id,
    email,
    role,
    token_balance,
    ROUND(token_balance / 10000.0, 1) AS points,
    CASE 
        WHEN role = 'admin' THEN 'Admin (无限制)'
        WHEN role IS NULL OR role = '' THEN 'User (role为空，应视为user)'
        WHEN token_balance IS NULL THEN 'User (token_balance为NULL，应视为0)'
        WHEN token_balance < 1000 THEN 'User (积分不足 < 0.1)'
        ELSE 'User (正常)'
    END AS status,
    CASE 
        WHEN role = 'admin' THEN false
        WHEN role IS NULL OR role = '' OR role != 'admin' THEN 
            (token_balance IS NULL OR token_balance < 1000)
        ELSE false
    END AS should_be_blocked
FROM users
ORDER BY user_id;

-- 2. 特别检查 user_id = 5（从日志中看到的用户）
SELECT 
    user_id,
    email,
    role,
    token_balance,
    ROUND(token_balance / 10000.0, 1) AS points,
    -- 检查 role 的各种可能值
    role IS NULL AS role_is_null,
    role = '' AS role_is_empty,
    role = 'admin' AS role_is_admin,
    role = 'user' AS role_is_user,
    -- 检查 token_balance
    token_balance IS NULL AS token_balance_is_null,
    token_balance < 0 AS token_balance_is_negative,
    token_balance < 1000 AS token_balance_insufficient,
    -- 判断逻辑
    (role IS NULL OR role = '' OR role != 'admin') AS is_not_admin,
    (token_balance IS NULL OR token_balance < 1000) AS is_insufficient,
    -- 最终判断：是否应该被阻止
    (role IS NULL OR role = '' OR role != 'admin') 
    AND (token_balance IS NULL OR token_balance < 1000) AS should_be_blocked
FROM users
WHERE user_id = 5;

-- 3. 统计信息
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

-- 4. 查找可能有问题的用户（应该被阻止但仍能使用的）
SELECT 
    user_id,
    email,
    role,
    token_balance,
    ROUND(token_balance / 10000.0, 1) AS points,
    '应该被阻止但仍可能可以使用' AS issue
FROM users
WHERE 
    (role IS NULL OR role = '' OR role != 'admin')
    AND (token_balance IS NULL OR token_balance < 1000)
ORDER BY user_id;
