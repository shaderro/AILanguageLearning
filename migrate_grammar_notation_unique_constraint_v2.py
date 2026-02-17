#!/usr/bin/env python3
"""
迁移 GrammarNotation 表的唯一约束（重建表方式）
将唯一约束从 (user_id, text_id, sentence_id) 改为 (user_id, text_id, sentence_id, grammar_id)
以支持同一句子有多个不同的语法知识点

注意：SQLite 不支持直接修改表结构中的唯一约束，需要重建表
"""

import sqlite3
import os
import sys

def migrate_db(db_path):
    """迁移单个数据库"""
    if not os.path.exists(db_path):
        print(f"⚠️  数据库文件不存在: {db_path}")
        return False
    
    print(f"\n🔄 开始迁移: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. 检查当前表结构
        cursor.execute("PRAGMA table_info(grammar_notations)")
        columns = cursor.fetchall()
        print(f"📋 当前表结构: {len(columns)} 列")
        
        # 2. 检查是否存在旧的唯一约束（通过检查表定义）
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='grammar_notations'")
        table_sql = cursor.fetchone()
        needs_rebuild = False
        
        if table_sql and table_sql[0]:
            table_def = table_sql[0]
            print(f"📋 当前表定义: {table_def[:200]}...")
            
            # 检查唯一约束是否包含 grammar_id
            if 'UNIQUE' in table_def:
                # 提取 UNIQUE 约束部分
                unique_part = table_def.split('UNIQUE')[1].split(')')[0] if 'UNIQUE' in table_def else ''
                if 'grammar_id' not in unique_part:
                    print(f"🔧 检测到旧唯一约束（不包含 grammar_id），需要重建表")
                    needs_rebuild = True
                else:
                    print(f"✅ 唯一约束已包含 grammar_id，无需迁移")
                    return True
            else:
                # 检查是否有唯一索引
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND name='uq_grammar_notation'")
                index_sql = cursor.fetchone()
                if index_sql and index_sql[0]:
                    index_def = index_sql[0]
                    print(f"📋 当前唯一索引定义: {index_def}")
                    if 'grammar_id' not in index_def:
                        print(f"🔧 检测到旧唯一索引（不包含 grammar_id），需要重建")
                        needs_rebuild = True
                    else:
                        print(f"✅ 唯一索引已包含 grammar_id，无需迁移")
                        return True
                else:
                    print(f"⚠️  未找到唯一约束或索引，创建新的")
                    needs_rebuild = True
        else:
            print(f"⚠️  无法获取表定义")
            needs_rebuild = True
        
        if needs_rebuild:
            print(f"\n🔧 开始重建表...")
            
            # 3. 备份现有数据
            cursor.execute("SELECT * FROM grammar_notations")
            existing_data = cursor.fetchall()
            print(f"📋 备份了 {len(existing_data)} 条现有数据")
            
            # 4. 删除旧表
            cursor.execute("DROP TABLE IF EXISTS grammar_notations_old")
            cursor.execute("ALTER TABLE grammar_notations RENAME TO grammar_notations_old")
            print(f"✅ 已重命名旧表为 grammar_notations_old")
            
            # 5. 创建新表（包含新的唯一约束）
            cursor.execute("""
                CREATE TABLE grammar_notations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    text_id INTEGER NOT NULL,
                    sentence_id INTEGER NOT NULL,
                    grammar_id INTEGER,
                    marked_token_ids TEXT NOT NULL DEFAULT '[]',
                    created_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (text_id, sentence_id) REFERENCES sentences(text_id, sentence_id) ON DELETE CASCADE,
                    FOREIGN KEY (grammar_id) REFERENCES grammar_rules(rule_id) ON DELETE CASCADE,
                    UNIQUE(user_id, text_id, sentence_id, grammar_id)
                )
            """)
            print(f"✅ 已创建新表（包含新的唯一约束）")
            
            # 6. 恢复数据
            if existing_data:
                # 获取列名
                cursor.execute("PRAGMA table_info(grammar_notations_old)")
                old_columns = [col[1] for col in cursor.fetchall()]
                print(f"📋 旧表列: {old_columns}")
                
                # 插入数据
                placeholders = ','.join(['?' for _ in old_columns])
                insert_sql = f"INSERT INTO grammar_notations ({','.join(old_columns)}) VALUES ({placeholders})"
                cursor.executemany(insert_sql, existing_data)
                print(f"✅ 已恢复 {len(existing_data)} 条数据")
            
            # 7. 删除旧表
            cursor.execute("DROP TABLE grammar_notations_old")
            print(f"✅ 已删除旧表")
        
        # 8. 确保唯一索引存在（作为额外保障）
        cursor.execute("DROP INDEX IF EXISTS uq_grammar_notation")
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_grammar_notation 
            ON grammar_notations(user_id, text_id, sentence_id, grammar_id)
        """)
        print(f"✅ 已创建/更新唯一索引")
        
        # 9. 验证迁移结果
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='grammar_notations'")
        new_table_sql = cursor.fetchone()
        if new_table_sql and new_table_sql[0]:
            if 'UNIQUE(user_id, text_id, sentence_id, grammar_id)' in new_table_sql[0] or \
               'UNIQUE (user_id, text_id, sentence_id, grammar_id)' in new_table_sql[0]:
                print(f"✅ 验证通过：新表定义包含 grammar_id 的唯一约束")
            else:
                print(f"⚠️  警告：新表定义可能不包含 grammar_id 的唯一约束")
                print(f"📋 新表定义: {new_table_sql[0][:300]}...")
        
        conn.commit()
        print(f"✅ 迁移完成: {db_path}")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        # 尝试恢复
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='grammar_notations_old'")
            if cursor.fetchone():
                print(f"🔄 尝试恢复旧表...")
                cursor.execute("DROP TABLE IF EXISTS grammar_notations")
                cursor.execute("ALTER TABLE grammar_notations_old RENAME TO grammar_notations")
                conn.commit()
                print(f"✅ 已恢复旧表")
        except Exception as restore_error:
            print(f"❌ 恢复失败: {restore_error}")
        return False
    finally:
        conn.close()

def main():
    """主函数"""
    print("=" * 60)
    print("GrammarNotation 唯一约束迁移脚本（重建表方式）")
    print("=" * 60)
    
    # 获取项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 要迁移的数据库列表
    db_files = [
        os.path.join(script_dir, "database_system", "data_storage", "data", "dev.db"),
        os.path.join(script_dir, "database_system", "data_storage", "data", "language_learning.db"),
        os.path.join(script_dir, "database_system", "data_storage", "data", "test.db"),
    ]
    
    success_count = 0
    for db_path in db_files:
        if migrate_db(db_path):
            success_count += 1
    
    print(f"\n{'=' * 60}")
    print(f"迁移完成: {success_count}/{len(db_files)} 个数据库")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()

