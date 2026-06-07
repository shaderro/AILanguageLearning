-- ============================================================
-- Migration: 添加邀请码和 Token 系统相关表结构
-- 数据库: PostgreSQL
-- 执行方式: 在 pgAdmin 中连接到生产数据库后执行此脚本
-- ============================================================

-- ============================================================
-- 步骤 1: 给 users 表添加新字段
-- ============================================================

-- 添加 role 字段（角色：admin/user）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'role'
    ) THEN
        ALTER TABLE users ADD COLUMN role VARCHAR(32) NOT NULL DEFAULT 'user';
        RAISE NOTICE 'Added column: users.role';
    ELSE
        RAISE NOTICE 'Column users.role already exists, skipping';
    END IF;
END $$;

-- 添加 token_balance 字段（当前 token 余额）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'token_balance'
    ) THEN
        ALTER TABLE users ADD COLUMN token_balance BIGINT NOT NULL DEFAULT 0;
        RAISE NOTICE 'Added column: users.token_balance';
    ELSE
        RAISE NOTICE 'Column users.token_balance already exists, skipping';
    END IF;
END $$;

-- 添加 token_updated_at 字段（最近一次余额变动时间）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'token_updated_at'
    ) THEN
        ALTER TABLE users ADD COLUMN token_updated_at TIMESTAMP;
        RAISE NOTICE 'Added column: users.token_updated_at';
    ELSE
        RAISE NOTICE 'Column users.token_updated_at already exists, skipping';
    END IF;
END $$;

-- 创建 role 索引（如果不存在）
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- ============================================================
-- 步骤 2: 创建 invite_codes 表（一次性邀请码）
-- ============================================================

CREATE TABLE IF NOT EXISTS invite_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(64) NOT NULL UNIQUE,
    token_grant BIGINT NOT NULL DEFAULT 1000000,
    status VARCHAR(16) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    redeemed_by_user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    redeemed_at TIMESTAMP,
    note VARCHAR(255)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_invite_codes_status ON invite_codes(status);
CREATE INDEX IF NOT EXISTS idx_invite_codes_redeemed_by_user_id ON invite_codes(redeemed_by_user_id);

-- 添加注释
COMMENT ON TABLE invite_codes IS '一次性邀请码表：每个邀请码只能被一个用户兑换一次，固定发放 1,000,000 token';
COMMENT ON COLUMN invite_codes.code IS '邀请码文本（建议存储时统一为大写）';
COMMENT ON COLUMN invite_codes.token_grant IS '兑换时发放的 token 数量（默认 1,000,000）';
COMMENT ON COLUMN invite_codes.status IS '状态：active（可用）、disabled（禁用）、redeemed（已兑换）、expired（已过期）';
COMMENT ON COLUMN invite_codes.redeemed_by_user_id IS '兑换此邀请码的用户 ID（单用户生效的关键字段）';

-- ============================================================
-- 步骤 3: 创建 token_ledger 表（token 账本）
-- ============================================================

CREATE TABLE IF NOT EXISTS token_ledger (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    delta BIGINT NOT NULL,
    reason VARCHAR(32) NOT NULL,
    ref_type VARCHAR(32),
    ref_id VARCHAR(128),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    idempotency_key VARCHAR(128) UNIQUE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_token_ledger_user_id ON token_ledger(user_id);
CREATE INDEX IF NOT EXISTS idx_token_ledger_user_time ON token_ledger(user_id, created_at);

-- 添加注释
COMMENT ON TABLE token_ledger IS 'Token 账本：记录所有 token 增减的审计日志，用于余额回算和并发安全';
COMMENT ON COLUMN token_ledger.delta IS 'token 变动量：正数为发放（如 +1000000），负数为消耗（如 -1）';
COMMENT ON COLUMN token_ledger.reason IS '变动原因：invite_grant（邀请码发放）、ai_usage（AI调用消耗）、admin_adjust（管理员调整）、refund（退款）';
COMMENT ON COLUMN token_ledger.idempotency_key IS '幂等键：防止网络重试导致重复扣费/重复发放（唯一约束）';

-- ============================================================
-- 验证迁移结果
-- ============================================================

-- 检查 users 表新字段
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'role'
    ) THEN
        RAISE NOTICE '✓ users.role column exists';
    ELSE
        RAISE WARNING '✗ users.role column missing';
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'token_balance'
    ) THEN
        RAISE NOTICE '✓ users.token_balance column exists';
    ELSE
        RAISE WARNING '✗ users.token_balance column missing';
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'token_updated_at'
    ) THEN
        RAISE NOTICE '✓ users.token_updated_at column exists';
    ELSE
        RAISE WARNING '✗ users.token_updated_at column missing';
    END IF;
END $$;

-- 检查新表
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'invite_codes'
    ) THEN
        RAISE NOTICE '✓ invite_codes table exists';
    ELSE
        RAISE WARNING '✗ invite_codes table missing';
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'token_ledger'
    ) THEN
        RAISE NOTICE '✓ token_ledger table exists';
    ELSE
        RAISE WARNING '✗ token_ledger table missing';
    END IF;
END $$;

-- ============================================================
-- Migration 完成
-- ============================================================

SELECT 'Migration completed successfully!' AS status;
