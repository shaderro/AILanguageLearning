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

# 新结构模式开关
USE_NEW_STRUCTURE = False
# 新结构数据保存开关
SAVE_TO_NEW_DATA_CLASS = False

class DataController:
    """
    A controller class for managing data operations related to grammar rules, vocabulary expressions, and original texts.
    """
    def __init__(self, max_turns:int, use_new_structure: bool = None, save_to_new_data_class: bool = None):
        # 如果未指定，使用全局开关设置
        if use_new_structure is None:
            use_new_structure = USE_NEW_STRUCTURE
        if save_to_new_data_class is None:
            save_to_new_data_class = SAVE_TO_NEW_DATA_CLASS
            
        self.use_new_structure = use_new_structure
        self.save_to_new_data_class = save_to_new_data_class
        
        # 根据结构模式初始化相应的管理器
        if self.use_new_structure:
            # 使用现有管理器并开启新结构模式
            self.grammar_manager = GrammarRuleManager(use_new_structure=True)
            self.vocab_manager = VocabManager(use_new_structure=True)
            self.text_manager = OriginalTextManager(use_new_structure=True)
            print("✅ 已启用新数据结构模式")
        else:
            # 旧结构模式
            self._init_old_structure()
            
        if self.save_to_new_data_class:
            print("✅ 已启用新结构数据保存模式")
            
        self.dialogue_record = DialogueRecordBySentence()
        self.dialogue_history = DialogueHistory(max_turns)
    
    def _init_old_structure(self):
        """初始化旧结构的管理器"""
        self.grammar_manager = GrammarRuleManager(use_new_structure=False)
        self.vocab_manager = VocabManager(use_new_structure=False)
        self.text_manager = OriginalTextManager(use_new_structure=False)
        print("✅ 已启用旧数据结构模式")

    def load_data(self, grammar_path: str, vocab_path: str, text_path: str, dialogue_record_path: str, dialogue_history_path: str):
        """
        Load data from specified JSON files.
        """
        try:
            if self.use_new_structure:
                # 新结构模式的数据加载逻辑
                self._load_data_new_structure(grammar_path, vocab_path, text_path, dialogue_record_path, dialogue_history_path)
            else:
                # 旧结构模式的数据加载逻辑
                self._load_data_old_structure(grammar_path, vocab_path, text_path, dialogue_record_path, dialogue_history_path)
        except Exception as e:
            print(f"⚠️ 数据加载失败，尝试回退到旧结构: {e}")
            self.use_new_structure = False
            self._init_old_structure()
            self._load_data_old_structure(grammar_path, vocab_path, text_path, dialogue_record_path, dialogue_history_path)
    
    def _load_data_old_structure(self, grammar_path: str, vocab_path: str, text_path: str, dialogue_record_path: str, dialogue_history_path: str):
        """旧结构模式的数据加载"""
        self.grammar_manager.load_from_file(grammar_path)
        self.vocab_manager.load_from_file(vocab_path)
        self.text_manager.load_from_file(text_path)
        self.dialogue_record.load_from_file(dialogue_record_path)
        self.dialogue_history.load_from_file(dialogue_history_path)
    
    def _load_data_new_structure(self, grammar_path: str, vocab_path: str, text_path: str, dialogue_record_path: str, dialogue_history_path: str):
        """新结构模式的数据加载"""
        # 目前新旧结构共用旧 JSON 文件，直接调用旧加载
        self._load_data_old_structure(grammar_path, vocab_path, text_path, dialogue_record_path, dialogue_history_path)
        
    def save_data(self, grammar_path: str, vocab_path: str, text_path: str, dialogue_record_path: str, dialogue_history_path: str):
        """
        Save data to specified JSON files.
        """
        try:
            if self.use_new_structure:
                # 新结构模式的数据保存逻辑
                self._save_data_new_structure(grammar_path, vocab_path, text_path, dialogue_record_path, dialogue_history_path)
            else:
                # 旧结构模式的数据保存逻辑
                self._save_data_old_structure(grammar_path, vocab_path, text_path, dialogue_record_path, dialogue_history_path)
        except Exception as e:
            print(f"⚠️ 数据保存失败，尝试回退到旧结构: {e}")
            self.use_new_structure = False
            self._init_old_structure()
            self._save_data_old_structure(grammar_path, vocab_path, text_path, dialogue_record_path, dialogue_history_path)
    
    def _save_data_old_structure(self, grammar_path: str, vocab_path: str, text_path: str, dialogue_record_path: str, dialogue_history_path: str):
        """旧结构模式的数据保存"""
        self.grammar_manager.save_to_file(grammar_path)
        self.vocab_manager.save_to_file(vocab_path)
        self.text_manager.save_to_file(text_path)
        self.dialogue_record.save_all_to_file(dialogue_record_path)
        self.dialogue_history.save_to_file(dialogue_history_path)
    
    def _save_data_new_structure(self, grammar_path: str, vocab_path: str, text_path: str, dialogue_record_path: str, dialogue_history_path: str):
        """新结构模式的数据保存"""
        if self.save_to_new_data_class:
            # 保存新结构数据到新的 JSON 文件
            self._save_data_to_new_format(grammar_path, vocab_path, text_path, dialogue_record_path, dialogue_history_path)
        else:
            # 目前新旧结构共用旧 JSON 导出
            self._save_data_old_structure(grammar_path, vocab_path, text_path, dialogue_record_path, dialogue_history_path)
    
    def _save_data_to_new_format(self, grammar_path: str, vocab_path: str, text_path: str, dialogue_record_path: str, dialogue_history_path: str):
        """保存数据为新结构格式"""
        try:
            # 生成新格式的文件路径
            new_grammar_path = grammar_path.replace('.json', '_new.json')
            new_vocab_path = vocab_path.replace('.json', '_new.json')
            new_text_path = text_path.replace('.json', '_new.json')
            
            print(f"🔄 保存新结构数据到: {new_grammar_path}, {new_vocab_path}, {new_text_path}")
            
            # 保存新结构数据
            self.grammar_manager.save_to_new_format(new_grammar_path)
            self.vocab_manager.save_to_new_format(new_vocab_path)
            self.text_manager.save_to_new_format(new_text_path)
            
            # 对话记录和历史仍使用旧格式（因为结构没有变化）
            self.dialogue_record.save_all_to_file(dialogue_record_path)
            self.dialogue_history.save_to_file(dialogue_history_path)
            
            print("✅ 新结构数据保存完成")
            
        except Exception as e:
            print(f"❌ 新结构数据保存失败: {e}")
            print("⚠️ 回退到旧格式保存")
            self._save_data_old_structure(grammar_path, vocab_path, text_path, dialogue_record_path, dialogue_history_path)

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
    
    def switch_to_new_structure(self) -> bool:
        """
        切换到新结构模式
        
        Returns:
            bool: 切换是否成功
        """
        try:
            if not self.use_new_structure:
                # 保存当前数据（旧结构）
                self._save_data_old_structure(
                    "data/grammar_rules.json",
                    "data/vocab_expressions.json", 
                    "data/original_texts.json",
                    "data/dialogue_record.json",
                    "data/dialogue_history.json"
                )
                # 切换为新结构的管理器
                self.grammar_manager = GrammarRuleManager(use_new_structure=True)
                self.vocab_manager = VocabManager(use_new_structure=True)
                self.text_manager = OriginalTextManager(use_new_structure=True)
                self.use_new_structure = True
                print("✅ 已成功切换到新数据结构模式")
                return True
        except Exception as e:
            print(f"❌ 切换到新结构失败: {e}")
            return False
        return False
    
    def switch_to_old_structure(self) -> bool:
        """
        切换回旧结构模式
        
        Returns:
            bool: 切换是否成功
        """
        try:
            if self.use_new_structure:
                # 保存当前数据
                self._save_data_new_structure(
                    "data/grammar_rules.json",
                    "data/vocab_expressions.json",
                    "data/original_texts.json", 
                    "data/dialogue_record.json",
                    "data/dialogue_history.json"
                )
                
                # 切换回旧结构
                self._init_old_structure()
                print("✅ 已成功切换回旧数据结构模式")
                return True
        except Exception as e:
            print(f"❌ 切换回旧结构失败: {e}")
            return False
        return False
    
    def get_structure_mode(self) -> str:
        """
        获取当前使用的数据结构模式
        
        Returns:
            str: "new" 或 "old"
        """
        return "new" if self.use_new_structure else "old"
    
    def get_save_mode(self) -> str:
        """
        获取当前的数据保存模式
        
        Returns:
            str: "new" 或 "old"
        """
        return "new" if self.save_to_new_data_class else "old"