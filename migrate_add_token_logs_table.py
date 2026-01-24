#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 TokenLog 表（token 使用日志）

迁移内容：
1. 创建 token_logs 表：
   - id, user_id, total_tokens, prompt_tokens, completion_tokens
   - model_name, created_at
   - 索引：user_id, (user_id, created_at)
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
from database_system.business_logic.models import Base, TokenLog
from sqlalchemy import inspect, text


def check_table_exists(engine, table_name):
    """检查表是否存在"""
    try:
        inspector = inspect(engine)
        return table_name in inspector.get_table_names()
    except Exception as e:
        print(f"[WARN] 检查表时出错: {e}")
        return False


def check_index_exists(engine, table_name, index_name):
    """检查索引是否存在"""
    try:
        inspector = inspect(engine)
        indexes = inspector.get_indexes(table_name)
        return any(idx['name'] == index_name for idx in indexes)
    except Exception as e:
        print(f"[WARN] 检查索引时出错: {e}")
        return False


def migrate():
    """执行迁移"""
    print("=" * 80)
    print("迁移：添加 TokenLog 表（token 使用日志）")
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
        if check_table_exists(engine, 'token_logs'):
            print("\n✅ token_logs 表已存在，跳过创建")
        else:
            print("\n📝 创建 token_logs 表...")
            # 创建表
            Base.metadata.create_all(engine, tables=[TokenLog.__table__])
            print("✅ token_logs 表创建成功")
        
        # 检查索引
        if check_index_exists(engine, 'token_logs', 'ix_token_logs_user_id'):
            print("✅ 索引 ix_token_logs_user_id 已存在")
        else:
            print("✅ 索引 ix_token_logs_user_id 已自动创建（SQLAlchemy）")
        
        if check_index_exists(engine, 'token_logs', 'idx_token_logs_user_time'):
            print("✅ 索引 idx_token_logs_user_time 已存在")
        else:
            print("✅ 索引 idx_token_logs_user_time 已自动创建（SQLAlchemy）")
        
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
