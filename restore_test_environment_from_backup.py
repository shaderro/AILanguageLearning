#!/usr/bin/env python3
"""
从备份文件恢复测试环境数据

从备份文件读取数据，并导入到新结构的表中（包含user_id和language字段）
"""

import sys
import os
import sqlite3
from datetime import datetime

# 添加路径
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, BACKEND_DIR)

from database_system.database_manager import DatabaseManager
from database_system.data_storage.config.config import DB_FILES
from sqlalchemy import inspect, text


def find_latest_backup():
    """查找最新的备份文件"""
    db_dir = os.path.dirname(DB_FILES['test'])
    backup_files = []
    
    for filename in os.listdir(db_dir):
        if filename.startswith('test_backup_') and filename.endswith('.db'):
            backup_path = os.path.join(db_dir, filename)
            backup_files.append((backup_path, os.path.getmtime(backup_path)))
    
    if not backup_files:
        return None
    
    # 按修改时间排序，返回最新的
    backup_files.sort(key=lambda x: x[1], reverse=True)
    return backup_files[0][0]


def restore_from_backup():
    """从备份文件恢复数据"""
    print("\n" + "="*60)
    print("从备份文件恢复测试环境数据")
    print("="*60)
    
    # 查找最新的备份文件
    backup_path = find_latest_backup()
    if not backup_path:
        print("❌ 找不到备份文件")
        return False
    
    print(f"📁 备份文件: {backup_path}")
    
    # 从备份文件读取数据
    print(f"\n📤 从备份文件读取数据...")
    backup_conn = sqlite3.connect(backup_path)
    backup_cursor = backup_conn.cursor()
    
    # 读取vocab数据
    backup_cursor.execute("SELECT * FROM vocab_expressions")
    vocab_rows = backup_cursor.fetchall()
    backup_cursor.execute("PRAGMA table_info(vocab_expressions)")
    vocab_columns = [col[1] for col in backup_cursor.fetchall()]
    
    vocabs = []
    for row in vocab_rows:
        vocab_dict = dict(zip(vocab_columns, row))
        vocabs.append(vocab_dict)
    
    print(f"   📚 词汇: {len(vocabs)} 条")
    
    # 读取grammar数据
    backup_cursor.execute("SELECT * FROM grammar_rules")
    grammar_rows = backup_cursor.fetchall()
    backup_cursor.execute("PRAGMA table_info(grammar_rules)")
    grammar_columns = [col[1] for col in backup_cursor.fetchall()]
    
    grammar_rules = []
    for row in grammar_rows:
        grammar_dict = dict(zip(grammar_columns, row))
        grammar_rules.append(grammar_dict)
    
    print(f"   📖 语法规则: {len(grammar_rules)} 条")
    
    backup_conn.close()
    
    if len(vocabs) == 0 and len(grammar_rules) == 0:
        print("⚠️  备份文件中没有数据")
        return False
    
    # 导入数据到新结构的表
    print(f"\n📥 导入数据到新结构表...")
    db_manager = DatabaseManager('testing')
    session = db_manager.get_session()
    
    try:
        # 导入词汇
        if len(vocabs) > 0:
            print(f"   📝 导入 {len(vocabs)} 条词汇...")
            imported_count = 0
            for v in vocabs:
                try:
                    # 处理时间字段：如果updated_at为None，使用created_at或当前时间
                    created_at = v.get('created_at')
                    updated_at = v.get('updated_at') or created_at or datetime.now()
                    
                    session.execute(text("""
                        INSERT INTO vocab_expressions 
                        (vocab_id, user_id, vocab_body, explanation, language, source, is_starred, created_at, updated_at)
                        VALUES (:vocab_id, 1, :vocab_body, :explanation, '德文', :source, :is_starred, :created_at, :updated_at)
                    """), {
                        'vocab_id': v.get('vocab_id'),
                        'vocab_body': v.get('vocab_body'),
                        'explanation': v.get('explanation'),
                        'source': v.get('source', 'auto'),
                        'is_starred': v.get('is_starred', False),
                        'created_at': created_at,
                        'updated_at': updated_at,
                    })
                    imported_count += 1
                except Exception as e:
                    print(f"   ⚠️  导入词汇 {v.get('vocab_id')} 时出错: {e}")
            
            session.commit()
            print(f"   ✅ 成功导入 {imported_count}/{len(vocabs)} 条词汇")
        
        # 导入语法规则
        if len(grammar_rules) > 0:
            print(f"   📝 导入 {len(grammar_rules)} 条语法规则...")
            imported_count = 0
            for g in grammar_rules:
                try:
                    # 处理时间字段：如果updated_at为None，使用created_at或当前时间
                    created_at = g.get('created_at')
                    updated_at = g.get('updated_at') or created_at or datetime.now()
                    
                    session.execute(text("""
                        INSERT INTO grammar_rules 
                        (rule_id, user_id, rule_name, rule_summary, language, source, is_starred, created_at, updated_at)
                        VALUES (:rule_id, 1, :rule_name, :rule_summary, '德文', :source, :is_starred, :created_at, :updated_at)
                    """), {
                        'rule_id': g.get('rule_id'),
                        'rule_name': g.get('rule_name'),
                        'rule_summary': g.get('rule_summary'),
                        'source': g.get('source', 'auto'),
                        'is_starred': g.get('is_starred', False),
                        'created_at': created_at,
                        'updated_at': updated_at,
                    })
                    imported_count += 1
                except Exception as e:
                    print(f"   ⚠️  导入语法规则 {g.get('rule_id')} 时出错: {e}")
            
            session.commit()
            print(f"   ✅ 成功导入 {imported_count}/{len(grammar_rules)} 条语法规则")
        
        session.close()
        
        # 验证数据
        print(f"\n🔍 验证数据...")
        session = db_manager.get_session()
        
        vocab_count_result = session.execute(text("SELECT COUNT(*) FROM vocab_expressions")).fetchone()
        vocab_count = vocab_count_result[0] if vocab_count_result else 0
        
        grammar_count_result = session.execute(text("SELECT COUNT(*) FROM grammar_rules")).fetchone()
        grammar_count = grammar_count_result[0] if grammar_count_result else 0
        
        print(f"   📊 词汇: {vocab_count} 条")
        print(f"   📊 语法规则: {grammar_count} 条")
        
        session.close()
        
        if vocab_count > 0 or grammar_count > 0:
            print(f"\n✅ 数据恢复完成！")
            return True
        else:
            print(f"\n⚠️  数据恢复失败：没有数据")
            return False
            
    except Exception as e:
        session.rollback()
        print(f"❌ 数据恢复失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


def main():
    print("\n" + "="*60)
    print("从备份文件恢复测试环境数据")
    print("="*60)
    print("\n📋 此脚本将：")
    print("  1. 查找最新的备份文件")
    print("  2. 从备份文件读取数据")
    print("  3. 导入数据到新结构的表（user_id=1, language=德文）")
    print("  4. 验证数据恢复结果")
    
    if restore_from_backup():
        print("\n✅ 数据恢复成功！")
    else:
        print("\n❌ 数据恢复失败")


if __name__ == "__main__":
    main()

