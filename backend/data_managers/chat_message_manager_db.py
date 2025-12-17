"""
ChatMessageManagerDB - 使用 SQLite 将聊天记录持久化到数据库

设计目标：
- 独立于现有 ORM / business_logic，实现一个轻量级的聊天记录表
- 不影响当前 JSON 存储逻辑，作为新增的持久化层
- 后续可通过单独的 API 读取，实现跨设备聊天记录展示
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


class ChatMessageManagerDB:
  """
  简单的聊天记录 Manager，直接操作 SQLite 数据库。

  表结构：chat_messages
    - id               INTEGER PK
    - user_id          TEXT (预留，当前可为 NULL，后续可接入登录系统)
    - text_id          INTEGER
    - sentence_id      INTEGER
    - is_user          INTEGER (1=用户，0=AI)
    - content          TEXT
    - quote_sentence_id INTEGER (引用的句子 id，可选)
    - quote_text       TEXT (引用句子内容，可选)
    - selected_token_json TEXT (SelectedToken.to_dict() 的 JSON，可选)
    - created_at       TEXT (ISO 时间)
  """

  def __init__(self, db_path: Optional[str] = None) -> None:
    # 默认使用现有 language_learning.db
    if db_path is None:
      # backend/data_managers/chat_message_manager_db.py -> backend/
      base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
      db_path = os.path.join(
        base_dir, "database_system", "data_storage", "data", "language_learning.db"
      )
    self.db_path = db_path
    self._lock = threading.Lock()
    self._init_table()

  # ---------- 内部工具 ----------
  def _get_conn(self) -> sqlite3.Connection:
    return sqlite3.connect(self.db_path)

  def _init_table(self) -> None:
    """确保 chat_messages 表存在。"""
    with self._get_conn() as conn:
      conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id TEXT,
          text_id INTEGER,
          sentence_id INTEGER,
          is_user INTEGER NOT NULL,
          content TEXT NOT NULL,
          quote_sentence_id INTEGER,
          quote_text TEXT,
          selected_token_json TEXT,
          created_at TEXT NOT NULL
        );
        """
      )

  # ---------- 对外接口 ----------
  def add_message(
    self,
    *,
    user_id: Optional[str] = None,
    text_id: Optional[int] = None,
    sentence_id: Optional[int] = None,
    is_user: bool,
    content: str,
    quote_sentence_id: Optional[int] = None,
    quote_text: Optional[str] = None,
    selected_token: Optional[Any] = None,
  ) -> None:
    """
    写入一条聊天消息。

    selected_token:
      - 可以是 dict / dataclass / 其他对象（将被 json.dumps）。
    """
    created_at = datetime.utcnow().isoformat()

    if selected_token is None:
      selected_token_json = None
    else:
      try:
        if is_dataclass(selected_token):
          selected_token = asdict(selected_token)
        selected_token_json = json.dumps(selected_token, ensure_ascii=False)
      except TypeError:
        # 不可序列化时，退化为 str
        selected_token_json = json.dumps(str(selected_token), ensure_ascii=False)

    with self._lock, self._get_conn() as conn:
      conn.execute(
        """
        INSERT INTO chat_messages (
          user_id, text_id, sentence_id,
          is_user, content,
          quote_sentence_id, quote_text,
          selected_token_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
          user_id,
          text_id,
          sentence_id,
          1 if is_user else 0,
          content,
          quote_sentence_id,
          quote_text,
          selected_token_json,
          created_at,
        ),
      )

  def list_messages(
    self,
    *,
    user_id: Optional[str] = None,
    text_id: Optional[int] = None,
    sentence_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
  ) -> List[Dict[str, Any]]:
    """
    读取消息列表，按 created_at 升序返回（旧→新）。
    后续用于跨设备聊天记录展示。
    """
    conditions = []
    params: List[Any] = []

    if user_id is not None:
      conditions.append("user_id = ?")
      params.append(user_id)
    if text_id is not None:
      conditions.append("text_id = ?")
      params.append(text_id)
    if sentence_id is not None:
      conditions.append("sentence_id = ?")
      params.append(sentence_id)

    where_clause = ""
    if conditions:
      where_clause = "WHERE " + " AND ".join(conditions)

    query = f"""
      SELECT
        id, user_id, text_id, sentence_id,
        is_user, content,
        quote_sentence_id, quote_text,
        selected_token_json, created_at
      FROM chat_messages
      {where_clause}
      ORDER BY datetime(created_at) ASC
      LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    with self._get_conn() as conn:
      cursor = conn.execute(query, params)
      rows = cursor.fetchall()

    results: List[Dict[str, Any]] = []
    for (
      mid,
      u_id,
      t_id,
      s_id,
      is_user_int,
      content,
      q_sid,
      q_text,
      selected_json,
      created_at,
    ) in rows:
      try:
        selected = json.loads(selected_json) if selected_json else None
      except json.JSONDecodeError:
        selected = selected_json

      results.append(
        {
          "id": mid,
          "user_id": u_id,
          "text_id": t_id,
          "sentence_id": s_id,
          "is_user": bool(is_user_int),
          "content": content,
          "quote_sentence_id": q_sid,
          "quote_text": q_text,
          "selected_token": selected,
          "created_at": created_at,
        }
      )

    return results


