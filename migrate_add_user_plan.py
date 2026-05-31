#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add users.plan column ('free' | 'pro', default 'free')."""

import io
import os
import sys

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
        print(f"[WARN] check column failed: {e}")
        return False


def add_user_plan_column(engine, session):
    if check_column_exists(engine, 'users', 'plan'):
        print("[SKIP] users.plan already exists")
        return
    print("[ADD] users.plan ...")
    session.execute(text("ALTER TABLE users ADD COLUMN plan VARCHAR(16) DEFAULT 'free' NOT NULL"))
    session.commit()
    print("[OK] users.plan added")


def main():
    try:
        from backend.config import ENV
        environment = ENV
    except ImportError:
        environment = os.getenv("ENV", "development")

    print(f"[INFO] migrate users.plan (env={environment})")
    db_manager = DatabaseManager(environment)
    engine = db_manager.get_engine()
    session = db_manager.get_session()
    try:
        add_user_plan_column(engine, session)
        print("[DONE]")
    finally:
        session.close()


if __name__ == "__main__":
    main()
