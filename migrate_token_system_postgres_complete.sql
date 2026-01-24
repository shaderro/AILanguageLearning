-- ============================================================
-- Migration: 完整的 Token 和邀请码系统迁移脚本
-- 数据库: PostgreSQL
-- 执行方式: 在 pgAdmin 中连接到生产数据库后执行此脚本
-- 
-- 迁移内容：
-- 1. users 表新增字段（role, token_balance, token_updated_at）
-- 2. 创建 invite_codes 表（一次性邀请码）
-- 3. 创建 token_ledger 表（token 账本）
-- 4. 创建 token_logs 表（token 使用日志）
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
-- 步骤 4: 创建 token_logs 表（token 使用日志）
-- ============================================================

CREATE TABLE IF NOT EXISTS token_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    total_tokens INTEGER NOT NULL,
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    model_name VARCHAR(64) NOT NULL,
    assistant_name VARCHAR(128),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS ix_token_logs_user_id ON token_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_token_logs_user_time ON token_logs(user_id, created_at);

-- 添加注释
COMMENT ON TABLE token_logs IS 'Token 使用日志表：记录每次 DeepSeek API 调用的真实 token 使用量，用于统计用户累计使用量和调试成本异常';
COMMENT ON COLUMN token_logs.total_tokens IS '本次 API 调用使用的 token 数量（从 response.usage.total_tokens 获取）';
COMMENT ON COLUMN token_logs.prompt_tokens IS 'Prompt tokens（用于详细记录）';
COMMENT ON COLUMN token_logs.completion_tokens IS 'Completion tokens（用于详细记录）';
COMMENT ON COLUMN token_logs.model_name IS '使用的模型名称（如 "deepseek-chat"）';
COMMENT ON COLUMN token_logs.assistant_name IS '调用的 SubAssistant 名称（如 "AnswerQuestionAssistant", "CheckIfGrammarRelevantAssistant" 等）';

-- ============================================================
-- 步骤 5: 如果 token_logs 表已存在，检查并添加 assistant_name 字段
-- ============================================================

DO $$
BEGIN
    -- 检查 token_logs 表是否存在
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'token_logs'
    ) THEN
        -- 检查 assistant_name 字段是否存在
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'token_logs' AND column_name = 'assistant_name'
        ) THEN
            ALTER TABLE token_logs ADD COLUMN assistant_name VARCHAR(128);
            RAISE NOTICE 'Added column: token_logs.assistant_name';
        ELSE
            RAISE NOTICE 'Column token_logs.assistant_name already exists, skipping';
        END IF;
    END IF;
END $$;

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
    
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'token_logs'
    ) THEN
        RAISE NOTICE '✓ token_logs table exists';
    ELSE
        RAISE WARNING '✗ token_logs table missing';
    END IF;
END $$;

-- 检查 token_logs 表的 assistant_name 字段
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'token_logs'
    ) THEN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'token_logs' AND column_name = 'assistant_name'
        ) THEN
            RAISE NOTICE '✓ token_logs.assistant_name column exists';
        ELSE
            RAISE WARNING '✗ token_logs.assistant_name column missing';
        END IF;
    END IF;
END $$;

-- ============================================================
-- Migration 完成
-- ============================================================

SELECT 'Migration completed successfully!' AS status;
