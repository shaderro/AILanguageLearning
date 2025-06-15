from assistants.chat_info.dialogue_history import DialogueHistory
from data_managers.data_classes import Sentence
from dataclasses import dataclass
from typing import Union, Optional
from typing import List, Optional, Union

@dataclass
class GrammarToAdd:
    rule_name: str
    rule_explanation: str

@dataclass
class VocabToAdd:
    vocab: str

@dataclass
class GrammarSummary:
    grammar_rule_name: str
    grammar_rule_summary: str

@dataclass
class VocabSummary:
    vocab: str

@dataclass
class CheckRelevantDecision:
    grammar: bool
    vocab: bool

class SessionState:
    def __init__(self, max_turns=5):
        #self.dialogue_history = DialogueHistory(max_turns=max_turns)
        self.current_sentence: Optional[Sentence] = None
        self.current_input: Optional[str] = None
        self.current_response: Optional[str] = None
        self.check_relevant_decision: Optional[CheckRelevantDecision] = None
        self.summarized_results: List[Union[GrammarSummary, VocabSummary]] = []
        self.grammar_to_add: List[GrammarToAdd] = []
        self.vocab_to_add: List[VocabToAdd] = []
    
    def set_current_sentence(self, sentence: Sentence):
        """
        设置当前对话中引用的句子。
        """
        self.current_sentence = sentence

    def set_current_input(self, user_input: str):
        """
        设置当前用户输入。
        """
        self.current_input = user_input

    def set_current_response(self, ai_response: str):   
        """
        设置当前 AI 响应。
        """
        self.current_response = ai_response
    
    def set_check_relevant_decision(self, grammar: bool, vocab: bool):
        """
        设置当前是否与语法或词汇相关的决策。
        """
        self.check_relevant_decision = CheckRelevantDecision(grammar=grammar, vocab=vocab)
    
    def add_grammar_summary(self, name: str, summary: str):
        self.summarized_results.append(GrammarSummary(grammar_rule_name=name, grammar_rule_summary=summary))

    def add_vocab_summary(self, vocab: str):
        self.summarized_results.append(VocabSummary(vocab=vocab))

    def add_grammar_to_add(self, rule_name: str, rule_explanation: str):
        self.grammar_to_add.append(GrammarToAdd(rule_name=rule_name, rule_explanation=rule_explanation))

    def add_vocab_to_add(self, vocab: str):
        self.vocab_to_add.append(VocabToAdd(vocab=vocab))

    def reset(self):
        self.current_sentence = None
        self.current_input = None
        self.current_response = None
        self.check_relevant_decision = None
        self.summarized_results.clear()
        self.grammar_to_add.clear()
        self.vocab_to_add.clear()

