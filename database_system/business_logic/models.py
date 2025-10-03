from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, JSON, Enum, ForeignKeyConstraint, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import enum

Base = declarative_base()

class SourceType(enum.Enum):
    AUTO = 'auto'
    QA = 'qa'
    MANUAL = 'manual'

class DifficultyLevel(enum.Enum):
    EASY = 'easy'
    HARD = 'hard'

class TokenType(enum.Enum):
    TEXT = 'text'
    PUNCTUATION = 'punctuation'
    SPACE = 'space'

class VocabExpression(Base):
    __tablename__ = 'vocab_expressions'

    vocab_id = Column(Integer, primary_key=True, autoincrement=True)
    vocab_body = Column(String(255), nullable=False, unique=True)
    explanation = Column(Text, nullable=False)
    source = Column(Enum(SourceType), default=SourceType.AUTO, nullable=False)
    is_starred = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    examples = relationship('VocabExpressionExample', back_populates='vocab', cascade='all, delete-orphan')
    tokens = relationship('Token', back_populates='linked_vocab')

class GrammarRule(Base):
    __tablename__ = 'grammar_rules'

    rule_id = Column(Integer, primary_key=True, autoincrement=True)
    rule_name = Column(String(255), nullable=False, unique=True)
    rule_summary = Column(Text, nullable=False)
    source = Column(Enum(SourceType), default=SourceType.AUTO, nullable=False)
    is_starred = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    examples = relationship('GrammarExample', back_populates='grammar_rule', cascade='all, delete-orphan')

class OriginalText(Base):
    __tablename__ = 'original_texts'

    text_id = Column(Integer, primary_key=True, autoincrement=True)
    text_title = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    sentences = relationship('Sentence', back_populates='text', cascade='all, delete-orphan')

class Sentence(Base):
    __tablename__ = 'sentences'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sentence_id = Column(Integer, nullable=False)
    text_id = Column(Integer, ForeignKey('original_texts.text_id', ondelete='CASCADE'), nullable=False)
    sentence_body = Column(Text, nullable=False)
    sentence_difficulty_level = Column(Enum(DifficultyLevel))
    grammar_annotations = Column(JSON)
    vocab_annotations = Column(JSON)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    __table_args__ = (
        UniqueConstraint('text_id', 'sentence_id', name='uq_sentence_text_sentence'),
    )

    text = relationship('OriginalText', back_populates='sentences')
    tokens = relationship('Token', back_populates='sentence', cascade='all, delete-orphan')

class VocabExpressionExample(Base):
    __tablename__ = 'vocab_expression_examples'

    example_id = Column(Integer, primary_key=True, autoincrement=True)
    vocab_id = Column(Integer, ForeignKey('vocab_expressions.vocab_id', ondelete='CASCADE'), nullable=False)
    text_id = Column(Integer, ForeignKey('original_texts.text_id', ondelete='CASCADE'), nullable=False)
    sentence_id = Column(Integer, nullable=False)
    context_explanation = Column(Text)
    token_indices = Column(JSON)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    vocab = relationship('VocabExpression', back_populates='examples')

class GrammarExample(Base):
    __tablename__ = 'grammar_examples'

    example_id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey('grammar_rules.rule_id', ondelete='CASCADE'), nullable=False)
    text_id = Column(Integer, ForeignKey('original_texts.text_id', ondelete='CASCADE'), nullable=False)
    sentence_id = Column(Integer, nullable=False)
    explanation_context = Column(Text)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    grammar_rule = relationship('GrammarRule', back_populates='examples')

class Token(Base):
    __tablename__ = 'tokens'

    token_id = Column(Integer, primary_key=True, autoincrement=True)
    text_id = Column(Integer, ForeignKey('original_texts.text_id', ondelete='CASCADE'), nullable=False)
    sentence_id = Column(Integer, nullable=False)
    token_body = Column(String(255), nullable=False)
    token_type = Column(Enum(TokenType), nullable=False)
    difficulty_level = Column(Enum(DifficultyLevel))
    global_token_id = Column(Integer)
    sentence_token_id = Column(Integer)
    pos_tag = Column(String(50))
    lemma = Column(String(255))
    is_grammar_marker = Column(Boolean, default=False, nullable=False)
    linked_vocab_id = Column(Integer, ForeignKey('vocab_expressions.vocab_id', ondelete='SET NULL'))
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ['text_id', 'sentence_id'],
            ['sentences.text_id', 'sentences.sentence_id'],
            ondelete='CASCADE'
        ),
    )

    sentence = relationship('Sentence', back_populates='tokens')
    linked_vocab = relationship('VocabExpression', back_populates='tokens')

class AskedToken(Base):
    __tablename__ = 'asked_tokens'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False)
    text_id = Column(Integer, ForeignKey('original_texts.text_id', ondelete='CASCADE'), nullable=False)
    sentence_id = Column(Integer, nullable=False)
    sentence_token_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ['text_id', 'sentence_id'],
            ['sentences.text_id', 'sentences.sentence_id'],
            ondelete='CASCADE'
        ),
        UniqueConstraint('user_id', 'text_id', 'sentence_id', 'sentence_token_id', name='uq_asked_token_user_text_sentence_token')
    )


def create_database_engine(database_url: str):
    return create_engine(database_url, echo=False, future=True)


def create_session(engine):
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return Session()


def init_database(engine):
    Base.metadata.create_all(engine)
    print("数据库表创建完成") 