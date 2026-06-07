#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add Paddle Billing columns (users.paddle_*) and paddle_webhook_events table."""

import io
import os
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(REPO_ROOT)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from sqlalchemy import inspect, text
from database_system.business_logic.models import Base, PaddleWebhookEvent
from database_system.database_manager import DatabaseManager


def column_exists(engine, table: str, column: str) -> bool:
    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return False
    return column in {c["name"] for c in inspector.get_columns(table)}


def table_exists(engine, table: str) -> bool:
    return table in inspect(engine).get_table_names()


def main():
    try:
        from backend.config import ENV
        environment = ENV
    except ImportError:
        environment = os.getenv("ENV", "development")

    print(f"[INFO] migrate paddle billing (env={environment})")
    db_manager = DatabaseManager(environment)
    engine = db_manager.get_engine()
    session = db_manager.get_session()
    try:
        for col_name, col_sql in (
            ("paddle_customer_id", "VARCHAR(64)"),
            ("paddle_subscription_id", "VARCHAR(64)"),
        ):
            if column_exists(engine, "users", col_name):
                print(f"[SKIP] users.{col_name} already exists")
            else:
                print(f"[ADD] users.{col_name} ...")
                session.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_sql}"))
                session.commit()
                print(f"[OK] users.{col_name} added")

        if table_exists(engine, "paddle_webhook_events"):
            print("[SKIP] paddle_webhook_events already exists")
        else:
            print("[ADD] paddle_webhook_events ...")
            Base.metadata.create_all(engine, tables=[PaddleWebhookEvent.__table__])
            print("[OK] paddle_webhook_events created")

        print("[DONE]")
    finally:
        session.close()


if __name__ == "__main__":
    main()
