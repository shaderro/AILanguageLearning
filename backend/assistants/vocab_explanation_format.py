"""Normalize vocab explanation LLM output for DB storage (structured JSON v2)."""
from __future__ import annotations

import ast
import json
import re
from typing import Any, Iterable


STRUCTURED_KEYS = (
    "part_of_speech",
    "word_features",
    "definitions",
    "rare_senses",
    "collocations",
    "grammar_notes",
)


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, dict):
        return [str(v).strip() for v in value.values() if str(v).strip()]
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        out: list[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                out.append(text)
        return out
    text = str(value).strip()
    return [text] if text else []


def _coerce_dict(raw: Any) -> dict | None:
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    if not text:
        return None
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass
    try:
        parsed = ast.literal_eval(text)
        return parsed if isinstance(parsed, dict) else None
    except (ValueError, SyntaxError):
        return None


def is_structured_vocab_explanation(data: dict) -> bool:
    return any(key in data for key in STRUCTURED_KEYS)


def build_structured_vocab_explanation(data: dict) -> dict:
    return {
        "part_of_speech": str(data.get("part_of_speech") or "").strip(),
        "word_features": _as_str_list(data.get("word_features")),
        "definitions": _as_str_list(data.get("definitions")),
        "rare_senses": _as_str_list(data.get("rare_senses")),
        "collocations": _as_str_list(data.get("collocations")),
        "grammar_notes": _as_str_list(data.get("grammar_notes")),
    }


def normalize_vocab_explanation_for_storage(raw: Any) -> str:
    """
    Store structured explanations as JSON; legacy {"explanation": "..."} stays as plain text.
    """
    if raw is None:
        return "No explanation provided"

    data = _coerce_dict(raw) if not isinstance(raw, dict) else raw
    if data is not None:
        if is_structured_vocab_explanation(data):
            structured = build_structured_vocab_explanation(data)
            return json.dumps(structured, ensure_ascii=False)
        legacy = data.get("explanation")
        if legacy is not None:
            legacy_text = str(legacy).strip()
            return legacy_text or "No explanation provided"

    if isinstance(raw, str):
        text = raw.strip()
        return text or "No explanation provided"

    return str(raw)


def sanitize_vocab_example_explanation(text: Any) -> str:
    """Strip internal token-index markers from inline vocab notation."""
    if text is None:
        return ""
    s = str(text).strip()
    if not s:
        return s
    s = re.sub(r"\(\s*tokens?\s+[\d,\s]+\s*\)", "", s, flags=re.I)
    s = re.sub(r"\(\s*sentence_token_id\s*[=:]\s*[\d,\s]+\s*\)", "", s, flags=re.I)
    s = re.sub(r";\s*tokens?\s+[\d,\s]+", "", s, flags=re.I)
    s = re.sub(r"\s{2,}", " ", s)
    s = re.sub(r";\s*;+", ";", s)
    s = re.sub(r";\s*$", "", s.strip())
    return s.strip()
