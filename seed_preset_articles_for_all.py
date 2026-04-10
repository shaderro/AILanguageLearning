#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为多个用户批量导入预置文章（基于 backend/data/presets/articles 下的 JSON）。

用法示例（在项目根目录运行）：

    # 为所有用户导入所有语言的预置文章（使用 ENV 或默认 development）
    python seed_preset_articles_for_all.py

    # 仅为所有用户导入中文预置文章
    python seed_preset_articles_for_all.py --languages zh

    # 仅为指定用户导入（例如 3,5,7），只导入德文预置
    python seed_preset_articles_for_all.py --user-ids 3,5,7 --languages de

    # 指定环境（如 production），一般只在线上运维时使用
    python seed_preset_articles_for_all.py --env production

    # 为所有用户导入后，再全库回填预置文中缺失的 WordToken（发版后推荐执行一次）
    python seed_preset_articles_for_all.py --env production --backfill-word-tokens
"""

import os
import sys
import io
import argparse
from typing import List, Optional

# Fix Windows 控制台编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 将项目根目录加入 sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database_system.database_manager import DatabaseManager  # type: ignore
from database_system.business_logic.models import User  # type: ignore
from backend.data_managers.preset_articles import (  # type: ignore
    LANG_CODE_TO_NAME,
    backfill_word_tokens_missing_word_level,
    seed_presets_for_user,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="为多个用户批量导入预置阅读文章（基于 backend/data/presets/articles）。"
    )
    parser.add_argument(
        '--user-ids',
        type=str,
        default='',
        help="逗号分隔的用户 ID 列表（如 '3,5,7'）。如果留空，则为所有用户导入。",
    )
    parser.add_argument(
        '--languages',
        type=str,
        default='',
        help="逗号分隔的语言代码列表（如 'de,zh'）。留空表示导入所有支持语言。",
    )
    parser.add_argument(
        '--env',
        type=str,
        default=None,
        help="DatabaseManager 环境名称（默认使用 backend.config.ENV 或 ENV 环境变量，缺省为 'development'）。",
    )
    parser.add_argument(
        '--backfill-word-tokens',
        action='store_true',
        help="全部用户预置导入结束后，再执行一次全库预置文章分词回填（补全仅有字符 Token、无 WordToken 的中/日预置文）。线上推荐定期或在发版后执行一次。",
    )
    return parser.parse_args()


def resolve_environment(cli_env: Optional[str]) -> str:
    if cli_env:
        return cli_env
    try:
        from backend.config import ENV  # type: ignore
        return ENV
    except Exception:
        return os.getenv('ENV', 'development')


def main() -> None:
    args = parse_args()

    # 解析用户 ID 列表
    user_ids: List[int] = []
    if args.user_ids.strip():
        for part in args.user_ids.split(','):
            part = part.strip()
            if not part:
                continue
            try:
                user_ids.append(int(part))
            except ValueError:
                print(f"[WARN] 无法解析用户 ID '{part}'，已跳过。")

    # 解析语言代码列表
    languages: List[str] = []
    if args.languages.strip():
        for part in args.languages.split(','):
            code = part.strip()
            if not code:
                continue
            if code not in LANG_CODE_TO_NAME:
                print(f"[WARN] 不支持的语言代码 '{code}'，已跳过。支持: {list(LANG_CODE_TO_NAME.keys())}")
                continue
            languages.append(code)

    environment = resolve_environment(args.env)

    print(f"[INFO] 批量导入预置文章:")
    print(f"       环境: {environment}")
    print(f"       目标用户: {'ALL' if not user_ids else user_ids}")
    print(f"       语言: {languages or 'ALL'}")

    db_manager = DatabaseManager(environment)

    # 如果未指定 user_ids，则从数据库中读取所有用户
    if not user_ids:
        session = db_manager.get_session()
        try:
            all_users = session.query(User).all()
            user_ids = [u.user_id for u in all_users]
            print(f"[INFO] 从数据库中读取到 {len(user_ids)} 个用户。")
        finally:
            session.close()

    total_users = len(user_ids)
    processed = 0

    for uid in user_ids:
        processed += 1
        print(f"\n[INFO] ({processed}/{total_users}) 为用户 user_id={uid} 导入预置文章...")

        session = db_manager.get_session()
        try:
            seed_presets_for_user(
                session=session,
                user_id=uid,
                language_codes=languages,
                commit=True,
            )
            print(f"[OK] 用户 {uid} 处理完成。")
        except Exception as e:
            session.rollback()
            print(f"[ERROR] 为用户 {uid} 导入预置文章失败: {e}")
        finally:
            session.close()

    print(f"\n[DONE] 已尝试为 {total_users} 个用户导入预置文章。")

    if args.backfill_word_tokens:
        print("\n[INFO] 开始全库预置文章 WordToken 回填（仅标题匹配预置 JSON 的 zh/ja）...")
        session = db_manager.get_session()
        try:
            stats = backfill_word_tokens_missing_word_level(
                session,
                only_preset_titles=True,
                commit=True,
            )
            print(f"[OK] 回填完成: {stats}")
        except Exception as e:
            session.rollback()
            print(f"[ERROR] WordToken 回填失败: {e}")
            raise
        finally:
            session.close()


if __name__ == '__main__':
    main()

