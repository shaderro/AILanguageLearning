#!/usr/bin/env python3
"""
数据库迁移脚本：为 original_texts 表添加 language 字段（自动模式）

此脚本会自动检测并迁移所有环境的数据库
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


def check_column_exists(engine, table_name, column_name):
    """检查表中是否已存在指定列"""
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception as e:
        print(f"⚠️  检查列时出错: {e}")
        return False


def add_language_column(engine, session):
    """添加 language 字段到 original_texts 表"""
    try:
        # 检查 language 字段是否已存在
        if check_column_exists(engine, 'original_texts', 'language'):
            print("   ✅ language 字段已存在，跳过")
            return True
        
        print("   📋 添加 language 字段...")
        
        # 使用 ALTER TABLE 添加列
        # SQLite 支持添加可空列
        alter_sql = text("ALTER TABLE original_texts ADD COLUMN language VARCHAR(50)")
        session.execute(alter_sql)
        session.commit()
        
        print("   ✅ language 字段添加成功")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"   ❌ 添加 language 字段失败: {e}")
        # 如果是列已存在的错误，忽略
        if 'duplicate column name' in str(e).lower() or 'already exists' in str(e).lower():
            print("   ℹ️  列可能已存在，继续...")
            return True
        raise


def migrate_database(environment, db_path):
    """迁移指定环境的数据库"""
    print(f"\n📋 迁移 {environment} 环境数据库...")
    print(f"   📁 数据库路径: {db_path}")
    
    # 1. 检查数据库文件是否存在
    if not os.path.exists(db_path):
        print(f"   ⚠️  数据库文件不存在: {db_path}")
        print(f"   ℹ️  将在首次使用时自动创建（包含 language 字段）")
        return True
    
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
        
        if 'original_texts' not in table_names:
            print("   ⚠️  original_texts 表不存在，将创建新表...")
            # 如果表不存在，创建表（会包含 language 字段）
            from database_system.business_logic.models import Base
            Base.metadata.create_all(engine)
            print("   ✅ 表已创建（包含 language 字段）")
        else:
            # 5. 检查并添加 language 字段
            add_language_column(engine, session)
        
        # 6. 验证字段是否添加成功
        if check_column_exists(engine, 'original_texts', 'language'):
            print(f"   ✅ {environment} 环境迁移完成！")
            return True
        else:
            print(f"   ❌ {environment} 环境验证失败：language 字段未成功添加")
            return False
            
    except Exception as e:
        print(f"   ❌ {environment} 环境迁移失败: {e}")
        if backup_path:
            print(f"   💾 可以从备份恢复: {backup_path}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


def main():
    print("\n" + "="*60)
    print("数据库迁移：为 original_texts 表添加 language 字段")
    print("="*60)
    
    # 迁移所有环境的数据库
    environments = [
        ('development', DB_FILES['dev']),
        ('production', DB_FILES['prod']),
    ]
    
    success_count = 0
    for env, db_path in environments:
        if migrate_database(env, db_path):
            success_count += 1
    
    print("\n" + "="*60)
    if success_count == len(environments):
        print("✅ 所有迁移完成！")
    else:
        print(f"⚠️  部分迁移完成 ({success_count}/{len(environments)})")
    print("="*60)
    print("\n下一步：")
    print("1. 重启后端服务器")
    print("2. 测试文章上传功能")
    print("3. 验证 language 字段是否正确保存")


if __name__ == "__main__":
    main()

