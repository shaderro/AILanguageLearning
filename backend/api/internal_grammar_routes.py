"""
Internal-only grammar canonical key dashboard APIs.

Read-only aggregation of the current user's GrammarRule rows by canonical_key.
Not linked from product navigation.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from backend.api.auth_routes import get_current_user
from backend.api.db_deps import get_db_session
from database_system.business_logic.models import (
    GrammarExample,
    GrammarNotation,
    GrammarRule,
    OriginalText,
    Sentence,
    User,
)

router = APIRouter(
    prefix="/api/v2/internal/grammar",
    tags=["internal-grammar"],
)

UNGROUPED_BUCKET = "__ungrouped__"
_PREVIEW_LEN = 160


def _truncate(text: Optional[str], limit: int = _PREVIEW_LEN) -> str:
    raw = (text or "").strip()
    if len(raw) <= limit:
        return raw
    return raw[: limit - 1].rstrip() + "…"


def _rule_title(rule: GrammarRule) -> str:
    display = (getattr(rule, "display_name", None) or "").strip()
    if display:
        return display
    return (rule.rule_name or "").strip() or "(unnamed)"


def _group_bucket_key(canonical_key: Optional[str]) -> str:
    key = (canonical_key or "").strip()
    return key if key else UNGROUPED_BUCKET


def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def _parse_annotation_pattern(explanation_context: Optional[str]) -> Optional[str]:
    """Best-effort extract of a pattern annotation from explanation_context."""
    if not explanation_context:
        return None
    text = explanation_context.strip()
    if not text:
        return None

    # Try JSON payloads first
    if text.startswith("{") or text.startswith("["):
        try:
            payload = json.loads(text)
        except Exception:
            payload = None
        if isinstance(payload, dict):
            for path in (
                ("pattern",),
                ("annotation", "pattern"),
                ("highlighted_structure",),
                ("structure",),
                ("canonical", "pattern"),
            ):
                cur: Any = payload
                ok = True
                for part in path:
                    if not isinstance(cur, dict) or part not in cur:
                        ok = False
                        break
                    cur = cur[part]
                if ok and isinstance(cur, str) and cur.strip():
                    return cur.strip()
            # Common nested shapes from AI summaries
            for key in ("summary", "explanation", "text"):
                val = payload.get(key)
                if isinstance(val, str) and val.strip():
                    # fall through to regex on inner text
                    text = val
                    break

    # Lightweight pattern hints in free text
    patterns = [
        r"(?:pattern|结构|句式)\s*[:：]\s*(.+)",
        r"(把\s*\+\s*[^\n。；;]+)",
        r"(被\s*\+\s*[^\n。；;]+)",
    ]
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()[:200]
    return None


def _load_user_rules(session: Session, user_id: int) -> List[GrammarRule]:
    return (
        session.query(GrammarRule)
        .options(joinedload(GrammarRule.examples))
        .filter(GrammarRule.user_id == user_id)
        .order_by(GrammarRule.created_at.asc(), GrammarRule.rule_id.asc())
        .all()
    )


def _article_meta_map(session: Session, text_ids: List[int]) -> Dict[int, OriginalText]:
    if not text_ids:
        return {}
    rows = session.query(OriginalText).filter(OriginalText.text_id.in_(text_ids)).all()
    return {r.text_id: r for r in rows}


def _sentence_map(session: Session, pairs: List[Tuple[int, int]]) -> Dict[Tuple[int, int], str]:
    if not pairs:
        return {}
    text_ids = sorted({t for t, _ in pairs})
    rows = (
        session.query(Sentence)
        .filter(Sentence.text_id.in_(text_ids))
        .all()
    )
    wanted = set(pairs)
    out: Dict[Tuple[int, int], str] = {}
    for row in rows:
        key = (row.text_id, row.sentence_id)
        if key in wanted:
            out[key] = row.sentence_body
    return out


def _notation_map(
    session: Session, user_id: int, rule_ids: List[int]
) -> Dict[Tuple[int, int, int], List[Any]]:
    """Map (grammar_id, text_id, sentence_id) -> marked_token_ids."""
    if not rule_ids:
        return {}
    rows = (
        session.query(GrammarNotation)
        .filter(
            GrammarNotation.user_id == user_id,
            GrammarNotation.grammar_id.in_(rule_ids),
        )
        .all()
    )
    out: Dict[Tuple[int, int, int], List[Any]] = {}
    for row in rows:
        if row.grammar_id is None:
            continue
        out[(row.grammar_id, row.text_id, row.sentence_id)] = row.marked_token_ids or []
    return out


def _derived_levels_for_articles(articles: List[OriginalText]) -> List[str]:
    levels: List[str] = []
    seen = set()
    for art in articles:
        for value in (art.exam_content, art.difficulty):
            if not value:
                continue
            normalized = str(value).strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            levels.append(normalized)
    return levels


def _dedupe_examples(examples: List[GrammarExample]) -> List[GrammarExample]:
    deduped: Dict[Tuple[int, int, int], GrammarExample] = {}
    for ex in examples or []:
        key = (ex.rule_id, ex.text_id, ex.sentence_id)
        existing = deduped.get(key)
        if existing is None:
            deduped[key] = ex
            continue
        if not getattr(existing, "explanation_context", None) and getattr(ex, "explanation_context", None):
            deduped[key] = ex
    return list(deduped.values())


def _collect_group_examples(
    rules: List[GrammarRule],
) -> List[GrammarExample]:
    examples: List[GrammarExample] = []
    for rule in rules:
        examples.extend(list(rule.examples or []))
    return _dedupe_examples(examples)


def _build_groups(
    rules: List[GrammarRule],
    articles_by_id: Dict[int, OriginalText],
) -> List[Dict[str, Any]]:
    buckets: Dict[str, List[GrammarRule]] = defaultdict(list)
    for rule in rules:
        buckets[_group_bucket_key(rule.canonical_key)].append(rule)

    groups: List[Dict[str, Any]] = []
    for bucket_key, bucket_rules in buckets.items():
        bucket_rules = sorted(
            bucket_rules,
            key=lambda r: (r.created_at or datetime.min, r.rule_id or 0),
        )
        primary = bucket_rules[0]
        examples = _collect_group_examples(bucket_rules)
        text_ids = sorted({ex.text_id for ex in examples if ex.text_id is not None})
        articles = [articles_by_id[tid] for tid in text_ids if tid in articles_by_id]
        derived_levels = _derived_levels_for_articles(articles)

        # Prefer a rule that already has display_name / richer summary
        titled = next((r for r in bucket_rules if (r.display_name or "").strip()), primary)
        summary_src = next(
            (r for r in bucket_rules if (r.rule_summary or "").strip()),
            primary,
        )

        is_ungrouped = bucket_key == UNGROUPED_BUCKET
        groups.append(
            {
                "canonical_key": None if is_ungrouped else bucket_key,
                "is_ungrouped": is_ungrouped,
                "title": _rule_title(titled) if not is_ungrouped else "Ungrouped (no canonical_key)",
                "display_name": (titled.display_name or None),
                "rule_name": titled.rule_name,
                "language": titled.language,
                "canonical_category": titled.canonical_category if not is_ungrouped else None,
                "canonical_subtype": titled.canonical_subtype if not is_ungrouped else None,
                "canonical_function": titled.canonical_function if not is_ungrouped else None,
                "description_preview": _truncate(summary_src.rule_summary),
                "example_count": len(examples),
                "rule_count": len(bucket_rules),
                "rule_ids": [r.rule_id for r in bucket_rules],
                "created_at": _iso(min((r.created_at for r in bucket_rules if r.created_at), default=None)),
                "updated_at": _iso(max((r.updated_at for r in bucket_rules if r.updated_at), default=None)),
                "derived_levels": derived_levels,
            }
        )
    return groups


def _apply_filters(
    groups: List[Dict[str, Any]],
    *,
    q: Optional[str],
    canonical_key: Optional[str],
    language: Optional[str],
    level: Optional[str],
    min_examples: int,
    include_ungrouped: bool,
) -> List[Dict[str, Any]]:
    filtered = groups

    if not include_ungrouped:
        filtered = [g for g in filtered if not g.get("is_ungrouped")]

    if min_examples > 0:
        filtered = [g for g in filtered if int(g.get("example_count") or 0) >= min_examples]

    if language and language.strip().lower() not in ("", "all"):
        lang = language.strip().lower()
        filtered = [
            g for g in filtered
            if (g.get("language") or "").strip().lower() == lang
            or lang in (g.get("language") or "").strip().lower()
        ]

    if canonical_key and canonical_key.strip():
        needle = canonical_key.strip().lower()
        filtered = [
            g for g in filtered
            if g.get("canonical_key")
            and needle in str(g["canonical_key"]).lower()
        ]

    if level and level.strip():
        needle = level.strip().lower()
        filtered = [
            g for g in filtered
            if any(needle in str(lv).lower() for lv in (g.get("derived_levels") or []))
        ]

    if q and q.strip():
        needle = q.strip().lower()

        def matches(g: Dict[str, Any]) -> bool:
            haystacks = [
                g.get("canonical_key"),
                g.get("title"),
                g.get("display_name"),
                g.get("rule_name"),
                g.get("description_preview"),
                g.get("canonical_category"),
                g.get("canonical_subtype"),
                g.get("language"),
            ]
            return any(needle in str(h).lower() for h in haystacks if h)

        filtered = [g for g in filtered if matches(g)]

    return filtered


def _sort_groups(groups: List[Dict[str, Any]], sort: str) -> List[Dict[str, Any]]:
    sort_key = (sort or "recent").strip().lower()

    def recent_key(g: Dict[str, Any]):
        return (g.get("created_at") or "", g.get("canonical_key") or "")

    if sort_key == "examples":
        return sorted(
            groups,
            key=lambda g: (-int(g.get("example_count") or 0), g.get("canonical_key") or ""),
        )
    if sort_key == "key":
        return sorted(
            groups,
            key=lambda g: (
                1 if g.get("is_ungrouped") else 0,
                (g.get("canonical_key") or "").lower(),
                g.get("title") or "",
            ),
        )
    # recent (default): newest first
    return sorted(groups, key=recent_key, reverse=True)


@router.get("/keys", summary="List grammar groups aggregated by canonical_key")
async def list_canonical_keys(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    q: Optional[str] = Query(default=None, description="Search key / name / summary"),
    canonical_key: Optional[str] = Query(default=None, description="Filter by canonical_key substring"),
    language: Optional[str] = Query(default=None),
    level: Optional[str] = Query(default=None, description="Derived article level filter"),
    min_examples: int = Query(default=0, ge=0),
    sort: str = Query(default="recent", description="recent | examples | key"),
    include_ungrouped: bool = Query(default=True),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    try:
        rules = _load_user_rules(session, current_user.user_id)
        text_ids: List[int] = []
        for rule in rules:
            for ex in rule.examples or []:
                if ex.text_id is not None:
                    text_ids.append(ex.text_id)
        articles_by_id = _article_meta_map(session, sorted(set(text_ids)))

        groups = _build_groups(rules, articles_by_id)
        groups = _apply_filters(
            groups,
            q=q,
            canonical_key=canonical_key,
            language=language,
            level=level,
            min_examples=min_examples,
            include_ungrouped=include_ungrouped,
        )
        groups = _sort_groups(groups, sort)
        total = len(groups)
        page = groups[skip : skip + limit]

        return {
            "success": True,
            "data": page,
            "count": len(page),
            "total": total,
            "skip": skip,
            "limit": limit,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keys/detail", summary="Detail for one canonical_key (or ungrouped)")
async def get_canonical_key_detail(
    canonical_key: Optional[str] = Query(default=None),
    ungrouped: bool = Query(default=False, description="Load rules with null/empty canonical_key"),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    try:
        if not ungrouped and not (canonical_key and canonical_key.strip()):
            raise HTTPException(
                status_code=400,
                detail="Provide canonical_key, or set ungrouped=true",
            )

        query = session.query(GrammarRule).options(joinedload(GrammarRule.examples)).filter(
            GrammarRule.user_id == current_user.user_id
        )

        if ungrouped:
            rules = [
                r
                for r in query.all()
                if not (r.canonical_key or "").strip()
            ]
            bucket_key = None
        else:
            key = canonical_key.strip()
            rules = query.filter(GrammarRule.canonical_key == key).all()
            bucket_key = key

        if not rules:
            raise HTTPException(status_code=404, detail="No grammar rules found for this key")

        rules = sorted(rules, key=lambda r: (r.created_at or datetime.min, r.rule_id or 0))
        primary = rules[0]
        titled = next((r for r in rules if (r.display_name or "").strip()), primary)
        summary_src = next((r for r in rules if (r.rule_summary or "").strip()), primary)

        examples = _collect_group_examples(rules)
        text_ids = sorted({ex.text_id for ex in examples if ex.text_id is not None})
        pairs = [(ex.text_id, ex.sentence_id) for ex in examples if ex.text_id is not None and ex.sentence_id is not None]
        articles_by_id = _article_meta_map(session, text_ids)
        sentences = _sentence_map(session, pairs)
        notations = _notation_map(session, current_user.user_id, [r.rule_id for r in rules])

        example_payload = []
        for ex in sorted(examples, key=lambda e: (e.created_at or datetime.min, e.example_id or 0)):
            article = articles_by_id.get(ex.text_id)
            sentence = sentences.get((ex.text_id, ex.sentence_id))
            marked = notations.get((ex.rule_id, ex.text_id, ex.sentence_id), [])
            pattern = _parse_annotation_pattern(ex.explanation_context)
            example_payload.append(
                {
                    "example_id": ex.example_id,
                    "rule_id": ex.rule_id,
                    "text_id": ex.text_id,
                    "sentence_id": ex.sentence_id,
                    "sentence": sentence,
                    "original_sentence": sentence,
                    "article_title": article.text_title if article else None,
                    "article_difficulty": article.difficulty if article else None,
                    "article_exam_content": article.exam_content if article else None,
                    "derived_levels": _derived_levels_for_articles([article] if article else []),
                    "explanation_context": ex.explanation_context,
                    "marked_token_ids": marked,
                    "annotation": {"pattern": pattern} if pattern else None,
                    "created_at": _iso(ex.created_at),
                }
            )

        return {
            "success": True,
            "data": {
                "canonical_key": bucket_key,
                "is_ungrouped": ungrouped,
                "title": _rule_title(titled) if not ungrouped else "Ungrouped (no canonical_key)",
                "display_name": titled.display_name,
                "rule_name": titled.rule_name,
                "language": titled.language,
                "canonical_category": primary.canonical_category if not ungrouped else None,
                "canonical_subtype": primary.canonical_subtype if not ungrouped else None,
                "canonical_function": primary.canonical_function if not ungrouped else None,
                "description": summary_src.rule_summary,
                "explanation": summary_src.rule_summary,
                "derived_levels": _derived_levels_for_articles(
                    [articles_by_id[tid] for tid in text_ids if tid in articles_by_id]
                ),
                "created_at": _iso(min((r.created_at for r in rules if r.created_at), default=None)),
                "rules": [
                    {
                        "rule_id": r.rule_id,
                        "rule_name": r.rule_name,
                        "display_name": r.display_name,
                        "language": r.language,
                        "canonical_key": r.canonical_key,
                        "source": r.source.value if hasattr(r.source, "value") else str(r.source),
                        "learn_status": (
                            r.learn_status.value
                            if hasattr(r.learn_status, "value")
                            else str(r.learn_status)
                        ),
                        "created_at": _iso(r.created_at),
                        "updated_at": _iso(r.updated_at),
                    }
                    for r in rules
                ],
                "examples": example_payload,
                "example_count": len(example_payload),
                "rule_count": len(rules),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
