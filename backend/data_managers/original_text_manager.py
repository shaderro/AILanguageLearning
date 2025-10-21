import json
import os
import chardet  
from typing import List, Dict
from dataclasses import asdict, dataclass
from data_managers.data_classes import OriginalText, Sentence, GrammarRule, GrammarExample, GrammarBundle, VocabExpression, VocabExpressionExample

# 导入新的数据结构类
try:
    from data_managers.data_classes_new import Sentence as NewSentence, OriginalText as NewOriginalText
    NEW_STRUCTURE_AVAILABLE = True
except ImportError:
    NEW_STRUCTURE_AVAILABLE = False
    print("⚠️ 新数据结构类不可用，将使用旧结构")


class OriginalTextManager:
    """
    A manager class for handling operations related to OriginalText objects.
    Methods:
        get_new_text_id() -> int:
            Generate a new unique text ID. If no texts exist, returns 1.
        add_text(text: OriginalText):
            Add a new OriginalText object to the manager. Raises ValueError if the text_id already exists.
        add_sentence_to_text(text_id: int, sentence: str):
            Add a sentence to an existing text by its text_id. Raises ValueError if the text_id does not exist.
        create_text_from_string(text_body: str, text_id: int) -> OriginalText:
            Create an OriginalText object from a string, splitting it into sentences.
        get_text(text_id: int) -> OriginalText:
            Retrieve an OriginalText object by its text_id. Returns None if not found.
        remove_text(text_id: int):
            Remove an OriginalText object by its text_id.
        list_texts() -> List[OriginalText]:
            List all OriginalText objects managed by this class.
        save_to_file(path: str):
            Save all OriginalText objects to a file in JSON format.
        load_from_file(path: str):
            Load OriginalText objects from a JSON file and populate the manager.
    """
    def __init__(self, use_new_structure: bool = False):
        self.original_texts: Dict[int, OriginalText] = {} # text_id -> OriginalText
        self.use_new_structure = use_new_structure and NEW_STRUCTURE_AVAILABLE
        
        if self.use_new_structure:
            print("✅ OriginalTextManager: 已启用新数据结构模式")
        else:
            print("✅ OriginalTextManager: 使用旧数据结构模式")

