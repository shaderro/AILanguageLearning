-- ============================================================================
-- PostgreSQL Migration Script for pgAdmin
-- Update GrammarNotation Unique Constraint
-- ============================================================================
-- 
-- 目的：修改 grammar_notations 表的唯一约束，将 grammar_id 加入约束中
-- 效果：允许同一句子有多个不同的语法知识点（只要 grammar_id 不同）
-- 
-- 执行前请务必备份数据库！
-- 
-- 使用方法：
-- 1. 在 pgAdmin 中连接到目标数据库
-- 2. 打开 Query Tool (Tools -> Query Tool)
-- 3. 复制粘贴本脚本
-- 4. 点击 Execute (F5) 执行
-- ============================================================================

-- 开始事务（确保原子性）
BEGIN;

-- ============================================================================
-- Step 1: 检查当前约束状态
-- ============================================================================
DO $$
DECLARE
    constraint_exists BOOLEAN;
    constraint_includes_grammar_id BOOLEAN;
    constraint_name TEXT;
BEGIN
    -- 查找现有的唯一约束
    SELECT EXISTS (
        SELECT 1 
        FROM pg_constraint 
        WHERE conrelid = 'grammar_notations'::regclass
        AND contype = 'u'  -- unique constraint
        AND (
            conname LIKE '%grammar_notation%' 
            OR conname LIKE '%uq_grammar%'
        )
    ) INTO constraint_exists;
    
    IF constraint_exists THEN
        -- 检查约束是否包含 grammar_id
        SELECT EXISTS (
            SELECT 1 
            FROM pg_constraint c
            JOIN pg_attribute a ON a.attrelid = c.conrelid 
                AND a.attnum = ANY(c.conkey) 
                AND a.attname = 'grammar_id'
            WHERE c.conrelid = 'grammar_notations'::regclass
            AND c.contype = 'u'
        ) INTO constraint_includes_grammar_id;
        
        -- 获取约束名称
        SELECT conname INTO constraint_name
        FROM pg_constraint
        WHERE conrelid = 'grammar_notations'::regclass
        AND contype = 'u'
        LIMIT 1;
        
        RAISE NOTICE '当前约束状态: 存在 = %, 包含 grammar_id = %, 约束名称 = %', 
            constraint_exists, constraint_includes_grammar_id, constraint_name;
    ELSE
        RAISE NOTICE '当前约束状态: 不存在唯一约束';
    END IF;
END $$;

-- ============================================================================
-- Step 2: 删除旧的唯一约束（如果存在且不包含 grammar_id）
-- ============================================================================
DO $$
DECLARE
    constraint_name TEXT;
    constraint_includes_grammar_id BOOLEAN;
BEGIN
    -- 查找现有的唯一约束名称
    SELECT conname INTO constraint_name
    FROM pg_constraint
    WHERE conrelid = 'grammar_notations'::regclass
    AND contype = 'u'
    LIMIT 1;
    
    IF constraint_name IS NOT NULL THEN
        -- 检查约束是否包含 grammar_id
        SELECT EXISTS (
            SELECT 1 
            FROM pg_constraint c
            JOIN pg_attribute a ON a.attrelid = c.conrelid 
                AND a.attnum = ANY(c.conkey) 
                AND a.attname = 'grammar_id'
            WHERE c.conname = constraint_name
            AND c.conrelid = 'grammar_notations'::regclass
        ) INTO constraint_includes_grammar_id;
        
        -- 如果约束存在但不包含 grammar_id，则删除它
        IF NOT constraint_includes_grammar_id THEN
            EXECUTE format('ALTER TABLE grammar_notations DROP CONSTRAINT IF EXISTS %I', constraint_name);
            RAISE NOTICE '已删除旧约束: %', constraint_name;
        ELSE
            RAISE NOTICE '约束已包含 grammar_id，跳过删除步骤: %', constraint_name;
        END IF;
    ELSE
        RAISE NOTICE '未找到现有唯一约束，跳过删除步骤';
    END IF;
