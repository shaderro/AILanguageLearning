"""Persistent reading articles. No credit checks or billing calls in this workflow."""
from copy import deepcopy
from datetime import datetime
from uuid import uuid4
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool
from backend.api.auth_routes import get_current_user, get_bearer_or_cookie_token
from backend.api.db_deps import get_db_session
from database_system.business_logic.models import (
    OriginalText, Sentence, ReadingArticle, ReadingAnalysis,
    ArticleKnowledgePoint, ArticleKnowledgeExample, UserKnowledgeProgress,
)

router = APIRouter(prefix="/api/v2/german-reading", tags=["reading"])

def optional_reading_user(raw_token=Depends(get_bearer_or_cookie_token), session=Depends(get_db_session)):
    return get_current_user(raw_token, session) if raw_token else None

class AnalyzeRequest(BaseModel):
    content_language: str = Field(default='de', min_length=1, max_length=64)
    ui_language: str = Field(default='English', min_length=1, max_length=64)
    text: str = Field(min_length=1, max_length=12000)
    level: Literal["A1", "A2", "B1", "B2", "C1", "C2"] = "B1"
    reading_mode: Literal["paragraph", "line"] = "paragraph"
    title: str = Field(default="德语精读", max_length=500)
    request_key: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=128)

class ProgressRequest(BaseModel):
    status: Literal["not_mastered", "learning", "mastered"]

def accessible(session, text_id, user_id):
    row = session.query(ReadingArticle).join(OriginalText).filter(
        ReadingArticle.text_id == text_id,
        or_(ReadingArticle.visibility == "public", OriginalText.user_id == user_id),
    ).first()
    if row is None:
        raise HTTPException(404, "文章不存在")
    return row

def article_result(session, run, user_id):
    if run.status == "processing" and datetime.now() - run.created_at > timedelta(minutes=15):
        run.status = "failed"
        run.error_message = "分析超时或服务重启，请重新上传"
        session.get(OriginalText, run.text_id).processing_status = "failed"
        session.commit()
    result = deepcopy(run.result_json or {})
    progress = dict(session.query(UserKnowledgeProgress.knowledge_point_id, UserKnowledgeProgress.status)
                    .join(ArticleKnowledgePoint).filter(UserKnowledgeProgress.user_id == user_id,
                     ArticleKnowledgePoint.text_id == run.text_id).all())
    for group in ("vocab_knowledge_points", "grammar_knowledge_points"):
        for point in result.get(group, []):
            point["learn_status"] = progress.get(point["knowledge_point_id"], "not_mastered")
    article = session.get(ReadingArticle, run.text_id)
    result.update(text_id=run.text_id, analysis_id=run.id, status=run.status,
                  raw_text=article.raw_text, level=article.level, visibility=article.visibility,
                  title=session.get(OriginalText, run.text_id).text_title)
    from backend.api.reading_questions import snapshot
    result["review"] = snapshot(session, run)
    return result

def save_result(session, run, result):
    """Save all normalized rows and their render snapshot in one transaction."""
    result = deepcopy(result)
    if not isinstance(result, dict) or not result.get("sentences"):
        raise ValueError("分析结果没有有效句子")
    result["text_id"] = run.text_id
    sentence_map = {}
    for item in result["sentences"]:
        sid = int(item["sentence_id"])
        if sid in sentence_map or not item.get("sentence_body"):
            raise ValueError("分析结果句子无效")
        row = Sentence(text_id=run.text_id, sentence_id=sid, sentence_body=item["sentence_body"],
                       paragraph_id=item.get("paragraph_id"), is_new_paragraph=item.get("is_new_paragraph", False))
        session.add(row)
        session.flush()
        sentence_map[sid] = row.id
        item.update(text_id=run.text_id, id=row.id)
    for group, id_field, kind in (("vocab_knowledge_points", "vocab_id", "vocabulary"),
                                  ("grammar_knowledge_points", "rule_id", "grammar")):
        mapping = {}
        for position, point in enumerate(result.get(group, [])):
            label = str(point.get("vocab_body") or point.get("display_name") or "").strip()
            point_kind = "expression" if kind == "vocabulary" and " " in label else kind
            row = ArticleKnowledgePoint(text_id=run.text_id, kind=point_kind,
                canonical_key=" ".join(label.casefold().split())[:500], payload={}, position=position)
            session.add(row)
            session.flush()
            mapping[point[id_field]] = row.id
            point.update({id_field: row.id, "knowledge_point_id": row.id, "learn_status": "not_mastered"})
            for example in point.get("examples", []):
                example.update({id_field: row.id, "text_id": run.text_id})
                sentence_pk = sentence_map.get(int(example["sentence_id"]))
                if sentence_pk is None:
                    raise ValueError("知识点引用无效句子")
                session.add(ArticleKnowledgeExample(knowledge_point_id=row.id, sentence_id=sentence_pk, payload=deepcopy(example)))
            row.payload = deepcopy(point)
        field = "vocab_knowledge_point_ids" if kind == "vocabulary" else "grammar_knowledge_point_ids"
        for sentence in result["sentences"]:
            sentence[field] = [mapping[value] for value in sentence.get(field, []) if value in mapping]
    result.update(ids_are_persisted=True, result_schema_version=1)
    run.result_json = result
    run.status = "completed"
    run.completed_at = datetime.now()
    session.get(OriginalText, run.text_id).processing_status = "completed"
    session.commit()

