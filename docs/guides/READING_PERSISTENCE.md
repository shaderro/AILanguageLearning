# Analyze text persistence

The reading workflow requires authentication. It does not pass a billing user/session to the analyzer and does not check or deduct credits.

## Storage and migration

Five additive tables are registered in the existing startup migration for SQLite and PostgreSQL: reading_articles, reading_analyses, article_knowledge_points, article_knowledge_examples, user_knowledge_progress. OriginalText and Sentence remain shared with the legacy application. No existing columns are changed. Article visibility and raw input live in reading_articles to avoid rewriting legacy tables. Legacy vocabulary/grammar ownership is unchanged.

Start/restart the backend to create missing tables. Apply and verify on a development database before production rollout. Existing legacy articles are not automatically imported. Existing in-memory page results cannot be recovered.

## API

All routes have prefix /api/v2/german-reading and use existing bearer/cookie authentication.

- POST /analyze: text, level, optional title and request_key. Creates a PRIVATE article. Same user/key/content returns the existing completed result without a model call; a changed payload conflicts. Failed requests need a new key.
- GET /articles: own private and all public articles, offset/limit pagination.
- GET /articles/{text_id}: saved snapshot with the requesting user's progress. Inaccessible IDs return 404. Processing runs older than 15 minutes are marked failed when opened.
- PUT /knowledge-points/{id}/progress: status is not_mastered, learning, or mastered. Access requires article visibility. No row means not_mastered.
- POST /articles/{text_id}/publish: admin only, completed articles only. To seed: log in as admin, analyze a preset, then publish its text_id. Public readers reuse the saved result; publishing does not copy content per user.

The reading page exposes a library button and restores an article from ?text_id=.... The built-in preset choice opens the saved library rather than analyzing a per-user copy. Administrators must publish presets before they appear. Paste input is the current upload entry point; file attachments are not implemented.

## Scope

Progress is per user and per article knowledge point; matching terms in separate articles do not share mastery. Quiz generation and answers remain transient. Reanalysis creates another article rather than overwriting IDs. There is no background worker or automatic failed-job retry. The snapshot preserves token/anchor and presentation fields; Sentence rows and example relations support normalized references.

## Verification

Run `.venv/Scripts/python.exe -m unittest scripts.checks.test_reading_persistence` for private access, public sharing, independent progress, ID mapping, idempotent replay and transactional rollback checks.


## Review question persistence

`reading_question_sets` stores generation status, language/version and a 15-minute worker lease;
`reading_questions` stores validated question payloads with foreign keys to the set and article knowledge point.
Both tables are created by the existing additive startup migration. No existing tables are modified.
POST `/api/v2/german-reading/articles/{text_id}/review` requires article access and derives all model input
from saved article data. It returns stable `rq:<database id>` question IDs and `question_status`.
Article detail embeds the same snapshot under `review`. Existing completed sets are reused.
Each validated batch commits independently; partial failures retain saved questions and retry only missing points.
An atomic lease claim prevents duplicate active workers; expired workers are fenced before writing.
The standalone UI uses this persistent endpoint; the legacy `/review` endpoint remains session-only for compatibility.
Answer history is not stored. Current question language is English (generation version 1).
