from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Enum,
    ForeignKeyConstraint,
    UniqueConstraint,
    TypeDecorator,
    BigInteger,
    Index,
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

class AskedTokenType(enum.Enum):
    TOKEN = 'token'      # 标记的是单词（需要 sentence_token_id）
    SENTENCE = 'sentence'  # 标记的是句子（sentence_token_id 可为空）

class LearnStatus(enum.Enum):
    """学习状态枚举"""
    NOT_MASTERED = 'not_mastered'  # 未掌握
    MASTERED = 'mastered'  # 已掌握


class EnumType(TypeDecorator):
    """自定义枚举类型，用于 SQLite 兼容性"""
    impl = String
    cache_ok = True
    
    def __init__(self, enum_class, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enum_class = enum_class
    
    def process_bind_param(self, value, dialect):
        """将枚举对象转换为字符串存储"""
        if value is None:
            return None
        if isinstance(value, enum.Enum):
            return value.value
        return str(value)
    
    def process_result_value(self, value, dialect):
        """将字符串值转换回枚举对象"""
        if value is None:
            return None
        if isinstance(value, self.enum_class):
            return value
        # 尝试通过值查找枚举
        for enum_item in self.enum_class:
            if enum_item.value == value:
                return enum_item
        # 如果找不到，尝试通过名称查找
        try:
            return self.enum_class[value]
        except KeyError:
            # 如果都找不到，返回默认值
            return list(self.enum_class)[0] if self.enum_class else None

class VocabExpression(Base):
    __tablename__ = 'vocab_expressions'

    vocab_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    vocab_body = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=False)
    language = Column(String(50), nullable=True)  # 语言：中文、英文、德文
    source = Column(EnumType(SourceType, length=50), default=SourceType.AUTO, nullable=False)
    is_starred = Column(Boolean, default=False, nullable=False)
    learn_status = Column(EnumType(LearnStatus, length=50), default=LearnStatus.NOT_MASTERED, nullable=False)  # 学习状态：未掌握/已掌握
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'vocab_body', name='uq_user_vocab_body'),
    )

    examples = relationship('VocabExpressionExample', back_populates='vocab', cascade='all, delete-orphan')
    tokens = relationship('Token', back_populates='linked_vocab')
    owner = relationship('User', backref='vocab_expressions')

class GrammarRule(Base):
    __tablename__ = 'grammar_rules'

    rule_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    rule_name = Column(String(255), nullable=False)
    rule_summary = Column(Text, nullable=False)
    language = Column(String(50), nullable=True)  # 语言：中文、英文、德文
    source = Column(EnumType(SourceType, length=50), default=SourceType.AUTO, nullable=False)
    is_starred = Column(Boolean, default=False, nullable=False)
    learn_status = Column(EnumType(LearnStatus, length=50), default=LearnStatus.NOT_MASTERED, nullable=False)  # 学习状态：未掌握/已掌握
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'rule_name', name='uq_user_rule_name'),
    )

    examples = relationship('GrammarExample', back_populates='grammar_rule', cascade='all, delete-orphan')
    owner = relationship('User', backref='grammar_rules')

class OriginalText(Base):
    __tablename__ = 'original_texts'

    text_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    text_title = Column(String(500), nullable=False)
    language = Column(String(50), nullable=True)  # 语言：中文、英文、德文
    processing_status = Column(String(50), default='completed', nullable=False)  # 处理状态：processing（处理中）、completed（已完成）、failed（失败）
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    sentences = relationship('Sentence', back_populates='text', cascade='all, delete-orphan')
    owner = relationship('User', backref='original_texts')

class Sentence(Base):
    __tablename__ = 'sentences'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sentence_id = Column(Integer, nullable=False)
    text_id = Column(Integer, ForeignKey('original_texts.text_id', ondelete='CASCADE'), nullable=False)
    sentence_body = Column(Text, nullable=False)
    sentence_difficulty_level = Column(EnumType(DifficultyLevel, length=50))
    grammar_annotations = Column(JSON)
    vocab_annotations = Column(JSON)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    __table_args__ = (
        UniqueConstraint('text_id', 'sentence_id', name='uq_sentence_text_sentence'),
    )

    text = relationship('OriginalText', back_populates='sentences')
    tokens = relationship('Token', back_populates='sentence', cascade='all, delete-orphan')
    word_tokens = relationship('WordToken', back_populates='sentence', cascade='all, delete-orphan')  # 仅用于非空格语言

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
    token_type = Column(EnumType(TokenType, length=50), nullable=False)
    difficulty_level = Column(EnumType(DifficultyLevel, length=50))
    global_token_id = Column(Integer)
    sentence_token_id = Column(Integer)
    pos_tag = Column(String(50))
    lemma = Column(String(255))
    is_grammar_marker = Column(Boolean, default=False, nullable=False)
    linked_vocab_id = Column(Integer, ForeignKey('vocab_expressions.vocab_id', ondelete='SET NULL'))
    word_token_id = Column(Integer, ForeignKey('word_tokens.word_token_id', ondelete='SET NULL'), nullable=True)  # 仅用于非空格语言：指向所属的 WordToken
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
    word_token = relationship('WordToken', back_populates='char_tokens', foreign_keys=[word_token_id])


