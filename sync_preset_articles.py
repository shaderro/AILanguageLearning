#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步已有预置文章：根据当前 backend/data/presets/articles/*.json 内容，
更新已导入过的用户预置文章（按标题+语言匹配），使句子与 JSON 一致。

使用场景：修改了预置 JSON 后，手动执行此脚本，使已导入该预置的用户数据与 JSON 同步。

用法示例：

    # 同步所有用户、所有语言的预置文章
    python sync_preset_articles.py

    # 仅同步指定用户
    python sync_preset_articles.py --user-id 2

    # 仅同步指定语言
    python sync_preset_articles.py --languages de,zh

    # 试跑（不写入数据库）
    python sync_preset_articles.py --dry-run
"""

import os
import sys
import io
import argparse
from typing import List, Optional

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy.orm import Session  # type: ignore
from database_system.database_manager import DatabaseManager  # type: ignore
from database_system.business_logic.models import OriginalText, Sentence  # type: ignore
from backend.data_managers.preset_articles import (  # type: ignore
    load_preset_files,
    LANG_CODE_TO_NAME,
)
from backend.data_managers import OriginalTextManagerDB  # type: ignore


def sync_one_text(
    session: Session,
    text: OriginalText,
    sentences_from_preset: List[str],
    text_manager: OriginalTextManagerDB,
    dry_run: bool,
) -> bool:
    """
    将一篇已存在的预置文章内容替换为 preset 的 sentences。
    按标题+语言已确认为预置来源；直接删除该 text 下所有句子再按 JSON 重插。
    """
    if dry_run:
        return True

    # 删除该文章下所有句子（DB 层 FK ondelete=CASCADE 会清理 tokens 等）
    session.query(Sentence).filter(Sentence.text_id == text.text_id).delete(synchronize_session=False)
    session.flush()

    for raw in sentences_from_preset:
        if isinstance(raw, dict):
            sentence_body = raw.get('sentence') or raw.get('text') or raw.get('sentence_body')
            difficulty = raw.get('difficulty')
        else:
            sentence_body = str(raw)
            difficulty = None

        if not sentence_body or not sentence_body.strip():
            continue

        text_manager.add_sentence_to_text(
            text_id=text.text_id,
            sentence_text=sentence_body.strip(),
            difficulty_level=difficulty,
        )
    return True


def run_sync(
    environment: str,
    user_id: Optional[int],
    languages: List[str],
    dry_run: bool,
) -> None:
    base_languages = languages if languages else list(LANG_CODE_TO_NAME.keys())
    presets = load_preset_files(base_languages)
    if not presets:
        print("[INFO] No preset definitions found, nothing to sync.")
        return

    db_manager = DatabaseManager(environment)
    session = db_manager.get_session()
    text_manager = OriginalTextManagerDB(session)

    synced_count = 0
    try:
        for preset in presets:
            lang_code = preset.get('language_code')
            title = preset.get('title')
            sentences = preset.get('sentences') or []
            if not lang_code or not title or not sentences:
                continue

            language_name = LANG_CODE_TO_NAME.get(lang_code)
            if not language_name:
                continue

            q = (
                session.query(OriginalText)
                .filter(
                    OriginalText.text_title == title,
                    OriginalText.language == language_name,
                )
            )
            if user_id is not None:
                q = q.filter(OriginalText.user_id == user_id)
            texts = q.all()

            for text in texts:
                if dry_run:
                    print(f"[DRY-RUN] Would sync user_id={text.user_id} text_id={text.text_id} '{title}' ({language_name})")
                else:
                    sync_one_text(session, text, sentences, text_manager, dry_run=False)
                    print(f"[SYNC] user_id={text.user_id} text_id={text.text_id} '{title}' ({language_name})")
                synced_count += 1

        if not dry_run:
            session.commit()
        print(f"[DONE] Synced {synced_count} preset article(s)." + (" (dry-run)" if dry_run else ""))
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Sync failed: {e}")
        raise
    finally:
        session.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync existing preset articles to match current JSON definitions (by title + language)."
    )
    parser.add_argument(
        "--user-id",
        type=int,
        default=None,
        help="If set, only sync preset articles for this user.",
    )
    parser.add_argument(
        "--languages",
        type=str,
        default="",
        help="Comma-separated language codes (e.g. de,zh). Empty = all.",
    )
    parser.add_argument(
        "--env",
        type=str,
        default=None,
        help="Environment for DatabaseManager (default: backend.config.ENV or 'development').",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print what would be synced, do not write to DB.",
    )
    return parser.parse_args()


def resolve_environment(cli_env: Optional[str]) -> str:
    if cli_env:
        return cli_env
    try:
        from backend.config import ENV  # type: ignore
        return ENV
    except Exception:
        return os.getenv("ENV", "development")


def main() -> None:
    args = parse_args()
    user_id = args.user_id
    languages_raw = args.languages.strip()
    languages = [s.strip() for s in languages_raw.split(",") if s.strip()] if languages_raw else []
    environment = resolve_environment(args.env)

    print(f"[INFO] user_id={user_id}, languages={languages or 'ALL'}, env={environment}, dry_run={args.dry_run}")
    run_sync(environment, user_id, languages, args.dry_run)


if __name__ == "__main__":
    main()
