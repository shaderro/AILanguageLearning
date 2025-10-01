from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from .models import (
    VocabExpression, GrammarRule, OriginalText, Sentence, Token,
    SourceType,
    VocabExpressionExample,
)

# ==================== 词汇相关CRUD操作 ====================

def _coerce_source(value: Optional[str]) -> SourceType:
    if isinstance(value, SourceType):
        return value
    if value is None:
        return SourceType.AUTO
    try:
        return SourceType(value)
    except Exception:
        return SourceType.AUTO


def create_vocab(session: Session, vocab_body: str, explanation: str, 
                source: str = "auto", is_starred: bool = False) -> VocabExpression:
    vocab = VocabExpression(
        vocab_body=vocab_body,
        explanation=explanation,
        source=_coerce_source(source),
        is_starred=is_starred
    )
    session.add(vocab)
    session.commit()
    session.refresh(vocab)
    return vocab


def get_or_create_vocab(session: Session, vocab_body: str, explanation: str,
                        source: str = "auto", is_starred: bool = False) -> VocabExpression:
    existing = session.query(VocabExpression).filter(VocabExpression.vocab_body == vocab_body).first()
    if existing:
        return existing
    return create_vocab(session, vocab_body, explanation, source, is_starred)


def get_vocab_by_id(session: Session, vocab_id: int) -> Optional[VocabExpression]:
    return session.query(VocabExpression).filter(VocabExpression.vocab_id == vocab_id).first()


def get_vocab_by_body(session: Session, vocab_body: str) -> Optional[VocabExpression]:
    return session.query(VocabExpression).filter(VocabExpression.vocab_body == vocab_body).first()


def get_all_vocabs(session: Session, skip: int = 0, limit: int = 100) -> List[VocabExpression]:
    return session.query(VocabExpression).offset(skip).limit(limit).all()


def get_starred_vocabs(session: Session) -> List[VocabExpression]:
    return session.query(VocabExpression).filter(VocabExpression.is_starred == True).all()


def search_vocabs(session: Session, keyword: str) -> List[VocabExpression]:
    return session.query(VocabExpression).filter(
        or_(
            VocabExpression.vocab_body.contains(keyword),
            VocabExpression.explanation.contains(keyword)
        )
    ).all()


def update_vocab(session: Session, vocab_id: int, **kwargs) -> Optional[VocabExpression]:
    vocab = get_vocab_by_id(session, vocab_id)
    if vocab:
        for key, value in kwargs.items():
            if key == "source":
                value = _coerce_source(value)
            if hasattr(vocab, key):
                setattr(vocab, key, value)
        session.commit()
        session.refresh(vocab)
    return vocab


def delete_vocab(session: Session, vocab_id: int) -> bool:
    vocab = get_vocab_by_id(session, vocab_id)
    if vocab:
        session.delete(vocab)
        session.commit()
        return True
    return False

# ==================== 词汇例句相关CRUD操作 ====================

def create_vocab_example(session: Session, *, vocab_id: int, text_id: int,
                         sentence_id: int, context_explanation: Optional[str] = None,
                         token_indices: Optional[list] = None) -> VocabExpressionExample:
    example = VocabExpressionExample(
        vocab_id=vocab_id,
        text_id=text_id,
        sentence_id=sentence_id,
        context_explanation=context_explanation,
        token_indices=token_indices or [],
    )
    session.add(example)
    session.commit()
    session.refresh(example)
    return example

# ==================== 语法规则相关CRUD操作 ====================

