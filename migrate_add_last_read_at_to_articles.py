#!/usr/bin/env python3
"""
数据库迁移脚本：为 original_texts 表添加 last_read_at 字段

执行步骤：
1. 备份当前数据库
2. 检查 last_read_at 字段是否已存在
3. 如果不存在，添加 last_read_at 字段（DATETIME, nullable, indexed）
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
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def add_last_read_at_column(engine, session):
    """添加 last_read_at 字段到 original_texts 表"""
    try:
        # 检查 last_read_at 字段是否已存在
        if check_column_exists(engine, 'original_texts', 'last_read_at'):
            print("✅ last_read_at 字段已存在，跳过迁移")
            return True
        
        print("📋 添加 last_read_at 字段到 original_texts 表...")
        
        # 添加字段（SQLite 使用 DATETIME 类型）
        session.execute(text("""
            ALTER TABLE original_texts 
            ADD COLUMN last_read_at DATETIME
        """))
        session.commit()
        
        # 创建索引以提高查询性能
        print("📋 创建 last_read_at 索引...")
        try:
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_original_texts_last_read_at 
                ON original_texts(last_read_at)
            """))
            session.commit()
        except Exception as e:
            print(f"⚠️ 创建索引时出错（可能已存在）: {e}")
            session.rollback()
        
        print("✅ last_read_at 字段添加成功")
        return True
    except Exception as e:
        print(f"❌ 添加 last_read_at 字段失败: {e}")
        session.rollback()
        raise


def migrate_database(environment):
    """执行数据库迁移"""
    print(f"\n{'='*60}")
    print(f"开始迁移数据库: {environment}")
    print(f"{'='*60}\n")
    
    # 获取数据库路径
    db_key = 'dev' if environment == 'development' else ('test' if environment == 'test' else 'prod')
    db_path = DB_FILES.get(db_key)
    
    if not db_path:
        print(f"⚠️ 环境 {environment} 的数据库路径未配置，跳过")
        return
    
    print(f"数据库路径: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"⚠️ 数据库文件不存在: {db_path}")
        print("   将在首次运行时自动创建")
        return
    
    # 备份数据库
    backup_path = backup_database(db_path)
    
    try:
        # 创建数据库管理器
        db_manager = DatabaseManager(environment)
        engine = db_manager.get_engine()
        session = db_manager.get_session()
        
        # 执行迁移
        add_last_read_at_column(engine, session)
        
        print(f"\n✅ 迁移完成: {environment}")
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {environment}")
        print(f"错误: {e}")
        if backup_path:
            print(f"\n💾 可以从备份恢复: {backup_path}")
        raise
    finally:
        if 'session' in locals():
            session.close()


def main():
    """主函数"""
    environments = ['development', 'test', 'production']
    
    print("="*60)
    print("数据库迁移：添加 last_read_at 字段到 original_texts 表")
    print("="*60)
    
    for env in environments:
        try:
            migrate_database(env)
        except Exception as e:
            print(f"跳过环境 {env}: {e}")
            continue
    
    print("\n" + "="*60)
    print("所有迁移完成！")
    print("="*60)


if __name__ == "__main__":
    main()

