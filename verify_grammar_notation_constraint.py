#!/usr/bin/env python3
"""验证 GrammarNotation 表的唯一约束是否正确"""

import sqlite3
import os

def verify_db(db_path):
    """验证单个数据库"""
    if not os.path.exists(db_path):
        print(f"⚠️  数据库文件不存在: {db_path}")
        return False
    
    print(f"\n🔍 验证: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. 检查表定义
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='grammar_notations'")
        table_sql = cursor.fetchone()
        if table_sql and table_sql[0]:
            table_def = table_sql[0]
            if 'UNIQUE(user_id, text_id, sentence_id, grammar_id)' in table_def or \
               'UNIQUE (user_id, text_id, sentence_id, grammar_id)' in table_def:
                print(f"✅ 表定义包含正确的唯一约束（包含 grammar_id）")
            else:
                print(f"❌ 表定义不包含正确的唯一约束")
                print(f"📋 表定义: {table_def}")
                return False
        
        # 2. 检查唯一索引
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND name='uq_grammar_notation'")
        index_sql = cursor.fetchone()
        if index_sql and index_sql[0]:
            index_def = index_sql[0]
            if 'grammar_id' in index_def:
                print(f"✅ 唯一索引包含 grammar_id")
            else:
                print(f"❌ 唯一索引不包含 grammar_id")
                print(f"📋 索引定义: {index_def}")
                return False
        
        # 3. 测试插入多个 grammar notations（相同句子，不同 grammar_id）
        cursor.execute("SELECT COUNT(*) FROM grammar_notations")
        before_count = cursor.fetchone()[0]
        print(f"📋 当前 grammar_notations 数量: {before_count}")
        
        # 尝试插入测试数据（如果不存在）
        test_user_id = 999999
        test_text_id = 999999
        test_sentence_id = 999999
        
        # 清理测试数据
        cursor.execute("DELETE FROM grammar_notations WHERE user_id = ? AND text_id = ? AND sentence_id = ?",
                      (test_user_id, test_text_id, test_sentence_id))
        
        # 插入第一个 grammar notation
        try:
            cursor.execute("""
                INSERT INTO grammar_notations (user_id, text_id, sentence_id, grammar_id, marked_token_ids, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (test_user_id, test_text_id, test_sentence_id, 1, '[]'))
            print(f"✅ 成功插入第一个 grammar notation (grammar_id=1)")
        except Exception as e:
            print(f"❌ 插入第一个 grammar notation 失败: {e}")
            return False
        
        # 插入第二个 grammar notation（相同句子，不同 grammar_id）
        try:
            cursor.execute("""
                INSERT INTO grammar_notations (user_id, text_id, sentence_id, grammar_id, marked_token_ids, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (test_user_id, test_text_id, test_sentence_id, 2, '[]'))
            print(f"✅ 成功插入第二个 grammar notation (grammar_id=2)")
        except Exception as e:
            print(f"❌ 插入第二个 grammar notation 失败: {e}")
            conn.rollback()
            return False
        
        # 验证两个记录都存在
        cursor.execute("SELECT COUNT(*) FROM grammar_notations WHERE user_id = ? AND text_id = ? AND sentence_id = ?",
                      (test_user_id, test_text_id, test_sentence_id))
        count = cursor.fetchone()[0]
        if count == 2:
            print(f"✅ 验证通过：同一句子可以有两个不同的 grammar notations")
        else:
            print(f"❌ 验证失败：期望 2 条记录，实际 {count} 条")
            conn.rollback()
            return False
        
        # 清理测试数据
        cursor.execute("DELETE FROM grammar_notations WHERE user_id = ? AND text_id = ? AND sentence_id = ?",
                      (test_user_id, test_text_id, test_sentence_id))
        conn.commit()
        print(f"✅ 已清理测试数据")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

def main():
    """主函数"""
    print("=" * 60)
    print("GrammarNotation 唯一约束验证脚本")
    print("=" * 60)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "database_system", "data_storage", "data", "dev.db")
    
    if verify_db(db_path):
        print(f"\n✅ 验证通过：唯一约束已正确更新")
    else:
        print(f"\n❌ 验证失败：唯一约束可能未正确更新")

if __name__ == "__main__":
    main()

