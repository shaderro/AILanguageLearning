from dataclasses import dataclass
from typing import List


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

@dataclass
class Sentence:
    text_id: int
    sentence_id: int
    sentence_body: str
    grammar_annotations: list[int] #rule id
    vocab_annotations: list[int] #word id

@dataclass
class OriginalText:
    text_id: int
    text_title: str
    text_by_sentence: list[Sentence]