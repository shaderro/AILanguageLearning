#!/usr/bin/env python3
"""
回填预置文章（及可选的全部 zh/ja 旧文章）的 WordToken 分词数据。

适用场景：早期导入的预置文只有字符级 Token，没有 WordToken；新上传文章已正常分词。

用法（在项目根目录执行）:
  python backend/scripts/backfill_preset_word_tokens.py
  python backend/scripts/backfill_preset_word_tokens.py --all-zh-ja

需要: jieba（中文）、janome（日文），与 requirements.txt 一致。

--- 线上如何保证日语（及中文）预置文章都经过分词 ---

1) 依赖：生产镜像/环境必须安装 requirements（含 janome、jieba）。若构建阶段未装，分词不会生成。

2) 发版后执行一次回填（幂等，已分词的文章会 skipped）:
     ENV=production python backend/scripts/backfill_preset_word_tokens.py
   或在批量导入预置后顺带执行:
     python seed_preset_articles_for_all.py --env production --backfill-word-tokens

3) 新用户：注册时仍会 seed 预置；若某预置文已存在，会走修复逻辑补 WordToken。

4) 仅日语：默认只处理「预置 JSON 标题匹配」的 zh/ja；若还要修用户自己上传的旧日文，请加 --all-zh-ja。
"""
from __future__ import annotations

import argparse
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(REPO_ROOT)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill WordToken segmentation for preset (or all zh/ja) texts.")
    parser.add_argument(
        "--all-zh-ja",
        action="store_true",
        help="Also fix any Chinese/Japanese article missing word tokens, not only preset titles.",
    )
    parser.add_argument(
        "--no-commit",
        action="store_true",
        help="Run changes but roll back at the end (dry-run for DB writes).",
    )
    args = parser.parse_args()

    from backend.config import ENV
    from database_system.database_manager import get_database_manager
    from backend.data_managers.preset_articles import backfill_word_tokens_missing_word_level

    db_manager = get_database_manager(ENV)
    session = db_manager.get_session()
    try:
        stats = backfill_word_tokens_missing_word_level(
            session,
            only_preset_titles=not args.all_zh_ja,
            commit=not args.no_commit,
        )
        print("Done.")
        for k, v in stats.items():
            if k == "error_details" and not v:
                continue
            print(f"  {k}: {v}")
        if args.no_commit:
            session.rollback()
            print("(no-commit: rolled back)")
    finally:
        session.close()


if __name__ == "__main__":
    main()
