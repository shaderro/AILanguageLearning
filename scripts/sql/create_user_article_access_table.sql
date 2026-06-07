-- 创建 user_article_access 表的 SQL 脚本
-- 可以在 Render 的 PostgreSQL 数据库控制台直接执行

-- 检查表是否存在，如果不存在则创建
CREATE TABLE IF NOT EXISTS user_article_access (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    text_id INTEGER NOT NULL,
    last_opened_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL,
    CONSTRAINT fk_user_article_access_user 
        FOREIGN KEY (user_id) 
        REFERENCES users(user_id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_user_article_access_text 
        FOREIGN KEY (text_id) 
        REFERENCES original_texts(text_id) 
        ON DELETE CASCADE,
    CONSTRAINT uq_user_article_access 
        UNIQUE (user_id, text_id)
);

-- 创建索引以提升查询性能
CREATE INDEX IF NOT EXISTS idx_user_article_access_user_id 
    ON user_article_access(user_id);

CREATE INDEX IF NOT EXISTS idx_user_article_access_text_id 
    ON user_article_access(text_id);

CREATE INDEX IF NOT EXISTS idx_user_article_access_last_opened 
    ON user_article_access(last_opened_at DESC);

-- 验证表是否创建成功
SELECT 
    table_name, 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns
WHERE table_name = 'user_article_access'
ORDER BY ordinal_position;
