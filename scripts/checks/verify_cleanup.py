#!/usr/bin/env python3
"""验证清理结果"""

import sqlite3
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(REPO_ROOT)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

def verify_cleanup(db_path, user_id=2, text_id=1771150777):
    """验证清理结果"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查 grammar notations
        cursor.execute("""
            SELECT COUNT(*) FROM grammar_notations 
            WHERE user_id = ? AND text_id = ?
        """, (user_id, text_id))
        notation_count = cursor.fetchone()[0]
        
        # 检查 grammar examples
        cursor.execute("""
            SELECT COUNT(*) FROM grammar_examples 
            WHERE text_id = ?
        """, (text_id,))
        example_count = cursor.fetchone()[0]
        
        print(f"📋 验证结果:")
        print(f"   - Grammar notations: {notation_count} 个")
        print(f"   - Grammar examples: {example_count} 个")
        
        if notation_count == 0 and example_count == 0:
            print(f"\n✅ 清理成功：该文章的所有语法数据已清空")
            return True
        else:
            print(f"\n⚠️  仍有残留数据")
            return False
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    script_dir = str(REPO_ROOT)
    db_path = os.path.join(str(REPO_ROOT), "database_system", "data_storage", "data", "dev.db")
    verify_cleanup(db_path)