@router.post("/analyze")
async def analyze(payload: AnalyzeRequest, user=Depends(optional_reading_user), session=Depends(get_db_session)):
    raw = payload.text.strip()
    if not raw:
        raise HTTPException(400, "请提供文章内容")
    if user is None:
        from backend.assistants.main_assistant_knowledge_detection import MainAssistant
        assistant = MainAssistant()
        assistant.set_user_context(user_id=None, session=None)
        result = await run_in_threadpool(assistant.analyze_text, raw, payload.content_language,
            payload.ui_language, 0, payload.title, "paragraph", learner_level=payload.level,
            reading_split_mode="line" if payload.reading_mode == "line" else "punctuation")
        result.update(status="completed", text_id=None, ids_are_persisted=False,
                      title=payload.title, reading_mode=payload.reading_mode)
        return result
    existing = session.query(ReadingAnalysis).filter_by(user_id=user.user_id, request_key=payload.request_key).first()
    if existing:
        article = session.get(ReadingArticle, existing.text_id)
        if (article.raw_text != raw or article.level != payload.level
                or (existing.result_json or {}).get("reading_mode", "paragraph") != payload.reading_mode):
            raise HTTPException(409, "请求标识已用于其他内容")
        if existing.status == "completed":
            return article_result(session, existing, user.user_id)
        raise HTTPException(409, {"analysis_id": existing.id, "status": existing.status,
                                  "message": "分析处理中或已失败；重新分析请使用新的请求标识"})
    uid = user.user_id
    text = OriginalText(user_id=uid, text_title=payload.title, language="de", processing_status="processing")
    session.add(text)
    session.flush()
    session.add(ReadingArticle(text_id=text.text_id, visibility="private", raw_text=raw, level=payload.level))
    session.flush()
    run = ReadingAnalysis(text_id=text.text_id, user_id=uid, request_key=payload.request_key)
    session.add(run)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "请求已提交，请刷新文章列表")
    run_id, text_id = run.id, text.text_id
    session.commit()  # release the connection before model work
    try:
        from backend.assistants.main_assistant_knowledge_detection import MainAssistant
        assistant = MainAssistant()
        assistant.set_user_context(user_id=None, session=None)  # explicitly disable legacy billing
        result = await run_in_threadpool(assistant.analyze_text, raw, payload.content_language, payload.ui_language, text_id,
                                         payload.title, "paragraph", learner_level=payload.level,
                                         reading_split_mode="line" if payload.reading_mode == "line" else "punctuation")
        result["reading_mode"] = payload.reading_mode
        run = session.get(ReadingAnalysis, run_id)
        save_result(session, run, result)
    except Exception:
        session.rollback()
        run = session.get(ReadingAnalysis, run_id)
        run.status = "failed"
        run.error_message = "分析或保存失败，请重试"
        run.completed_at = datetime.now()
        session.get(OriginalText, text_id).processing_status = "failed"
        session.commit()
        raise HTTPException(502, "文章分析或保存失败，请重试")
    return article_result(session, run, uid)

