#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键回填所有预置文章的 difficulty / exam_content（覆盖已有值）。

用法:
    python backfill_preset_text_metadata.py
    python backfill_preset_text_metadata.py --no-force   # 仅填空字段
"""

import argparse
import io
import os
import sys

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(REPO_ROOT)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
from sqlalchemy import inspect, text
from database_system.database_manager import DatabaseManager
from backend.data_managers.preset_articles import backfill_all_preset_metadata



def column_exists(engine, table_name, column_name):
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return False
    return column_name in {c['name'] for c in inspector.get_columns(table_name)}


def ensure_columns(engine):
    with engine.begin() as conn:
        if not column_exists(engine, 'original_texts', 'difficulty'):
            conn.execute(text('ALTER TABLE original_texts ADD COLUMN difficulty VARCHAR(32)'))
            print('[OK] Added original_texts.difficulty')
        else:
            print('[SKIP] original_texts.difficulty exists')

        if not column_exists(engine, 'original_texts', 'exam_content'):
            conn.execute(text('ALTER TABLE original_texts ADD COLUMN exam_content VARCHAR(64)'))
            print('[OK] Added original_texts.exam_content')
        else:
            print('[SKIP] original_texts.exam_content exists')


def main():
    parser = argparse.ArgumentParser(description='Backfill preset article metadata')
    parser.add_argument(
        '--no-force',
        action='store_true',
        help='Only fill empty fields; default is force overwrite from preset JSON',
    )
    args = parser.parse_args()
    force = not args.no_force

    try:
        from backend.config import ENV
        environment = ENV
    except ImportError:
        environment = os.getenv('ENV', 'development')

    print(f'[INFO] Environment: {environment}, force={force}')
    db_manager = DatabaseManager(environment)
    engine = db_manager.get_engine()
    session = db_manager.get_session()

    try:
        ensure_columns(engine)
        stats = backfill_all_preset_metadata(session, force=force)
        session.commit()
        print(
            f"[DONE] scanned={stats['scanned']} matched_preset={stats['matched']} "
            f"difficulty_updated={stats['difficulty_updated']} "
            f"exam_updated={stats['exam_updated']} exam_cleared={stats['exam_cleared']}"
        )
    except Exception as e:
        session.rollback()
        print(f'[ERROR] {e}')
        raise
    finally:
        session.close()


if __name__ == '__main__':
    main()
