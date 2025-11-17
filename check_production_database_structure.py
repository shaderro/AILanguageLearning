#!/usr/bin/env python3
"""
检查生产环境数据库结构
"""
import sys
import os
import sqlite3

# 添加路径
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, BACKEND_DIR)

from database_system.data_storage.config.config import DB_FILES
from database_system.database_manager import DatabaseManager
from sqlalchemy import inspect, text


def check_production_db():
    """检查生产环境数据库结构"""
    print("\n" + "="*60)
    print("检查生产环境数据库结构")
    print("="*60)
    
    db_path = DB_FILES['prod']
    print(f"\n📁 数据库路径: {db_path}")
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return
    
    # 1. 使用原生SQL检查表结构
    print("\n" + "="*60)
    print("📊 使用原生SQL检查表结构")
    print("="*60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\n📋 所有表: {[t[0] for t in tables]}")
    
    # 检查vocab_expressions表
    if 'vocab_expressions' in [t[0] for t in tables]:
        print("\n📊 vocab_expressions 表结构:")
        cursor.execute("PRAGMA table_info(vocab_expressions)")
        cols = cursor.fetchall()
        column_names = [col[1] for col in cols]
        print(f"  列名: {column_names}")
        print(f"  是否有user_id: {'user_id' in column_names}")
        print(f"  是否有language: {'language' in column_names}")
        
        # 检查数据量
        cursor.execute("SELECT COUNT(*) FROM vocab_expressions")
        count = cursor.fetchone()[0]
        print(f"  记录数: {count}")
        
        if count > 0:
            # 检查user_id分布
            if 'user_id' in column_names:
                cursor.execute("SELECT user_id, COUNT(*) FROM vocab_expressions GROUP BY user_id")
                user_counts = cursor.fetchall()
                print(f"  user_id分布: {dict(user_counts)}")
            else:
                print("  ⚠️  没有user_id列")
            
            # 检查language分布
            if 'language' in column_names:
                cursor.execute("SELECT language, COUNT(*) FROM vocab_expressions GROUP BY language")
                lang_counts = cursor.fetchall()
                print(f"  language分布: {dict(lang_counts)}")
            else:
                print("  ⚠️  没有language列")
    else:
        print("\n⚠️  vocab_expressions 表不存在")
    
    # 检查grammar_rules表
    if 'grammar_rules' in [t[0] for t in tables]:
        print("\n📊 grammar_rules 表结构:")
        cursor.execute("PRAGMA table_info(grammar_rules)")
        cols = cursor.fetchall()
        column_names = [col[1] for col in cols]
        print(f"  列名: {column_names}")
        print(f"  是否有user_id: {'user_id' in column_names}")
        print(f"  是否有language: {'language' in column_names}")
        
        # 检查数据量
        cursor.execute("SELECT COUNT(*) FROM grammar_rules")
        count = cursor.fetchone()[0]
        print(f"  记录数: {count}")
        
        if count > 0:
            # 检查user_id分布
            if 'user_id' in column_names:
                cursor.execute("SELECT user_id, COUNT(*) FROM grammar_rules GROUP BY user_id")
                user_counts = cursor.fetchall()
                print(f"  user_id分布: {dict(user_counts)}")
            else:
                print("  ⚠️  没有user_id列")
            
            # 检查language分布
            if 'language' in column_names:
                cursor.execute("SELECT language, COUNT(*) FROM grammar_rules GROUP BY language")
                lang_counts = cursor.fetchall()
                print(f"  language分布: {dict(lang_counts)}")
            else:
                print("  ⚠️  没有language列")
    else:
        print("\n⚠️  grammar_rules 表不存在")
    
    # 检查original_texts表
    if 'original_texts' in [t[0] for t in tables]:
        print("\n📊 original_texts 表结构:")
        cursor.execute("PRAGMA table_info(original_texts)")
        cols = cursor.fetchall()
        column_names = [col[1] for col in cols]
        print(f"  列名: {column_names}")
        print(f"  是否有user_id: {'user_id' in column_names}")
        print(f"  是否有language: {'language' in column_names}")
        
        # 检查数据量
        cursor.execute("SELECT COUNT(*) FROM original_texts")
        count = cursor.fetchone()[0]
        print(f"  记录数: {count}")
        
        if count > 0:
            # 检查user_id分布
            if 'user_id' in column_names:
                cursor.execute("SELECT user_id, COUNT(*) FROM original_texts GROUP BY user_id")
                user_counts = cursor.fetchall()
                print(f"  user_id分布: {dict(user_counts)}")
            else:
                print("  ⚠️  没有user_id列")
            
            # 检查language分布
            if 'language' in column_names:
                cursor.execute("SELECT language, COUNT(*) FROM original_texts GROUP BY language")
                lang_counts = cursor.fetchall()
                print(f"  language分布: {dict(lang_counts)}")
            else:
                print("  ⚠️  没有language列")
    else:
        print("\n⚠️  original_texts 表不存在")
    
    conn.close()
    
    # 2. 使用ORM检查（通过DatabaseManager）
    print("\n" + "="*60)
    print("📊 使用ORM检查（通过DatabaseManager）")
    print("="*60)
    
    try:
        db_manager = DatabaseManager('production')
        engine = db_manager.get_engine()
        session = db_manager.get_session()
        
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        print(f"\n📋 表名: {table_names}")
        
        # 检查vocab_expressions
        if 'vocab_expressions' in table_names:
            columns = [col['name'] for col in inspector.get_columns('vocab_expressions')]
            print(f"\n  vocab_expressions 列: {columns}")
            print(f"    有user_id: {'user_id' in columns}")
            print(f"    有language: {'language' in columns}")
        
        # 检查grammar_rules
        if 'grammar_rules' in table_names:
            columns = [col['name'] for col in inspector.get_columns('grammar_rules')]
            print(f"\n  grammar_rules 列: {columns}")
            print(f"    有user_id: {'user_id' in columns}")
            print(f"    有language: {'language' in columns}")
        
        session.close()
    except Exception as e:
        print(f"❌ 使用ORM检查失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("✅ 检查完成")
    print("="*60)
    
    print("\n📝 总结:")
    print("  1. 如果表没有user_id列，说明数据库结构是旧版本")
    print("  2. 如果表有user_id列但没有数据，说明数据库结构已更新但数据为空")
    print("  3. 如果表有user_id列且有数据，说明数据库结构已更新且有数据")


if __name__ == "__main__":
    check_production_db()

