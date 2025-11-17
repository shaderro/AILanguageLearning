#!/usr/bin/env python3
"""
检查所有环境（开发、测试、生产）的数据库状态
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


def check_environment_status(environment, db_path):
    """检查环境数据库状态"""
    print(f"\n" + "="*60)
    print(f"📊 {environment.upper()} 环境数据库状态")
    print("="*60)
    print(f"📁 数据库路径: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在")
        return
    
    # 1. 使用原生SQL检查表结构
    print(f"\n📋 使用原生SQL检查...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    table_names = [t[0] for t in tables]
    print(f"📋 所有表: {table_names}")
    
    # 检查核心表
    core_tables = {
        'vocab_expressions': '词汇',
        'grammar_rules': '语法规则',
        'original_texts': '文章',
        'users': '用户'
    }
    
    for table_name, desc in core_tables.items():
        if table_name not in table_names:
            print(f"\n⚠️  {desc} ({table_name}): 表不存在")
            continue
        
        print(f"\n📊 {desc} ({table_name}):")
        
        # 检查表结构
        cursor.execute(f"PRAGMA table_info({table_name})")
        cols = cursor.fetchall()
        column_names = [col[1] for col in cols]
        print(f"   列名: {column_names}")
        
        has_user_id = 'user_id' in column_names
        has_language = 'language' in column_names
        
        print(f"   有user_id: {'✅' if has_user_id else '❌'}")
        print(f"   有language: {'✅' if has_language else '❌'}")
        
        # 检查数据量
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"   记录数: {count}")
        
        # 如果有数据，检查user_id分布
        if count > 0 and has_user_id:
            cursor.execute(f"SELECT user_id, COUNT(*) FROM {table_name} GROUP BY user_id")
            user_counts = cursor.fetchall()
            print(f"   user_id分布: {dict(user_counts)}")
        
        # 如果有数据，检查language分布
        if count > 0 and has_language:
            cursor.execute(f"SELECT language, COUNT(*) FROM {table_name} GROUP BY language")
            lang_counts = cursor.fetchall()
            lang_dict = {lang: cnt for lang, cnt in lang_counts if lang is not None}
            null_count = sum(cnt for lang, cnt in lang_counts if lang is None)
            if lang_dict:
                print(f"   language分布: {lang_dict}")
            if null_count > 0:
                print(f"   language为NULL: {null_count}")
    
    conn.close()
    
    # 2. 使用ORM检查（通过DatabaseManager）
    print(f"\n📋 使用ORM检查（通过DatabaseManager）...")
    try:
        db_manager = DatabaseManager(environment)
        engine = db_manager.get_engine()
        session = db_manager.get_session()
        
        inspector = inspect(engine)
        table_names_orm = inspector.get_table_names()
        print(f"📋 表名: {table_names_orm}")
        
        # 检查核心表的结构
        for table_name in ['vocab_expressions', 'grammar_rules', 'original_texts']:
            if table_name in table_names_orm:
                columns = [col['name'] for col in inspector.get_columns(table_name)]
                has_user_id = 'user_id' in columns
                has_language = 'language' in columns
                
                status = "✅" if has_user_id and has_language else "⚠️"
                print(f"   {status} {table_name}:")
                print(f"      user_id: {'有' if has_user_id else '无'}")
                print(f"      language: {'有' if has_language else '无'}")
        
        session.close()
    except Exception as e:
        print(f"❌ 使用ORM检查失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("\n" + "="*60)
    print("检查所有环境的数据库状态")
    print("="*60)
    
    # 检查所有环境
    environments = [
        ('development', DB_FILES['dev']),
        ('testing', DB_FILES['test']),
        ('production', DB_FILES['prod']),
    ]
    
    for env, db_path in environments:
        check_environment_status(env, db_path)
    
    print("\n" + "="*60)
    print("✅ 检查完成")
    print("="*60)
    
    print("\n📝 总结:")
    print("  1. 检查每个环境是否有user_id字段")
    print("  2. 检查每个环境是否有language字段")
    print("  3. 检查每个环境的数据量")
    print("  4. 根据检查结果决定是否需要迁移")


if __name__ == "__main__":
    main()

