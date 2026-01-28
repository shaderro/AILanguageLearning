-- ============================================================
-- 查看所有用户信息（不包括密码）
-- 在 pgAdmin 的 Query Tool 中执行此查询
-- ============================================================

-- 查看所有用户的基本信息（不包括密码哈希）
SELECT 
    user_id,
    email,
    role,
    token_balance,
    ROUND(token_balance / 10000.0, 1) AS points,
    created_at,
    token_updated_at,
    -- 注意：password_hash 字段包含加密后的密码，不能直接查看明文密码
    CASE 
        WHEN password_hash IS NOT NULL THEN '***已设置密码***'
        ELSE '未设置密码'
    END AS password_status
FROM users
ORDER BY user_id;

-- ============================================================
-- 查看用户数量统计
-- ============================================================

SELECT 
    COUNT(*) AS total_users,
    COUNT(CASE WHEN email IS NOT NULL THEN 1 END) AS users_with_email,
    COUNT(CASE WHEN role = 'admin' THEN 1 END) AS admin_count,
    COUNT(CASE WHEN role IS NULL OR role = '' OR role != 'admin' THEN 1 END) AS user_count
FROM users;