def create_grammar_rule(session: Session, rule_name: str, rule_summary: str,
                       source: str = "auto", is_starred: bool = False) -> GrammarRule:
    rule = GrammarRule(
        rule_name=rule_name,
        rule_summary=rule_summary,
        source=_coerce_source(source),
        is_starred=is_starred
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


def get_grammar_rule_by_id(session: Session, rule_id: int) -> Optional[GrammarRule]:
    return session.query(GrammarRule).filter(GrammarRule.rule_id == rule_id).first()


def get_grammar_rule_by_name(session: Session, rule_name: str) -> Optional[GrammarRule]:
    return session.query(GrammarRule).filter(GrammarRule.rule_name == rule_name).first()


def get_all_grammar_rules(session: Session, skip: int = 0, limit: int = 100) -> List[GrammarRule]:
    return session.query(GrammarRule).offset(skip).limit(limit).all()


def get_starred_grammar_rules(session: Session) -> List[GrammarRule]:
    return session.query(GrammarRule).filter(GrammarRule.is_starred == True).all()


def search_grammar_rules(session: Session, keyword: str) -> List[GrammarRule]:
    return session.query(GrammarRule).filter(
        or_(
            GrammarRule.rule_name.contains(keyword),
            GrammarRule.rule_summary.contains(keyword)
        )
    ).all()


def update_grammar_rule(session: Session, rule_id: int, **kwargs) -> Optional[GrammarRule]:
    rule = get_grammar_rule_by_id(session, rule_id)
    if rule:
        for key, value in kwargs.items():
            if key == "source":
                value = _coerce_source(value)
            if hasattr(rule, key):
                setattr(rule, key, value)
        session.commit()
        session.refresh(rule)
    return rule


def delete_grammar_rule(session: Session, rule_id: int) -> bool:
    rule = get_grammar_rule_by_id(session, rule_id)
    if rule:
        session.delete(rule)
        session.commit()
        return True
    return False


def get_or_create_grammar_rule(session: Session, rule_name: str, rule_summary: str,
                                source: str = "auto", is_starred: bool = False) -> GrammarRule:
    """若存在则返回，否则创建语法规则"""
    existing = session.query(GrammarRule).filter(GrammarRule.rule_name == rule_name).first()
    if existing:
        return existing
    return create_grammar_rule(session, rule_name, rule_summary, source, is_starred)

# ==================== 语法例句相关CRUD操作 ====================


def create_grammar_example(session: Session, *, rule_id: int, text_id: int,
                           sentence_id: int, explanation_context: Optional[str] = None):
    """创建语法例句记录"""
    from .models import GrammarExample
    example = GrammarExample(
        rule_id=rule_id,
        text_id=text_id,
        sentence_id=sentence_id,
        explanation_context=explanation_context,
    )
    session.add(example)
    session.commit()
    session.refresh(example)
    return example

# ==================== 文章相关CRUD操作 ====================

def create_text(session: Session, text_title: str) -> OriginalText:
    text = OriginalText(text_title=text_title)
    session.add(text)
    session.commit()
    session.refresh(text)
    return text


def get_text_by_id(session: Session, text_id: int) -> Optional[OriginalText]:
    return session.query(OriginalText).filter(OriginalText.text_id == text_id).first()


def get_all_texts(session: Session) -> List[OriginalText]:
    return session.query(OriginalText).all()


def search_texts(session: Session, keyword: str) -> List[OriginalText]:
    return session.query(OriginalText).filter(OriginalText.text_title.contains(keyword)).all()

# ==================== 句子相关CRUD操作 ====================

def create_sentence(session: Session, text_id: int, sentence_id: int, sentence_body: str,
                   difficulty_level: Optional[str] = None) -> Sentence:
    sentence = Sentence(
        text_id=text_id,
        sentence_id=sentence_id,
        sentence_body=sentence_body,
        sentence_difficulty_level=difficulty_level
    )
    session.add(sentence)
    session.commit()
    return sentence


def get_sentences_by_text(session: Session, text_id: int) -> List[Sentence]:
    return session.query(Sentence).filter(Sentence.text_id == text_id).all()


def get_sentence_by_id(session: Session, text_id: int, sentence_id: int) -> Optional[Sentence]:
    return session.query(Sentence).filter(
        and_(Sentence.text_id == text_id, Sentence.sentence_id == sentence_id)
    ).first()

# ==================== 词汇标记相关CRUD操作 ====================

def create_token(session: Session, text_id: int, sentence_id: int, token_body: str,
                token_type: str, **kwargs) -> Token:
    token = Token(
        text_id=text_id,
        sentence_id=sentence_id,
        token_body=token_body,
        token_type=token_type,
        **kwargs
    )
    session.add(token)
    session.commit()
    session.refresh(token)
    return token


def get_tokens_by_sentence(session: Session, text_id: int, sentence_id: int) -> List[Token]:
    return session.query(Token).filter(
        and_(Token.text_id == text_id, Token.sentence_id == sentence_id)
    ).all()


def get_tokens_by_vocab(session: Session, vocab_id: int) -> List[Token]:
    return session.query(Token).filter(Token.linked_vocab_id == vocab_id).all()

# ==================== 统计查询 ====================

def get_vocab_stats(session: Session) -> dict:
    total_vocabs = session.query(VocabExpression).count()
    starred_vocabs = session.query(VocabExpression).filter(VocabExpression.is_starred == True).count()
    auto_vocabs = session.query(VocabExpression).filter(VocabExpression.source == SourceType.AUTO).count()
    manual_vocabs = session.query(VocabExpression).filter(VocabExpression.source == SourceType.MANUAL).count()
    
    return {
        "total": total_vocabs,
        "starred": starred_vocabs,
        "auto": auto_vocabs,
        "manual": manual_vocabs
    }


def get_grammar_stats(session: Session) -> dict:
    total_rules = session.query(GrammarRule).count()
    starred_rules = session.query(GrammarRule).filter(GrammarRule.is_starred == True).count()
    auto_rules = session.query(GrammarRule).filter(GrammarRule.source == SourceType.AUTO).count()
    manual_rules = session.query(GrammarRule).filter(GrammarRule.source == SourceType.MANUAL).count()
    
    return {
        "total": total_rules,
        "starred": starred_rules,
        "auto": auto_rules,
        "manual": manual_rules
    }


def get_learning_progress(session: Session) -> dict:
    vocab_stats = get_vocab_stats(session)
    grammar_stats = get_grammar_stats(session)
    
    total_texts = session.query(OriginalText).count()
    total_sentences = session.query(Sentence).count()
    
    return {
        "vocab": vocab_stats,
        "grammar": grammar_stats,
        "texts": total_texts,
        "sentences": total_sentences,
    } 