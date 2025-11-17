#!/usr/bin/env python3
"""
从 JSON original_texts.json 补齐数据库 sentences 表的句子数据。

逻辑：
- 读取 backend/data/current/original_texts.json
- 连接 development 环境数据库
- 确认 original_texts 与 sentences 表存在
- 对于每个 text_id / sentence_id：
  - 若 sentences 表中不存在对应记录，则插入一条
  - 不改动已有记录
"""

import os
import sys
import json
from datetime import datetime

from sqlalchemy import inspect, text

# 确保能导入 backend / database_system
BASE_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
  sys.path.insert(0, BACKEND_DIR)

from database_system.database_manager import DatabaseManager
from database_system.data_storage.config.config import DB_FILES


def main(environment: str = "development") -> None:
  print("=" * 80)
  print(f"🚀 开始从 JSON 补齐 sentences 表 (环境: {environment})")
  print("=" * 80)

  json_path = os.path.join(BASE_DIR, "backend", "data", "current", "original_texts.json")
  if not os.path.exists(json_path):
    print(f"❌ 找不到 JSON 文件: {json_path}")
    return

  # 读取 JSON
  try:
    with open(json_path, "r", encoding="utf-8") as f:
      texts = json.load(f)
    print(f"📖 从 JSON 读取到 {len(texts)} 篇文章")
  except Exception as e:
    print(f"❌ 读取 JSON 失败: {e}")
    return

  # 连接数据库
  try:
    db_manager = DatabaseManager(environment)
    engine = db_manager.get_engine()
    session = db_manager.get_session()
  except Exception as e:
    print(f"❌ 连接数据库失败: {e}")
    return

  try:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "original_texts" not in tables or "sentences" not in tables:
      print(f"❌ original_texts 或 sentences 表不存在，当前表列表: {tables}")
      return

    # 预先加载 DB 里已有的 sentences (text_id, sentence_id) 集合
    existing_pairs = set()
    try:
      rows = session.execute(
        text("SELECT text_id, sentence_id FROM sentences")
      ).fetchall()
      for row in rows:
        if hasattr(row, "_mapping"):
          text_id = row._mapping["text_id"]
          sentence_id = row._mapping["sentence_id"]
        else:
          text_id, sentence_id = row
        existing_pairs.add((text_id, sentence_id))
      print(f"📊 当前数据库中已有 {len(existing_pairs)} 条句子记录")
    except Exception as e:
      print(f"⚠️ 读取现有 sentences 失败: {e}")

    inserted_count = 0
    skipped_count = 0

    for t in texts:
      text_id = t.get("text_id")
      sentences = t.get("text_by_sentence") or []
      print(f"\n📝 处理文章 text_id={text_id}, 句子数={len(sentences)}")

      for s in sentences:
        s_text_id = s.get("text_id", text_id)
        s_sentence_id = s.get("sentence_id")
        s_body = s.get("sentence_body", "").strip()

        if s_text_id is None or s_sentence_id is None:
          print(f"  ⚠️ 跳过无效句子: text_id={s_text_id}, sentence_id={s_sentence_id}")
          continue

        key = (s_text_id, s_sentence_id)
        if key in existing_pairs:
          skipped_count += 1
          continue

        # 插入新的 sentence 记录
        try:
          session.execute(
            text(
              """
              INSERT INTO sentences (text_id, sentence_id, sentence_body, sentence_difficulty_level, grammar_annotations, vocab_annotations, created_at)
              VALUES (:text_id, :sentence_id, :sentence_body, NULL, :grammar_annotations, :vocab_annotations, :created_at)
              """
            ),
            {
              "text_id": s_text_id,
              "sentence_id": s_sentence_id,
              "sentence_body": s_body,
              "grammar_annotations": json.dumps(s.get("grammar_annotations") or []),
              "vocab_annotations": json.dumps(s.get("vocab_annotations") or []),
              "created_at": datetime.now(),
            },
          )
          existing_pairs.add(key)
          inserted_count += 1
        except Exception as e:
          print(
            f"  ❌ 插入句子失败: text_id={s_text_id}, sentence_id={s_sentence_id}, error={e}"
          )

    session.commit()
    print("\n" + "=" * 80)
    print(
      f"✅ 迁移完成: 新插入 {inserted_count} 条句子记录，跳过 {skipped_count} 条已存在记录"
    )
    print("=" * 80)
  finally:
    session.close()


if __name__ == "__main__":
  main()


