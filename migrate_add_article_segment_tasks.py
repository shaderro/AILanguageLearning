#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 article_segment_tasks 表（文章分页阅读任务状态）。

在 Render 生产库或本地 PostgreSQL 上运行：
  ENV=production python migrate_add_article_segment_tasks.py
"""

import sys
import os
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_system.database_manager import DatabaseManager
from database_system.business_logic.models import Base, ArticleSegmentTask
from sqlalchemy import inspect


def table_exists(engine, name: str) -> bool:
    try:
        return name in inspect(engine).get_table_names()
    except Exception:
        return False


def migrate() -> int:
    try:
        from backend.config import ENV as environment
    except ImportError:
        environment = os.getenv("ENV", "development")

    print(f"环境: {environment}")
    db_manager = DatabaseManager(environment)
    engine = db_manager.get_engine()
    session = db_manager.get_session()
    tbl = "article_segment_tasks"
    try:
        if table_exists(engine, tbl):
            print(f"✅ {tbl} 已存在，跳过")
        else:
            print(f"📝 创建 {tbl} ...")
            Base.metadata.create_all(engine, tables=[ArticleSegmentTask.__table__])
            print(f"✅ {tbl} 创建完成")
        session.commit()
        return 0
    except Exception as e:
        session.rollback()
        print(f"❌ 迁移失败: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(migrate())
