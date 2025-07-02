from data_managers.data_classes import Sentence
from assistants.sub_assistants.summarize_dialogue_history import SummarizeDialogueHistoryAssistant
import json
import chardet

class DialogueHistory:
    def __init__(self, max_turns):
        self.max_turns = max_turns
        self.messages_history = []
        self.summary = str()
        self.summarize_dialogue_assistant = SummarizeDialogueHistoryAssistant()

    def add_message(self, user_input: str, ai_response: str, quoted_sentence: Sentence):
        self.messages_history.append({
            "user": user_input,
            "ai": ai_response,
            "quote": quoted_sentence
        })
        self.keep_in_max_turns()

    def _summarize_and_clear(self):
        summary = self.summarize_dialogue_history()
        self.summary = summary
        self.messages_history.clear()
        pass

    def message_history_to_string(self) -> str:
        return "\n".join(
            f"User: {msg['user']}\nAI: {msg['ai']}\nQuote: {msg['quote'].sentence_body}"
            for msg in self.messages_history
        )
    
    def summarize_dialogue_history(self) -> str:
        dialogue_history_str = self.message_history_to_string()
        if not dialogue_history_str:
            return "No dialogue history to summarize."
        print("Summarizing dialogue history...")
        quoted_sentence = self.messages_history[-1]['quote'].sentence_body if self.messages_history else ""
        print("Quoted sentence for summary:", quoted_sentence)
        summary = self.summarize_dialogue_assistant.run(dialogue_history_str, self.messages_history[-1]['quote'], verbose=True)
        if isinstance(summary, str):
            print("Summary is: \n" + summary)
            return summary
        elif isinstance(summary, list) and summary:
            return summary[0].get("summary", "No summary available.")
        else:
            return "No summary available."

    def keep_in_max_turns(self):
        self._summarize_and_clear() if len(self.messages_history) > self.max_turns else None

    def save_to_file(self, path: str):
        # 按text_id组织数据
        organized_data = {"texts": {}}
        
        for msg in self.messages_history:
            text_id = str(msg["quote"].text_id)
            sentence_id = msg["quote"].sentence_id
            
            # 初始化text结构
            if text_id not in organized_data["texts"]:
                organized_data["texts"][text_id] = {
                    "text_title": f"Text {text_id}",  # 可以从text_manager获取真实标题
                    "current_summary": self.summary,
                    "messages": [],
                    "max_turns": self.max_turns
                }
            
            # 添加消息
            organized_data["texts"][text_id]["messages"].append({
                "user": msg["user"],
                "ai": msg["ai"],
                "sentence_id": sentence_id,
                "quote": {
                    "text_id": msg["quote"].text_id,
                    "sentence_id": msg["quote"].sentence_id,
                    "sentence_body": msg["quote"].sentence_body,
                    "grammar_annotations": msg["quote"].grammar_annotations,
                    "vocab_annotations": msg["quote"].vocab_annotations,
                },
                "timestamp": "2024-01-01T10:00:00Z"  # 可以添加真实时间戳
            })
        
        # 如果没有消息，保存空结构
        if not organized_data["texts"]:
            organized_data = {
                "summary": self.summary,
                "messages": []
            }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(organized_data, f, ensure_ascii=False, indent=2)

    def load_from_file(self, path: str):
        import os
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
        self.messages_history = []
        
        # 处理新的组织格式
        if isinstance(data, dict) and "texts" in data:
            for text_id_str, text_data in data["texts"].items():
                self.summary = text_data.get("current_summary", "")
                for msg in text_data.get("messages", []):
                    self.messages_history.append({
                        "user": msg["user"],
                        "ai": msg["ai"],
                        "quote": Sentence(
                            text_id=msg["quote"]["text_id"],
                            sentence_id=msg["quote"]["sentence_id"],
                            sentence_body=msg["quote"]["sentence_body"],
                            grammar_annotations=msg["quote"]["grammar_annotations"],
                            vocab_annotations=msg["quote"]["vocab_annotations"]
                        )
                    })
        
        # 兼容旧的格式
        elif isinstance(data, dict) and "messages" in data:
            self.summary = data.get("summary", "")
            self.messages_history = [
                {
                    "user": item["user"],
                    "ai": item["ai"],
                    "quote": Sentence(
                        text_id=item["quote"]["text_id"],
                        sentence_id=item["quote"]["sentence_id"],
                        sentence_body=item["quote"]["sentence_body"],
                        grammar_annotations=item["quote"]["grammar_annotations"],
                        vocab_annotations=item["quote"]["vocab_annotations"]
                    )
                }
                for item in data.get("messages", [])
            ]
        else:
            print(f"[Warning] Unknown data format in {path}. Starting with empty history.")
            self.summary = ""
            self.messages_history = []

