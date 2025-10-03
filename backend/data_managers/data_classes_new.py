from typing import Optional, Literal
from dataclasses import dataclass, field


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
    sentence_token_id: int