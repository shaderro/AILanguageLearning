#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为 users 表添加跨设备语言偏好字段：

1. ui_language: VARCHAR(16) NULL
   - 用户界面语言偏好（如 'zh' / 'en'）

2. content_language: VARCHAR(16) NULL
   - 当前正在学习的内容语言代码（如 'zh' / 'en' / 'de'）

3. languages_list: JSON NULL
   - 已添加的内容语言代码列表（JSON 数组）
"""

import sys
import os
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import inspect, text
from database_system.database_manager import DatabaseManager


def check_column_exists(engine, table_name, column_name):
    try:
        inspector = inspect(engine)
        if table_name not in inspector.get_table_names():
            return False
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception as e:
        print(f"[WARN] 检查列时出错: {e}")
        return False


def add_user_language_columns(engine, session):
    """给 users 表添加语言偏好字段"""
    try:
        print("   [CHECK] 检查 users 表语言偏好字段...")

        # ui_language
        if not check_column_exists(engine, 'users', 'ui_language'):
            print("   [ADD] 添加 ui_language 字段...")
            alter_sql = text("ALTER TABLE users ADD COLUMN ui_language VARCHAR(16)")
            session.execute(alter_sql)
            session.commit()
            print("   [OK] ui_language 字段添加成功")
        else:
            print("   [SKIP] ui_language 字段已存在，跳过")

        # content_language
        if not check_column_exists(engine, 'users', 'content_language'):
            print("   [ADD] 添加 content_language 字段...")
            alter_sql = text("ALTER TABLE users ADD COLUMN content_language VARCHAR(16)")
            session.execute(alter_sql)
            session.commit()
            print("   [OK] content_language 字段添加成功")
        else:
            print("   [SKIP] content_language 字段已存在，跳过")

        # languages_list（JSON）
        if not check_column_exists(engine, 'users', 'languages_list'):
            print("   [ADD] 添加 languages_list 字段 (JSON)...")
            # SQLite 和 PostgreSQL 都支持 JSON 类型（在 SQLite 中会退化为 TEXT）
            alter_sql = text("ALTER TABLE users ADD COLUMN languages_list JSON")
            session.execute(alter_sql)
            session.commit()
            print("   [OK] languages_list 字段添加成功")
        else:
            print("   [SKIP] languages_list 字段已存在，跳过")

    except Exception as e:
        session.rollback()
        print(f"[ERROR] 添加语言偏好字段失败: {e}")
        raise


def main():
    # 默认使用 ENV 指定的环境
    try:
        from backend.config import ENV
        environment = ENV
    except ImportError:
        environment = os.getenv("ENV", "development")

    print(f"[INFO] 开始迁移用户语言偏好字段（环境: {environment}）")
    db_manager = DatabaseManager(environment)
    engine = db_manager.get_engine()
    session = db_manager.get_session()

    try:
        add_user_language_columns(engine, session)
        print("[DONE] 用户语言偏好字段迁移完成")
    finally:
        session.close()


if __name__ == "__main__":
    main()

