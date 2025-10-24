from typing import Optional, Literal
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Token:
    token_body: str
    token_type: Literal["text", "punctuation", "space"]
    difficulty_level: Optional[Literal["easy", "hard"]] = None
    global_token_id: Optional[int] = None         # 全文级别 ID
    sentence_token_id: Optional[int] = None       # 当前句子内 ID
    pos_tag: Optional[str] = None              # 词性标注（可选：用于后续语法分析）
    lemma: Optional[str] = None                # 原型词（用于合并变形、统一解释）
    is_grammar_marker: Optional[bool] = False  # 是否参与语法结构识别
    linked_vocab_id: Optional[int] = None  # 指向词汇中心解释

@dataclass(frozen=True)
class Sentence:
    text_id: int
    sentence_id: int
    sentence_body: str
    grammar_annotations: tuple[int, ...] = ()  # rule id
    vocab_annotations: tuple[int, ...] = ()    # word id
    sentence_difficulty_level: Optional[Literal["easy", "hard"]] = None
    tokens: tuple[Token, ...] = ()

@dataclass
class OriginalText:
    text_id: int
    text_title: str
    text_by_sentence: list[Sentence]

@dataclass
class GrammarExample:
    rule_id: int
    text_id: int
    sentence_id: int
    explanation_context: str

@dataclass
class GrammarRule:
    rule_id: int
    name: str
    explanation: str
    source: Literal["auto", "qa", "manual"] = "auto"
    is_starred: bool = False
    examples: list[GrammarExample] = field(default_factory=list)

@dataclass
class VocabExpressionExample:
    vocab_id: int
    text_id: int
    sentence_id: int
    context_explanation: str
    token_indices: list[int] = field(default_factory=list)

@dataclass
class VocabExpression:
    vocab_id: int
    vocab_body: str
    explanation: str
    source: Literal["auto", "qa", "manual"] = "auto"
    is_starred: bool = False
    examples: list[VocabExpressionExample] = field(default_factory=list)

@dataclass
class AskedToken:
    """已提问的 token 记录"""
    user_id: str
    text_id: int
    sentence_id: int
    sentence_token_id: Optional[int] = None  # 改为可选：当 type='sentence' 时可以为空
    type: Literal["token", "sentence"] = "token"  # 新增：标记类型，默认为 token
    # 约定：当 type='token' 时填写 vocab_id；当 type='sentence' 时填写 grammar_id；其余保持 None
    vocab_id: Optional[int] = None
    grammar_id: Optional[int] = None

@dataclass
class VocabNotation:
    """词汇标注"""
    user_id: str
    text_id: int
    sentence_id: int
    token_id: int               # 当前句子中哪个 token
    vocab_id: Optional[int]     # 对应词汇表中的词汇
    created_at: Optional[str] = None  # 时间戳（可选）

@dataclass
class GrammarNotation:
    """语法标注"""
    user_id: str
    text_id: int
    sentence_id: int
    grammar_id: Optional[int]   # 对应 grammar_rules 表
    marked_token_ids: list[int] # 句中重点语法成分的 token id 列表
    created_at: Optional[str] = None

@dataclass
class User:
    """用户DTO - 最简版本"""
    user_id: int          # 唯一标识
    password: str         # 密码（实际应存储哈希值）
    created_at: Optional[datetime] = None  # 创建时间