#Generate a new unique text ID. If no texts exist, returns 1.
    def get_new_text_id(self) -> int:
        if not self.original_texts:
            return 1
        return max(self.original_texts.keys()) + 1

    def add_text(self, text_title: str):
        text_id = self.get_new_text_id()
        if self.use_new_structure:
            # 使用新结构创建文本
            text = NewOriginalText(text_id=text_id, text_title=text_title, text_by_sentence=[])
        else:
            # 使用旧结构创建文本
            text = OriginalText(text_id=text_id, text_title=text_title, text_by_sentence=[])
        self.original_texts[text_id] = text

    def get_next_sentence_id(self, text_id: int) -> int:
        text = self.original_texts[text_id]
        return len(text.text_by_sentence)+1

    def add_sentence_to_text(self, text_id: int, sentence_text: str):
        if text_id not in self.original_texts:
            raise ValueError(f"text_id {text_id} does not exist.")
        current_text = self.original_texts[text_id]
        current_sentence_id = self.get_next_sentence_id(text_id)
        
        if self.use_new_structure:
            # 使用新结构创建句子，tokens先留空
            new_sentence = NewSentence(
                text_id=text_id, 
                sentence_id=current_sentence_id,
                sentence_body=sentence_text, 
                grammar_annotations=[], 
                vocab_annotations=[],
                sentence_difficulty_level=None,  # 暂时不设置难度
                tokens=None  # tokens先留空，先不分词
            )
        else:
            # 使用旧结构创建句子
            new_sentence = Sentence(
                text_id=text_id, 
                sentence_id=current_sentence_id,
                sentence_body=sentence_text, 
                grammar_annotations=(), 
                vocab_annotations=()
            )
        
        current_text.text_by_sentence.append(new_sentence)


    def get_text_by_id(self, text_id: int) -> OriginalText | None:
        return self.original_texts.get(text_id)
    
    def get_text(self, text_id: int) -> OriginalText | None:
        """兼容性方法，与get_text_by_id相同"""
        return self.original_texts.get(text_id)
    
    def get_text_by_title(self, text_title: str) -> OriginalText | None:
        for text in self.original_texts.values():
            if text.text_title == text_title:
                return text
        return None
    
    def get_sentence_by_id(self, text_id: int, sentence_id: int) -> Sentence | None:
        """根据text_id和sentence_id获取句子"""
        text = self.original_texts.get(text_id)
        if not text:
            return None
        
        for sentence in text.text_by_sentence:
            if sentence.sentence_id == sentence_id:
                return sentence
        
        return None

    def remove_text_by_id(self, text_id: int):
        if text_id in self.original_texts:
            del self.original_texts[text_id]
    
    def remove_text_by_title(self, text_title: str): 
        for text_id, text in list(self.original_texts.items()):
            if text.text_title == text_title:
                del self.original_texts[text_id]
                break

    def list_texts_by_title(self) -> List[OriginalText]:
        return sorted(self.original_texts.values(), key=lambda x: x.text_title)
    
    def list_titles(self) -> List[str]:
            return sorted([text.text_title for text in self.original_texts.values()])
    
    def save_to_file(self, path: str):
        """
        保存数据到文件，始终使用旧JSON格式以确保兼容性
        """
        # 转换为旧格式进行保存
        export_data = {}
        for tid, text in self.original_texts.items():
            # 提取旧格式的数据结构
            text_data = {
                'text_id': text.text_id,
                'text_title': text.text_title,
                'text_by_sentence': []
            }
            
            for sentence in text.text_by_sentence:
                # 提取句子的基本信息，忽略新字段
                sentence_data = {
                    'text_id': sentence.text_id,
                    'sentence_id': sentence.sentence_id,
                    'sentence_body': sentence.sentence_body,
                    'grammar_annotations': sentence.grammar_annotations or [],
                    'vocab_annotations': sentence.vocab_annotations or []
                }
                text_data['text_by_sentence'].append(sentence_data)
            
            export_data[tid] = text_data
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    def save_to_new_format(self, path: str):
        """
        保存数据为新结构格式（数组格式，包含 sentence_difficulty_level、tokens 等新字段）
        """
        if not self.use_new_structure:
            print("⚠️ 当前未使用新结构，无法保存为新格式")
            return
            
        export_data = []
        for tid, text in sorted(self.original_texts.items()):
            # 新结构：保存为数组格式（更简洁）
            text_data = {
                'text_id': text.text_id,
                'text_title': text.text_title,
                'text_by_sentence': []
            }
            
            for sentence in text.text_by_sentence:
                sentence_data = {
                    'text_id': sentence.text_id,
                    'sentence_id': sentence.sentence_id,
                    'sentence_body': sentence.sentence_body,
                    'grammar_annotations': sentence.grammar_annotations or [],
                    'vocab_annotations': sentence.vocab_annotations or []
                }
                
                # 只在有值时才添加这些字段，保持文件简洁
                if hasattr(sentence, 'sentence_difficulty_level') and sentence.sentence_difficulty_level is not None:
                    sentence_data['sentence_difficulty_level'] = sentence.sentence_difficulty_level
                
                if hasattr(sentence, 'tokens') and sentence.tokens is not None:
                    sentence_data['tokens'] = sentence.tokens
                
                text_data['text_by_sentence'].append(sentence_data)
            
            export_data.append(text_data)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 已保存 {len(export_data)} 个文本到文件（数组格式）: {path}")

    def add_grammar_example_to_sentence(self, text_id: int, sentence_id: int, rule_id: int):
        text = self.original_texts.get(text_id)
        if not text:
            raise ValueError(f"Text ID {text_id} does not exist.")
        sentence = next((s for s in text.text_by_sentence if s.sentence_id == sentence_id), None)
        if not sentence:
            raise ValueError(f"Sentence ID {sentence_id} does not exist in Text ID {text_id}.")
        sentence.grammar_annotations.append(rule_id)

    def add_vocab_example_to_sentence(self, text_id: int, sentence_id: int, vocab_id: int):
        text = self.original_texts.get(text_id)
        if not text:
            raise ValueError(f"Text ID {text_id} does not exist.")
        sentence = next((s for s in text.text_by_sentence if s.sentence_id == sentence_id), None)
        if not sentence:
            raise ValueError(f"Sentence ID {sentence_id} does not exist in Text ID {text_id}.")
        sentence.vocab_annotations.append(vocab_id)

    def export_text_as_plaintext(self, text_id: int) -> str:
        text = self.original_texts.get(text_id)
        if not text:
            return ""
        return "\n".join([s.sentence_body for s in text.text_by_sentence])

    def load_from_file(self, path: str):
        """
        从文件加载数据，使用新的Sentence类（包含tokens字段），但tokens先留空
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
        self.original_texts = {}  # 清空当前状态
        
        try:
            # 支持两种格式：数组格式和字典格式
            if isinstance(data, list):
                # 数组格式：[{"text_id": 1, "text_title": "...", ...}, ...]
                items_to_process = [(item.get('text_id'), item) for item in data]
            elif isinstance(data, dict):
                # 字典格式：{"1": {"text_id": 1, ...}, ...}
                items_to_process = list(data.items())
            else:
                raise ValueError(f"Unexpected data format: {type(data)}")
            
            for tid, text_data in items_to_process:
                if self.use_new_structure:
                    # 使用新结构加载，tokens先留空
                    text = NewOriginalText(
                        text_id=text_data['text_id'],
                        text_title=text_data['text_title'],
                        text_by_sentence=[
                            NewSentence(
                                text_id=sentence['text_id'],
                                sentence_id=sentence['sentence_id'],
                                sentence_body=sentence['sentence_body'],
                                grammar_annotations=sentence.get('grammar_annotations', []),
                                vocab_annotations=sentence.get('vocab_annotations', []),
                                sentence_difficulty_level=None,  # 暂时不设置难度
                                tokens=None  # tokens先留空，先不分词
                            ) for sentence in text_data['text_by_sentence']
                        ]
                    )
                else:
                    # 使用旧结构加载
                    text = OriginalText(
                        text_id=text_data['text_id'],
                        text_title=text_data['text_title'],
                        text_by_sentence=[
                            Sentence(
                                text_id=sentence['text_id'],
                                sentence_id=sentence['sentence_id'],
                                sentence_body=sentence['sentence_body'],
                                grammar_annotations=tuple(sentence.get('grammar_annotations', [])),
                                vocab_annotations=tuple(sentence.get('vocab_annotations', []))
                            ) for sentence in text_data['text_by_sentence']
                        ]
                    )
                self.original_texts[int(tid)] = text
                
            print(f"✅ 成功加载 {len(self.original_texts)} 个文本文件")
            if self.use_new_structure:
                print("📝 使用新数据结构，tokens字段已预留但暂未分词")
            else:
                print("📝 使用旧数据结构")
                
        except FileNotFoundError:
            print(f"[Warning] File '{path}' not found. No texts loaded.")
        except json.JSONDecodeError:
            print(f"[Error] Failed to parse JSON from '{path}'.")
        except Exception as e:
            print(f"[Error] Unexpected error during loading: {e}")
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
    
    #优化：save and load，不需要每次都重写全部，而是查找有没有修改