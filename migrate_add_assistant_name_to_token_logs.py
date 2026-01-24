#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 assistant_name 字段到 token_logs 表

迁移内容：
1. 在 token_logs 表中添加 assistant_name 字段：
   - assistant_name: VARCHAR(128) NULL（调用的 SubAssistant 名称）
"""

import sys
import os
import io

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_system.database_manager import DatabaseManager
from sqlalchemy import inspect, text


def check_column_exists(engine, table_name, column_name):
    """检查列是否存在"""
    try:
        inspector = inspect(engine)
        if table_name not in inspector.get_table_names():
            return False
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception as e:
        print(f"[WARN] 检查列时出错: {e}")
        return False


def migrate():
    """执行迁移"""
    print("=" * 80)
    print("迁移：添加 assistant_name 字段到 token_logs 表")
    print("=" * 80)
    
    # 从环境变量读取环境配置
    try:
        from backend.config import ENV
        environment = ENV
    except ImportError:
        import os
        environment = os.getenv("ENV", "development")
    
    print(f"\n📦 使用环境: {environment}")
    
    db_manager = DatabaseManager(environment)
    engine = db_manager.get_engine()
    session = db_manager.get_session()
    
    try:
        # 检查表是否存在
        inspector = inspect(engine)
        if 'token_logs' not in inspector.get_table_names():
            print("\n❌ token_logs 表不存在，请先运行 migrate_add_token_logs_table.py")
            return 1
        
        # 检查字段是否存在
        if check_column_exists(engine, 'token_logs', 'assistant_name'):
            print("\n✅ assistant_name 字段已存在，跳过添加")
        else:
            print("\n📝 添加 assistant_name 字段...")
            # 添加字段（允许 NULL，因为旧记录可能没有这个字段）
            alter_sql = text("ALTER TABLE token_logs ADD COLUMN assistant_name VARCHAR(128)")
            session.execute(alter_sql)
            session.commit()
            print("✅ assistant_name 字段添加成功")
        
        session.commit()
        print("\n✅ 迁移完成！")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()
    
    return 0


if __name__ == "__main__":
    exit_code = migrate()
    sys.exit(exit_code)