@router.get("/articles")
def articles(offset: int = 0, limit: int = 50, user=Depends(get_current_user), session=Depends(get_db_session)):
    rows = session.query(OriginalText, ReadingArticle, ReadingAnalysis).join(
        ReadingArticle, ReadingArticle.text_id == OriginalText.text_id).join(
        ReadingAnalysis, ReadingAnalysis.text_id == OriginalText.text_id).filter(
        or_(ReadingArticle.visibility == "public", OriginalText.user_id == user.user_id)
    ).order_by(OriginalText.created_at.desc()).offset(max(0, offset)).limit(min(max(1, limit), 100)).all()
    return {"articles": [{"text_id": t.text_id, "title": t.text_title, "visibility": a.visibility,
             "level": a.level, "status": r.status, "created_at": t.created_at,
             "preview": a.raw_text[:240], "word_count": len(a.raw_text.split())} for t, a, r in rows]}

@router.get("/articles/{text_id}")
def detail(text_id: int, user=Depends(get_current_user), session=Depends(get_db_session)):
    accessible(session, text_id, user.user_id)
    run = session.query(ReadingAnalysis).filter_by(text_id=text_id).one()
    return article_result(session, run, user.user_id)

@router.put("/knowledge-points/{point_id}/progress")
def progress(point_id: int, payload: ProgressRequest, user=Depends(get_current_user), session=Depends(get_db_session)):
    point = session.get(ArticleKnowledgePoint, point_id)
    if point is None:
        raise HTTPException(404, "知识点不存在")
    accessible(session, point.text_id, user.user_id)
    key = (user.user_id, point_id)
    row = session.get(UserKnowledgeProgress, key)
    if row is None:
        row = UserKnowledgeProgress(user_id=user.user_id, knowledge_point_id=point_id)
        session.add(row)
    row.status = payload.status
    row.mastered_at = datetime.now() if payload.status == "mastered" else None
    session.commit()
    return {"knowledge_point_id": point_id, "status": row.status}


@router.post("/articles/{text_id}/publish")
def publish(text_id: int, user=Depends(get_current_user), session=Depends(get_db_session)):
    if user.role != "admin":
        raise HTTPException(403, "仅管理员可发布预置文章")
    article = accessible(session, text_id, user.user_id)
    run = session.query(ReadingAnalysis).filter_by(text_id=text_id).one()
    if run.status != "completed":
        raise HTTPException(409, "仅能发布已完成分析的文章")
    article.visibility = "public"
    session.commit()
    return {"text_id": text_id, "visibility": "public"}


@router.post('/articles/{text_id}/review')
async def persistent_review(text_id: int, ui_language: str = 'English', user=Depends(get_current_user), session=Depends(get_db_session)):
    article = accessible(session, text_id, user.user_id)
    run = session.query(ReadingAnalysis).filter_by(text_id=text_id).one()
    from backend.api.reading_questions import generate
    return await generate(session, run, article, ui_language)

class GuestReviewRequest(BaseModel):
    ui_language: str = Field(default='English', min_length=1, max_length=64)
    text: str = Field(min_length=1, max_length=12000)
    points: list[dict] = Field(max_length=100)
    level: Literal['A1','A2','B1','B2','C1','C2'] = 'B1'

@router.post('/guest-review')
async def guest_review(payload: GuestReviewRequest):
    from backend.assistants.review_quiz_generator import ReviewQuizGenerator
    from backend.api.reading_questions import normalize_review_language
    questions = await run_in_threadpool(ReviewQuizGenerator(ui_language=normalize_review_language(payload.ui_language)).generate, payload.text, payload.points, payload.level)
    return {'questions': questions}

@router.get("/knowledge-points")
def knowledge_points(user=Depends(get_current_user), session=Depends(get_db_session)):
    rows = session.query(ArticleKnowledgePoint, OriginalText).join(
        ReadingArticle, ReadingArticle.text_id == ArticleKnowledgePoint.text_id).join(
        OriginalText, OriginalText.text_id == ReadingArticle.text_id).filter(
        or_(ReadingArticle.visibility == "public", OriginalText.user_id == user.user_id)
    ).order_by(ArticleKnowledgePoint.id.desc()).all()
    statuses = dict(session.query(UserKnowledgeProgress.knowledge_point_id, UserKnowledgeProgress.status)
                    .filter(UserKnowledgeProgress.user_id == user.user_id).all())
    return {"knowledge_points": [dict(id=p.id, text_id=p.text_id, title=t.text_title,
        kind=p.kind, payload=p.payload, status=statuses.get(p.id, "not_mastered")) for p, t in rows]}
