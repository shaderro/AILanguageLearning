import json
from typing import List, Dict
from dataclasses import asdict
from data_managers.data_classes import VocabExpression, VocabExpressionExample, VocabExpressionBundle
import os
import chardet
from data_managers.original_text_manager import OriginalTextManager

# 导入新的数据结构类
try:
    from data_managers.data_classes_new import VocabExpression as NewVocabExpression, VocabExpressionExample as NewVocabExpressionExample
    NEW_STRUCTURE_AVAILABLE = True
except ImportError:
    NEW_STRUCTURE_AVAILABLE = False
    print("⚠️ 新数据结构类不可用，将使用旧结构")

class VocabManager:
    def __init__(self, use_new_structure: bool = False):
        self.vocab_bundles: Dict[int, VocabExpressionBundle] = {}  # vocab_id -> Bundle
        self.use_new_structure = use_new_structure and NEW_STRUCTURE_AVAILABLE
        
        if self.use_new_structure:
            print("✅ VocabManager: 已启用新数据结构模式")
        else:
            print("✅ VocabManager: 使用旧数据结构模式")

    def get_new_vocab_id(self) -> int:
        if not self.vocab_bundles:
            return 1
        return max(self.vocab_bundles.keys()) + 1

    def add_new_vocab(self, vocab_body: str, explanation: str) -> int:
        new_vocab_id = self.get_new_vocab_id()
        
        if self.use_new_structure:
            # 使用新结构创建词汇
            new_vocab = NewVocabExpression(
                vocab_id=new_vocab_id, 
                vocab_body=vocab_body, 
                explanation=explanation,
                source="qa",  # 新结构默认source为qa
                is_starred=False,  # 新结构默认is_starred为False
                examples=[]  # 新结构直接包含examples列表
            )
            # 新结构不需要Bundle包装
            self.vocab_bundles[new_vocab_id] = new_vocab
        else:
            # 使用旧结构创建词汇
            new_vocab = VocabExpression(vocab_id=new_vocab_id, vocab_body=vocab_body, explanation=explanation)
            self.vocab_bundles[new_vocab_id] = VocabExpressionBundle(vocab=new_vocab, example=[])
        
        return new_vocab_id

    def add_vocab_example(self, text_manager: OriginalTextManager, vocab_id: int, text_id: int, sentence_id: int, context_explanation: str):
        if vocab_id not in self.vocab_bundles:
            raise ValueError(f"Vocab ID {vocab_id} does not exist.")
        
        if self.use_new_structure:
            # 新结构：直接添加到词汇的examples列表
            vocab = self.vocab_bundles[vocab_id]
            # 检查是否已存在
            for example in vocab.examples:
                if example.text_id == text_id and example.sentence_id == sentence_id and example.vocab_id == vocab_id:
                    print(f"Example for vocab_id {vocab_id}, text_id {text_id}, sentence_id {sentence_id} already exists.")
                    return
            
            new_example = NewVocabExpressionExample(
                vocab_id=vocab_id,
                text_id=text_id,
                sentence_id=sentence_id,
                context_explanation=context_explanation,
                token_indices=[]  # 新结构包含token_indices字段
            )
            vocab.examples.append(new_example)
        else:
            # 旧结构：使用Bundle包装
            for example in self.vocab_bundles[vocab_id].example:
                if example.text_id == text_id and example.sentence_id == sentence_id and example.vocab_id == vocab_id:
                    print(f"Example for vocab_id {vocab_id}, text_id {text_id}, sentence_id {sentence_id} already exists.")
                    return
            
            new_example = VocabExpressionExample(
                vocab_id=vocab_id,
                text_id=text_id,
                sentence_id=sentence_id,
                context_explanation=context_explanation
            )
            self.vocab_bundles[vocab_id].example.append(new_example)
        
        text_manager.add_vocab_example_to_sentence(text_id, sentence_id, vocab_id)
        
    def get_vocab_by_id(self, vocab_id: int) -> VocabExpression:
        if vocab_id not in self.vocab_bundles:
            raise ValueError(f"Vocab ID {vocab_id} does not exist.")
        
        if self.use_new_structure:
            # 新结构：直接返回词汇
            return self.vocab_bundles[vocab_id]
        else:
            # 旧结构：通过Bundle返回词汇
            return self.vocab_bundles[vocab_id].vocab

    def get_examples_by_vocab_id(self, vocab_id: int) -> List[VocabExpressionExample]:
        if vocab_id not in self.vocab_bundles:
            raise ValueError(f"Vocab ID {vocab_id} does not exist.")
        
        if self.use_new_structure:
            # 新结构：直接返回词汇的examples
            return self.vocab_bundles[vocab_id].examples
        else:
            # 旧结构：通过Bundle返回examples
            return self.vocab_bundles[vocab_id].example

    def get_example_by_text_sentence_id(self, text_id: int, sentence_id: int) -> VocabExpressionExample:
        for bundle in self.vocab_bundles.values():
            if self.use_new_structure:
                # 新结构：直接遍历词汇的examples
                for example in bundle.examples:
                    if example.text_id == text_id and example.sentence_id == sentence_id:
                        return example
            else:
                # 旧结构：通过Bundle遍历examples
                for example in bundle.example:
                    if example.text_id == text_id and example.sentence_id == sentence_id:
                        return example
        return None
    
    def get_id_by_vocab_body(self, vocab_body: str) -> int:
        for vocab_id, bundle in self.vocab_bundles.items():
            if self.use_new_structure:
                # 新结构：直接访问词汇
                if bundle.vocab_body == vocab_body:
                    return vocab_id
            else:
                # 旧结构：通过Bundle访问词汇
                if bundle.vocab.vocab_body == vocab_body:
                    return vocab_id
        raise ValueError(f"Vocab body '{vocab_body}' does not exist.")
    
    def get_all_vocab_body(self) -> List[str]:
        if self.use_new_structure:
            # 新结构：直接获取词汇体
            return [bundle.vocab_body for bundle in self.vocab_bundles.values()]
        else:
            # 旧结构：通过Bundle获取词汇体
            return [bundle.vocab.vocab_body for bundle in self.vocab_bundles.values()]

    def save_to_file(self, path: str):
        """
        保存数据到文件，始终使用旧JSON格式以确保兼容性
        """
        export_data = {}
        for vocab_id, bundle in self.vocab_bundles.items():
            if self.use_new_structure:
                # 新结构：转换为旧格式进行保存
                vocab = bundle
                bundle_data = {
                    'vocab': {
                        'vocab_id': vocab.vocab_id,
                        'vocab_body': vocab.vocab_body,
                        'explanation': vocab.explanation
                    },
                    'example': [
                        {
                            'vocab_id': ex.vocab_id,
                            'text_id': ex.text_id,
                            'sentence_id': ex.sentence_id,
                            'context_explanation': ex.context_explanation
                        } for ex in vocab.examples
                    ]
                }
            else:
                # 旧结构：直接使用asdict
                bundle_data = asdict(bundle)
            
            export_data[vocab_id] = bundle_data
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=4, ensure_ascii=False)
    
    def save_to_new_format(self, path: str):
        """
        保存数据为新结构格式（包含 source、is_starred、token_indices 等新字段）
        """
        if not self.use_new_structure:
            print("⚠️ 当前未使用新结构，无法保存为新格式")
            return
            
        export_data = {}
        for vocab_id, vocab in self.vocab_bundles.items():
            # 新结构：直接保存所有字段
            vocab_data = {
                'vocab_id': vocab.vocab_id,
                'vocab_body': vocab.vocab_body,
                'explanation': vocab.explanation,
                'source': getattr(vocab, 'source', 'qa'),
                'is_starred': getattr(vocab, 'is_starred', False),
                'examples': [
                    {
                        'vocab_id': ex.vocab_id,
                        'text_id': ex.text_id,
                        'sentence_id': ex.sentence_id,
                        'context_explanation': ex.context_explanation,
                        'token_indices': getattr(ex, 'token_indices', [])
                    } for ex in vocab.examples
                ]
            }
            export_data[vocab_id] = vocab_data
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=4, ensure_ascii=False)
        
        print(f"✅ 已保存 {len(export_data)} 个词汇表达到新格式文件: {path}")
    
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
        self.vocab_bundles = {}  # 清空当前状态
        
        try:
            for vocab_id, bundle_data in data.items():
                if self.use_new_structure:
                    # 新结构：直接创建词汇对象
                    vocab_data = bundle_data['vocab']
                    examples_data = bundle_data.get('example', [])
                    
                    vocab = NewVocabExpression(
                        vocab_id=vocab_data['vocab_id'],
                        vocab_body=vocab_data['vocab_body'],
                        explanation=vocab_data['explanation'],
                        source="qa",  # 默认值
                        is_starred=False,  # 默认值
                        examples=[
                            NewVocabExpressionExample(
                                vocab_id=ex['vocab_id'],
                                text_id=ex['text_id'],
                                sentence_id=ex['sentence_id'],
                                context_explanation=ex['context_explanation'],
                                token_indices=[]  # 默认空列表
                            ) for ex in examples_data
                        ]
                    )
                    self.vocab_bundles[int(vocab_id)] = vocab
                else:
                    # 旧结构：使用Bundle包装
                    vocab = VocabExpression(**bundle_data['vocab'])
                    examples = [VocabExpressionExample(**ex) for ex in bundle_data['example']]
                    self.vocab_bundles[int(vocab_id)] = VocabExpressionBundle(vocab=vocab, example=examples)
            
            print(f"✅ 成功加载 {len(self.vocab_bundles)} 个词汇表达")
            if self.use_new_structure:
                print("📝 使用新数据结构，包含examples列表、source=qa、is_starred=False")
            else:
                print("📝 使用旧数据结构")
                
        except Exception as e:
            print(f"[Error] Failed to load vocabulary expressions: {e}")
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
