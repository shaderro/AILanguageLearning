import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_system.business_logic.models import (
    Base,
    VocabExpression,
    VocabExpressionExample,
    SourceType,
)

# 目标数据库（开发环境）
DB_URL = "sqlite:///database_system/data_storage/data/dev.db"
# 词汇 JSON 路径
VOCAB_JSON = "backend/data/current/vocab.json"

def get_session():
    """创建会话并确保表已创建。"""
    engine = create_engine(DB_URL, echo=True, future=True)
    Base.metadata.create_all(engine)  # 首次/开发期确保表存在
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return Session()

def migrate_vocab():
    """迁移词汇与词汇例句数据到数据库。"""
    path = Path(VOCAB_JSON)
    if not path.exists():
        raise FileNotFoundError(f"JSON not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        rows = json.load(f)

    session = get_session()
    inserted_vocab = 0
    inserted_examples = 0

    try:
        for r in rows:
            vocab = VocabExpression(
                vocab_body=r["vocab_body"],
                explanation=r["explanation"],
                source=SourceType(r.get("source", "auto")),
                is_starred=bool(r.get("is_starred", False)),
            )
            session.add(vocab)
            session.flush()  # 获取自增ID

            for ex in r.get("examples", []):
                ex_row = VocabExpressionExample(
                    vocab_id=vocab.vocab_id,
                    text_id=ex["text_id"],
                    sentence_id=ex["sentence_id"],
                    context_explanation=ex.get("context_explanation"),
                    token_indices=ex.get("token_indices", []),
                )
                session.add(ex_row)
                inserted_examples += 1

            inserted_vocab += 1

        session.commit()
        print(f"[OK] inserted vocab={inserted_vocab}, examples={inserted_examples}")
    except Exception as e:
        session.rollback()
        print(f"[ERR] migration failed: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    migrate_vocab()