#!/usr/bin/env python3
"""
数据库迁移脚本：为 sentences 表添加段落相关字段

新增字段：
- paragraph_id      INTEGER  可空
- is_new_paragraph  INTEGER/BOOLEAN  可空，默认 0

适用数据库：
- database_system/data_storage/data/dev.db
- database_system/data_storage/data/language_learning.db
- database_system/data_storage/data/test.db

说明：
- 仅在字段不存在时执行 ALTER TABLE
- 不修改已有数据
"""

import os
import sqlite3


DB_PATHS = [
    "database_system/data_storage/data/dev.db",               # 开发环境
    "database_system/data_storage/data/language_learning.db", # 生产环境/本地主库
    "database_system/data_storage/data/test.db",              # 测试环境
]


def ensure_sentences_columns(db_path: str) -> None:
    if not os.path.exists(db_path):
        print(f"⏭️  跳过不存在的数据库: {db_path}")
        return

    print("\n" + "=" * 60)
    print(f"📂 处理数据库: {db_path}")
    print("=" * 60)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 检查 sentences 表是否存在
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sentences'"
        )
        if not cursor.fetchone():
            print("⏭️  表 sentences 不存在，跳过")
            return

        # 获取现有字段
        cursor.execute("PRAGMA table_info(sentences)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 当前 sentences 表字段: {', '.join(columns)}")

        added = 0

        if "paragraph_id" not in columns:
            sql = "ALTER TABLE sentences ADD COLUMN paragraph_id INTEGER"
            print(f"➕ 执行: {sql}")
            cursor.execute(sql)
            added += 1
        else:
            print("⏭️  字段 paragraph_id 已存在，跳过")

        if "is_new_paragraph" not in columns:
            # SQLite 中 BOOLEAN 实际是整数存储，这里用 INTEGER，默认 0
            sql = "ALTER TABLE sentences ADD COLUMN is_new_paragraph INTEGER DEFAULT 0"
            print(f"➕ 执行: {sql}")
            cursor.execute(sql)
            added += 1
        else:
            print("⏭️  字段 is_new_paragraph 已存在，跳过")

        if added > 0:
            conn.commit()
            print(f"✅ 迁移完成，新增字段数: {added}")
        else:
            print("✅ 所有字段已存在，无需迁移")

        # 验证结果
        cursor.execute("PRAGMA table_info(sentences)")
        final_cols = [row[1] for row in cursor.fetchall()]
        print(f"📋 更新后的字段列表: {', '.join(final_cols)}")

    except sqlite3.Error as e:
        print(f"❌ 错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def main() -> None:
    for path in DB_PATHS:
        ensure_sentences_columns(path)

    print("\n" + "=" * 60)
    print("✅ 所有数据库 sentences 表段落字段迁移完成")
    print("=" * 60)


if __name__ == "__main__":
    main()


