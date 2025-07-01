from typing import Dict, List, Tuple, Optional
from data_managers.data_classes import Sentence
import json
import chardet
import os

class DialogueRecordBySentence:
    def __init__(self):
        self.records: Dict[Tuple[int, int], List[Dict[str, Optional[str]]]] = {}
        #Tuple[text_id, sentence_id], List[Dict[user question, Optional[ai response ]]]
        self.messages_history: List[Dict] = []
        self.max_turns: int = 100  # 默认保留最近100条消息

    def add_user_message(self, sentence: Sentence, user_input: str):
        key = (sentence.text_id, sentence.sentence_id)
        if key not in self.records:
            self.records[key] = []
        self.records[key].append({user_input: None})

    def add_ai_response(self, sentence: Sentence, ai_response: str):
        key = (sentence.text_id, sentence.sentence_id)
        if key in self.records and self.records[key]:
            # 补充到最近一条没有 AI 回复的记录中
            for turn in reversed(self.records[key]):
                for user_question, ai_response_old in turn.items():
                    if ai_response_old is None:
                        turn[user_question] = ai_response
                        return
        # 如果没有找到，就直接加一个完整条目
        self.records.setdefault(key, []).append({"[Missing user input]": ai_response})

    def get_records_by_sentence(self, sentence: Sentence) -> List[Dict[str, Optional[str]]]:
        return self.records.get((sentence.text_id, sentence.sentence_id), [])
    
    def to_dict_list(self) -> List[Dict]:
        result = []
        for (text_id, sentence_id), turns in self.records.items():
            for turn in turns:
                for user_question, ai_response in turn.items():
                    result.append({
                        "text_id": text_id,
                        "sentence_id": sentence_id,
                        "user_question": user_question,
                        "ai_response": ai_response,
                        "is_learning_related": True
                    })
        return result
    
    def save_all_to_file(self, path: str):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict_list(), f, ensure_ascii=False, indent=2)

    def save_filtered_to_file(self, path: str, only_learning_related: bool = True):
        filtered = [m for m in self.to_dict_list() if m["is_learning_related"] == only_learning_related]
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(filtered, f, ensure_ascii=False, indent=2)

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

        try:
            data = json.loads(content)
            if isinstance(data, list):
                self.records = {}
                for item in data:
                    text_id = item.get("text_id")
                    sentence_id = item.get("sentence_id")
                    if text_id is not None and sentence_id is not None:
                        key = (text_id, sentence_id)
                        if key not in self.records:
                            self.records[key] = []
                        self.records[key].append({
                            item.get("user_question", ""): item.get("ai_response", "")
                        })
            else:
                # 兼容其他格式，暂不处理
                pass
        except FileNotFoundError:
            print(f"[Warning] File not found: {path}. Starting with empty dialogue history.")
            self.records = {}
        except json.JSONDecodeError:
            print(f"[Error] Failed to parse JSON from '{path}'.")

    def print_records_by_sentence(self, sentence: Sentence):
        print(f"\n📚 对话记录 - 第 {sentence.text_id} 篇 第 {sentence.sentence_id} 句：{sentence.sentence_body}")
        for turn in self.get_records_by_sentence(sentence):
            for user_question, ai_response in turn.items():
                print(f"👤 User: {user_question}")
                print(f"🤖 AI: {ai_response or '(waiting...)'}\n")

