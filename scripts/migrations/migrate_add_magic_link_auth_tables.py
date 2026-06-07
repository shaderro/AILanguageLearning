#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 magic_link_tokens、auth_sessions 表（邮箱 magic link + 会话认证）。

与 InviteCode / TokenLedger 无关；AuthSession 仅映射 User。
"""

import sys
import os
import io

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(REPO_ROOT)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from database_system.database_manager import DatabaseManager
from database_system.business_logic.models import Base, MagicLinkToken, AuthSession
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
    try:
        for tbl, model in (
            ("magic_link_tokens", MagicLinkToken),
            ("auth_sessions", AuthSession),
        ):
            if table_exists(engine, tbl):
                print(f"✅ {tbl} 已存在，跳过")
            else:
                print(f"📝 创建 {tbl} ...")
                Base.metadata.create_all(engine, tables=[model.__table__])
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
