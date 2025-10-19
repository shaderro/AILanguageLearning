"""
数据库迁移脚本：为 asked_tokens 表添加 type 字段

此脚本执行以下操作：
1. 备份现有的 asked_tokens 数据
2. 删除旧的 asked_tokens 表
3. 创建新的 asked_tokens 表（包含 type 字段）
4. 恢复数据，为所有现有记录设置 type='token'

注意：SQLite 不支持直接修改列，所以需要重建表
"""

import sqlite3
from datetime import datetime
import os

def migrate_asked_tokens(db_path: str = "database_system/data_storage/data/dev.db"):
    """
    迁移 asked_tokens 表，添加 type 字段
    
    Args:
        db_path: 数据库文件路径
    """
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    print(f"🔄 开始迁移数据库: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 检查表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='asked_tokens'
        """)
        if not cursor.fetchone():
            print("⚠️ asked_tokens 表不存在，跳过迁移")
            conn.close()
            return True
        
        # 2. 检查是否已经有 type 字段
        cursor.execute("PRAGMA table_info(asked_tokens)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'type' in columns:
            print("✅ type 字段已存在，无需迁移")
            conn.close()
            return True
        
        print("📊 开始迁移...")
        
        # 3. 备份现有数据
        print("  - 备份现有数据...")
        cursor.execute("SELECT * FROM asked_tokens")
        old_data = cursor.fetchall()
        print(f"  - 找到 {len(old_data)} 条记录")
        
        # 4. 创建临时表
        print("  - 创建新表结构...")
        cursor.execute("""
            CREATE TABLE asked_tokens_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id VARCHAR(255) NOT NULL,
                text_id INTEGER NOT NULL,
                sentence_id INTEGER NOT NULL,
                sentence_token_id INTEGER,
                type VARCHAR(20) NOT NULL DEFAULT 'token',
                created_at DATETIME NOT NULL,
                FOREIGN KEY (text_id) REFERENCES original_texts(text_id) ON DELETE CASCADE,
                FOREIGN KEY (text_id, sentence_id) REFERENCES sentences(text_id, sentence_id) ON DELETE CASCADE,
                CONSTRAINT uq_asked_token_user_text_sentence_token_type 
                    UNIQUE (user_id, text_id, sentence_id, sentence_token_id, type)
            )
        """)
        
        # 5. 迁移数据（为所有现有记录设置 type='token'）
        print("  - 迁移数据并设置默认 type='token'...")
        for row in old_data:
            # 原表结构: id, user_id, text_id, sentence_id, sentence_token_id, created_at
            cursor.execute("""
                INSERT INTO asked_tokens_new 
                (id, user_id, text_id, sentence_id, sentence_token_id, type, created_at)
                VALUES (?, ?, ?, ?, ?, 'token', ?)
            """, row)
        
        # 6. 删除旧表
        print("  - 删除旧表...")
        cursor.execute("DROP TABLE asked_tokens")
        
        # 7. 重命名新表
        print("  - 重命名新表...")
        cursor.execute("ALTER TABLE asked_tokens_new RENAME TO asked_tokens")
        
        # 8. 提交更改
        conn.commit()
        print(f"✅ 迁移完成！共迁移 {len(old_data)} 条记录")
        
        # 9. 验证迁移
        cursor.execute("SELECT COUNT(*) FROM asked_tokens")
        new_count = cursor.fetchone()[0]
        print(f"✅ 验证：新表包含 {new_count} 条记录")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
            conn.close()
        return False


def verify_migration(db_path: str = "database_system/data_storage/data/dev.db"):
    """验证迁移结果"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表结构
        cursor.execute("PRAGMA table_info(asked_tokens)")
        columns = cursor.fetchall()
        
        print("\n📋 新表结构:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULLABLE'} DEFAULT={col[4]}")
        
        # 检查数据
        cursor.execute("SELECT COUNT(*), type FROM asked_tokens GROUP BY type")
        type_counts = cursor.fetchall()
        
        print("\n📊 按类型统计:")
        for count, type_val in type_counts:
            print(f"  - {type_val}: {count} 条记录")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("数据库迁移：为 asked_tokens 表添加 type 字段")
    print("=" * 60)
    print()
    
    # 执行迁移
    success = migrate_asked_tokens()
    
    if success:
        print()
        # 验证迁移结果
        verify_migration()
        print()
        print("=" * 60)
        print("✅ 迁移完成！")
        print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("❌ 迁移失败，请检查错误信息")
        print("=" * 60)


