"""Persistent article review questions; model work never holds a transaction."""
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool
from database_system.business_logic.models import ReadingQuestionSet, ReadingQuestion, ArticleKnowledgePoint

VERSION = 2

def normalize_review_language(value):
    languages = {'en': 'English', 'english': 'English', 'zh': 'Chinese', 'chinese': 'Chinese'}
    language = languages.get(value.strip().lower())
    if not language:
        raise HTTPException(422, 'Unsupported review UI language')
    return language

def snapshot(session, run, ui_language='English'):
    ui_language = normalize_review_language(ui_language)
    batch = session.query(ReadingQuestionSet).filter_by(analysis_id=run.id, ui_language=ui_language, generation_version=VERSION).first()
    if batch is None:
        return {'questions': [], 'question_status': 'pending', 'ids_are_persisted': True, 'ui_language': ui_language}
    rows = session.query(ReadingQuestion).filter_by(question_set_id=batch.id).order_by(ReadingQuestion.id).all()
    status = batch.status
    if status == 'processing' and batch.updated_at < datetime.now() - timedelta(minutes=15):
        status = 'partial' if rows else 'failed'
    return {'questions': [dict(row.payload, question_id=f'rq:{row.id}') for row in rows],
            'question_status': status, 'question_set_id': batch.id, 'ids_are_persisted': True, 'ui_language': ui_language}

async def generate(session, run, article, ui_language='English'):
    ui_language = normalize_review_language(ui_language)
    if run.status != 'completed':
        raise HTTPException(409, '文章分析尚未完成')
    batch = session.query(ReadingQuestionSet).filter_by(analysis_id=run.id, ui_language=ui_language, generation_version=VERSION).first()
    if batch is None:
        batch = ReadingQuestionSet(analysis_id=run.id, ui_language=ui_language, generation_version=VERSION)
        session.add(batch)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            batch = session.query(ReadingQuestionSet).filter_by(analysis_id=run.id, ui_language=ui_language, generation_version=VERSION).one()
    batch_id = batch.id
    if batch.status == 'completed':
        return snapshot(session, run, ui_language)
    token = str(uuid4())
    claimed = session.query(ReadingQuestionSet).filter(ReadingQuestionSet.id == batch_id,
        or_(ReadingQuestionSet.status != 'processing', ReadingQuestionSet.updated_at < datetime.now()-timedelta(minutes=15))).update(
        {'status': 'processing', 'lease_token': token, 'updated_at': datetime.now(), 'error_message': None}, synchronize_session=False)
    session.commit()
    if not claimed:
        session.expire_all()
        return snapshot(session, run, ui_language)
    raw, level = article.raw_text, article.level
    saved = {r.knowledge_point_id for r in session.query(ReadingQuestion).filter_by(question_set_id=batch_id)}
    points = []
    for row in session.query(ArticleKnowledgePoint).filter_by(text_id=run.text_id).order_by(ArticleKnowledgePoint.id):
        if row.id in saved:
            continue
        payload = row.payload
        points.append({'id': f"{'grammar' if row.kind == 'grammar' else 'vocab'}:{row.id}",
                       'type': row.kind, 'display_name': payload.get('vocab_body') or payload.get('display_name') or row.canonical_key,
                       'explanation': payload.get('explanation', ''),
                       'sentence_contexts': [e.get('sentence_body', '') for e in payload.get('examples', [])]})
    session.commit()
    try:
        from backend.assistants.review_quiz_generator import ReviewQuizGenerator
        generator = ReviewQuizGenerator(ui_language=ui_language)
        for start in range(0, len(points), 5):
            pending = points[start:start+5]
            for attempt in range(3):
                generated = await run_in_threadpool(generator._generate_batch, raw, pending, level)
                # Lock and verify ownership before every batch commit (also fences expired workers).
                owner = session.query(ReadingQuestionSet).filter_by(id=batch_id, lease_token=token).update(
                    {'updated_at': datetime.now()}, synchronize_session=False)
                if not owner:
                    session.rollback()
                    raise HTTPException(409, '出题任务已被重试接管，请重新读取')
                allowed = {p['id'] for p in pending}
                covered = set()
                for question in generated:
                    related = question['related_knowledge_point_ids']
                    if len(related) != 1 or related[0] not in allowed or related[0] in covered:
                        continue
                    covered.add(related[0])
                    session.add(ReadingQuestion(question_set_id=batch_id, knowledge_point_id=int(related[0].split(':')[1]), payload=question))
                session.commit()
                pending = [p for p in pending if p['id'] not in covered]
                if not pending:
                    break
            if pending:
                raise ValueError('部分知识点尚未生成有效题目')
        session.query(ReadingQuestionSet).filter_by(id=batch_id, lease_token=token).update(
            {'status': 'completed', 'lease_token': None, 'updated_at': datetime.now()}, synchronize_session=False)
        session.commit()
    except HTTPException:
        raise
    except Exception:
        session.rollback()
        count = session.query(ReadingQuestion).filter_by(question_set_id=batch_id).count()
        session.query(ReadingQuestionSet).filter_by(id=batch_id, lease_token=token).update(
            {'status': 'partial' if count else 'failed', 'lease_token': None,
             'error_message': '复习题生成未完成，请重试', 'updated_at': datetime.now()}, synchronize_session=False)
        session.commit()
    session.expire_all()
    return snapshot(session, run, ui_language)
