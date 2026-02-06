"""
ChatMessageManagerDB - 使用统一数据库连接将聊天记录持久化到数据库

设计目标：
- 使用 DatabaseManager 统一连接（本地 dev.db，线上 PostgreSQL）
- 使用 SQLAlchemy Core 操作表，兼容 SQLite 和 PostgreSQL
- 不影响当前 JSON 存储逻辑，作为新增的持久化层
- 后续可通过单独的 API 读取，实现跨设备聊天记录展示
"""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Table, Column, Integer, String, Text, MetaData, 
    select, insert, and_
)

# 导入配置和数据库管理器
try:
    from backend.config import ENV
    from database_system.database_manager import DatabaseManager
except ImportError:
    # 如果导入失败，使用默认值
    ENV = "development"
    DatabaseManager = None


class ChatMessageManagerDB:
  """
  聊天记录 Manager，使用统一数据库连接（DatabaseManager）。
  
  本地环境：使用 dev.db (SQLite)
  线上环境：使用 PostgreSQL (通过 DATABASE_URL)
  
  表结构：chat_messages
    - id               SERIAL/INTEGER PRIMARY KEY
    - user_id          TEXT/VARCHAR
    - text_id          INTEGER
    - sentence_id      INTEGER
    - is_user          INTEGER (1=用户，0=AI)
    - content          TEXT
    - quote_sentence_id INTEGER
    - quote_text       TEXT
    - selected_token_json TEXT
    - created_at       TEXT (ISO 时间字符串)
  """

  def __init__(self, environment: Optional[str] = None) -> None:
    """
    初始化聊天记录管理器。
    
    参数:
      environment: 数据库环境（development/testing/production），默认使用 ENV
    """
    self.environment = environment or ENV
    self._lock = threading.Lock()
    
    # 使用 DatabaseManager 获取 engine
    if DatabaseManager is None:
      raise RuntimeError("DatabaseManager 不可用，请检查数据库配置")
    
    self.db_manager = DatabaseManager(self.environment)
    self.engine = self.db_manager.get_engine()
    self._is_postgres = self._check_is_postgres()
    
    # 定义表结构（使用 SQLAlchemy Core）
    self.metadata = MetaData()
    self._table = Table(
      'chat_messages',
      self.metadata,
      Column('id', Integer, primary_key=True, autoincrement=True),
      Column('user_id', String(255), nullable=True),
      Column('text_id', Integer, nullable=True),
      Column('sentence_id', Integer, nullable=True),
      Column('is_user', Integer, nullable=False),
      Column('content', Text, nullable=False),
      Column('quote_sentence_id', Integer, nullable=True),
      Column('quote_text', Text, nullable=True),
      Column('selected_token_json', Text, nullable=True),
      Column('created_at', String(255), nullable=False),
    )
    
    # 确保表存在
    self._init_table()
    
    print(f"✅ [ChatMessageManagerDB] 已初始化（环境: {self.environment}, 数据库: {'PostgreSQL' if self._is_postgres else 'SQLite'}）")

  def _check_is_postgres(self) -> bool:
    """检查当前数据库是否为 PostgreSQL"""
    database_url = self.db_manager.database_url
    return (
      database_url.startswith('postgresql://') or 
      database_url.startswith('postgresql+psycopg2://') or
      database_url.startswith('postgres://')
    )

  def _init_table(self) -> None:
    """确保 chat_messages 表存在（使用 SQLAlchemy 创建表）"""
    try:
      # 使用 SQLAlchemy 的 create_all 创建表（如果不存在）
      self.metadata.create_all(self.engine, checkfirst=True)
      print(f"✅ [ChatMessageManagerDB] 表 chat_messages 已就绪")
    except Exception as e:
      print(f"⚠️ [ChatMessageManagerDB] 创建表时出错（表可能已存在）: {e}")

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

    # 使用 SQLAlchemy Core 插入数据
    with self._lock:
      stmt = insert(self._table).values(
        user_id=user_id,
        text_id=text_id,
        sentence_id=sentence_id,
        is_user=1 if is_user else 0,
        content=content,
        quote_sentence_id=quote_sentence_id,
        quote_text=quote_text,
        selected_token_json=selected_token_json,
        created_at=created_at,
      )
      
      with self.engine.connect() as conn:
        conn.execute(stmt)
        conn.commit()

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
    # 使用 SQLAlchemy Core 构建查询
    stmt = select(
      self._table.c.id,
      self._table.c.user_id,
      self._table.c.text_id,
      self._table.c.sentence_id,
      self._table.c.is_user,
      self._table.c.content,
      self._table.c.quote_sentence_id,
      self._table.c.quote_text,
      self._table.c.selected_token_json,
      self._table.c.created_at,
    )

    # 添加过滤条件
    conditions = []
    if user_id is not None:
      conditions.append(self._table.c.user_id == user_id)
    if text_id is not None:
      conditions.append(self._table.c.text_id == text_id)
    if sentence_id is not None:
      conditions.append(self._table.c.sentence_id == sentence_id)

    print(f"🔍 [ChatMessageManagerDB] list_messages 调用: user_id={user_id}, text_id={text_id}, sentence_id={sentence_id}, limit={limit}, offset={offset}, conditions={len(conditions)}")

    if conditions:
      stmt = stmt.where(and_(*conditions))

    # 排序和分页
    # 注意：SQLite 和 PostgreSQL 对字符串时间排序的处理不同
    # 这里直接按 created_at 字符串排序（ISO 格式字符串可以正确排序）
    stmt = stmt.order_by(self._table.c.created_at.asc()).limit(limit).offset(offset)

    # 执行查询
    with self.engine.connect() as conn:
      rows = conn.execute(stmt).fetchall()

    print(f"✅ [ChatMessageManagerDB] 查询结果: 找到 {len(rows)} 条消息")
    if len(rows) > 0:
      first_row = rows[0]
      print(f"📋 [ChatMessageManagerDB] 第一条消息: user_id={first_row.user_id}, text_id={first_row.text_id}, sentence_id={first_row.sentence_id}, is_user={first_row.is_user}")

    # 转换结果
    results: List[Dict[str, Any]] = []
    for row in rows:
      try:
        selected = json.loads(row.selected_token_json) if row.selected_token_json else None
      except (json.JSONDecodeError, TypeError):
        selected = row.selected_token_json

      results.append(
        {
          "id": row.id,
          "user_id": row.user_id,
          "text_id": row.text_id,
          "sentence_id": row.sentence_id,
          "is_user": bool(row.is_user),
          "content": row.content,
          "quote_sentence_id": row.quote_sentence_id,
          "quote_text": row.quote_text,
          "selected_token": selected,
          "created_at": row.created_at,
        }
      )

    return results


