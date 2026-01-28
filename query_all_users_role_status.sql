-- ============================================================
-- 查询所有用户的 role 和 status
-- 在 pgAdmin 的 Query Tool 中执行此查询
-- ============================================================

-- 查询所有用户的详细信息，包括 role 和 status
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
        WHEN role = 'admin' THEN false
        WHEN role IS NULL OR role = '' OR role != 'admin' THEN 
            (token_balance IS NULL OR token_balance < 1000)
        ELSE false
    END AS should_be_blocked,
    CASE 
        WHEN token_balance IS NULL THEN 'Token为NULL'
        WHEN token_balance < 0 THEN 'Token为负数'
        WHEN token_balance < 1000 THEN '积分不足 (< 0.1)'
        WHEN token_balance >= 1000 THEN '积分充足 (>= 0.1)'
        ELSE 'Unknown'
    END AS token_status,
    created_at,
    token_updated_at
FROM users
ORDER BY user_id;

-- ============================================================
-- 统计信息
-- ============================================================

SELECT 
    COUNT(*) AS total_users,
    COUNT(CASE WHEN role = 'admin' THEN 1 END) AS admin_count,
    COUNT(CASE WHEN role IS NULL OR role = '' OR role != 'admin' THEN 1 END) AS user_count,
    COUNT(CASE WHEN token_balance < 0 THEN 1 END) AS negative_balance_count,
    COUNT(CASE 
        WHEN (role IS NULL OR role = '' OR role != 'admin') 
        AND (token_balance IS NULL OR token_balance < 1000) 
        THEN 1 
    END) AS insufficient_count,
    COUNT(CASE WHEN role = 'admin' THEN 1 END) AS admin_unlimited_count
FROM users;

-- ============================================================
-- 按角色分组统计
-- ============================================================

SELECT 
    COALESCE(role, 'NULL') AS role_value,
    COUNT(*) AS user_count,
    MIN(token_balance) AS min_balance,
    MAX(token_balance) AS max_balance,
    AVG(token_balance) AS avg_balance,
    SUM(CASE WHEN token_balance < 0 THEN 1 ELSE 0 END) AS negative_count,
    SUM(CASE WHEN token_balance < 1000 THEN 1 ELSE 0 END) AS insufficient_count
FROM users
GROUP BY role
ORDER BY role;
