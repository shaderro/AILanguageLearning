#!/usr/bin/env python3
"""
清理脚本：清除 User2 的所有 vocab 和 grammar 数据，只保留原始文章数据

执行步骤：
1. 备份当前数据库
2. 连接数据库
3. 删除 User2 的所有：
   - VocabExpression（词汇）
   - GrammarRule（语法规则）
   - VocabNotation（词汇标注）
   - GrammarNotation（语法标注）
   - AskedToken（已询问的 token 标记）
4. 保留 OriginalText（文章数据）
5. 验证清理结果
"""

import sys
import os
import shutil
import argparse
from datetime import datetime

# 添加路径
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, BACKEND_DIR)

from database_system.database_manager import DatabaseManager
from database_system.data_storage.config.config import DB_FILES
from sqlalchemy import text


def backup_database(db_path):
    """备份数据库"""
    if os.path.exists(db_path):
        backup_path = db_path.replace('.db', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
        shutil.copy2(db_path, backup_path)
        print(f"✅ 数据库已备份到: {backup_path}")
        return backup_path
    return None


def clear_user2_vocab_grammar(environment, db_path, user_id=2):
    """清除 User2 的所有 vocab 和 grammar 数据"""
    print(f"\n📋 清理 {environment} 环境数据库...")
    print(f"   📁 数据库路径: {db_path}")
    print(f"   👤 用户ID: {user_id}")
    
    # 1. 检查数据库文件是否存在
    if not os.path.exists(db_path):
        print(f"   ⚠️  数据库文件不存在: {db_path}")
        return False
    
    # 2. 备份数据库
    backup_path = backup_database(db_path)
    
    # 3. 连接数据库
    try:
        db_manager = DatabaseManager(environment)
        engine = db_manager.get_engine()
        session = db_manager.get_session()
    except Exception as e:
        print(f"   ❌ 连接数据库失败: {e}")
        return False
    
    try:
        # 4. 检查表是否存在
        from sqlalchemy import inspect
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        
        deleted_counts = {}
        
        # 5. 删除 VocabNotation（词汇标注）
        if 'vocab_notations' in table_names:
            vocab_notation_count = session.execute(text("""
                SELECT COUNT(*) FROM vocab_notations 
                WHERE user_id = :user_id
            """), {"user_id": user_id}).fetchone()[0]
            
            if vocab_notation_count > 0:
                session.execute(text("""
                    DELETE FROM vocab_notations 
                    WHERE user_id = :user_id
                """), {"user_id": user_id})
                session.commit()
                deleted_counts['vocab_notations'] = vocab_notation_count
                print(f"   ✅ 删除了 {vocab_notation_count} 条词汇标注记录")
            else:
                print(f"   ℹ️  没有找到 User {user_id} 的词汇标注记录")
        
        # 6. 删除 GrammarNotation（语法标注）
        if 'grammar_notations' in table_names:
            grammar_notation_count = session.execute(text("""
                SELECT COUNT(*) FROM grammar_notations 
                WHERE user_id = :user_id
            """), {"user_id": user_id}).fetchone()[0]
            
            if grammar_notation_count > 0:
                session.execute(text("""
                    DELETE FROM grammar_notations 
                    WHERE user_id = :user_id
                """), {"user_id": user_id})
                session.commit()
                deleted_counts['grammar_notations'] = grammar_notation_count
                print(f"   ✅ 删除了 {grammar_notation_count} 条语法标注记录")
            else:
                print(f"   ℹ️  没有找到 User {user_id} 的语法标注记录")
        
        # 7. 删除 AskedToken（已询问的 token 标记）
        if 'asked_tokens' in table_names:
            asked_token_count = session.execute(text("""
                SELECT COUNT(*) FROM asked_tokens 
                WHERE user_id = :user_id
            """), {"user_id": user_id}).fetchone()[0]
            
            if asked_token_count > 0:
                session.execute(text("""
                    DELETE FROM asked_tokens 
                    WHERE user_id = :user_id
                """), {"user_id": user_id})
                session.commit()
                deleted_counts['asked_tokens'] = asked_token_count
                print(f"   ✅ 删除了 {asked_token_count} 条已询问 token 记录")
            else:
                print(f"   ℹ️  没有找到 User {user_id} 的已询问 token 记录")
        
        # 8. 删除 VocabExpressionExample（词汇例句）- 通过关联的 vocab_id 删除
        if 'vocab_expression_examples' in table_names:
            vocab_example_count = session.execute(text("""
                SELECT COUNT(*) FROM vocab_expression_examples 
                WHERE vocab_id IN (
                    SELECT vocab_id FROM vocab_expressions WHERE user_id = :user_id
                )
            """), {"user_id": user_id}).fetchone()[0]
            
            if vocab_example_count > 0:
                session.execute(text("""
                    DELETE FROM vocab_expression_examples 
                    WHERE vocab_id IN (
                        SELECT vocab_id FROM vocab_expressions WHERE user_id = :user_id
                    )
                """), {"user_id": user_id})
                session.commit()
                deleted_counts['vocab_expression_examples'] = vocab_example_count
                print(f"   ✅ 删除了 {vocab_example_count} 条词汇例句记录")
            else:
                print(f"   ℹ️  没有找到 User {user_id} 的词汇例句记录")
        
        # 9. 删除 GrammarExample（语法例句）- 通过关联的 rule_id 删除
        if 'grammar_examples' in table_names:
            grammar_example_count = session.execute(text("""
                SELECT COUNT(*) FROM grammar_examples 
                WHERE rule_id IN (
                    SELECT rule_id FROM grammar_rules WHERE user_id = :user_id
                )
            """), {"user_id": user_id}).fetchone()[0]
            
            if grammar_example_count > 0:
                session.execute(text("""
                    DELETE FROM grammar_examples 
                    WHERE rule_id IN (
                        SELECT rule_id FROM grammar_rules WHERE user_id = :user_id
                    )
                """), {"user_id": user_id})
                session.commit()
                deleted_counts['grammar_examples'] = grammar_example_count
                print(f"   ✅ 删除了 {grammar_example_count} 条语法例句记录")
            else:
                print(f"   ℹ️  没有找到 User {user_id} 的语法例句记录")
        
        # 10. 删除 VocabExpression（词汇）
        if 'vocab_expressions' in table_names:
            vocab_count = session.execute(text("""
                SELECT COUNT(*) FROM vocab_expressions 
                WHERE user_id = :user_id
            """), {"user_id": user_id}).fetchone()[0]
            
            if vocab_count > 0:
                session.execute(text("""
                    DELETE FROM vocab_expressions 
                    WHERE user_id = :user_id
                """), {"user_id": user_id})
                session.commit()
                deleted_counts['vocab_expressions'] = vocab_count
                print(f"   ✅ 删除了 {vocab_count} 条词汇记录")
            else:
                print(f"   ℹ️  没有找到 User {user_id} 的词汇记录")
        
        # 11. 删除 GrammarRule（语法规则）
        if 'grammar_rules' in table_names:
            grammar_count = session.execute(text("""
                SELECT COUNT(*) FROM grammar_rules 
                WHERE user_id = :user_id
            """), {"user_id": user_id}).fetchone()[0]
            
            if grammar_count > 0:
                session.execute(text("""
                    DELETE FROM grammar_rules 
                    WHERE user_id = :user_id
                """), {"user_id": user_id})
                session.commit()
                deleted_counts['grammar_rules'] = grammar_count
                print(f"   ✅ 删除了 {grammar_count} 条语法规则记录")
            else:
                print(f"   ℹ️  没有找到 User {user_id} 的语法规则记录")
        
        # 12. 验证清理结果
        print(f"\n   🔍 验证清理结果...")
        verification_passed = True
        
        if 'vocab_expressions' in table_names:
            remaining_vocab = session.execute(text("""
                SELECT COUNT(*) FROM vocab_expressions 
                WHERE user_id = :user_id
            """), {"user_id": user_id}).fetchone()[0]
            if remaining_vocab > 0:
                print(f"   ⚠️  仍有 {remaining_vocab} 条词汇记录未删除")
                verification_passed = False
            else:
                print(f"   ✅ 词汇记录已全部清除")
        
        if 'grammar_rules' in table_names:
            remaining_grammar = session.execute(text("""
                SELECT COUNT(*) FROM grammar_rules 
                WHERE user_id = :user_id
            """), {"user_id": user_id}).fetchone()[0]
            if remaining_grammar > 0:
                print(f"   ⚠️  仍有 {remaining_grammar} 条语法规则记录未删除")
                verification_passed = False
            else:
                print(f"   ✅ 语法规则记录已全部清除")
        
        if 'vocab_notations' in table_names:
            remaining_vocab_notation = session.execute(text("""
                SELECT COUNT(*) FROM vocab_notations 
                WHERE user_id = :user_id
            """), {"user_id": user_id}).fetchone()[0]
            if remaining_vocab_notation > 0:
                print(f"   ⚠️  仍有 {remaining_vocab_notation} 条词汇标注记录未删除")
                verification_passed = False
            else:
                print(f"   ✅ 词汇标注记录已全部清除")
        
        if 'grammar_notations' in table_names:
            remaining_grammar_notation = session.execute(text("""
                SELECT COUNT(*) FROM grammar_notations 
                WHERE user_id = :user_id
            """), {"user_id": user_id}).fetchone()[0]
            if remaining_grammar_notation > 0:
                print(f"   ⚠️  仍有 {remaining_grammar_notation} 条语法标注记录未删除")
                verification_passed = False
            else:
                print(f"   ✅ 语法标注记录已全部清除")
        
        # 13. 检查文章数据是否保留
        if 'original_texts' in table_names:
            article_count = session.execute(text("""
                SELECT COUNT(*) FROM original_texts 
                WHERE user_id = :user_id
            """), {"user_id": user_id}).fetchone()[0]
            print(f"   ✅ 保留了 {article_count} 篇文章数据")
        
        # 14. 打印删除统计
        print(f"\n   📊 删除统计:")
        total_deleted = sum(deleted_counts.values())
        if total_deleted > 0:
            for table_name, count in deleted_counts.items():
                print(f"      - {table_name}: {count} 条")
            print(f"   📈 总计删除: {total_deleted} 条记录")
        else:
            print(f"      ℹ️  没有找到需要删除的记录")
        
        return verification_passed
            
    except Exception as e:
        session.rollback()
        print(f"   ❌ {environment} 环境清理失败: {e}")
        if backup_path:
            print(f"   💾 可以从备份恢复: {backup_path}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


def main():
    # 设置 Windows 控制台编码
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='清除 User2 的所有 vocab 和 grammar 数据')
    parser.add_argument('--yes', '-y', action='store_true', help='跳过确认，直接执行')
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("清理脚本：清除 User2 的所有 vocab 和 grammar 数据")
    print("="*60)
    print("\n警告：此操作将永久删除 User2 的所有词汇和语法数据！")
    print("   文章数据将被保留。")
    print("\n" + "="*60)
    
    # 确认操作
    if not args.yes:
        try:
            confirm = input("\n确认继续？(yes/no): ").strip().lower()
            if confirm not in ['yes', 'y']:
                print("操作已取消")
                return
        except (EOFError, KeyboardInterrupt):
            print("\n操作已取消")
            return
    else:
        print("\n使用 --yes 参数，跳过确认，直接执行...")
    
    # 清理所有环境的数据库
    environments = [
        ('development', DB_FILES['dev']),
        ('production', DB_FILES['prod']),
    ]
    
    success_count = 0
    total_tasks = len(environments)
    
    for env, db_path in environments:
        if clear_user2_vocab_grammar(env, db_path, user_id=2):
            success_count += 1
    
    print("\n" + "="*60)
    if success_count == total_tasks:
        print("✅ 所有清理完成！")
    else:
        print(f"⚠️  部分清理完成 ({success_count}/{total_tasks})")
    print("="*60)
    print("\n下一步：")
    print("1. 验证 User2 的 vocab 和 grammar 数据已清除")
    print("2. 验证 User2 的文章数据已保留")
    print("3. 测试 User2 的干净测试环境")


if __name__ == "__main__":
    main()

