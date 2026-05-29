-- pgAdmin / Render PostgreSQL：创建 article_segment_tasks（文章分页任务表）
-- 若表已存在可跳过；执行前请连接到生产库。

CREATE TABLE IF NOT EXISTS article_segment_tasks (
    id SERIAL PRIMARY KEY,
    text_id INTEGER NOT NULL REFERENCES original_texts (text_id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
    page_index INTEGER NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'processing',
    sentence_start_id INTEGER,
    sentence_end_id INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    CONSTRAINT uq_article_segment_task_text_page UNIQUE (text_id, page_index)
);

CREATE INDEX IF NOT EXISTS ix_article_segment_tasks_text_id
    ON article_segment_tasks (text_id);

CREATE INDEX IF NOT EXISTS ix_article_segment_tasks_user_id
    ON article_segment_tasks (user_id);

CREATE INDEX IF NOT EXISTS idx_article_segment_task_text_status
    ON article_segment_tasks (text_id, status);
