from assistants.chat_info.dialogue_history import DialogueHistory
from data_managers.data_classes import Sentence
from data_managers.data_classes_new import Sentence as NewSentence
from dataclasses import dataclass
from typing import Union, Optional, List
from assistants.chat_info.selected_token import SelectedToken

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

# 类型别名，支持新旧两种句子类型
SentenceType = Union[Sentence, NewSentence]

class SessionState:
    def __init__(self):
        #self.dialogue_history = DialogueHistory(max_turns=max_turns)
        self.current_sentence: Optional[SentenceType] = None
        self.current_selected_token: Optional[SelectedToken] = None  # 新增：当前选择的token
        self.current_input: Optional[str] = None
        self.current_response: Optional[str] = None
        self.check_relevant_decision: Optional[CheckRelevantDecision] = None
        self.summarized_results: List[Union[GrammarSummary, VocabSummary]] = []
        self.grammar_to_add: List[GrammarToAdd] = []
        self.vocab_to_add: List[VocabToAdd] = []
    
    def set_current_sentence(self, sentence: SentenceType):
        """
        设置当前对话中引用的句子。
        支持新旧两种数据结构。
        """
        self.current_sentence = sentence

    def set_current_selected_token(self, selected_token: SelectedToken):
        """
        设置当前用户选择的token。
        """
        self.current_selected_token = selected_token

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
        """完全重置所有状态（上下文 + 处理结果）"""
        self.current_sentence = None
        self.current_selected_token = None
        self.current_input = None
        self.current_response = None
        self.check_relevant_decision = None
        self.summarized_results.clear()
        self.grammar_to_add.clear()
        self.vocab_to_add.clear()
    
    def reset_processing_results(self):
        """只重置处理结果，保留上下文（避免重复设置）"""
        self.current_response = None
        self.check_relevant_decision = None
        self.summarized_results.clear()
        self.grammar_to_add.clear()
        self.vocab_to_add.clear()
        # 保留：current_sentence、current_selected_token、current_input

    def get_current_sentence_info(self) -> dict:
        """获取当前句子的详细信息，适配新旧数据结构"""
        if not self.current_sentence:
            return {"error": "No current sentence"}
        
        info = {
            "text_id": self.current_sentence.text_id,
            "sentence_id": self.current_sentence.sentence_id,
            "sentence_body": self.current_sentence.sentence_body,
            "data_type": "new" if hasattr(self.current_sentence, 'sentence_difficulty_level') else "old"
        }
        
        # 新数据结构特有信息
        if hasattr(self.current_sentence, 'sentence_difficulty_level'):
            info["difficulty_level"] = self.current_sentence.sentence_difficulty_level
        
        if hasattr(self.current_sentence, 'tokens') and self.current_sentence.tokens:
            info["token_count"] = len(self.current_sentence.tokens)
            info["has_tokens"] = True
        else:
            info["has_tokens"] = False
        
        if hasattr(self.current_sentence, 'grammar_annotations'):
            info["grammar_annotations"] = self.current_sentence.grammar_annotations
        
        if hasattr(self.current_sentence, 'vocab_annotations'):
            info["vocab_annotations"] = self.current_sentence.vocab_annotations
        
        return info

    def get_current_sentence_tokens(self) -> dict:
        """获取当前句子的token信息，仅适用于新数据结构"""
        if not self.current_sentence or not hasattr(self.current_sentence, 'tokens'):
            return {"error": "No tokens available"}
        
        tokens_info = {
            "total_tokens": len(self.current_sentence.tokens),
            "text_tokens": [],
            "punctuation_tokens": [],
            "space_tokens": [],
            "grammar_markers": [],
            "hard_tokens": [],
            "easy_tokens": [],
            "pos_tags": {}
        }
        
        for token in self.current_sentence.tokens:
            # 按类型分类
            if token.token_type == "text":
                tokens_info["text_tokens"].append(token.token_body)
            elif token.token_type == "punctuation":
                tokens_info["punctuation_tokens"].append(token.token_body)
            elif token.token_type == "space":
                tokens_info["space_tokens"].append(token.token_body)
            
            # 按难度分类
            if hasattr(token, 'difficulty_level'):
                if token.difficulty_level == "hard":
                    tokens_info["hard_tokens"].append(token.token_body)
                elif token.difficulty_level == "easy":
                    tokens_info["easy_tokens"].append(token.token_body)
            
            # 语法标记
            if hasattr(token, 'is_grammar_marker') and token.is_grammar_marker:
                tokens_info["grammar_markers"].append(token.token_body)
            
            # 词性标注统计
            if hasattr(token, 'pos_tag') and token.pos_tag:
                if token.pos_tag not in tokens_info["pos_tags"]:
                    tokens_info["pos_tags"][token.pos_tag] = []
                tokens_info["pos_tags"][token.pos_tag].append(token.token_body)
        
        return tokens_info

    def get_learning_context(self) -> dict:
        """获取学习上下文信息，包括句子信息和当前状态"""
        context = {
            "current_sentence": self.get_current_sentence_info(),
            "current_input": self.current_input,
            "current_response": self.current_response,
            "summarized_results_count": len(self.summarized_results),
            "grammar_to_add_count": len(self.grammar_to_add),
            "vocab_to_add_count": len(self.vocab_to_add)
        }
        
        # 如果是新数据结构，添加token信息
        if self.current_sentence and hasattr(self.current_sentence, 'tokens'):
            context["tokens_info"] = self.get_current_sentence_tokens()
        
        return context

    def is_new_structure_sentence(self) -> bool:
        """判断当前句子是否为新数据结构"""
        return (self.current_sentence is not None and 
                hasattr(self.current_sentence, 'sentence_difficulty_level'))

    def get_sentence_difficulty(self) -> str:
        """获取句子难度级别，仅适用于新数据结构"""
        if self.is_new_structure_sentence():
            return self.current_sentence.sentence_difficulty_level
        return "unknown"

    def get_hard_tokens(self) -> list:
        """获取困难词汇列表，仅适用于新数据结构"""
        if not self.is_new_structure_sentence() or not self.current_sentence.tokens:
            return []
        
        return [t.token_body for t in self.current_sentence.tokens 
                if hasattr(t, 'difficulty_level') and t.difficulty_level == "hard"]

    def get_grammar_markers(self) -> list:
        """获取语法标记词汇列表，仅适用于新数据结构"""
        if not self.is_new_structure_sentence() or not self.current_sentence.tokens:
            return []
        
        return [t.token_body for t in self.current_sentence.tokens 
                if hasattr(t, 'is_grammar_marker') and t.is_grammar_marker]

