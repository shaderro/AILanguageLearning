import json
from typing import List, Dict
from dataclasses import asdict, dataclass
from data_managers.data_classes import OriginalText, Sentence, GrammarRule, GrammarExample, GrammarBundle, VocabExpression, VocabExpressionExample
from data_managers.original_text_manager import OriginalTextManager
import os
import chardet

class GrammarRuleManager:
    def __init__(self):
        self.grammar_bundles: Dict[int,GrammarBundle] = {} # rule_id -> Bundle

    def get_new_rule_id(self) -> int:
        if not self.grammar_bundles:
            return 1
        return max(self.grammar_bundles.keys()) + 1
    
    def add_new_rule(self, rule_name: str, rule_explanation: str) -> int:
        new_rule_id = self.get_new_rule_id()
        new_rule = GrammarRule(rule_id=new_rule_id, name=rule_name, explanation=rule_explanation)
        self.grammar_bundles[new_rule_id] = GrammarBundle(rule=new_rule, examples=[])
        return new_rule_id
    
    def add_grammar_example(self, text_manager: OriginalTextManager, rule_id: int, text_id: int, sentence_id: int, explanation_context: str):
        if rule_id not in self.grammar_bundles:
            raise ValueError(f"Rule ID {rule_id} does not exist.")
        for example in self.grammar_bundles[rule_id].examples:
            if example.text_id == text_id and example.sentence_id == sentence_id:
                print(f"Example with text_id {text_id} and sentence_id {sentence_id} already exists for rule_id {rule_id}.")
                return
                # raise ValueError(f"Example with text_id {text_id} and sentence_id {sentence_id} already exists for rule_id {rule_id}.")
        new_example = GrammarExample(rule_id=rule_id, text_id=text_id, sentence_id=sentence_id, explanation_context=explanation_context)
        self.grammar_bundles[rule_id].examples.append(new_example)
        text_manager.add_grammar_example_to_sentence(text_id, sentence_id,rule_id)
    
    def get_id_by_rule_name(self, rule_name: str) -> int:
        for rule_id, bundle in self.grammar_bundles.items():
            if bundle.rule.name == rule_name:
                return rule_id
        raise ValueError(f"Rule name '{rule_name}' does not exist.")

    def get_rule_by_id(self, rule_id: int) -> GrammarRule:
        if rule_id not in self.grammar_bundles:
            raise ValueError(f"Rule ID {rule_id} does not exist.")
        return self.grammar_bundles[rule_id].rule

    def get_examples_by_rule_id(self, rule_id: int) -> List[GrammarExample]:
        if rule_id not in self.grammar_bundles:
            raise ValueError(f"Rule ID {rule_id} does not exist.")
        return self.grammar_bundles[rule_id].examples
    
    def get_example_by_text_sentence_id(self, text_id: int, sentence_id: int) -> GrammarExample:
        for bundle in self.grammar_bundles.values():
            for example in bundle.examples:
                if example.text_id == text_id and example.sentence_id == sentence_id:
                    return example
        return None
    
    def get_all_rules_name(self) -> List[str]:
        return [bundle.rule.name for bundle in self.grammar_bundles.values()]
    
    def save_to_file(self, path: str):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({rule_id: asdict(bundle) for rule_id, bundle in self.grammar_bundles.items()}, f, indent=4)
    
    def load_from_file(self, path: str):
            if not os.path.exists(path):
                raise FileNotFoundError(f"The file at path {path} does not exist.")
            if not os.path.isfile(path):
                raise ValueError(f"The path {path} is not a file.")

            with open(path, 'rb') as f:
                raw_data = f.read()

            detected = chardet.detect(raw_data)
            encoding = detected['encoding'] or 'utf-8'

            try:
                content = raw_data.decode(encoding).strip()
            except UnicodeDecodeError as e:
                print(f"❗️无法用 {encoding} 解码文件 {path}：{e}")
                raise e

            if not content:
                print(f"[Warning] File {path} is empty. Starting with empty record.")
                return

            data = json.loads(content)
            for rule_id, bundle_data in data.items():
                rule = GrammarRule(**bundle_data['rule'])
                examples = [GrammarExample(**ex) for ex in bundle_data['examples']]
                self.grammar_bundles[int(rule_id)] = GrammarBundle(rule=rule, examples=examples)    
