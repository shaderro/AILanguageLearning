"""
预置文章导入与同步逻辑（供 API 与脚本复用）。

- seed_presets_for_user: 按用户、语言导入预置文章（幂等：同用户同标题已存在则跳过）。
- load_preset_files: 从 backend/data/presets/articles 加载 JSON 定义。
"""

import os
import json
from typing import List, Dict, Any

from sqlalchemy.orm import Session

from database_system.business_logic.models import OriginalText
from backend.data_managers import OriginalTextManagerDB


LANG_CODE_TO_NAME = {
    'zh': '中文',
    'en': '英文',
    'de': '德文',
}


def get_presets_base_dir() -> str:
    """Return backend/data/presets/articles absolute path."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'presets', 'articles')


def load_preset_files(languages: List[str]) -> List[Dict[str, Any]]:
    """
    加载预置文章 JSON。支持子目录（如 de/、zh/）及根目录下的 .json。
    languages: 语言代码列表，空表示全部。
    """
    base_dir = get_presets_base_dir()
    presets: List[Dict[str, Any]] = []

    if not os.path.isdir(base_dir):
        return presets

    for root, _dirs, files in os.walk(base_dir):
        for filename in files:
            if not filename.endswith('.json'):
                continue
            path = os.path.join(root, filename)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                lang_code = data.get('language_code')
                if languages and lang_code not in languages:
                    continue
                presets.append(data)
            except Exception:
                continue

    return presets


def seed_presets_for_user(
    session: Session,
    user_id: int,
    language_codes: List[str],
    *,
    commit: bool = True,
) -> None:
    """
    为指定用户按语言导入预置文章（幂等：同用户同标题已存在则跳过）。

    - session: 当前请求或脚本的 DB Session。
    - user_id: 用户 ID。
    - language_codes: 要导入的语言代码列表（如 ['de', 'zh']），空表示导入全部支持语言。
    - commit: 是否在本函数内提交；从 API 调用时传 False，由路由统一 commit。
    """
    text_manager = OriginalTextManagerDB(session)
    languages = language_codes if language_codes else list(LANG_CODE_TO_NAME.keys())
    presets = load_preset_files(languages)
    if not presets:
        return

    for preset in presets:
        preset_id = preset.get('preset_id') or preset.get('id')
        lang_code = preset.get('language_code')
        title = preset.get('title')
        sentences = preset.get('sentences') or []

        if not lang_code or not title or not sentences:
            continue

        language_name = LANG_CODE_TO_NAME.get(lang_code)
        if not language_name:
            continue

        existing = (
            session.query(OriginalText)
            .filter(
                OriginalText.user_id == user_id,
                OriginalText.text_title == title,
            )
            .first()
        )
        if existing:
            continue

        text_dto = text_manager.add_text(
            text_title=title,
            user_id=user_id,
            language=language_name,
            processing_status='completed',
        )

        for raw in sentences:
            if isinstance(raw, dict):
                sentence_body = raw.get('sentence') or raw.get('text') or raw.get('sentence_body')
                difficulty = raw.get('difficulty')
            else:
                sentence_body = str(raw)
                difficulty = None

            if not sentence_body or not sentence_body.strip():
                continue

            text_manager.add_sentence_to_text(
                text_id=text_dto.text_id,
                sentence_text=sentence_body.strip(),
                difficulty_level=difficulty,
            )

    if commit:
        session.commit()
