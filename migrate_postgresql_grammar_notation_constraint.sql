-- PostgreSQL Migration Script: Update GrammarNotation Unique Constraint
-- Add grammar_id to unique constraint to support multiple grammar points per sentence
-- This script is idempotent and can be run multiple times safely

DO $$
BEGIN
    -- Step 1: Drop the old unique constraint if it exists (without grammar_id)
    IF EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uq_grammar_notation' 
        AND conrelid = 'grammar_notations'::regclass
    ) THEN
        -- Check if the constraint includes grammar_id
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            JOIN pg_attribute a1 ON a1.attrelid = c.conrelid AND a1.attnum = ANY(c.conkey) AND a1.attname = 'grammar_id'
            WHERE c.conname = 'uq_grammar_notation' 
            AND c.conrelid = 'grammar_notations'::regclass
        ) THEN
            ALTER TABLE grammar_notations DROP CONSTRAINT IF EXISTS uq_grammar_notation;
            RAISE NOTICE 'Dropped old unique constraint uq_grammar_notation (without grammar_id)';
        ELSE
            RAISE NOTICE 'Unique constraint uq_grammar_notation already includes grammar_id, skipping';
        END IF;
    END IF;
    
    -- Step 2: Create the new unique constraint (with grammar_id) if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uq_grammar_notation' 
        AND conrelid = 'grammar_notations'::regclass
    ) THEN
        ALTER TABLE grammar_notations 
        ADD CONSTRAINT uq_grammar_notation 
        UNIQUE (user_id, text_id, sentence_id, grammar_id);
        RAISE NOTICE 'Created new unique constraint uq_grammar_notation (with grammar_id)';
    END IF;
    
    -- Step 3: Drop old unique index if it exists (without grammar_id)
    IF EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'uq_grammar_notation_old' 
        AND tablename = 'grammar_notations'
    ) THEN
        DROP INDEX IF EXISTS uq_grammar_notation_old;
        RAISE NOTICE 'Dropped old unique index uq_grammar_notation_old';
    END IF;
    
    RAISE NOTICE 'Migration completed successfully';
END $$;

-- Verification: Check the constraint
SELECT 
    conname AS constraint_name,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'grammar_notations'::regclass
AND conname = 'uq_grammar_notation';