class WordToken(Base):
    """
    词级别 Token（仅用于非空格语言：中文、日文等）
    
    用途：
    - 用于 vocab 功能的语义分析
    - 通过分词库生成（如 jieba、mecab 等）
    - 与 char token（Token）建立映射关系
    """
    __tablename__ = 'word_tokens'

    word_token_id = Column(Integer, primary_key=True, autoincrement=True)
    text_id = Column(Integer, ForeignKey('original_texts.text_id', ondelete='CASCADE'), nullable=False)
    sentence_id = Column(Integer, nullable=False)
    word_body = Column(String(255), nullable=False)  # 分词后的词，如 "喜欢"
    token_ids = Column(JSON, nullable=False)  # 由哪些 char token 的 sentence_token_id 组成，如 [2, 3]
    pos_tag = Column(String(50), nullable=True)  # 词性标注
    lemma = Column(String(255), nullable=True)  # 词形还原
    linked_vocab_id = Column(Integer, ForeignKey('vocab_expressions.vocab_id', ondelete='SET NULL'), nullable=True)  # 指向词汇表中的词汇解释
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ['text_id', 'sentence_id'],
            ['sentences.text_id', 'sentences.sentence_id'],
            ondelete='CASCADE'
        ),
        UniqueConstraint('text_id', 'sentence_id', 'word_token_id', name='uq_word_token_text_sentence_word'),
    )

    sentence = relationship('Sentence', back_populates='word_tokens')
    linked_vocab = relationship('VocabExpression', backref='word_tokens')
    char_tokens = relationship('Token', back_populates='word_token', foreign_keys='Token.word_token_id')


class AskedToken(Base):
    __tablename__ = 'asked_tokens'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    text_id = Column(Integer, ForeignKey('original_texts.text_id', ondelete='CASCADE'), nullable=False)
    sentence_id = Column(Integer, nullable=False)
    sentence_token_id = Column(Integer, nullable=True)  # 改为可空：当 type='sentence' 时可以为空
    type = Column(EnumType(AskedTokenType, length=50), default=AskedTokenType.TOKEN, nullable=False)  # 新增：标记类型
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ['text_id', 'sentence_id'],
            ['sentences.text_id', 'sentences.sentence_id'],
            ondelete='CASCADE'
        ),
        # 修改唯一约束：对于 sentence 类型，sentence_token_id 可以为 NULL
        # SQLite 中 NULL != NULL，所以同一句子可以有多个 NULL 的 sentence_token_id
        # 我们需要确保：对于 token 类型，同一用户的同一 token 只能标记一次
        # 对于 sentence 类型，同一用户的同一句子只能标记一次（但 sentence_token_id 为 NULL）
        UniqueConstraint('user_id', 'text_id', 'sentence_id', 'sentence_token_id', 'type', name='uq_asked_token_user_text_sentence_token_type')
    )

class VocabNotation(Base):
    __tablename__ = 'vocab_notations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    text_id = Column(Integer, ForeignKey('original_texts.text_id', ondelete='CASCADE'), nullable=False)
    sentence_id = Column(Integer, nullable=False)
    token_id = Column(Integer, nullable=False)  # sentence_token_id（保持向后兼容）
    word_token_id = Column(Integer, ForeignKey('word_tokens.word_token_id', ondelete='SET NULL'), nullable=True)  # 新增：用于非空格语言的 word token 级别标注
    vocab_id = Column(Integer, ForeignKey('vocab_expressions.vocab_id', ondelete='CASCADE'))
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    __table_args__ = (
        ForeignKeyConstraint(
            ['text_id', 'sentence_id'],
            ['sentences.text_id', 'sentences.sentence_id'],
            ondelete='CASCADE'
        ),
        UniqueConstraint('user_id', 'text_id', 'sentence_id', 'token_id', name='uq_vocab_notation')
    )
    
    # 关系
    vocab = relationship('VocabExpression', backref='notations')
    text = relationship('OriginalText', backref='vocab_notations')
    word_token = relationship('WordToken', backref='vocab_notations')  # 新增：关联到 WordToken

class GrammarNotation(Base):
    __tablename__ = 'grammar_notations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    text_id = Column(Integer, ForeignKey('original_texts.text_id', ondelete='CASCADE'), nullable=False)
    sentence_id = Column(Integer, nullable=False)
    grammar_id = Column(Integer, ForeignKey('grammar_rules.rule_id', ondelete='CASCADE'))
    marked_token_ids = Column(JSON, nullable=False, default=[])
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    __table_args__ = (
        ForeignKeyConstraint(
            ['text_id', 'sentence_id'],
            ['sentences.text_id', 'sentences.sentence_id'],
            ondelete='CASCADE'
        ),
        UniqueConstraint('user_id', 'text_id', 'sentence_id', name='uq_grammar_notation')
    )
    
    # 关系
    grammar_rule = relationship('GrammarRule', backref='notations')
    text = relationship('OriginalText', backref='grammar_notations')

