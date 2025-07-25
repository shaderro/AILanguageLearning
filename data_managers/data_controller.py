import json
from typing import List, Dict
from dataclasses import asdict, dataclass
from data_managers.data_classes import OriginalText, Sentence, GrammarRule, GrammarExample, GrammarBundle, VocabExpression, VocabExpressionExample
from data_managers.grammar_rule_manager import GrammarRuleManager
from data_managers.vocab_manager import VocabManager
from data_managers.original_text_manager import OriginalTextManager
from data_managers.dialogue_record import DialogueRecordBySentence
from assistants.chat_info.dialogue_history import DialogueHistory
from data_managers.data_classes import VocabExpressionBundle

class DataController:
    """
    A controller class for managing data operations related to grammar rules, vocabulary expressions, and original texts.
    """
    def __init__(self, max_turns:int):
        self.grammar_manager = GrammarRuleManager()
        self.vocab_manager = VocabManager()
        self.text_manager = OriginalTextManager()
        self.dialogue_record = DialogueRecordBySentence()
        self.dialogue_history = DialogueHistory(max_turns)

    def load_data(self, grammar_path: str, vocab_path: str, text_path: str, dialogue_record_path: str, dialogue_history_path: str):
        """
        Load data from specified JSON files.
        """
        self.grammar_manager.load_from_file(grammar_path)
        self.vocab_manager.load_from_file(vocab_path)
        self.text_manager.load_from_file(text_path)
        self.dialogue_record.load_from_file(dialogue_record_path)
        self.dialogue_history.load_from_file(dialogue_history_path)
        
    def save_data(self, grammar_path: str, vocab_path: str, text_path: str, dialogue_record_path: str, dialogue_history_path: str):
        """
        Save data to specified JSON files.
        """
        self.grammar_manager.save_to_file(grammar_path)
        self.vocab_manager.save_to_file(vocab_path)
        self.text_manager.save_to_file(text_path)
        self.dialogue_record.save_all_to_file(dialogue_record_path)
        self.dialogue_history.save_to_file(dialogue_history_path)

    def add_new_text(self, text_title: str):
        """
        Add a new text with the given title.
        """
        self.text_manager.add_text(text_title)

    def add_sentence_to_text(self, text_id: int, sentence: str):
        """
        Add a sentence to the specified text.
        """
        self.text_manager.add_sentence_to_text(text_id, sentence)
    
    def add_new_grammar_rule(self, rule_name: str, rule_explanation: str) -> int:
        """
        Add a new grammar rule with the specified name and explanation.
        """
        return self.grammar_manager.add_new_rule(rule_name, rule_explanation)
    
    def add_new_vocab(self, vocab_body: str, explanation: str) -> int:
        """
        Add a new vocabulary expression with the specified body and explanation.
        """
        return self.vocab_manager.add_new_vocab(vocab_body, explanation)
    
    def add_grammar_example(self, rule_id: int, text_id: int, sentence_id: int, explanation_context: str):
        """
        Add a grammar example to the specified rule and sentence.
        """
        self.grammar_manager.add_grammar_example(self.text_manager, rule_id, text_id, sentence_id, explanation_context)

    def add_vocab_example(self, vocab_id: int, text_id: int, sentence_id: int, context_explanation: str):
        """
        Add a vocabulary example to the specified vocab and sentence.
        """
        self.vocab_manager.add_vocab_example(self.text_manager, vocab_id, text_id, sentence_id, context_explanation)

    def get_grammar_examples_by_rule_id(self, rule_id: int) -> List[GrammarExample]:
        """
        Get all grammar examples for the specified rule ID.
        """
        return self.grammar_manager.get_examples_by_rule_id(rule_id)
    
    def get_vocab_examples_by_vocab_id(self, vocab_id: int) -> List[VocabExpressionExample]:
        """
        Get all vocabulary examples for the specified vocab ID.
        """
        return self.vocab_manager.get_examples_by_vocab_id(vocab_id)
    
    def get_example_by_text_sentence_id(self, text_id: int, sentence_id: int) -> GrammarExample:
        """
        Get a grammar example by text and sentence ID.
        """
        return self.grammar_manager.get_example_by_text_sentence_id(text_id, sentence_id)
    
    def get_vocab_example_by_text_sentence_id(self, text_id: int, sentence_id: int) -> VocabExpressionExample:
        """
        Get a vocabulary example by text and sentence ID.
        """
        return self.vocab_manager.get_example_by_text_sentence_id(text_id, sentence_id)
    
    def get_text_by_id(self, text_id: int) -> OriginalText | None:
        """
        Get the original text by its ID.
        """
        return self.text_manager.get_text_by_id(text_id)
    
    def list_texts_by_title(self) -> List[str]:
        """
        List all original texts by their titles.
        """
        return self.text_manager.list_titles()
    
    def get_all_vocab_data(self) -> List[tuple]:
        """
        Get all vocabulary data as a list of tuples (vocab_body, explanation, example_text, difficulty)
        """
        vocab_data = []
        for vocab_id, bundle in self.vocab_manager.vocab_bundles.items():
            vocab = bundle.vocab
            # 获取第一个例子作为示例
            example_text = ""
            if bundle.example:
                example = bundle.example[0]
                # 这里可以进一步获取句子的实际内容，暂时使用context_explanation
                example_text = example.context_explanation
            
            # 根据词汇长度或复杂度判断难度
            difficulty = "简单" if len(vocab.vocab_body) <= 6 else "中等" if len(vocab.vocab_body) <= 10 else "困难"
            
            vocab_data.append((vocab.vocab_body, vocab.explanation, example_text, difficulty))
        
        return vocab_data