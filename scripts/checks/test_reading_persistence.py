"""Run: python -m unittest scripts.checks.test_reading_persistence"""
import unittest
def completed_without_io(coroutine):
    # The replay path must return before reaching any async model work.
    try:
        coroutine.send(None)
    except StopIteration as done:
        return done.value
    finally:
        coroutine.close()
    raise AssertionError('Replay unexpectedly attempted async work')

from types import SimpleNamespace
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from backend.api.reading_routes import (save_result, accessible, article_result, progress,
    ProgressRequest, publish, articles, analyze, AnalyzeRequest)
from database_system.business_logic.models import (Base, User, OriginalText, ReadingArticle,
    ReadingAnalysis, ArticleKnowledgePoint, Sentence)

class ReadingPersistenceTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.a = User(password_hash='test', email='a@test.local')
        self.b = User(password_hash='test', email='b@test.local')
        self.db.add_all([self.a, self.b]); self.db.commit()
        text = OriginalText(user_id=self.a.user_id, text_title='Test', language='de')
        self.db.add(text); self.db.flush()
        self.tid = text.text_id
        self.db.add(ReadingArticle(text_id=self.tid, visibility='private', raw_text='Hallo Welt.', level='B1'))
        self.db.flush()
        self.run = ReadingAnalysis(text_id=self.tid, user_id=self.a.user_id, request_key='test')
        self.db.add(self.run); self.db.commit()

    def tearDown(self):
        self.db.close(); self.engine.dispose()

    def result(self):
        return {'sentences':[{'sentence_id':1,'sentence_body':'Hallo Welt.', 'vocab_knowledge_point_ids':[77]}],
                'vocab_knowledge_points':[{'vocab_id':77,'vocab_body':'Welt','explanation':'世界',
                  'examples':[{'sentence_id':1,'token_indices':[1]}]}], 'grammar_knowledge_points':[]}

    def test_private_access_and_public_progress_isolation(self):
        save_result(self.db, self.run, self.result())
        point = self.db.query(ArticleKnowledgePoint).one()
        with self.assertRaises(HTTPException) as error:
            accessible(self.db,self.tid,self.b.user_id)
        self.assertEqual(error.exception.status_code,404)
        with self.assertRaises(HTTPException):
            progress(point.id, ProgressRequest(status='mastered'), self.b, self.db)
        self.assertEqual(articles(user=self.b,session=self.db)['articles'],[])
        with self.assertRaises(HTTPException):
            publish(self.tid,self.a,self.db)
        self.a.role='admin'; self.db.commit()
        publish(self.tid,self.a,self.db)
        accessible(self.db,self.tid,self.b.user_id)
        progress(point.id,ProgressRequest(status='mastered'),self.a,self.db)
        result_a=article_result(self.db,self.run,self.a.user_id)
        result_b=article_result(self.db,self.run,self.b.user_id)
        self.assertEqual(result_a['vocab_knowledge_points'][0]['learn_status'],'mastered')
        self.assertEqual(result_b['vocab_knowledge_points'][0]['learn_status'],'not_mastered')
        self.assertEqual(result_a['sentences'][0]['vocab_knowledge_point_ids'],[point.id])
        self.assertEqual(self.a.token_balance,0)

    def test_knowledge_catalog_survives_reload_and_isolates_users(self):
        from backend.api.reading_routes import knowledge_points
        save_result(self.db, self.run, self.result())
        point = self.db.query(ArticleKnowledgePoint).one()
        progress(point.id, ProgressRequest(status='mastered'), self.a, self.db)
        self.db.expire_all()
        catalog = knowledge_points(user=self.a, session=self.db)['knowledge_points']
        self.assertEqual(len(catalog), 1)
        self.assertEqual(catalog[0]['status'], 'mastered')
        self.assertEqual(catalog[0]['payload']['vocab_body'], 'Welt')
        self.assertEqual(knowledge_points(user=self.b, session=self.db)['knowledge_points'], [])

    def test_request_replay_returns_saved_result_without_model_call(self):
        save_result(self.db,self.run,self.result())
        result=completed_without_io(analyze(AnalyzeRequest(text='Hallo Welt.', request_key='test'),self.a,self.db))
        self.assertEqual(result['text_id'],self.tid)
        self.assertEqual(self.db.query(ReadingAnalysis).count(),1)
        with self.assertRaises(HTTPException) as error:
            completed_without_io(analyze(AnalyzeRequest(text='Different',request_key='test'),self.a,self.db))
        self.assertEqual(error.exception.status_code,409)

    def test_invalid_result_rolls_back_normalized_rows(self):
        data=self.result(); data['vocab_knowledge_points'][0]['examples'][0]['sentence_id']=99
        with self.assertRaises(ValueError):
            save_result(self.db,self.run,data)
        self.db.rollback()
        self.assertEqual(self.db.query(Sentence).count(),0)
        self.assertEqual(self.db.query(ArticleKnowledgePoint).count(),0)
        self.assertEqual(self.db.get(ReadingAnalysis,self.run.id).status,'processing')

if __name__ == '__main__':
    unittest.main()
