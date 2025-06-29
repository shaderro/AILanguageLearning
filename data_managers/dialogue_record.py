from typing import Dict, List, Tuple, Optional
from data_managers.data_classes import Sentence
import json

class DialogueRecordBySentence:
    def __init__(self):
        self.records: Dict[Tuple[int, int], List[Dict[str, Optional[str]]]] = {}

    def add_user_message(self, sentence: Sentence, user_input: str):
        key = (sentence.text_id, sentence.sentence_id)
        if key not in self.records:
            self.records[key] = []
        self.records[key].append({"user": user_input, "ai": None})

    def add_ai_response(self, sentence: Sentence, ai_response: str):
        key = (sentence.text_id, sentence.sentence_id)
        if key in self.records and self.records[key]:
            # 补充到最近一条没有 AI 回复的记录中
            for turn in reversed(self.records[key]):
                if turn["ai"] is None:
                    turn["ai"] = ai_response
                    return
        # 如果没有找到，就直接加一个完整条目
        self.records.setdefault(key, []).append({"user": "[Missing user input]", "ai": ai_response})

    def get_records_by_sentence(self, sentence: Sentence) -> List[Dict[str, Optional[str]]]:
        return self.records.get((sentence.text_id, sentence.sentence_id), [])
    
    def save_all_to_file(self, path: str):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict_list(), f, ensure_ascii=False, indent=2)

    def save_filtered_to_file(self, path: str, only_learning_related: bool = True):
        filtered = [m for m in self.to_dict_list() if m["is_learning_related"] == only_learning_related]
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(filtered, f, ensure_ascii=False, indent=2)

    def load_from_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    print(f"[Warning] File {path} is empty. Starting with empty record.")
                    return
                data = json.loads(content)
            self.summary = data.get("summary", "")
            loaded_messages = []
            for item in data.get("messages", []):
                quote_data = item.get("quote", {})
                quote = Sentence(
                    text_id=quote_data.get("text_id"),
                    sentence_id=quote_data.get("sentence_id"),
                    sentence_body=quote_data.get("sentence_body"),
                    grammar_annotations=quote_data.get("grammar_annotations", []),
                    vocab_annotations=quote_data.get("vocab_annotations", [])
                )

                loaded_messages.append({
                    "user": item.get("user", ""),
                    "ai": item.get("ai", ""),
                    "quote": quote
                })
            # 只保留最近 max_turns 条消息
            self.messages_history = loaded_messages[-self.max_turns:]
        except FileNotFoundError:
            print(f"[Warning] File not found: {path}. Starting with empty dialogue history.")
            self.messages_history = []
            self.summary = ""

    def print_records_by_sentence(self, sentence: Sentence):
        print(f"\n📚 对话记录 - 第 {sentence.text_id} 篇 第 {sentence.sentence_id} 句：{sentence.sentence_body}")
        for turn in self.get_records_by_sentence(sentence):
            print(f"👤 User: {turn['user']}")
            print(f"🤖 AI: {turn['ai'] or '(waiting...)'}\n")

