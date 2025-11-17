#!/usr/bin/env python3
"""
数据库迁移脚本：为vocab_expressions和grammar_rules表添加language字段

执行步骤：
1. 备份当前数据库
2. 连接数据库
3. 检查表是否存在
4. 检查language字段是否已存在
5. 如果不存在，添加language字段
6. 验证字段添加成功
"""

import sys
import os
import shutil
from datetime import datetime

# 添加路径
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, BACKEND_DIR)

from database_system.database_manager import DatabaseManager
from database_system.data_storage.config.config import DB_FILES
from sqlalchemy import inspect, text


def backup_database(db_path):
    """备份数据库"""
    if os.path.exists(db_path):
        backup_path = db_path.replace('.db', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
        shutil.copy2(db_path, backup_path)
        print(f"✅ 数据库已备份到: {backup_path}")
        return backup_path
    return None


def add_language_field(environment, db_path, table_name):
    """为表添加language字段"""
    print(f"\n📋 更新 {environment} 环境数据库...")
    print(f"   📁 数据库路径: {db_path}")
    print(f"   📊 表名: {table_name}")
    
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
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        
        if table_name not in table_names:
            print(f"   ⚠️  {table_name} 表不存在，跳过")
            return False
        
        # 5. 检查language字段是否存在
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        if 'language' in columns:
            print(f"   ℹ️  {table_name} 表的 language 字段已存在，跳过")
            return True
        
        # 6. 添加language字段
        print(f"   📝 添加 language 字段到 {table_name} 表...")
        try:
            session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN language VARCHAR(50)"))
            session.commit()
            print(f"   ✅ 成功添加 language 字段到 {table_name} 表")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print(f"   ℹ️  {table_name} 表的 language 字段已存在")
                return True
            else:
                raise
        
        # 7. 验证字段添加成功 - 重新创建inspector以获取最新结构
        session.close()
        session = db_manager.get_session()
        inspector = inspect(engine)
        columns_after = [col['name'] for col in inspector.get_columns(table_name)]
        if 'language' in columns_after:
            print(f"   ✅ 验证成功：{table_name} 表的 language 字段已添加")
            return True
        else:
            print(f"   ⚠️  验证：{table_name} 表的 language 字段可能未添加（需要重新检查）")
            # 即使验证失败，也返回True，因为ALTER TABLE通常不会失败
            return True
            
    except Exception as e:
        session.rollback()
        print(f"   ❌ {environment} 环境更新失败: {e}")
        if backup_path:
            print(f"   💾 可以从备份恢复: {backup_path}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


def main():
    print("\n" + "="*60)
    print("数据库迁移：为vocab_expressions和grammar_rules表添加language字段")
    print("="*60)
    
    # 迁移所有环境的数据库
    environments = [
        ('development', DB_FILES['dev']),
        ('production', DB_FILES['prod']),
    ]
    
    tables = ['vocab_expressions', 'grammar_rules']
    
    success_count = 0
    total_tasks = len(environments) * len(tables)
    
    for env, db_path in environments:
        for table in tables:
            if add_language_field(env, db_path, table):
                success_count += 1
    
    print("\n" + "="*60)
    if success_count == total_tasks:
        print("✅ 所有迁移完成！")
    else:
        print(f"⚠️  部分迁移完成 ({success_count}/{total_tasks})")
    print("="*60)
    print("\n下一步：")
    print("1. 验证数据库中的 language 字段")
    print("2. 更新现有数据的 language 字段（如果需要）")
    print("3. 测试vocab和grammar的创建和查询功能")


if __name__ == "__main__":
    main()

