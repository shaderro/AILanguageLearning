#!/usr/bin/env python3
"""
迁移 GrammarNotation 表的唯一约束
将唯一约束从 (user_id, text_id, sentence_id) 改为 (user_id, text_id, sentence_id, grammar_id)
以支持同一句子有多个不同的语法知识点
"""

import sqlite3
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(REPO_ROOT)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

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
        
        # 2. 检查是否存在旧的唯一约束索引（不包含 grammar_id）
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='uq_grammar_notation'")
        old_index = cursor.fetchone()
        
        # 3. 检查是否存在新的唯一约束索引（包含 grammar_id）
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='uq_grammar_notation'")
        new_index = cursor.fetchone()
        
        # 4. 如果存在旧的唯一约束，需要先删除（SQLite 不支持直接修改）
        # 注意：SQLite 的唯一约束实际上是通过唯一索引实现的
        # 我们需要删除旧索引，然后创建新索引（使用相同的名称，以匹配模型定义）
        if old_index:
            print(f"🔍 找到旧的唯一约束索引: {old_index[0]}")
            # 先检查旧索引的定义
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND name='uq_grammar_notation'")
            old_sql = cursor.fetchone()
            if old_sql and old_sql[0]:
                print(f"📋 旧索引定义: {old_sql[0]}")
                # 检查是否包含 grammar_id
                if 'grammar_id' not in old_sql[0]:
                    print(f"🔧 旧索引不包含 grammar_id，需要更新")
                    # 删除旧索引
                    cursor.execute("DROP INDEX IF EXISTS uq_grammar_notation")
                    print(f"✅ 已删除旧的唯一约束索引")
                else:
                    print(f"✅ 旧索引已包含 grammar_id，无需更新")
                    return True
        
        # 5. 创建新的唯一约束索引（包含 grammar_id，使用与模型相同的名称）
        # SQLite 不支持直接修改唯一约束，需要创建唯一索引
        # 注意：grammar_id 可能为 NULL，SQLite 中 NULL != NULL，所以多个 NULL 值不会违反唯一约束
        # 但我们需要确保相同的非 NULL grammar_id 不能重复
        if not new_index or (old_index and 'grammar_id' not in (old_sql[0] if old_sql and old_sql[0] else '')):
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS uq_grammar_notation 
                ON grammar_notations(user_id, text_id, sentence_id, grammar_id)
            """)
            print(f"✅ 已创建/更新唯一约束索引（包含 grammar_id）")
        else:
            print(f"⏭️  唯一约束索引已存在且正确，跳过")
        
        # 6. 清理重复的索引（如果存在）
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='uq_grammar_notation_new'")
        duplicate_index = cursor.fetchone()
        if duplicate_index:
            cursor.execute("DROP INDEX IF EXISTS uq_grammar_notation_new")
            print(f"✅ 已删除重复的索引: uq_grammar_notation_new")
        
        # 7. 验证迁移结果
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'uq_grammar_notation%'")
        indexes = cursor.fetchall()
        print(f"📋 当前唯一约束索引: {[idx[0] for idx in indexes]}")
        
        conn.commit()
        print(f"✅ 迁移完成: {db_path}")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

def main():
    """主函数"""
    print("=" * 60)
    print("GrammarNotation 唯一约束迁移脚本")
    print("=" * 60)
    
    # 获取项目根目录
    script_dir = str(REPO_ROOT)
    
    # 要迁移的数据库列表
    db_files = [
        os.path.join(str(REPO_ROOT), "database_system", "data_storage", "data", "dev.db"),
        os.path.join(str(REPO_ROOT), "database_system", "data_storage", "data", "language_learning.db"),
        os.path.join(str(REPO_ROOT), "database_system", "data_storage", "data", "test.db"),
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

