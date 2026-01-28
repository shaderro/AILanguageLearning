-- ============================================================
-- 添加邀请码到 PostgreSQL 数据库
-- 在 pgAdmin 的 Query Tool 中执行此脚本
-- ============================================================

-- 邀请码列表：
-- 1. JHDKCNTG - 1,000,000 tokens (100 积分)
-- 2. NHUB46HU - 1,000,000 tokens (100 积分)
-- 3. G3BJPX3H - 1,000,000 tokens (100 积分)
-- 4. 83CP37W6 - 1,000,000 tokens (100 积分)
-- 5. S7U5ZGNK - 1,000,000 tokens (100 积分)
-- 无限次数 无限期限

-- ============================================================
-- 方法 1: 使用 INSERT ... ON CONFLICT（推荐）
-- 如果邀请码已存在，则跳过（不会报错）
-- ============================================================

INSERT INTO invite_codes (code, token_grant, status, created_at, expires_at, note)
VALUES 
    ('JHDKCNTG', 1000000, 'active', CURRENT_TIMESTAMP, NULL, '批量添加 - 无限期限'),
    ('NHUB46HU', 1000000, 'active', CURRENT_TIMESTAMP, NULL, '批量添加 - 无限期限'),
    ('G3BJPX3H', 1000000, 'active', CURRENT_TIMESTAMP, NULL, '批量添加 - 无限期限'),
    ('83CP37W6', 1000000, 'active', CURRENT_TIMESTAMP, NULL, '批量添加 - 无限期限'),
    ('S7U5ZGNK', 1000000, 'active', CURRENT_TIMESTAMP, NULL, '批量添加 - 无限期限')
ON CONFLICT (code) DO NOTHING;

-- ============================================================
-- 验证插入结果
-- ============================================================

SELECT 
    code,
    token_grant,
    status,
    created_at,
    expires_at,
    redeemed_by_user_id,
    note
FROM invite_codes
WHERE code IN ('JHDKCNTG', 'NHUB46HU', 'G3BJPX3H', '83CP37W6', 'S7U5ZGNK')
ORDER BY code;

-- ============================================================
-- 统计信息
-- ============================================================

SELECT 
    COUNT(*) AS total_invite_codes,
    COUNT(CASE WHEN status = 'active' THEN 1 END) AS active_count,
    COUNT(CASE WHEN status = 'redeemed' THEN 1 END) AS redeemed_count,
    COUNT(CASE WHEN redeemed_by_user_id IS NOT NULL THEN 1 END) AS used_count
FROM invite_codes;