END $$;

-- ============================================================================
-- Step 3: 创建新的唯一约束（包含 grammar_id）
-- ============================================================================
DO $$
DECLARE
    constraint_exists BOOLEAN;
BEGIN
    -- 检查新约束是否已存在
    SELECT EXISTS (
        SELECT 1 
        FROM pg_constraint 
        WHERE conrelid = 'grammar_notations'::regclass
        AND contype = 'u'
        AND conname = 'uq_grammar_notation'
    ) INTO constraint_exists;
    
    IF NOT constraint_exists THEN
        -- 检查是否包含 grammar_id 的约束已存在（可能名称不同）
        SELECT EXISTS (
            SELECT 1 
            FROM pg_constraint c
            JOIN pg_attribute a ON a.attrelid = c.conrelid 
                AND a.attnum = ANY(c.conkey) 
                AND a.attname = 'grammar_id'
            WHERE c.conrelid = 'grammar_notations'::regclass
            AND c.contype = 'u'
        ) INTO constraint_exists;
        
        IF NOT constraint_exists THEN
            ALTER TABLE grammar_notations 
            ADD CONSTRAINT uq_grammar_notation 
            UNIQUE (user_id, text_id, sentence_id, grammar_id);
            
            RAISE NOTICE '已创建新约束: uq_grammar_notation (user_id, text_id, sentence_id, grammar_id)';
        ELSE
            RAISE NOTICE '已存在包含 grammar_id 的唯一约束，跳过创建步骤';
        END IF;
    ELSE
        RAISE NOTICE '约束 uq_grammar_notation 已存在，跳过创建步骤';
    END IF;
END $$;

-- ============================================================================
-- Step 4: 验证迁移结果
-- ============================================================================
DO $$
DECLARE
    constraint_def TEXT;
    constraint_name TEXT;
BEGIN
    -- 查找包含 grammar_id 的唯一约束
    SELECT 
        conname,
        pg_get_constraintdef(oid) 
    INTO constraint_name, constraint_def
    FROM pg_constraint
    WHERE conrelid = 'grammar_notations'::regclass
    AND contype = 'u'
    AND EXISTS (
        SELECT 1 
        FROM pg_attribute a
        WHERE a.attrelid = pg_constraint.conrelid
        AND a.attnum = ANY(pg_constraint.conkey)
        AND a.attname = 'grammar_id'
    )
    LIMIT 1;
    
    IF constraint_name IS NOT NULL THEN
        RAISE NOTICE '✅ 迁移成功！';
        RAISE NOTICE '约束名称: %', constraint_name;
        RAISE NOTICE '约束定义: %', constraint_def;
    ELSE
        RAISE WARNING '⚠️ 未找到包含 grammar_id 的唯一约束，请检查迁移是否成功';
    END IF;
END $$;

-- ============================================================================
-- Step 5: 显示最终约束信息（用于确认）
-- ============================================================================
SELECT 
    conname AS constraint_name,
    pg_get_constraintdef(oid) AS constraint_definition,
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM pg_attribute a
            WHERE a.attrelid = c.conrelid
            AND a.attnum = ANY(c.conkey)
            AND a.attname = 'grammar_id'
        ) THEN '✅ 包含 grammar_id'
        ELSE '❌ 不包含 grammar_id'
    END AS status
FROM pg_constraint c
WHERE conrelid = 'grammar_notations'::regclass
AND contype = 'u'
ORDER BY conname;

-- ============================================================================
-- 提交事务
-- ============================================================================
-- 如果一切正常，取消下面的注释来提交事务
-- 如果发现问题，可以执行 ROLLBACK; 来回滚
COMMIT;

-- ============================================================================
-- 回滚命令（如果需要）
-- ============================================================================
-- 如果迁移出现问题，可以执行以下命令回滚：
-- ROLLBACK;
--
-- 或者手动删除新约束：
-- ALTER TABLE grammar_notations DROP CONSTRAINT IF EXISTS uq_grammar_notation;
-- ============================================================================

