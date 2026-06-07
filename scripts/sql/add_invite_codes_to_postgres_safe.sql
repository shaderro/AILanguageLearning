-- ============================================================
-- 安全添加邀请码到 PostgreSQL 数据库（带检查）
-- 在 pgAdmin 的 Query Tool 中执行此脚本
-- 
-- 特点：
-- - 先检查邀请码是否已存在
-- - 如果不存在才插入
-- - 显示详细的执行结果
-- ============================================================

-- 邀请码列表：
-- 1. JHDKCNTG - 1,000,000 tokens (100 积分)
-- 2. NHUB46HU - 1,000,000 tokens (100 积分)
-- 3. G3BJPX3H - 1,000,000 tokens (100 积分)
-- 4. 83CP37W6 - 1,000,000 tokens (100 积分)
-- 5. S7U5ZGNK - 1,000,000 tokens (100 积分)
-- 无限次数 无限期限

-- ============================================================
-- 步骤 1: 检查哪些邀请码已存在
-- ============================================================

DO $$
DECLARE
    existing_codes TEXT[];
    code_to_check TEXT;
    codes_to_add TEXT[] := ARRAY['JHDKCNTG', 'NHUB46HU', 'G3BJPX3H', '83CP37W6', 'S7U5ZGNK'];
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE '检查邀请码是否已存在...';
    RAISE NOTICE '============================================================';
    
    -- 检查每个邀请码
    FOREACH code_to_check IN ARRAY codes_to_add
    LOOP
        IF EXISTS (SELECT 1 FROM invite_codes WHERE code = code_to_check) THEN
            RAISE NOTICE '⚠️  邀请码 % 已存在，将跳过', code_to_check;
            existing_codes := array_append(existing_codes, code_to_check);
        ELSE
            RAISE NOTICE '✅ 邀请码 % 不存在，将添加', code_to_check;
        END IF;
    END LOOP;
    
    RAISE NOTICE '============================================================';
END $$;

-- ============================================================
-- 步骤 2: 插入不存在的邀请码
-- ============================================================

-- 插入 JHDKCNTG
INSERT INTO invite_codes (code, token_grant, status, created_at, expires_at, note)
SELECT 'JHDKCNTG', 1000000, 'active', CURRENT_TIMESTAMP, NULL, '批量添加 - 无限期限'
WHERE NOT EXISTS (SELECT 1 FROM invite_codes WHERE code = 'JHDKCNTG');

-- 插入 NHUB46HU
INSERT INTO invite_codes (code, token_grant, status, created_at, expires_at, note)
SELECT 'NHUB46HU', 1000000, 'active', CURRENT_TIMESTAMP, NULL, '批量添加 - 无限期限'
WHERE NOT EXISTS (SELECT 1 FROM invite_codes WHERE code = 'NHUB46HU');

-- 插入 G3BJPX3H
INSERT INTO invite_codes (code, token_grant, status, created_at, expires_at, note)
SELECT 'G3BJPX3H', 1000000, 'active', CURRENT_TIMESTAMP, NULL, '批量添加 - 无限期限'
WHERE NOT EXISTS (SELECT 1 FROM invite_codes WHERE code = 'G3BJPX3H');

-- 插入 83CP37W6
INSERT INTO invite_codes (code, token_grant, status, created_at, expires_at, note)
SELECT '83CP37W6', 1000000, 'active', CURRENT_TIMESTAMP, NULL, '批量添加 - 无限期限'
WHERE NOT EXISTS (SELECT 1 FROM invite_codes WHERE code = '83CP37W6');

-- 插入 S7U5ZGNK
INSERT INTO invite_codes (code, token_grant, status, created_at, expires_at, note)
SELECT 'S7U5ZGNK', 1000000, 'active', CURRENT_TIMESTAMP, NULL, '批量添加 - 无限期限'
WHERE NOT EXISTS (SELECT 1 FROM invite_codes WHERE code = 'S7U5ZGNK');

-- ============================================================
-- 步骤 3: 验证插入结果
-- ============================================================

SELECT 
    code,
    token_grant,
    ROUND(token_grant / 10000.0, 0) AS points,
    status,
    created_at,
    expires_at,
    redeemed_by_user_id,
    redeemed_at,
    note,
    CASE 
        WHEN expires_at IS NULL THEN '无限期限'
        ELSE '有期限'
    END AS expiry_status
FROM invite_codes
WHERE code IN ('JHDKCNTG', 'NHUB46HU', 'G3BJPX3H', '83CP37W6', 'S7U5ZGNK')
ORDER BY code;

-- ============================================================
-- 步骤 4: 显示统计信息
-- ============================================================

SELECT 
    COUNT(*) AS total_invite_codes,
    COUNT(CASE WHEN status = 'active' THEN 1 END) AS active_count,
    COUNT(CASE WHEN status = 'redeemed' THEN 1 END) AS redeemed_count,
    COUNT(CASE WHEN redeemed_by_user_id IS NOT NULL THEN 1 END) AS used_count,
    COUNT(CASE WHEN expires_at IS NULL THEN 1 END) AS unlimited_expiry_count
FROM invite_codes;
