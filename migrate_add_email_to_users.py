#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 email 字段到 users 表

迁移内容：
- 在 users 表中添加 email 字段
- 类型：VARCHAR(255)
- 可空：是（允许已注册用户email为空）
- 唯一性：是（UNIQUE约束）
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


def add_email_column(engine, session):
    """添加 email 字段到 users 表"""
    try:
        # 检查 email 字段是否已存在
        if check_column_exists(engine, 'users', 'email'):
            print("   ✅ email 字段已存在，跳过")
            return True
        
        print("   📋 添加 email 字段...")
        
        # 使用 ALTER TABLE 添加列
        # SQLite 支持添加可空列，并添加唯一性约束
        # 注意：SQLite 的 UNIQUE 约束在添加列时需要使用 CREATE UNIQUE INDEX
        alter_sql = text("ALTER TABLE users ADD COLUMN email VARCHAR(255)")
        session.execute(alter_sql)
        session.commit()
        
        # 创建唯一索引（SQLite 中 UNIQUE 约束通过索引实现）
        try:
            create_index_sql = text("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            session.execute(create_index_sql)
            session.commit()
            print("   ✅ email 唯一索引创建成功")
        except Exception as e:
            # 如果索引已存在，忽略错误
            if 'already exists' not in str(e).lower() and 'duplicate' not in str(e).lower():
                print(f"   ⚠️  创建唯一索引时出错（可能已存在）: {e}")
        
        print("   ✅ email 字段添加成功")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"   ❌ 添加 email 字段失败: {e}")
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
        print("   将创建新数据库（包含 email 字段）")
    
    # 1. 初始化数据库管理器
    db_manager = DatabaseManager(environment)
    engine = db_manager.get_engine()
    session = db_manager.get_session()
    
    try:
        # 2. 检查表是否存在
        inspector = inspect(engine)
        if 'users' not in inspector.get_table_names():
            print("⚠️  users 表不存在，将创建新表...")
            # 如果表不存在，创建表（会包含 email 字段）
            from database_system.business_logic.models import Base
            Base.metadata.create_all(engine)
            print("✅ 表已创建（包含 email 字段）")
        else:
            # 3. 检查并添加 email 字段
            add_email_column(engine, session)
        
        # 4. 验证字段是否添加成功
        if check_column_exists(engine, 'users', 'email'):
            print(f"\n✅ {environment} 环境迁移完成！")
            return True
        else:
            print(f"\n❌ {environment} 环境验证失败：email 字段未成功添加")
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
    print("🚀 开始迁移：添加 email 字段到 users 表")
    print("="*60)
    
    # 从配置文件获取数据库路径
    from database_system.data_storage.config.config import DB_FILES
    
    # 迁移所有环境
    environments = {
        'development': DB_FILES['dev'],
        'testing': DB_FILES['test'],
        'production': DB_FILES['prod']
    }
    
    success_count = 0
    total_count = len(environments)
    
    for env, db_path in environments.items():
        try:
            if migrate_database(env, db_path):
                success_count += 1
        except Exception as e:
            print(f"\n❌ {env} 环境迁移失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print(f"📊 迁移完成：{success_count}/{total_count} 个环境成功")
    print("="*60)
    
    if success_count == total_count:
        print("\n✅ 所有环境迁移成功！")
        return 0
    else:
        print(f"\n⚠️  有 {total_count - success_count} 个环境迁移失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())

