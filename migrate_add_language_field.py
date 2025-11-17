#!/usr/bin/env python3
"""
数据库迁移脚本：为 original_texts 表添加 language 字段

执行步骤：
1. 备份当前数据库
2. 检查 language 字段是否已存在
3. 如果不存在，添加 language 字段（VARCHAR(50), nullable）
"""

import sys
import os
import shutil
from datetime import datetime

# 添加路径
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, BACKEND_DIR)

from database_system.database_manager import DatabaseManager
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
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def add_language_column(engine, session):
    """添加 language 字段到 original_texts 表"""
    try:
        # 检查 language 字段是否已存在
        if check_column_exists(engine, 'original_texts', 'language'):
            print("✅ language 字段已存在，跳过迁移")
            return True
        
        print("📋 添加 language 字段到 original_texts 表...")
        
        # 使用 ALTER TABLE 添加列
        # SQLite 支持添加可空列，且不需要指定默认值
        alter_sql = text("ALTER TABLE original_texts ADD COLUMN language VARCHAR(50)")
        session.execute(alter_sql)
        session.commit()
        
        print("✅ language 字段添加成功")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ 添加 language 字段失败: {e}")
        raise


def migrate_database(environment='development'):
    """迁移指定环境的数据库"""
    print(f"\n📋 迁移 {environment} 环境数据库...")
    
    # 根据环境获取数据库路径
    from database_system.data_storage.config.config import DB_FILES
    
    if environment == 'development':
        db_path = DB_FILES['dev']
    elif environment == 'production':
        db_path = DB_FILES['prod']
    else:
        db_path = DB_FILES['dev']
    
    print(f"📁 数据库路径: {db_path}")
    
    # 1. 备份数据库
    if os.path.exists(db_path):
        backup_path = backup_database(db_path)
    else:
        print(f"⚠️  数据库文件不存在: {db_path}")
        print("   将创建新数据库...")
        backup_path = None
    
    # 2. 连接数据库
    db_manager = DatabaseManager(environment)
    engine = db_manager.get_engine()
    session = db_manager.get_session()
    
    try:
        # 3. 检查表是否存在
        inspector = inspect(engine)
        if 'original_texts' not in inspector.get_table_names():
            print("⚠️  original_texts 表不存在，将创建新表...")
            # 如果表不存在，创建表（会包含 language 字段）
            from database_system.business_logic.models import Base
            Base.metadata.create_all(engine)
            print("✅ 表已创建（包含 language 字段）")
        else:
            # 4. 检查并添加 language 字段
            add_language_column(engine, session)
        
        # 5. 验证字段是否添加成功
        if check_column_exists(engine, 'original_texts', 'language'):
            print(f"✅ {environment} 环境迁移完成！")
            return True
        else:
            print(f"❌ {environment} 环境验证失败：language 字段未成功添加")
            return False
            
    except Exception as e:
        print(f"❌ {environment} 环境迁移失败: {e}")
        if backup_path:
            print(f"\n可以从备份恢复: {backup_path}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


def main():
    print("\n" + "="*60)
    print("数据库迁移：为 original_texts 表添加 language 字段")
    print("="*60)
    
    # 询问要迁移的环境
    print("\n请选择要迁移的数据库环境：")
    print("1. development (dev.db)")
    print("2. production (language_learning.db)")
    print("3. 两者都迁移")
    
    choice = input("\n请输入选项 (1/2/3，默认: 3): ").strip()
    
    try:
        if choice == '1':
            migrate_database('development')
        elif choice == '2':
            migrate_database('production')
        else:
            # 默认迁移两者
            migrate_database('development')
            migrate_database('production')
        
        print("\n" + "="*60)
        print("✅ 所有迁移完成！")
        print("="*60)
        print("\n下一步：")
        print("1. 重启后端服务器")
        print("2. 测试文章上传功能")
        print("3. 验证 language 字段是否正确保存")
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()

