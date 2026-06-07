#!/usr/bin/env python3
"""
清理 User 2 的 "Advanced English Grammar Structures" 文章的语法数据
恢复干净的测试环境
"""

import sqlite3
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(REPO_ROOT)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

def clean_grammar_data(db_path, user_id=2, text_title="Advanced English Grammar Structures"):
    """清理指定用户的指定文章的语法数据"""
    
    if not os.path.exists(db_path):
        print(f"⚠️  数据库文件不存在: {db_path}")
        return False
    
    print(f"\n🧹 开始清理: {db_path}")
    print(f"   用户ID: {user_id}")
    print(f"   文章标题: {text_title}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. 查找文章
        cursor.execute("""
            SELECT text_id, text_title, language 
            FROM original_texts 
            WHERE user_id = ? AND text_title LIKE ?
        """, (user_id, f"%{text_title}%"))
        
        articles = cursor.fetchall()
        if not articles:
            print(f"⚠️  未找到匹配的文章")
            return False
        
        print(f"\n📋 找到 {len(articles)} 篇文章:")
        for article in articles:
            text_id, title, language = article
            print(f"   - text_id: {text_id}, 标题: {title}, 语言: {language}")
        
        # 2. 对每篇文章进行清理
        total_cleaned = 0
        for article in articles:
            text_id, title, language = article
            print(f"\n🔧 清理文章: {title} (text_id={text_id})")
            
            # 2.1 查找该文章的所有 grammar notations
            cursor.execute("""
                SELECT COUNT(*) FROM grammar_notations 
                WHERE user_id = ? AND text_id = ?
            """, (user_id, text_id))
            notation_count = cursor.fetchone()[0]
            print(f"   📋 找到 {notation_count} 个 grammar notations")
            
            # 2.2 查找该文章的所有 grammar examples（通过 sentences）
            cursor.execute("""
                SELECT COUNT(*) FROM grammar_examples ge
                JOIN sentences s ON ge.text_id = s.text_id AND ge.sentence_id = s.sentence_id
                WHERE s.text_id = ?
            """, (text_id,))
            example_count = cursor.fetchone()[0]
            print(f"   📋 找到 {example_count} 个 grammar examples")
            
            # 2.3 查找该文章相关的 grammar rules（通过 grammar_examples）
            cursor.execute("""
                SELECT DISTINCT ge.rule_id 
                FROM grammar_examples ge
                JOIN sentences s ON ge.text_id = s.text_id AND ge.sentence_id = s.sentence_id
                WHERE s.text_id = ?
            """, (text_id,))
            rule_ids = [row[0] for row in cursor.fetchall()]
            print(f"   📋 找到 {len(rule_ids)} 个相关的 grammar rules: {rule_ids}")
            
            # 2.4 删除 grammar notations
            if notation_count > 0:
                cursor.execute("""
                    DELETE FROM grammar_notations 
                    WHERE user_id = ? AND text_id = ?
                """, (user_id, text_id))
                print(f"   ✅ 已删除 {notation_count} 个 grammar notations")
                total_cleaned += notation_count
            
            # 2.5 删除 grammar examples
            if example_count > 0:
                cursor.execute("""
                    DELETE FROM grammar_examples 
                    WHERE text_id = ?
                """, (text_id,))
                print(f"   ✅ 已删除 {example_count} 个 grammar examples")
                total_cleaned += example_count
            
            # 2.6 删除 grammar rules（如果它们没有其他 examples）
            if rule_ids:
                deleted_rules = []
                for rule_id in rule_ids:
                    # 检查该 rule 是否还有其他 examples
                    cursor.execute("""
                        SELECT COUNT(*) FROM grammar_examples 
                        WHERE rule_id = ?
                    """, (rule_id,))
                    remaining_examples = cursor.fetchone()[0]
                    
                    if remaining_examples == 0:
                        # 检查该 rule 是否属于当前用户
                        cursor.execute("""
                            SELECT user_id FROM grammar_rules 
                            WHERE rule_id = ?
                        """, (rule_id,))
                        rule_user = cursor.fetchone()
                        if rule_user and rule_user[0] == user_id:
                            cursor.execute("DELETE FROM grammar_rules WHERE rule_id = ?", (rule_id,))
                            deleted_rules.append(rule_id)
                            print(f"   ✅ 已删除 grammar rule: rule_id={rule_id} (没有其他 examples)")
                        else:
                            print(f"   ⏭️  跳过 grammar rule: rule_id={rule_id} (不属于当前用户或不存在)")
                    else:
                        print(f"   ⏭️  保留 grammar rule: rule_id={rule_id} (还有 {remaining_examples} 个其他 examples)")
                
                if deleted_rules:
                    print(f"   ✅ 总共删除了 {len(deleted_rules)} 个 grammar rules")
                    total_cleaned += len(deleted_rules)
        
        conn.commit()
        print(f"\n✅ 清理完成: 共清理 {total_cleaned} 条记录")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 清理失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

def main():
    """主函数"""
    print("=" * 60)
    print("清理 User 2 Advanced English Grammar Structures 语法数据")
    print("=" * 60)
    
    # 获取项目根目录
    script_dir = str(REPO_ROOT)
    
    # 清理 dev.db
    db_path = os.path.join(str(REPO_ROOT), "database_system", "data_storage", "data", "dev.db")
    
    if clean_grammar_data(db_path, user_id=2, text_title="Advanced English Grammar Structures"):
        print(f"\n✅ 清理完成")
    else:
        print(f"\n❌ 清理失败")
        sys.exit(1)

if __name__ == "__main__":
    main()

