import asyncio
from unittest.mock import patch, MagicMock
from scripts.checks.test_reading_persistence import ReadingPersistenceTest
from backend.api.reading_questions import generate, snapshot, VERSION
from database_system.business_logic.models import ReadingArticle, ReadingQuestionSet, ReadingQuestion

class ReadingQuestionPersistenceTest(ReadingPersistenceTest):
    def test_languages_have_separate_question_sets(self):
        self._save()
        with patch.dict('sys.modules', {'backend.assistants.review_quiz_generator': MagicMock()}) as modules:
            factory = modules['backend.assistants.review_quiz_generator'].ReviewQuizGenerator
            factory.return_value._generate_batch.side_effect = self.questions
            english = asyncio.run(generate(self.db, self.run, self.article, 'en'))
            chinese = asyncio.run(generate(self.db, self.run, self.article, 'zh'))
            self.assertNotEqual(english['question_set_id'], chinese['question_set_id'])
            self.assertEqual(chinese['ui_language'], 'Chinese')
            self.assertEqual(factory.call_args.kwargs['ui_language'], 'Chinese')
            self.assertEqual(snapshot(self.db, self.run, 'zh')['questions'], chinese['questions'])

    def test_saved_questions_survive_reload_and_are_reused(self):
        self._save()
        with patch.dict('sys.modules', {'backend.assistants.review_quiz_generator': MagicMock()}) as modules:
            factory = modules['backend.assistants.review_quiz_generator'].ReviewQuizGenerator
            factory.return_value._generate_batch.side_effect = self.questions
            first = asyncio.run(generate(self.db, self.run, self.article))
            self.assertEqual(first['question_status'], 'completed')
            self.db.expire_all()
            second = asyncio.run(generate(self.db, self.run, self.article))
            self.assertEqual(first['questions'], second['questions'])
            self.assertEqual(factory.return_value._generate_batch.call_count, 1)
            self.assertTrue(first['questions'][0]['question_id'].startswith('rq:'))

    def _save(self):
        from backend.api.reading_routes import save_result
        save_result(self.db, self.run, self.result())
        self.article = self.db.get(ReadingArticle, self.tid)

    @staticmethod
    def questions(article, points, level):
        return [dict(question_id='q1', question_type='vocabulary_in_context', question='Meaning?',
                     options=['world','house','tree','road'], correct_answer=0, explanation='World.',
                     related_knowledge_point_ids=[p['id']]) for p in points]

    def test_failure_keeps_saved_rows_and_retries_only_missing(self):
        result = self.result()
        result['vocab_knowledge_points'] *= 6
        # Distinct source IDs and independent payloads.
        from copy import deepcopy
        result['vocab_knowledge_points'] = [dict(deepcopy(p), vocab_id=77+i) for i,p in enumerate(result['vocab_knowledge_points'])]
        from backend.api.reading_routes import save_result
        save_result(self.db, self.run, result)
        article = self.db.get(ReadingArticle, self.tid)
        calls = []
        def failing(raw, points, level):
            calls.append(len(points))
            if len(calls)>1: raise ValueError('model unavailable')
            return self.questions(raw, points, level)
        with patch.dict('sys.modules', {'backend.assistants.review_quiz_generator': MagicMock()}) as modules:
            factory = modules['backend.assistants.review_quiz_generator'].ReviewQuizGenerator
            factory.return_value._generate_batch.side_effect=failing
            first=asyncio.run(generate(self.db,self.run,article))
            self.assertEqual(first['question_status'],'partial')
            self.assertEqual(len(first['questions']),5)
            factory.return_value._generate_batch.side_effect=self.questions
            second=asyncio.run(generate(self.db,self.run,article))
            self.assertEqual(second['question_status'],'completed')
            self.assertEqual(len(second['questions']),6)
            self.assertEqual(len(factory.return_value._generate_batch.call_args.args[1]),1)

    def test_active_worker_does_not_trigger_second_generation(self):
        self._save()
        from datetime import datetime
        self.db.add(ReadingQuestionSet(analysis_id=self.run.id,ui_language='English',generation_version=VERSION,
                    status='processing',lease_token='other',updated_at=datetime.now()))
        self.db.commit()
        with patch.dict('sys.modules', {'backend.assistants.review_quiz_generator': MagicMock()}) as modules:
            factory = modules['backend.assistants.review_quiz_generator'].ReviewQuizGenerator
            result=asyncio.run(generate(self.db,self.run,self.article))
            self.assertEqual(result['question_status'],'processing')
            factory.assert_not_called()
