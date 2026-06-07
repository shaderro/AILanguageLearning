#!/usr/bin/env python3
"""Generate pgAdmin SQL for preset difficulty backfill."""
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(REPO_ROOT)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from backend.data_managers.preset_articles import (
    load_preset_files,
    _normalize_preset_difficulty,
    _normalize_exam_content,
    LANG_CODE_TO_NAME,
)


def esc(s: str) -> str:
    return (s or "").replace("'", "''")


def main():
    out_path = os.path.join(os.path.dirname(__file__), "backfill_preset_difficulty_pgadmin.sql")
    lines = [
        "-- LinkText: backfill preset article difficulty (PostgreSQL / pgAdmin)",
        "-- Match rows by original_texts.language + text_title",
        "",
        "ALTER TABLE original_texts ADD COLUMN IF NOT EXISTS difficulty VARCHAR(32);",
        "ALTER TABLE original_texts ADD COLUMN IF NOT EXISTS exam_content VARCHAR(64);",
        "",
        "BEGIN;",
        "",
    ]

    for p in load_preset_files([]):
        lc = p.get("language_code")
        title = (p.get("title") or "").strip()
        if not lc or not title:
            continue
        lang_name = LANG_CODE_TO_NAME.get(lc)
        if not lang_name:
            continue
        t = esc(title)
        ln = esc(lang_name)
        diff = _normalize_preset_difficulty(p)
        exam = _normalize_exam_content(p)
        if diff:
            lines.append(
                f"UPDATE original_texts SET difficulty = '{diff}' "
                f"WHERE language = '{ln}' AND text_title = '{t}';"
            )
        exam_sql = "NULL" if not exam else f"'{esc(exam)}'"
        lines.append(
            f"UPDATE original_texts SET exam_content = {exam_sql} "
            f"WHERE language = '{ln}' AND text_title = '{t}';"
        )

    lines.extend(
        [
            "",
            "COMMIT;",
            "",
            "-- Check results:",
            "SELECT language, difficulty, COUNT(*) AS cnt",
            "FROM original_texts",
            "WHERE difficulty IS NOT NULL",
            "GROUP BY language, difficulty",
            "ORDER BY language, difficulty;",
            "",
            "SELECT text_id, language, text_title, difficulty, exam_content",
            "FROM original_texts",
            "WHERE difficulty IS NULL AND language IN ('德文','英文','中文','日语','西班牙语','法语','韩语','阿拉伯语','俄语');",
        ]
    )

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Wrote {out_path} ({len(load_preset_files([]))} presets)")


if __name__ == "__main__":
    main()
