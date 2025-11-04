import json
from typing import List, Dict
from dataclasses import asdict, dataclass
from backend.data_managers.data_classes import OriginalText, Sentence, GrammarRule, GrammarExample, GrammarBundle, VocabExpression, VocabExpressionExample
from backend.data_managers.original_text_manager import OriginalTextManager
import os
import chardet

# 导入新的数据结构类
try:
    from backend.data_managers.data_classes_new import GrammarRule as NewGrammarRule, GrammarExample as NewGrammarExample
    NEW_STRUCTURE_AVAILABLE = True
except ImportError:
    NEW_STRUCTURE_AVAILABLE = False
    print("⚠️ 新数据结构类不可用，将使用旧结构")

class GrammarRuleManager:
    def __init__(self, use_new_structure: bool = False):
        self.grammar_bundles: Dict[int,GrammarBundle] = {} # rule_id -> Bundle
        self.use_new_structure = use_new_structure and NEW_STRUCTURE_AVAILABLE
        
        if self.use_new_structure:
            print("✅ GrammarRuleManager: 已启用新数据结构模式")
        else:
            print("✅ GrammarRuleManager: 使用旧数据结构模式")

    def get_new_rule_id(self) -> int:
        """获取新的规则ID，使用连续分配策略"""
        if not self.grammar_bundles:
            return 1
        
        # 找到第一个可用的连续ID
        used_ids = set(self.grammar_bundles.keys())
        next_id = 1
        while next_id in used_ids:
            next_id += 1
        return next_id
    
    def add_new_rule(self, rule_name: str, rule_explanation: str) -> int:
        new_rule_id = self.get_new_rule_id()
        print(f"🆕 Adding new grammar rule: '{rule_name}' with ID: {new_rule_id}")
        print(f"📊 Current rule IDs: {sorted(self.grammar_bundles.keys())}")
        
        if self.use_new_structure:
            # 使用新结构创建规则
            new_rule = NewGrammarRule(
                rule_id=new_rule_id, 
                name=rule_name, 
                explanation=rule_explanation,
                source="qa",  # 新结构默认source为qa
                is_starred=False,  # 新结构默认is_starred为False
                examples=[]  # 新结构直接包含examples列表
            )
            # 新结构不需要Bundle包装
            self.grammar_bundles[new_rule_id] = new_rule
        else:
            # 使用旧结构创建规则
            new_rule = GrammarRule(rule_id=new_rule_id, name=rule_name, explanation=rule_explanation)
            self.grammar_bundles[new_rule_id] = GrammarBundle(rule=new_rule, examples=[])
        
        print(f"✅ Grammar rule added successfully. Total rules: {len(self.grammar_bundles)}")
        return new_rule_id
    
    def add_grammar_example(self, text_manager: OriginalTextManager, rule_id: int, text_id: int, sentence_id: int, explanation_context: str):
        if rule_id not in self.grammar_bundles:
            raise ValueError(f"Rule ID {rule_id} does not exist.")
        
        if self.use_new_structure:
            # 新结构：直接添加到规则的examples列表
            rule = self.grammar_bundles[rule_id]
            # 检查是否已存在
            for example in rule.examples:
                if example.text_id == text_id and example.sentence_id == sentence_id:
                    print(f"Example with text_id {text_id} and sentence_id {sentence_id} already exists for rule_id {rule_id}.")
                    return
            
            new_example = NewGrammarExample(
                rule_id=rule_id, 
                text_id=text_id, 
                sentence_id=sentence_id, 
                explanation_context=explanation_context
            )
            rule.examples.append(new_example)
        else:
            # 旧结构：使用Bundle包装
            for example in self.grammar_bundles[rule_id].examples:
                if example.text_id == text_id and example.sentence_id == sentence_id:
                    print(f"Example with text_id {text_id} and sentence_id {sentence_id} already exists for rule_id {rule_id}.")
                    return
            
            new_example = GrammarExample(rule_id=rule_id, text_id=text_id, sentence_id=sentence_id, explanation_context=explanation_context)
            self.grammar_bundles[rule_id].examples.append(new_example)
        
        text_manager.add_grammar_example_to_sentence(text_id, sentence_id, rule_id)
    
    def get_id_by_rule_name(self, rule_name: str) -> int:
        for rule_id, bundle in self.grammar_bundles.items():
            if self.use_new_structure:
                # 新结构：直接访问规则
                if bundle.name == rule_name:
                    return rule_id
            else:
                # 旧结构：通过Bundle访问规则
                if bundle.rule.name == rule_name:
                    return rule_id
        raise ValueError(f"Rule name '{rule_name}' does not exist.")

    def get_rule_by_id(self, rule_id: int) -> GrammarRule:
        if rule_id not in self.grammar_bundles:
            raise ValueError(f"Rule ID {rule_id} does not exist.")
        
        if self.use_new_structure:
            # 新结构：直接返回规则
            return self.grammar_bundles[rule_id]
        else:
            # 旧结构：通过Bundle返回规则
            return self.grammar_bundles[rule_id].rule

    def get_examples_by_rule_id(self, rule_id: int) -> List[GrammarExample]:
        if rule_id not in self.grammar_bundles:
            raise ValueError(f"Rule ID {rule_id} does not exist.")
        
        if self.use_new_structure:
            # 新结构：直接返回规则的examples
            return self.grammar_bundles[rule_id].examples
        else:
            # 旧结构：通过Bundle返回examples
            return self.grammar_bundles[rule_id].examples
    
    def get_example_by_text_sentence_id(self, text_id: int, sentence_id: int) -> GrammarExample:
        for bundle in self.grammar_bundles.values():
            if self.use_new_structure:
                # 新结构：直接遍历规则的examples
                for example in bundle.examples:
                    if example.text_id == text_id and example.sentence_id == sentence_id:
                        return example
            else:
                # 旧结构：通过Bundle遍历examples
                for example in bundle.examples:
                    if example.text_id == text_id and example.sentence_id == sentence_id:
                        return example
        return None
    
    def get_all_rules_name(self) -> List[str]:
        if self.use_new_structure:
            # 新结构：直接获取规则名称
            return [bundle.name for bundle in self.grammar_bundles.values()]
        else:
            # 旧结构：通过Bundle获取规则名称
            return [bundle.rule.name for bundle in self.grammar_bundles.values()]
    
    def get_all_rules_with_id(self) -> List[tuple]:
        """获取所有规则及其ID，按ID排序"""
        if self.use_new_structure:
            # 新结构：直接获取规则ID和名称
            return sorted([(rule_id, bundle.name) for rule_id, bundle in self.grammar_bundles.items()])
        else:
            # 旧结构：通过Bundle获取规则ID和名称
            return sorted([(rule_id, bundle.rule.name) for rule_id, bundle in self.grammar_bundles.items()])
    
    def print_rules_order(self):
        """打印所有规则的ID和名称，按ID排序"""
        rules_with_id = self.get_all_rules_with_id()
        print("📚 Grammar Rules (ordered by ID):")
        for rule_id, rule_name in rules_with_id:
            print(f"   ID {rule_id}: {rule_name}")
        print(f"📊 Total rules: {len(rules_with_id)}")
        
        # 检查ID连续性
        if rules_with_id:
            min_id = rules_with_id[0][0]
            max_id = rules_with_id[-1][0]
            expected_count = max_id - min_id + 1
            actual_count = len(rules_with_id)
            
            if actual_count < expected_count:
                print(f"⚠️  ID不连续！最小ID: {min_id}, 最大ID: {max_id}")
                print(f"   期望规则数: {expected_count}, 实际规则数: {actual_count}")
                print(f"   缺失的ID: {set(range(min_id, max_id + 1)) - set(rule_id for rule_id, _ in rules_with_id)}")
            else:
                print(f"✅ ID连续，从 {min_id} 到 {max_id}")
    
    def save_to_file(self, path: str):
        """
        保存数据到文件，始终使用旧JSON格式以确保兼容性
        """
        export_data = {}
        for rule_id, bundle in self.grammar_bundles.items():
            if self.use_new_structure:
                # 新结构：转换为旧格式进行保存
                rule = bundle
                bundle_data = {
                    'rule': {
                        'rule_id': rule.rule_id,
                        'name': rule.name,
                        'explanation': rule.explanation
                    },
                    'examples': [
                        {
                            'rule_id': ex.rule_id,
                            'text_id': ex.text_id,
                            'sentence_id': ex.sentence_id,
                            'explanation_context': ex.explanation_context
                        } for ex in rule.examples
                    ]
                }
            else:
                # 旧结构：直接使用asdict
                bundle_data = asdict(bundle)
            
            export_data[rule_id] = bundle_data
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=4)
    
    def save_to_new_format(self, path: str):
        """
        保存数据为新结构格式（数组格式，包含 source、is_starred 等新字段）
        """
        if not self.use_new_structure:
            print("⚠️ 当前未使用新结构，无法保存为新格式")
            return
            
        export_data = []
        for rule_id, rule in sorted(self.grammar_bundles.items()):
            # 新结构：保存为数组格式（更简洁）
            rule_data = {
                'rule_id': rule.rule_id,
                'rule_name': rule.name,  # 使用 rule_name 保持兼容性
                'rule_summary': rule.explanation,  # 使用 rule_summary 保持兼容性
                'examples': [
                    {
                        'rule_id': ex.rule_id,
                        'text_id': ex.text_id,
                        'sentence_id': ex.sentence_id,
                        'explanation_context': ex.explanation_context
                    } for ex in rule.examples
                ] if rule.examples else [],
                'source': getattr(rule, 'source', 'qa'),
                'is_starred': getattr(rule, 'is_starred', False)
            }
            export_data.append(rule_data)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 已保存 {len(export_data)} 个语法规则到文件（数组格式）: {path}")
    
    def load_from_file(self, path: str):
        """
        从文件加载数据，支持新旧两种结构
        """
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
        self.grammar_bundles = {}  # 清空当前状态
        
        try:
            # 支持两种格式：数组格式（简化）和字典格式（Bundle）
            if isinstance(data, list):
                # 数组格式：[{"rule_id": 1, "rule_name": "...", ...}, ...]
                items_to_process = [(item.get('rule_id'), item) for item in data]
            elif isinstance(data, dict):
                # 字典格式：{"1": {"rule": {...}, "examples": [...]}, ...}
                items_to_process = list(data.items())
            else:
                raise ValueError(f"Unexpected data format: {type(data)}")
            
            for rule_id, bundle_data in items_to_process:
                if self.use_new_structure:
                    # 新结构：直接创建规则对象
                    # 判断是数组格式还是Bundle格式
                    if 'rule' in bundle_data:
                        # Bundle格式：{"rule": {...}, "examples": [...]}
                        rule_data = bundle_data['rule']
                        examples_data = bundle_data.get('examples', [])
                    else:
                        # 数组格式：直接是规则数据（简化格式，用于Mock server）
                        rule_data = bundle_data
                        examples_data = bundle_data.get('examples', [])  # 从文件读取 examples
                    
                    rule = NewGrammarRule(
                        rule_id=rule_data['rule_id'],
                        name=rule_data.get('name') or rule_data.get('rule_name', ''),  # 兼容两种字段名
                        explanation=rule_data.get('explanation') or rule_data.get('rule_summary', ''),  # 兼容两种字段名
                        source=rule_data.get('source', 'qa'),  # 使用文件中的source，默认为qa
                        is_starred=rule_data.get('is_starred', False),  # 使用文件中的is_starred，默认为False
                        examples=[
                            NewGrammarExample(
                                rule_id=ex['rule_id'],
                                text_id=ex['text_id'],
                                sentence_id=ex['sentence_id'],
                                explanation_context=ex['explanation_context']
                            ) for ex in examples_data
                        ]
                    )
                    self.grammar_bundles[int(rule_id)] = rule
                else:
                    # 旧结构：使用Bundle包装
                    # 判断是数组格式还是Bundle格式
                    if 'rule' in bundle_data:
                        # Bundle格式
                        rule = GrammarRule(**bundle_data['rule'])
                        examples = [GrammarExample(**ex) for ex in bundle_data['examples']]
                    else:
                        # 数组格式：转换为Bundle格式
                        rule = GrammarRule(
                            rule_id=bundle_data['rule_id'],
                            name=bundle_data.get('rule_name', ''),  # 旧结构使用 name
                            explanation=bundle_data.get('rule_summary', '')  # 旧结构使用 explanation
                        )
                        # 从文件读取 examples
                        examples = [
                            GrammarExample(
                                rule_id=ex['rule_id'],
                                text_id=ex['text_id'],
                                sentence_id=ex['sentence_id'],
                                explanation_context=ex['explanation_context']
                            ) for ex in bundle_data.get('examples', [])
                        ]
                    self.grammar_bundles[int(rule_id)] = GrammarBundle(rule=rule, examples=examples)
            
            print(f"✅ 成功加载 {len(self.grammar_bundles)} 个语法规则")
            if self.use_new_structure:
                print("📝 使用新数据结构，包含examples列表、source=qa、is_starred=False")
            else:
                print("📝 使用旧数据结构")
                
        except Exception as e:
            print(f"[Error] Failed to load grammar rules: {e}")
            raise e
    
    def switch_to_new_structure(self) -> bool:
        """
        切换到新结构模式
        
        Returns:
            bool: 切换是否成功
        """
        if not NEW_STRUCTURE_AVAILABLE:
            print("❌ 新数据结构类不可用，无法切换")
            return False
            
        if self.use_new_structure:
            print("✅ 已经在使用新结构模式")
            return True
            
        try:
            # 重新加载所有数据到新结构
            self.use_new_structure = True
            print("✅ 已切换到新结构模式")
            return True
        except Exception as e:
            print(f"❌ 切换到新结构失败: {e}")
            self.use_new_structure = False
            return False
    
    def switch_to_old_structure(self) -> bool:
        """
        切换回旧结构模式
        
        Returns:
            bool: 切换是否成功
        """
        if not self.use_new_structure:
            print("✅ 已经在使用旧结构模式")
            return True
            
        try:
            # 重新加载所有数据到旧结构
            self.use_new_structure = False
            print("✅ 已切换回旧结构模式")
            return True
        except Exception as e:
            print(f"❌ 切换回旧结构失败: {e}")
            return False
    
    def get_structure_mode(self) -> str:
        """
        获取当前使用的数据结构模式
        
        Returns:
            str: "new" 或 "old"
        """
        return "new" if self.use_new_structure else "old"

    def get_grammar_example_by_location(self, text_id: int, sentence_id: int = None, token_index: int = None):
        """
        按层级查找语法例句：优先按 text_id 查找唯一结果，否则按 sentence_id，最后按 token_index
        
        Args:
            text_id: 文章ID（必需）
            sentence_id: 句子ID（可选）
            token_index: Token索引（可选）
            
        Returns:
            GrammarExample 或 None
        """
        matching_examples = []
        
        # 遍历所有语法规则的所有例句
        for rule_id, grammar_bundle in self.grammar_bundles.items():
            if self.use_new_structure:
                # 新结构：直接从 rule.examples 获取
                examples = grammar_bundle.examples if hasattr(grammar_bundle, 'examples') else []
            else:
                # 旧结构：从 bundle.example 获取
                examples = grammar_bundle.example if hasattr(grammar_bundle, 'example') else []
            
            for example in examples:
                # 首先检查 text_id 是否匹配
                if example.text_id == text_id:
                    # 如果只提供了 text_id，且这是该 text_id 的唯一例句，直接返回
                    if sentence_id is None and token_index is None:
                        matching_examples.append(example)
                    # 如果提供了 sentence_id，检查是否匹配
                    elif sentence_id is not None and example.sentence_id == sentence_id:
                        # 如果只提供了 sentence_id，且这是该 sentence_id 的唯一例句，直接返回
                        if token_index is None:
                            matching_examples.append(example)
                        # 语法例句通常不涉及具体 token，按 sentence_id 匹配即可
                        elif token_index is not None:
                            matching_examples.append(example)
        
        # 返回唯一结果
        if len(matching_examples) == 1:
            return matching_examples[0]
        elif len(matching_examples) > 1:
            print(f"⚠️ [GrammarRuleManager] 找到多个匹配的例句: {len(matching_examples)} 个")
            return matching_examples[0]  # 返回第一个
        else:
            print(f"🔍 [GrammarRuleManager] 未找到匹配的例句: text_id={text_id}, sentence_id={sentence_id}, token_index={token_index}")
            return None    
