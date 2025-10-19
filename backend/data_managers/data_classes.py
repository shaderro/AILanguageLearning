from dataclasses import dataclass
from typing import List, Optional


@dataclass
class GrammarRule:
    rule_id: int
    name: str
    explanation: str

@dataclass
class GrammarExample:
    rule_id: int
    text_id: int
    sentence_id: int
    explanation_context: str

@dataclass
class GrammarBundle:
	rule: GrammarRule
	examples: list[GrammarExample]

@dataclass
class VocabExpression:
    vocab_id: int
    vocab_body: str
    explanation: str

@dataclass
class VocabExpressionExample:
    vocab_id: int
    text_id: int
    sentence_id: int
    context_explanation: str

@dataclass
class VocabExpressionBundle:
    vocab: VocabExpression
    example: list[VocabExpressionExample]

@dataclass(frozen=True)
class Sentence:
    text_id: int
    sentence_id: int
    sentence_body: str
    grammar_annotations: tuple[int, ...] #rule id
    vocab_annotations: tuple[int, ...] #word id

@dataclass
class OriginalText:
    text_id: int
    text_title: str
    text_by_sentence: list[Sentence]

@dataclass
class AskedToken:
    """已提问的 token 记录"""
    user_id: str
    text_id: int
    sentence_id: int
    sentence_token_id: Optional[int] = None  # 改为可选：当 type='sentence' 时可以为空
    type: str = "token"  # 新增：标记类型，默认为 token（'token' 或 'sentence'）
    asked_at: Optional[int] = None