import json
import os
import chardet  
from typing import List, Dict
from dataclasses import asdict, dataclass
from data_managers.data_classes import OriginalText, Sentence, GrammarRule, GrammarExample, GrammarBundle, VocabExpression, VocabExpressionExample


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
    def __init__(self):
        self.original_texts: Dict[int, OriginalText] = {} # text_id -> OriginalText

#Generate a new unique text ID. If no texts exist, returns 1.
    def get_new_text_id(self) -> int:
        if not self.original_texts:
            return 1
        return max(self.original_texts.keys()) + 1

    def add_text(self, text_title: str):
        text_id = self.get_new_text_id()
        text = OriginalText(text_id=text_id, text_title=text_title, text_by_sentence=[])
        self.original_texts[text_id] = text

    def get_next_sentence_id(self, text_id: int) -> int:
        text = self.original_texts[text_id]
        return len(text.text_by_sentence)+1

    def add_sentence_to_text(self, text_id: int, input_sentence: str):
        if text_id not in self.original_texts:
            raise ValueError(f"text_id {text_id} does not exist.")
        current_text = self.original_texts[text_id]
        current_sentence_id = self.get_next_sentence_id(text_id)
        # Create a new Sentence object
        input_sentence = Sentence(text_id=text_id, sentence_id=current_sentence_id,
                      sentence_body=input_sentence, grammar_annotations=[], vocab_annotations=[])
        
        current_text.text_by_sentence.append(input_sentence)


    def get_text_by_id(self, text_id: int) -> OriginalText:
        return self.original_texts.get(text_id)
    
    def get_text_by_title(self, text_title: str) -> OriginalText:
        for text in self.original_texts.values():
            if text.text_title == text_title:
                return text
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
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(
                {tid: asdict(text) for tid, text in self.original_texts.items()},
                f, ensure_ascii=False, indent=2
            )
    
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
                    for tid, text_data in data.items():
                        text = OriginalText(
                            text_id=text_data['text_id'],
                            text_title=text_data['text_title'],
                            text_by_sentence=[
                                Sentence(
                                    text_id=sentence['text_id'],
                                    sentence_id=sentence['sentence_id'],
                                    sentence_body=sentence['sentence_body'],
                                    grammar_annotations=sentence['grammar_annotations'],
                                    vocab_annotations=sentence['vocab_annotations']
                                ) for sentence in text_data['text_by_sentence']
                            ]
                        )
                        self.original_texts[int(tid)] = text
                except FileNotFoundError:
                    print(f"[Warning] File '{path}' not found. No texts loaded.")
                except json.JSONDecodeError:
                    print(f"[Error] Failed to parse JSON from '{path}'.")
    
    #优化：save and load，不需要每次都重写全部，而是查找有没有修改