"""
预置文章导入与同步逻辑（供 API 与脚本复用）。

- seed_presets_for_user: 按用户、语言导入预置文章（幂等：同用户同标题已存在则跳过）。
- load_preset_files: 从 backend/data/presets/articles 加载 JSON 定义。
"""

import os
import json
import time
from functools import lru_cache
from typing import List, Dict, Any, Optional, Tuple, Set

from sqlalchemy import func, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from database_system.business_logic.models import (
    OriginalText,
    Sentence,
    Token,
    TokenType,
    WordToken,
)
from backend.data_managers import OriginalTextManagerDB
from backend.preprocessing.language_classification import (
    get_language_code,
    is_non_whitespace_language,
)
from backend.preprocessing.token_processor import (
    split_tokens,
    create_token_with_id,
)
from backend.preprocessing.word_segmentation import word_segmentation


# 远程 PostgreSQL 上单句 flush 过多行时，易触发大包 INSERT 被代理/服务端断开；分批落库。
WORD_TOKEN_FLUSH_CHUNK_SIZE = 8

LANG_CODE_TO_NAME = {
    'zh': '中文',
    'en': '英文',
    'de': '德文',
    'es': '西班牙语',
    'fr': '法语',
    'ja': '日语',
    'ko': '韩语',
    'ar': '阿拉伯语',
    'ru': '俄语',
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


@lru_cache(maxsize=1)
def _build_preset_difficulty_map() -> Dict[Tuple[str, str], str]:
    mapping: Dict[Tuple[str, str], str] = {}
    for preset in load_preset_files([]):
        lang_code = str(preset.get('language_code') or '').strip()
        title = str(preset.get('title') or '').strip()
        difficulty = str(preset.get('difficulty') or '').strip().lower()
        if not lang_code or not title or not difficulty:
            continue
        mapping[(lang_code, title)] = difficulty
    return mapping


def get_preset_difficulty_for_text(language_name: Optional[str], title: Optional[str]) -> Optional[str]:
    if not language_name or not title:
        return None

    reverse_lang_map = {name: code for code, name in LANG_CODE_TO_NAME.items()}
    lang_code = reverse_lang_map.get(str(language_name).strip())
    if not lang_code:
        return None

    return _build_preset_difficulty_map().get((lang_code, str(title).strip()))


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
            _repair_existing_preset_text_if_needed(
                session=session,
                text=existing,
                language_code=lang_code,
            )
            continue

        text_dto = text_manager.add_text(
            text_title=title,
            user_id=user_id,
            language=language_name,
            # 先标记为 processing，预处理完成后再更新为 completed
            processing_status='processing',
        )

        sentence_entries: List[Dict[str, Any]] = []
        for raw in sentences:
            if isinstance(raw, dict):
                sentence_body = raw.get('sentence') or raw.get('text') or raw.get('sentence_body')
                difficulty = raw.get('difficulty')
            else:
                sentence_body = str(raw)
                difficulty = None

            if not sentence_body or not sentence_body.strip():
                continue

            sentence_entries.append({
                "sentence_text": sentence_body.strip(),
                "difficulty_level": difficulty,
            })

        if sentence_entries:
            text_manager.add_sentences_to_text(
                text_id=text_dto.text_id,
                sentences=sentence_entries,
            )

        # 为该文章生成 Token / WordToken（包含中文分字）
        try:
            _generate_tokens_for_text(
                session=session,
                text_id=text_dto.text_id,
                language_code=lang_code,
            )
            # 预处理完成，更新处理状态
            existing_model = (
                session.query(OriginalText)
                .filter(OriginalText.text_id == text_dto.text_id)
                .first()
            )
            if existing_model:
                existing_model.processing_status = 'completed'
        except Exception:
            # 预处理失败时，不阻塞导入主流程，仅保留句子级数据
            existing_model = (
                session.query(OriginalText)
                .filter(OriginalText.text_id == text_dto.text_id)
                .first()
            )
            if existing_model:
                existing_model.processing_status = 'failed'

    if commit:
        session.commit()


def _needs_word_token_backfill(session: Session, text_id: int) -> bool:
    """True if the text has char tokens but no word-level rows (old seed without segmentation)."""
    token_n = session.query(Token).filter(Token.text_id == text_id).count()
    if token_n == 0:
        return False
    wt_n = session.query(WordToken).filter(WordToken.text_id == text_id).count()
    return wt_n == 0


def _clear_tokens_for_text(session: Session, text_id: int) -> None:
    """Remove Token / WordToken rows so _generate_tokens_for_text can run again."""
    session.query(WordToken).filter(WordToken.text_id == text_id).delete(synchronize_session=False)
    session.query(Token).filter(Token.text_id == text_id).delete(synchronize_session=False)
    session.flush()


def _repair_existing_preset_text_if_needed(
    session: Session,
    text: OriginalText,
    language_code: str | None,
) -> None:
    """
    Retry token generation for preset texts that already exist but were left in an
    incomplete state by a previous failed seed run.

    Also backfills word segmentation for zh/ja when older imports only created char tokens.
    """
    lc = (language_code or "").strip().lower()

    # 中文/日文：旧版预置导入可能只有字符 Token、没有 WordToken —— 清空后重跑分词
    if lc in ("zh", "ja") and _needs_word_token_backfill(session, text.text_id):
        try:
            _clear_tokens_for_text(session, text.text_id)
            _generate_tokens_for_text(
                session=session,
                text_id=text.text_id,
                language_code=lc,
            )
            text.processing_status = 'completed'
        except Exception:
            text.processing_status = 'failed'
        return

    if text.processing_status == 'completed':
        return

    existing_token_count = session.query(Token).filter(Token.text_id == text.text_id).count()
    if existing_token_count > 0:
        text.processing_status = 'completed'
        return

    try:
        _generate_tokens_for_text(
            session=session,
            text_id=text.text_id,
            language_code=lc or language_code,
        )
        text.processing_status = 'completed'
    except Exception:
        text.processing_status = 'failed'


def _generate_tokens_for_text(
    session: Session,
    text_id: int,
    language_code: str | None,
) -> None:
    """
    为指定文章生成 Token / WordToken：
    - 空格语言（英文、德文）按单词分词
    - 非空格语言（中文、日文等）按字符 + 分词（生成 WordToken；日文依赖 janome）

    仅在当前文章尚无 Token 时运行，避免重复生成。
    （需要重跑时请先用 _clear_tokens_for_text）
    """
    lc = (language_code or "").strip().lower()

    # 如果该文章已经有 Token，则不再重复生成（幂等保护）
    existing_token_count = session.query(Token).filter(Token.text_id == text_id).count()
    if existing_token_count:
        return

    is_non_whitespace = is_non_whitespace_language(lc) if lc else False

    sentences = (
        session.query(Sentence)
        .filter(Sentence.text_id == text_id)
        .order_by(Sentence.sentence_id.asc())
        .all()
    )
    if not sentences:
        return

    global_token_id = 0

    # Historical seeds inserted explicit word_token_id values. In PostgreSQL,
    # that may leave the sequence behind the actual max, so align it before
    # relying on DB-generated IDs.
    _sync_word_token_sequence_if_needed(session)

    for sentence in sentences:
        sentence_text = sentence.sentence_body or ""
        if not sentence_text.strip():
            continue

        # 1) 字符 / 单词级 token 切分
        token_dicts = split_tokens(sentence_text, is_non_whitespace=is_non_whitespace)
        tokens_with_id: list[dict] = []
        for sentence_token_id, token_dict in enumerate(token_dicts, 1):
            token_with_id = create_token_with_id(token_dict, global_token_id, sentence_token_id)
            tokens_with_id.append(token_with_id)
            global_token_id += 1

        # 2) 中文、日文等非空格语言：生成 WordToken，并回填到 char token 上
        sentence_word_tokens: list[dict] = []
        token_word_mapping: dict[int, int] = {}
        if lc in ("zh", "ja"):
            sentence_word_tokens, token_word_mapping, _ = word_segmentation(
                lc,
                sentence_text,
                tokens_with_id,
                1,
            )

            real_word_token_mapping = _create_word_tokens_and_get_mapping(
                session=session,
                text_id=text_id,
                sentence_id=sentence.sentence_id,
                sentence_word_tokens=sentence_word_tokens,
            )

            if real_word_token_mapping:
                for t in tokens_with_id:
                    temp_word_token_id = token_word_mapping.get(t["sentence_token_id"])
                    if temp_word_token_id is not None:
                        real_word_token_id = real_word_token_mapping.get(temp_word_token_id)
                        if real_word_token_id is not None:
                            t["word_token_id"] = real_word_token_id

        # 3) 写入 Token 表
        for t in tokens_with_id:
            token_type_str = (t.get("token_type") or "text").lower()
            if token_type_str == "punctuation":
                token_type_enum = TokenType.PUNCTUATION
            elif token_type_str == "space":
                token_type_enum = TokenType.SPACE
            else:
                token_type_enum = TokenType.TEXT

            token = Token(
                text_id=text_id,
                sentence_id=sentence.sentence_id,
                token_body=t.get("token_body", ""),
                token_type=token_type_enum,
                global_token_id=t.get("global_token_id"),
                sentence_token_id=t.get("sentence_token_id"),
                pos_tag=None,
                lemma=None,
                is_grammar_marker=False,
                word_token_id=t.get("word_token_id"),
            )
            session.add(token)

def _create_word_tokens_and_get_mapping(
    session: Session,
    text_id: int,
    sentence_id: int,
    sentence_word_tokens: List[Dict[str, Any]],
) -> Dict[int, int]:
    """
    Insert word tokens using database-generated primary keys, then return a
    mapping from temporary IDs (used during segmentation) to persisted IDs.
    """
    if not sentence_word_tokens:
        return {}

    entries: List[Tuple[int, Dict[str, Any]]] = []
    for wt in sentence_word_tokens:
        temp_word_token_id = wt.get("word_token_id")
        if temp_word_token_id is None:
            continue
        entries.append((int(temp_word_token_id), wt))

    temp_to_model: Dict[int, WordToken] = {}
    chunk = max(1, WORD_TOKEN_FLUSH_CHUNK_SIZE)
    for start in range(0, len(entries), chunk):
        for temp_word_token_id, wt in entries[start : start + chunk]:
            word_token = WordToken(
                text_id=text_id,
                sentence_id=sentence_id,
                word_body=wt.get("word_body", ""),
                token_ids=wt.get("token_ids") or [],
                pos_tag=wt.get("pos_tag"),
                lemma=wt.get("lemma"),
                linked_vocab_id=wt.get("linked_vocab_id"),
            )
            session.add(word_token)
            temp_to_model[temp_word_token_id] = word_token
        session.flush()

    return {
        temp_id: model.word_token_id
        for temp_id, model in temp_to_model.items()
        if model.word_token_id is not None
    }


def _sync_word_token_sequence_if_needed(session: Session) -> None:
    """
    Keep PostgreSQL sequence in sync with historical explicit inserts so
    autoincremented word_token_id values remain collision-free.
    """
    bind = session.get_bind()
    if bind is None or bind.dialect.name != "postgresql":
        return

    session.execute(
        text(
            """
            SELECT setval(
                pg_get_serial_sequence('word_tokens', 'word_token_id'),
                COALESCE((SELECT MAX(word_token_id) FROM word_tokens), 1),
                true
            )
            """
        )
    )


def preset_title_language_pairs() -> Set[Tuple[str, str]]:
    """
    All (language_code, title) pairs defined under backend/data/presets/articles.
    Used to match DB rows to preset articles only.
    """
    pairs: Set[Tuple[str, str]] = set()
    for p in load_preset_files([]):
        lc = (p.get("language_code") or "").strip().lower()
        title = (p.get("title") or "").strip()
        if lc and title:
            pairs.add((lc, title))
    return pairs


def backfill_word_tokens_missing_word_level(
    session: Session,
    *,
    only_preset_titles: bool = True,
    language_codes: Tuple[str, ...] = ("zh", "ja"),
    commit: bool = True,
) -> Dict[str, Any]:
    """
    一次性修复：数据库里已有字符级 Token，但没有任何 WordToken 的中文/日文文章
    （旧版预置导入或早期逻辑）。会删除该文下 Token/WordToken 后按当前逻辑重跑分词。

    - only_preset_titles=True：只处理标题+语言与预置 JSON 一致的记录（推荐）。
    - only_preset_titles=False：处理所有缺少 WordToken 的 zh/ja 文章（含用户上传的旧数据）。

    需要本机已安装 jieba（中文）与 janome（日文）。

    说明：对远程 PostgreSQL 使用「每篇文章单独 commit」，避免长事务 + 大批量 INSERT 导致连接被服务端断开；
    单篇失败会 rollback，不影响已成功的文章，可安全重跑。
    """
    preset_pairs = preset_title_language_pairs() if only_preset_titles else None
    stats: Dict[str, Any] = {
        "scanned": 0,
        "fixed": 0,
        "skipped_has_word_tokens": 0,
        "skipped_wrong_language": 0,
        "skipped_not_preset": 0,
        "errors": 0,
        "error_details": [],
    }

    work_queue: List[Dict[str, Any]] = []
    for text in session.query(OriginalText).all():
        stats["scanned"] += 1
        lang_name = (text.language or "").strip()
        lc = get_language_code(lang_name) if lang_name else ""
        if lc not in language_codes:
            stats["skipped_wrong_language"] += 1
            continue

        if preset_pairs is not None:
            key = (lc, (text.text_title or "").strip())
            if key not in preset_pairs:
                stats["skipped_not_preset"] += 1
                continue

        tid = text.text_id
        title = (text.text_title or "").strip()
        if not _needs_word_token_backfill(session, tid):
            stats["skipped_has_word_tokens"] += 1
            continue

        work_queue.append({"text_id": tid, "lc": lc, "title": title, "language": lang_name})

    for item in work_queue:
        tid = item["text_id"]
        lc = item["lc"]
        title = item["title"]
        last_err: Optional[Exception] = None
        for attempt in range(2):
            try:
                _clear_tokens_for_text(session, tid)
                _generate_tokens_for_text(session, tid, lc)
                stats["fixed"] += 1
                if commit:
                    session.commit()
                else:
                    session.rollback()
                last_err = None
                break
            except OperationalError as e:
                last_err = e
                try:
                    session.rollback()
                except Exception:
                    pass
                if attempt == 0:
                    time.sleep(2.0)
                    continue
            except Exception as e:
                last_err = e
                try:
                    session.rollback()
                except Exception:
                    pass
                break
        if last_err is not None:
            stats["errors"] += 1
            stats["error_details"].append(
                {
                    "text_id": tid,
                    "title": title,
                    "language": item.get("language"),
                    "error": str(last_err),
                }
            )

    return stats
