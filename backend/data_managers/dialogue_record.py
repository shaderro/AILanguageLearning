from typing import Dict, List, Tuple, Optional, Union
from backend.data_managers.data_classes import Sentence
from backend.data_managers.data_classes_new import Sentence as NewSentence
from backend.assistants.chat_info.selected_token import SelectedToken
import json
import chardet
import os

# 类型别名，支持新旧两种句子类型
SentenceType = Union[Sentence, NewSentence]

class DialogueRecordBySentence:
    def __init__(self):
        self.records: Dict[Tuple[int, int], List[Dict[str, Optional[str]]]] = {}
        #Tuple[text_id, sentence_id], List[Dict[user question, Optional[ai response ]]]
        self.messages_history: List[Dict] = []
        self.max_turns: int = 100  # 默认保留最近100条消息

    def add_user_message(self, sentence: SentenceType, user_input: str, selected_token: Optional[SelectedToken] = None):
        key = (sentence.text_id, sentence.sentence_id)
        if key not in self.records:
            self.records[key] = []
        
        # 创建消息记录，包含selected_token信息
        message_record = {
            "user_input": user_input,
            "ai_response": None,
            "selected_token": selected_token.to_dict() if selected_token else None
        }
        
        self.records[key].append(message_record)

    def add_ai_response(self, sentence: SentenceType, ai_response: str):
        key = (sentence.text_id, sentence.sentence_id)
        if key in self.records and self.records[key]:
            # 补充到最近一条没有 AI 回复的记录中
            for turn in reversed(self.records[key]):
                if isinstance(turn, dict) and turn.get("ai_response") is None:
                    turn["ai_response"] = ai_response
                    return
        # 如果没有找到，就直接加一个完整条目
        self.records.setdefault(key, []).append({
            "user_input": "[Missing user input]",
            "ai_response": ai_response,
            "selected_token": None
        })

    def get_records_by_sentence(self, sentence: SentenceType) -> List[Dict[str, Optional[str]]]:
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
    
    def to_organized_dict(self) -> Dict:
        """转换为按text_id和sentence_id组织的字典格式"""
        organized = {"texts": {}}
        
        for (text_id, sentence_id), turns in self.records.items():
            text_id_str = str(text_id)
            sentence_id_str = str(sentence_id)
            
            # 初始化text结构
            if text_id_str not in organized["texts"]:
                organized["texts"][text_id_str] = {
                    "text_title": f"Text {text_id}",  # 可以从text_manager获取真实标题
                    "sentences": {}
                }
            
            # 初始化sentence结构
            if sentence_id_str not in organized["texts"][text_id_str]["sentences"]:
                organized["texts"][text_id_str]["sentences"][sentence_id_str] = []
            
            # 添加对话记录
            for turn in turns:
                for user_question, ai_response in turn.items():
                    organized["texts"][text_id_str]["sentences"][sentence_id_str].append({
                        "user_question": user_question,
                        "ai_response": ai_response,
                        "timestamp": "2024-01-01T10:00:00Z",  # 可以添加真实时间戳
                        "is_learning_related": True
                    })
        
        return organized
    
    def save_all_to_file(self, path: str):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_organized_dict(), f, ensure_ascii=False, indent=2)

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
            self.records = {}
            
            # 处理新的组织格式
            if isinstance(data, dict) and "texts" in data:
                for text_id_str, text_data in data["texts"].items():
                    text_id = int(text_id_str)
                    for sentence_id_str, sentence_dialogues in text_data.get("sentences", {}).items():
                        sentence_id = int(sentence_id_str)
                        key = (text_id, sentence_id)
                        if key not in self.records:
                            self.records[key] = []
                        
                        for dialogue in sentence_dialogues:
                            self.records[key].append({
                                dialogue.get("user_question", ""): dialogue.get("ai_response", "")
                            })
            
            # 兼容旧的列表格式
            elif isinstance(data, list):
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
                print(f"[Warning] Unknown data format in {path}. Starting with empty record.")
                
        except FileNotFoundError:
            print(f"[Warning] File not found: {path}. Starting with empty dialogue history.")
            self.records = {}
        except json.JSONDecodeError:
            print(f"[Error] Failed to parse JSON from '{path}'.")

    def print_records_by_sentence(self, sentence: SentenceType):
        print(f"\n📚 对话记录 - 第 {sentence.text_id} 篇 第 {sentence.sentence_id} 句：{sentence.sentence_body}")
        for turn in self.get_records_by_sentence(sentence):
            for user_question, ai_response in turn.items():
                print(f"👤 User: {user_question}")
                print(f"🤖 AI: {ai_response or '(waiting...)'}\n")

