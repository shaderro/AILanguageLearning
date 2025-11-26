#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 processing_status 字段到 original_texts 表

迁移内容：
- 在 original_texts 表中添加 processing_status 字段
- 默认值：'completed'
- 类型：VARCHAR(50)
- 非空：是
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_system.database_manager import DatabaseManager
from sqlalchemy import inspect, text


def check_column_exists(engine, table_name, column_name):
    """检查列是否存在"""
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception as e:
        print(f"⚠️  检查列时出错: {e}")
        return False


def add_processing_status_column(engine, session):
    """添加 processing_status 字段到 original_texts 表"""
    try:
        # 检查 processing_status 字段是否已存在
        if check_column_exists(engine, 'original_texts', 'processing_status'):
            print("   ✅ processing_status 字段已存在，跳过")
            return True
        
        print("   📋 添加 processing_status 字段...")
        
        # 使用 ALTER TABLE 添加列
        # SQLite 支持添加可空列，但我们需要非空列，所以先添加可空列，然后更新默认值
        alter_sql = text("ALTER TABLE original_texts ADD COLUMN processing_status VARCHAR(50) DEFAULT 'completed'")
        session.execute(alter_sql)
        session.commit()
        
        # 对于 SQLite，我们需要确保现有记录都有默认值
        # 更新所有现有记录为 'completed'
        update_sql = text("UPDATE original_texts SET processing_status = 'completed' WHERE processing_status IS NULL")
        session.execute(update_sql)
        session.commit()
        
        print("   ✅ processing_status 字段添加成功")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"   ❌ 添加 processing_status 字段失败: {e}")
        # 如果是列已存在的错误，忽略
        if 'duplicate column name' in str(e).lower() or 'already exists' in str(e).lower():
            print("   ℹ️  列可能已存在，继续...")
            return True
        raise


def migrate_database(environment, db_path):
    """迁移指定环境的数据库"""
    print(f"\n{'='*60}")
    print(f"📦 迁移环境: {environment}")
    print(f"📁 数据库路径: {db_path}")
    print(f"{'='*60}\n")
    
    if not os.path.exists(db_path):
        print(f"⚠️  数据库文件不存在: {db_path}")
        print("   将创建新数据库（包含 processing_status 字段）")
    
    # 1. 初始化数据库管理器
    db_manager = DatabaseManager(environment)
    engine = db_manager.get_engine()
    session = db_manager.get_session()
    
    try:
        # 2. 检查表是否存在
        inspector = inspect(engine)
        if 'original_texts' not in inspector.get_table_names():
            print("⚠️  original_texts 表不存在，将创建新表...")
            # 如果表不存在，创建表（会包含 processing_status 字段）
            from database_system.business_logic.models import Base
            Base.metadata.create_all(engine)
            print("✅ 表已创建（包含 processing_status 字段）")
        else:
            # 3. 检查并添加 processing_status 字段
            add_processing_status_column(engine, session)
        
        # 4. 验证字段是否添加成功
        if check_column_exists(engine, 'original_texts', 'processing_status'):
            print(f"\n✅ {environment} 环境迁移完成！")
            return True
        else:
            print(f"\n❌ {environment} 环境验证失败：processing_status 字段未成功添加")
            return False
            
    except Exception as e:
        print(f"\n❌ {environment} 环境迁移失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


def main():
    print("\n" + "="*60)
    print("🚀 开始迁移：添加 processing_status 字段")
    print("="*60)
    
    # 迁移所有环境
    environments = {
        'development': 'database_system/data_storage/data/dev.db',
        'test': 'database_system/data_storage/data/test.db',
        'production': 'database_system/data_storage/data/language_learning.db'
    }
    
    results = {}
    for env, db_path in environments.items():
        try:
            results[env] = migrate_database(env, db_path)
        except Exception as e:
            print(f"\n❌ {env} 环境迁移失败: {e}")
            results[env] = False
    
    # 总结
    print("\n" + "="*60)
    print("📊 迁移总结")
    print("="*60)
    for env, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"  {env:15} {status}")
    
    all_success = all(results.values())
    if all_success:
        print("\n✅ 所有环境迁移完成！")
    else:
        print("\n⚠️  部分环境迁移失败，请检查上面的错误信息")
    
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())

