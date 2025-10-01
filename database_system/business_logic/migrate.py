import json
from pathlib import Path
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select
from .models import (
    Base, VocabExpression, VocabExpressionExample, GrammarRule, GrammarExample,
    OriginalText, Sentence, Token, DifficultyLevel, TokenType
)
from .crud import (
    get_or_create_vocab, create_vocab_example,
    get_or_create_grammar_rule, create_grammar_example
)

DEFAULT_DB_URL = "sqlite:///database_system/data_storage/data/dev.db"
DEFAULT_VOCAB_JSON = "backend/data/current/vocab.json"
DEFAULT_GRAMMAR_JSON = "backend/data/current/grammar.json"
DEFAULT_ARTICLES_DIR = "backend/data/current/articles"


def get_session(db_url: str = DEFAULT_DB_URL) -> Session:
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(db_url, echo=False, future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return SessionLocal()


def migrate_vocab_and_examples(session: Session, vocab_json_path: str = DEFAULT_VOCAB_JSON) -> Dict[str, int]:
    path = Path(vocab_json_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        rows: list[Dict[str, Any]] = json.load(f)

    inserted_vocab = 0
    inserted_examples = 0

    for r in rows:
        existing = session.query(VocabExpression).filter(VocabExpression.vocab_body == r["vocab_body"]).first()
        if existing is None:
            vocab = get_or_create_vocab(
                session=session,
                vocab_body=r["vocab_body"],
                explanation=r["explanation"],
                source=r.get("source", "auto"),
                is_starred=bool(r.get("is_starred", False)),
            )
            inserted_vocab += 1
        else:
            vocab = existing

        for ex in r.get("examples", []):
            create_vocab_example(
                session=session,
                vocab_id=vocab.vocab_id,
                text_id=ex["text_id"],
                sentence_id=ex["sentence_id"],
                context_explanation=ex.get("context_explanation"),
                token_indices=ex.get("token_indices", []),
            )
            inserted_examples += 1

    return {"inserted_vocab": inserted_vocab, "inserted_examples": inserted_examples}


def verify_counts_and_join(session: Session) -> Dict[str, int]:
    total_vocab = session.query(VocabExpression).count()
    total_examples = session.query(VocabExpressionExample).count()
    stmt = (
        select(VocabExpression.vocab_id)
        .join(VocabExpressionExample, VocabExpression.vocab_id == VocabExpressionExample.vocab_id)
        .group_by(VocabExpression.vocab_id)
    )
    vocab_with_examples = len(session.execute(stmt).scalars().all())
    return {
        "total_vocab": total_vocab,
        "total_examples": total_examples,
        "vocab_with_examples": vocab_with_examples,
    }


def migrate_grammar_and_examples(session: Session, 
                                 grammar_json_path: str = DEFAULT_GRAMMAR_JSON) -> Dict[str, int]:
    """迁移语法规则及其例句"""
    path = Path(grammar_json_path)
    if not path.exists():
        print(f"⚠️  语法规则文件不存在: {path}")
        return {"inserted_rules": 0, "inserted_examples": 0}

    with open(path, "r", encoding="utf-8") as f:
        rows: list[Dict[str, Any]] = json.load(f)

    inserted_rules = 0
    inserted_examples = 0

    for r in rows:
        # 检查是否已存在
        existing = session.query(GrammarRule).filter(
            GrammarRule.rule_name == r["rule_name"]
        ).first()
        
        if existing is None:
            # 创建语法规则
            rule = get_or_create_grammar_rule(
                session=session,
                rule_name=r["rule_name"],
                rule_summary=r["rule_summary"],
                source=r.get("source", "auto"),
                is_starred=bool(r.get("is_starred", False)),
            )
            inserted_rules += 1
        else:
            rule = existing

        # 迁移例句
        for ex in r.get("examples", []):
            try:
                # 处理两种格式：字符串列表 或 字典（包含text_id/sentence_id）
                if isinstance(ex, str):
                    # 如果是字符串，暂时跳过（需要text_id和sentence_id才能关联）
                    # print(f"   ⓘ 跳过纯文本例句 (rule={rule.rule_name}): {ex[:50]}...")
                    continue
                elif isinstance(ex, dict):
                    # 如果是字典，正常迁移
                    create_grammar_example(
                        session=session,
                        rule_id=rule.rule_id,
                        text_id=ex["text_id"],
                        sentence_id=ex["sentence_id"],
                        explanation_context=ex.get("explanation_context"),
                    )
                    inserted_examples += 1
            except Exception as e:
                print(f"⚠️  插入语法例句失败 (rule={rule.rule_name}): {e}")

    return {"inserted_rules": inserted_rules, "inserted_examples": inserted_examples}


def verify_grammar_counts(session: Session) -> Dict[str, int]:
    """验证语法数据"""
    total_rules = session.query(GrammarRule).count()
    total_examples = session.query(GrammarExample).count()
    
    stmt = (
        select(GrammarRule.rule_id)
        .join(GrammarExample, GrammarRule.rule_id == GrammarExample.rule_id)
        .group_by(GrammarRule.rule_id)
    )
    rules_with_examples = len(session.execute(stmt).scalars().all())
    
    return {
        "total_rules": total_rules,
        "total_examples": total_examples,
        "rules_with_examples": rules_with_examples,
    }


def _coerce_difficulty(value: Optional[str]) -> Optional[DifficultyLevel]:
    """转换难度等级字符串到枚举"""
    if value is None:
        return None
    value_lower = value.lower()
    if value_lower == 'easy':
        return DifficultyLevel.EASY
    elif value_lower == 'hard':
        return DifficultyLevel.HARD
    return None


def _coerce_token_type(value: str) -> TokenType:
    """转换token类型字符串到枚举"""
    value_lower = value.lower()
    if value_lower == 'text':
        return TokenType.TEXT
    elif value_lower == 'punctuation':
        return TokenType.PUNCTUATION
    elif value_lower == 'space':
        return TokenType.SPACE
    return TokenType.TEXT  # 默认为text


def migrate_articles(session: Session,
                    articles_dir: str = DEFAULT_ARTICLES_DIR) -> Dict[str, int]:
    """迁移所有文章数据（原文、句子、tokens）"""
    articles_path = Path(articles_dir)
    if not articles_path.exists():
        print(f"⚠️  文章目录不存在: {articles_path}")
        return {"inserted_texts": 0, "inserted_sentences": 0, "inserted_tokens": 0}
    
    inserted_texts = 0
    inserted_sentences = 0
    inserted_tokens = 0
    
    # 1. 迁移单文件格式的文章（如 hp1_processed_*.json）
    processed_files = sorted(articles_path.glob("*_processed_*.json"))
    if processed_files:
        print(f"   找到 {len(processed_files)} 个单文件格式文章")
        for article_file in processed_files:
            try:
                with open(article_file, "r", encoding="utf-8") as f:
                    article_data = json.load(f)
                
                text_id = article_data.get("text_id")
                text_title = article_data.get("text_title")
                
                if not text_id or not text_title:
                    print(f"   ⚠️  跳过 {article_file.name}：缺少text_id或text_title")
                    continue
                
                # 检查是否已存在
                existing_text = session.query(OriginalText).filter(
                    OriginalText.text_id == text_id
                ).first()
                
                if existing_text:
                    print(f"   ⓘ 文章 {text_id} 已存在，跳过")
                    continue
                
                # 创建文章
                text = OriginalText(text_id=text_id, text_title=text_title)
                session.add(text)
                session.flush()
                inserted_texts += 1
                
                # 处理嵌套的句子和tokens
                sentence_count = 0
                token_count = 0
                for sent in article_data.get("sentences", []):
                    sentence = Sentence(
                        text_id=text_id,
                        sentence_id=sent.get("sentence_id"),
                        sentence_body=sent.get("sentence_body", ""),
                        sentence_difficulty_level=_coerce_difficulty(sent.get("sentence_difficulty_level")),
                        grammar_annotations=sent.get("grammar_annotations"),
                        vocab_annotations=sent.get("vocab_annotations")
                    )
                    session.add(sentence)
                    inserted_sentences += 1
                    sentence_count += 1
                    
                    # 处理嵌套的tokens
                    for tok in sent.get("tokens", []):
                        linked_vocab_id = tok.get("linked_vocab_id")
                        if linked_vocab_id:
                            vocab_exists = session.query(VocabExpression).filter(
                                VocabExpression.vocab_id == linked_vocab_id
                            ).first()
                            if not vocab_exists:
                                linked_vocab_id = None
                        
                        token = Token(
                            text_id=text_id,
                            sentence_id=sent.get("sentence_id"),
                            token_body=tok.get("token_body", ""),
                            token_type=_coerce_token_type(tok.get("token_type", "text")),
                            difficulty_level=_coerce_difficulty(tok.get("difficulty_level")),
                            global_token_id=tok.get("global_token_id"),
                            sentence_token_id=tok.get("sentence_token_id"),
                            pos_tag=tok.get("pos_tag"),
                            lemma=tok.get("lemma"),
                            is_grammar_marker=tok.get("is_grammar_marker", False),
                            linked_vocab_id=linked_vocab_id
                        )
                        session.add(token)
                        inserted_tokens += 1
                        token_count += 1
                
                session.commit()
                print(f"   ✓ 迁移文章 {text_id}: {text_title[:40]}... ({sentence_count} 句, {token_count} tokens)")
                
            except Exception as e:
                print(f"   ✗ 迁移文章 {article_file.name} 失败: {e}")
                session.rollback()
                import traceback
                traceback.print_exc()
                continue
    
    # 2. 迁移目录格式的文章（text_*/ 目录）
    text_dirs = sorted(articles_path.glob("text_*"))
    if text_dirs:
        print(f"   找到 {len(text_dirs)} 个目录格式文章")
    
    for text_dir in text_dirs:
        if not text_dir.is_dir():
            continue
        
        try:
            # 1. 读取文章元数据
            original_text_file = text_dir / "original_text.json"
            if not original_text_file.exists():
                print(f"   ⚠️  跳过 {text_dir.name}：缺少 original_text.json")
                continue
            
            with open(original_text_file, "r", encoding="utf-8") as f:
                article_data = json.load(f)
            
            # 提取text_id和text_title
            text_id = article_data.get("text_id")
            text_title = article_data.get("text_title")
            
            if not text_id or not text_title:
                print(f"   ⚠️  跳过 {text_dir.name}：缺少text_id或text_title")
                continue
            
            # 检查文章是否已存在
            existing_text = session.query(OriginalText).filter(
                OriginalText.text_id == text_id
            ).first()
            
            if existing_text:
                print(f"   ⓘ 文章 {text_id} 已存在，跳过")
                continue
            
            # 2. 创建文章记录
            text = OriginalText(
                text_id=text_id,
                text_title=text_title
            )
            session.add(text)
            session.flush()
            inserted_texts += 1
            
            # 3. 读取句子文件
            sentences_file = text_dir / "sentences.json"
            if not sentences_file.exists():
                print(f"   ⚠️  文章 {text_id} 缺少 sentences.json")
                session.commit()
                continue
            
            with open(sentences_file, "r", encoding="utf-8") as f:
                sentences_data = json.load(f)
            
            sentence_count = 0
            for sent in sentences_data:
                # 创建句子
                sentence = Sentence(
                    text_id=text_id,
                    sentence_id=sent.get("sentence_id"),
                    sentence_body=sent.get("sentence_body", ""),
                    sentence_difficulty_level=_coerce_difficulty(sent.get("sentence_difficulty_level")),
                    grammar_annotations=sent.get("grammar_annotations"),
                    vocab_annotations=sent.get("vocab_annotations")
                )
                session.add(sentence)
                inserted_sentences += 1
                sentence_count += 1
            
            session.flush()
            
            # 4. 读取tokens文件
            tokens_file = text_dir / "tokens.json"
            if not tokens_file.exists():
                print(f"   ⚠️  文章 {text_id} 缺少 tokens.json")
                session.commit()
                continue
            
            with open(tokens_file, "r", encoding="utf-8") as f:
                tokens_data = json.load(f)
            
            token_count = 0
            for tok in tokens_data:
                # 验证linked_vocab_id是否存在
                linked_vocab_id = tok.get("linked_vocab_id")
                if linked_vocab_id:
                    vocab_exists = session.query(VocabExpression).filter(
                        VocabExpression.vocab_id == linked_vocab_id
                    ).first()
                    if not vocab_exists:
                        linked_vocab_id = None  # 设为None如果不存在
                
                token = Token(
                    text_id=text_id,
                    sentence_id=tok.get("sentence_id"),
                    token_body=tok.get("token_body", ""),
                    token_type=_coerce_token_type(tok.get("token_type", "text")),
                    difficulty_level=_coerce_difficulty(tok.get("difficulty_level")),
                    global_token_id=tok.get("global_token_id"),
                    sentence_token_id=tok.get("sentence_token_id"),
                    pos_tag=tok.get("pos_tag"),
                    lemma=tok.get("lemma"),
                    is_grammar_marker=tok.get("is_grammar_marker", False),
                    linked_vocab_id=linked_vocab_id
                )
                session.add(token)
                inserted_tokens += 1
                token_count += 1
            
            session.commit()
            print(f"   ✓ 迁移文章 {text_id}: {text_title[:40]}... ({sentence_count} 句, {token_count} tokens)")
            
        except Exception as e:
            print(f"   ✗ 迁移文章 {text_dir.name} 失败: {e}")
            session.rollback()
            import traceback
            traceback.print_exc()
            continue
    
    return {
        "inserted_texts": inserted_texts,
        "inserted_sentences": inserted_sentences,
        "inserted_tokens": inserted_tokens
    }


def verify_articles_counts(session: Session) -> Dict[str, int]:
    """验证文章数据"""
    from sqlalchemy import func
    
    total_texts = session.query(OriginalText).count()
    total_sentences = session.query(Sentence).count()
    total_tokens = session.query(Token).count()
    
    # 统计每篇文章的句子数
    texts_with_sentences = session.query(
        func.count(func.distinct(Sentence.text_id))
    ).scalar()
    
    return {
        "total_texts": total_texts,
        "total_sentences": total_sentences,
        "total_tokens": total_tokens,
        "texts_with_sentences": texts_with_sentences or 0,
    }


def main():
    """主迁移函数 - 执行所有数据迁移"""
    session = get_session()
    try:
        print("\n" + "="*70)
        print("📚 数据库迁移开始")
        print("="*70)
        
        # 1. 词汇迁移
        print("\n" + "="*70)
        print("1️⃣  迁移词汇数据")
        print("="*70)
        vocab_results = migrate_vocab_and_examples(session)
        print(f"   ✓ 插入词汇: {vocab_results['inserted_vocab']}")
        print(f"   ✓ 插入例句: {vocab_results['inserted_examples']}")
        
        vocab_verify = verify_counts_and_join(session)
        print(f"   ✓ 总词汇数: {vocab_verify['total_vocab']}")
        print(f"   ✓ 总例句数: {vocab_verify['total_examples']}")
        print(f"   ✓ 有例句的词汇: {vocab_verify['vocab_with_examples']}")
        
        # 2. 语法迁移
        print("\n" + "="*70)
        print("2️⃣  迁移语法规则")
        print("="*70)
        grammar_results = migrate_grammar_and_examples(session)
        print(f"   ✓ 插入规则: {grammar_results['inserted_rules']}")
        print(f"   ✓ 插入例句: {grammar_results['inserted_examples']}")
        
        grammar_verify = verify_grammar_counts(session)
        print(f"   ✓ 总规则数: {grammar_verify['total_rules']}")
        print(f"   ✓ 总例句数: {grammar_verify['total_examples']}")
        print(f"   ✓ 有例句的规则: {grammar_verify['rules_with_examples']}")
        
        # 3. 文章迁移
        print("\n" + "="*70)
        print("3️⃣  迁移文章数据")
        print("="*70)
        articles_results = migrate_articles(session)
        print(f"   ✓ 插入文章: {articles_results['inserted_texts']}")
        print(f"   ✓ 插入句子: {articles_results['inserted_sentences']}")
        print(f"   ✓ 插入tokens: {articles_results['inserted_tokens']}")
        
        articles_verify = verify_articles_counts(session)
        print(f"   ✓ 总文章数: {articles_verify['total_texts']}")
        print(f"   ✓ 总句子数: {articles_verify['total_sentences']}")
        print(f"   ✓ 总token数: {articles_verify['total_tokens']}")
        
        # 总结
        print("\n" + "="*70)
        print("✅ 迁移完成！")
        print("="*70)
        print(f"📊 总计:")
        print(f"   - 词汇: {vocab_verify['total_vocab']} 条")
        print(f"   - 语法规则: {grammar_verify['total_rules']} 条")
        print(f"   - 文章: {articles_verify['total_texts']} 篇")
        print(f"   - 句子: {articles_verify['total_sentences']} 条")
        print(f"   - Tokens: {articles_verify['total_tokens']} 个")
        print(f"   - 总例句: {vocab_verify['total_examples'] + grammar_verify['total_examples']} 条")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ 迁移过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    main() 