class UserArticleAccess(Base):
    """用户文章访问记录（用于记录最后打开时间，支持跨设备排序）"""
    __tablename__ = 'user_article_access'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    text_id = Column(Integer, ForeignKey('original_texts.text_id', ondelete='CASCADE'), nullable=False, index=True)
    last_opened_at = Column(DateTime, default=datetime.now, nullable=False)  # 最后打开时间
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'text_id', name='uq_user_article_access'),
    )
    
    # 关联关系
    user = relationship('User', backref='article_accesses')
    text = relationship('OriginalText', backref='user_accesses')


class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    password_hash = Column(String(255), nullable=False)  # 存储哈希后的密码
    email = Column(String(255), nullable=True, unique=True, index=True)  # 邮箱（唯一性约束）
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    # 角色：'admin' | 'user'，用于区分管理员和普通用户
    role = Column(String(32), nullable=False, default='user')
    # 当前可用 token 余额（使用 BigInteger 以避免后续累计溢出）
    token_balance = Column(BigInteger, nullable=False, default=0)
    # 最近一次 token 变动时间（用于排查和前端展示，可为空）
    token_updated_at = Column(DateTime, nullable=True)
    
    # 关联关系
    asked_tokens = relationship('AskedToken', backref='user', cascade='all, delete-orphan')
    vocab_notations = relationship('VocabNotation', backref='user', cascade='all, delete-orphan')
    grammar_notations = relationship('GrammarNotation', backref='user', cascade='all, delete-orphan')

    __table_args__ = (
        # 方便按角色筛选用户（例如统计 admin / user）
        Index('idx_users_role', 'role'),
    )


class InviteCode(Base):
    """
    一次性邀请码表：
    - 每条记录代表一个邀请码
    - 固定发放 token_grant（当前设计为 1,000,000）
    - 只能被兑换一次（单用户生效）
    """
    __tablename__ = 'invite_codes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # 邀请码文本（建议在业务层统一转为大写再存储，以实现大小写不敏感）
    code = Column(String(64), nullable=False, unique=True)
    # 本次邀请码可发放的 token 数量（默认 1,000,000）
    token_grant = Column(BigInteger, nullable=False, default=1000000)
    # 状态：active | disabled | redeemed | expired
    status = Column(String(16), nullable=False, default='active')
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    # 过期时间（可选）
    expires_at = Column(DateTime, nullable=True)
    # 被哪个用户兑换（单用户生效的关键字段）
    redeemed_by_user_id = Column(Integer, ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True, index=True)
    redeemed_at = Column(DateTime, nullable=True)
    # 备注：批次、渠道等
    note = Column(String(255), nullable=True)

    redeemed_by_user = relationship('User', backref='redeemed_invite_codes', foreign_keys=[redeemed_by_user_id])

    __table_args__ = (
        # 便于按状态筛选未使用/已使用邀请码
        Index('idx_invite_codes_status', 'status'),
    )


class TokenLedger(Base):
    """
    Token 账本表：
    - 记录所有 token 变动（正数发放，负数消耗）
    - 可用于审计与余额回算
    """
    __tablename__ = 'token_ledger'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    # 本次变动值：+1000000（邀请码发放）、-1（一次 AI 调用）等
    delta = Column(BigInteger, nullable=False)
    # 变动原因：invite_grant / ai_usage / admin_adjust / refund 等
    reason = Column(String(32), nullable=False)
    # 参考类型与 ID（如 invite_code / request）
    ref_type = Column(String(32), nullable=True)
    ref_id = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    # 幂等键：防止网络重试导致重复扣费/发放（可选）
    idempotency_key = Column(String(128), unique=True, nullable=True)

    user = relationship('User', backref='token_ledger_entries')

    __table_args__ = (
        Index('idx_token_ledger_user_time', 'user_id', 'created_at'),
    )


class TokenLog(Base):
    """
    Token 使用日志表：
    - 记录每次 DeepSeek API 调用的真实 token 使用量
    - 用于统计用户累计使用量和调试成本异常
    """
    __tablename__ = 'token_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    # 本次 API 调用使用的 token 数量（从 response.usage.total_tokens 获取）
    total_tokens = Column(Integer, nullable=False)
    # Prompt tokens（用于详细记录）
    prompt_tokens = Column(Integer, nullable=False)
    # Completion tokens（用于详细记录）
    completion_tokens = Column(Integer, nullable=False)
    # 使用的模型名称（如 "deepseek-chat"）
    model_name = Column(String(64), nullable=False)
    # 调用的 SubAssistant 名称（如 "AnswerQuestionAssistant", "CheckIfGrammarRelevantAssistant" 等）
    assistant_name = Column(String(128), nullable=True)
    # 记录创建时间
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    user = relationship('User', backref='token_logs')

    __table_args__ = (
        # 方便按用户和时间查询
        Index('idx_token_logs_user_time', 'user_id', 'created_at'),
    )


def create_database_engine(database_url: str):
    return create_engine(database_url, echo=False, future=True)


def create_session(engine):
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return Session()


def init_database(engine):
    Base.metadata.create_all(engine)
    print("数据库表创建完成") 