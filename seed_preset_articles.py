#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seed preset reading articles for a specific user.

Usage examples:

    # Seed all preset languages for user 2 (using ENV or default 'development')
    python seed_preset_articles.py --user-id 2

    # Seed only German presets for user 2
    python seed_preset_articles.py --user-id 2 --languages de

    # Seed German and Chinese presets for user 2
    python seed_preset_articles.py --user-id 2 --languages de,zh

Preset article files live under:
    backend/data/presets/articles/*.json

Each JSON file should have shape:
{
  "preset_id": "de_beginner_little_prince",
  "language_code": "de",
  "title": "Der kleine Prinz (Auszug)",
  "difficulty": "beginner",        # optional: 'beginner'|'intermediate'|'advanced'
  "sentences": [
    "First sentence.",
    "Second sentence."
  ]
}
"""

import os
import sys
import io
import argparse
from typing import List

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from database_system.database_manager import DatabaseManager  # type: ignore
from backend.data_managers.preset_articles import (  # type: ignore
    load_preset_files,
    seed_presets_for_user as _seed_presets_for_user,
)


def seed_presets_for_user(user_id: int, environment: str, languages: List[str]) -> None:
    """Create preset articles in DB for a specific user (CLI entrypoint)."""
    print(f"[INFO] Seeding preset articles for user_id={user_id}, environment={environment}, languages={languages or 'ALL'}")

    presets = load_preset_files(languages)
    if not presets:
        print("[INFO] No presets to import, exiting.")
        return

    db_manager = DatabaseManager(environment)
    session = db_manager.get_session()
    try:
        _seed_presets_for_user(session, user_id, languages, commit=True)
        print(f"[DONE] Seeded presets for user {user_id}")
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Failed to seed presets for user {user_id}: {e}")
        raise
    finally:
        session.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed preset reading articles for a specific user.")
    parser.add_argument(
        '--user-id',
        type=int,
        required=True,
        help='Target user ID to attach preset articles to.',
    )
    parser.add_argument(
        '--languages',
        type=str,
        default='',
        help="Comma separated language codes to seed (e.g. 'de,zh'). Empty means all supported languages.",
    )
    parser.add_argument(
        '--env',
        type=str,
        default=None,
        help="Environment name for DatabaseManager (default: use backend.config.ENV or ENV envvar, else 'development').",
    )
    return parser.parse_args()


def resolve_environment(cli_env: str | None) -> str:
    if cli_env:
        return cli_env
    try:
        from backend.config import ENV  # type: ignore
        return ENV
    except Exception:
        return os.getenv('ENV', 'development')


def main() -> None:
    args = parse_args()
    user_id = args.user_id
    languages_raw = args.languages.strip()
    languages = [s.strip() for s in languages_raw.split(',') if s.strip()] if languages_raw else []
    environment = resolve_environment(args.env)

    print(f"[INFO] Arguments: user_id={user_id}, languages={languages or 'ALL'}, env={environment}")
    seed_presets_for_user(user_id=user_id, environment=environment, languages=languages)


if __name__ == '__main__':
    main()

