#!/usr/bin/env python3
"""
生产环境数据库迁移：为vocab_expressions、grammar_rules、original_texts表添加user_id字段

执行步骤：
1. 备份当前数据库
2. 检查表是否存在
3. 检查user_id字段是否已存在
4. 如果不存在，添加user_id字段
5. 验证字段添加成功

注意：此脚本假设生产环境没有数据或数据可以安全迁移
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


def add_user_id_to_table(environment, db_path, table_name, user_id_type="INTEGER"):
    """为表添加user_id字段"""
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
        
        # 5. 检查user_id字段是否存在
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        if 'user_id' in columns:
            print(f"   ℹ️  {table_name} 表的 user_id 字段已存在，跳过")
            return True
        
        # 6. 检查是否有数据
        count_result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).fetchone()
        record_count = count_result[0] if count_result else 0
        print(f"   📊 当前记录数: {record_count}")
        
        if record_count > 0:
            print(f"   ⚠️  {table_name} 表有 {record_count} 条记录")
            print(f"   💡 建议：将这些记录归属到 user_id=1（默认用户）")
            response = input(f"   ❓ 是否继续？(y/n): ")
            if response.lower() != 'y':
                print(f"   ⏭️  跳过 {table_name} 表")
                return False
        
        # 7. 添加user_id字段
        print(f"   📝 添加 user_id 字段到 {table_name} 表...")
        try:
            # SQLite不支持直接添加NOT NULL约束，所以先添加NULLABLE字段
            # 注意：由于表是空的，我们可以安全地添加字段
            session.execute(text(f"""
                ALTER TABLE {table_name} 
                ADD COLUMN user_id {user_id_type}
            """))
            session.commit()
            print(f"   ✅ 成功添加 user_id 字段到 {table_name} 表")
            
            # 注意：SQLite不支持直接添加NOT NULL约束和外键约束
            # 如果需要这些约束，需要重建表
            print(f"   ℹ️  注意：添加的 user_id 字段是 NULLABLE 的")
            print(f"   ℹ️  如果需要 NOT NULL 约束，需要重建表（当前表是空的，可以重建）")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print(f"   ℹ️  {table_name} 表的 user_id 字段已存在")
                return True
            else:
                raise
        
        # 8. 如果有数据，设置默认user_id=1
        if record_count > 0:
            print(f"   📝 设置现有记录的 user_id = 1...")
            session.execute(text(f"""
                UPDATE {table_name} 
                SET user_id = 1 
                WHERE user_id IS NULL
            """))
            session.commit()
            print(f"   ✅ 成功设置 {record_count} 条记录的 user_id = 1")
        
        # 9. 添加外键约束（如果需要）
        # 注意：SQLite的ALTER TABLE不支持添加外键约束
        # 如果需要外键约束，需要重建表
        print(f"   ℹ️  注意：SQLite不支持直接添加外键约束")
        print(f"   ℹ️  如果需要外键约束，请使用重建表的方式")
        
        # 10. 验证字段添加成功
        session.close()
        session = db_manager.get_session()
        inspector = inspect(engine)
        columns_after = [col['name'] for col in inspector.get_columns(table_name)]
        if 'user_id' in columns_after:
            print(f"   ✅ 验证成功：{table_name} 表的 user_id 字段已添加")
            
            # 验证数据（如果有）
            if record_count > 0:
                user_count_result = session.execute(text(f"""
                    SELECT COUNT(*) FROM {table_name} 
                    WHERE user_id = 1
                """)).fetchone()
                user_count = user_count_result[0] if user_count_result else 0
                if user_count == record_count:
                    print(f"   ✅ 数据验证成功：{user_count}/{record_count} 条记录的 user_id = 1")
                else:
                    print(f"   ⚠️  数据验证：{user_count}/{record_count} 条记录的 user_id = 1")
            
            return True
        else:
            print(f"   ❌ 验证失败：{table_name} 表的 user_id 字段未添加")
            return False
            
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
    print("生产环境数据库迁移：添加user_id字段到核心表")
    print("="*60)
    print("\n⚠️  注意：此脚本会修改生产环境数据库")
    print("⚠️  请确保已经备份数据库")
    print("⚠️  建议在维护窗口期间运行")
    
    response = input("\n❓ 是否继续？(y/n): ")
    if response.lower() != 'y':
        print("⏭️  已取消")
        return
    
    # 迁移生产环境数据库
    environment = 'production'
    db_path = DB_FILES['prod']
    
    tables = [
        ('vocab_expressions', 'INTEGER'),
        ('grammar_rules', 'INTEGER'),
        ('original_texts', 'INTEGER'),
    ]
    
    success_count = 0
    total_tasks = len(tables)
    
    for table_name, user_id_type in tables:
        if add_user_id_to_table(environment, db_path, table_name, user_id_type):
            success_count += 1
    
    print("\n" + "="*60)
    if success_count == total_tasks:
        print("✅ 所有迁移完成！")
    else:
        print(f"⚠️  部分迁移完成 ({success_count}/{total_tasks})")
    print("="*60)
    print("\n下一步：")
    print("1. 验证数据库中的 user_id 字段")
    print("2. 测试用户隔离功能")
    print("3. 确认API正常工作")
    print("\n⚠️  注意：")
    print("  - SQLite不支持直接添加外键约束")
    print("  - 如果需要外键约束，需要重建表")
    print("  - 当前添加的user_id字段是NULLABLE的")
    print("  - 建议在应用层面确保user_id不为NULL")


if __name__ == "__main__":
    main()

