-- ============================================================
-- PostgreSQL Database Migration Script
-- Purpose: Migrate production PostgreSQL database to new schema
-- Usage: Open in pgAdmin Query Tool and execute
-- ============================================================

-- IMPORTANT NOTES:
-- 1. Backup database before execution!
-- 2. Recommended to execute during maintenance window
-- 3. Verify data integrity after migration

BEGIN;

-- ============================================================
-- 1. grammar_rules table: Add new columns
-- ============================================================

-- Check if table exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'grammar_rules'
    ) THEN
        RAISE EXCEPTION 'Table grammar_rules does not exist!';
    END IF;
END $$;

-- Add display_name column
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'grammar_rules' 
        AND column_name = 'display_name'
    ) THEN
        ALTER TABLE grammar_rules 
        ADD COLUMN display_name VARCHAR(255) NULL;
        
        RAISE NOTICE 'Column added: display_name';
    ELSE
        RAISE NOTICE 'Column display_name already exists, skipping';
    END IF;
END $$;

-- Add canonical_category column
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'grammar_rules' 
        AND column_name = 'canonical_category'
    ) THEN
        ALTER TABLE grammar_rules 
        ADD COLUMN canonical_category VARCHAR(255) NULL;
        
        RAISE NOTICE 'Column added: canonical_category';
    ELSE
        RAISE NOTICE 'Column canonical_category already exists, skipping';
    END IF;
END $$;

-- Add canonical_subtype column
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'grammar_rules' 
        AND column_name = 'canonical_subtype'
    ) THEN
        ALTER TABLE grammar_rules 
        ADD COLUMN canonical_subtype VARCHAR(255) NULL;
        
        RAISE NOTICE 'Column added: canonical_subtype';
    ELSE
        RAISE NOTICE 'Column canonical_subtype already exists, skipping';
    END IF;
END $$;

-- Add canonical_function column
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'grammar_rules' 
        AND column_name = 'canonical_function'
    ) THEN
        ALTER TABLE grammar_rules 
        ADD COLUMN canonical_function VARCHAR(255) NULL;
        
        RAISE NOTICE 'Column added: canonical_function';
    ELSE
        RAISE NOTICE 'Column canonical_function already exists, skipping';
    END IF;
END $$;

-- Add canonical_key column
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'grammar_rules' 
        AND column_name = 'canonical_key'
    ) THEN
        ALTER TABLE grammar_rules 
        ADD COLUMN canonical_key VARCHAR(255) NULL;
        
        RAISE NOTICE 'Column added: canonical_key';
    ELSE
        RAISE NOTICE 'Column canonical_key already exists, skipping';
    END IF;
END $$;

-- ============================================================
-- 2. sentences table: Add paragraph-related columns
-- ============================================================

-- Check if table exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'sentences'
    ) THEN
        RAISE NOTICE 'Table sentences does not exist, skipping paragraph columns migration';
        RETURN;
    END IF;
END $$;

-- Add paragraph_id column
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'sentences' 
        AND column_name = 'paragraph_id'
    ) THEN
        ALTER TABLE sentences 
        ADD COLUMN paragraph_id INTEGER NULL;
        
        RAISE NOTICE 'Column added: paragraph_id';
    ELSE
        RAISE NOTICE 'Column paragraph_id already exists, skipping';
    END IF;
END $$;

-- Add is_new_paragraph column
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'sentences' 
        AND column_name = 'is_new_paragraph'
    ) THEN
        ALTER TABLE sentences 
        ADD COLUMN is_new_paragraph BOOLEAN DEFAULT FALSE NULL;
        
        RAISE NOTICE 'Column added: is_new_paragraph';
    ELSE
        RAISE NOTICE 'Column is_new_paragraph already exists, skipping';
    END IF;
END $$;

-- ============================================================
-- 3. Data backfill (optional)
-- ============================================================

-- Backfill rule_name to display_name (if display_name is NULL)
UPDATE grammar_rules 
SET display_name = rule_name 
WHERE display_name IS NULL 
  AND rule_name IS NOT NULL;

-- Show update statistics
DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Backfilled % records for display_name', updated_count;
END $$;

-- ============================================================
-- 4. Verify migration results
-- ============================================================

-- Verify grammar_rules table structure
DO $$
DECLARE
    col_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO col_count
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'grammar_rules'
      AND column_name IN ('display_name', 'canonical_category', 'canonical_subtype', 'canonical_function', 'canonical_key');
    
    IF col_count = 5 THEN
        RAISE NOTICE 'grammar_rules table migration successful, all new columns exist';
    ELSE
        RAISE WARNING 'grammar_rules table migration incomplete, found % new columns', col_count;
    END IF;
END $$;

-- Verify sentences table structure
DO $$
DECLARE
    col_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO col_count
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'sentences'
      AND column_name IN ('paragraph_id', 'is_new_paragraph');
    
    IF col_count = 2 THEN
        RAISE NOTICE 'sentences table migration successful, all new columns exist';
    ELSIF col_count = 0 THEN
        RAISE NOTICE 'sentences table does not exist or no migration needed';
    ELSE
        RAISE WARNING 'sentences table migration incomplete, found % new columns', col_count;
    END IF;
END $$;

-- Show final message
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Migration completed! Please check messages above to confirm results.';
    RAISE NOTICE '========================================';
END $$;

COMMIT;

-- ============================================================
-- 5. Optional verification queries (uncomment to use)
-- ============================================================

-- View grammar_rules table structure
-- SELECT 
--     column_name, 
--     data_type, 
--     is_nullable,
--     column_default
-- FROM information_schema.columns
-- WHERE table_schema = 'public'
--   AND table_name = 'grammar_rules'
-- ORDER BY ordinal_position;

-- View sentences table structure
-- SELECT 
--     column_name, 
--     data_type, 
--     is_nullable,
--     column_default
-- FROM information_schema.columns
-- WHERE table_schema = 'public'
--   AND table_name = 'sentences'
-- ORDER BY ordinal_position;

-- Statistics
-- SELECT 
--     COUNT(*) as total_rules,
--     COUNT(display_name) as rules_with_display_name,
--     COUNT(canonical_key) as rules_with_canonical_key
-- FROM grammar_rules;
